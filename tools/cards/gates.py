"""Mechanical admission gates. Passage presence is never a semantic judgment.

A cards envelope may contain ``semantic_reviews`` keyed by ``digest_card(card)``.
Each review has schema_version=1, card_digest, evidence_digest, dataset_snapshot,
reviewer={id, independent: true}, extractor_id, decision='accept', and ``claims``.
A claim is keyed by card JSON path and has decision='accept', sources=[indices],
and rationale (a nonempty explanation). Link claims also require relation,
direction and context booleans, all true. Contested/priority/independence claims
require two distinct independent source groups and independent_support=true.
An extension uses card.extends (exact existing record ID) and an accepted
``extends`` claim instead of repeating identity/core claims; all bindings and
event/source requirements still apply. These are explicit reviewer attestations,
not conclusions made by this code.
"""
import hashlib
import html
import json
import re
import unicodedata
from pathlib import Path

from fetch_page import norm, source_snapshot


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                    separators=(',', ':')).encode()).hexdigest()


def digest_card(card):
    # A review cannot be embedded in its own input digest.
    return digest({key: value for key, value in card.items() if key != 'semantic_review'})


def dataset_snapshot(root):
    root = Path(root)
    return digest([(str(path.relative_to(root)), hashlib.sha256(path.read_bytes()).hexdigest())
                   for path in sorted((root / 'data').rglob('*')) if path.is_file()])


def card_evidence(card):
    rows = []
    for i, source in enumerate(card.get('sources') or []):
        saved = source_snapshot(source.get('url', ''))
        rows.append({'source': i, 'url': source.get('url'), 'status': saved.get('status'),
                     'content_sha256': saved.get('content_sha256')})
    return rows


def evidence_digest(card):
    return digest(card_evidence(card))


def meaningful_quote(quote):
    words = norm(quote).split()
    return len(words) >= 8 and len(' '.join(words)) >= 40


def exact_quote(text, quote):
    return meaningful_quote(quote) and (' ' + norm(quote) + ' ') in (' ' + norm(text) + ' ')


def locate_span(text, quote):
    """Map a complete normalized quotation back to original character offsets."""
    if not meaningful_quote(quote):
        return None
    chars, offsets = [], []
    # Decode entities while keeping their original extent, then normalize as norm() does.
    for match in re.finditer(r'&(?:#\d+|#x[0-9a-fA-F]+|[a-zA-Z][a-zA-Z0-9]+);|.', text, re.S):
        piece = unicodedata.normalize('NFKD', html.unescape(match.group()))
        for char in piece:
            if unicodedata.combining(char):
                continue
            for char in char.lower():
                char = char if char.isascii() and char.isalnum() else ' '
                if char == ' ' and (not chars or chars[-1] == ' '):
                    continue
                chars.append(char)
                offsets.append((match.start(), match.end()))
    normalized = ''.join(chars)
    needle = norm(quote)
    found = (' ' + normalized + ' ').find(' ' + needle + ' ')
    if found < 0:
        return None
    return offsets[found][0], offsets[found + len(needle) - 1][1]


def valid_source(index, sources):
    return type(index) is int and 0 <= index < len(sources)


def claim_supported(card, review, path):
    claims = review.get('claims') or {}
    if not isinstance(claims, dict):
        return False
    claim = claims.get(path, {})
    if not isinstance(claim, dict):
        return False
    sources = card.get('sources') or []
    refs = claim.get('sources') or []
    if (claim.get('decision') != 'accept' or not isinstance(claim.get('rationale'), str)
            or not claim['rationale'].strip() or not isinstance(refs, list) or not refs
            or any(not valid_source(i, sources) for i in refs)):
        return False
    if any(source_snapshot(sources[i].get('url', '')).get('status') != 'fetched' for i in refs):
        return False
    # Sources must actually be cited by a preserved event or link, not unattached bibliography.
    cited = {item.get('source') for item in (card.get('events') or []) + (card.get('links') or [])
             if valid_source(item.get('source'), sources)
             and exact_quote(source_snapshot(sources[item['source']].get('url', '')).get('text', ''), item.get('quote', ''))}
    if not set(refs) <= cited:
        return False
    # Conservative lexical flags supplement, but cannot replace, the reader's risk assessment.
    value = card
    try:
        for part in path.split('.'):
            value = value[int(part)] if isinstance(value, list) else value[part]
    except (KeyError, IndexError, TypeError, ValueError):
        value = ''
    priority_language = path != 'extends' and isinstance(value, str) and bool(re.search(
        r'\b(first(?:[ -]known)?|earliest|independent(?:ly)?|priority|contested)\b', value, re.I))
    risky = (priority_language or card.get('contested') is True or claim.get('contested') is True or claim.get('priority') is True
             or claim.get('independence') is True
             or (path == 'origin' and card.get('origin') in ('first_known', 'independent'))
             or (path.startswith('links.') and
                 card.get('links', [])[int(path.split('.')[1])].get('type') == 'independent_of'))
    if risky:
        groups = claim.get('independent_source_groups') or {}
        values = [groups.get(str(i)) for i in set(refs)] if isinstance(groups, dict) else []
        if (claim.get('independent_support') is not True or len(set(refs)) < 2
                or len({sources[i].get('url') for i in refs}) < 2
                or any(not isinstance(v, str) or not v.strip() for v in values)
                or len(set(values)) < 2):
            return False
    return True


def _validate_review(card, review, snapshot):
    errors = []
    if not isinstance(review, dict):
        return ['missing independent semantic review']
    for key, expected in (('schema_version', 1), ('card_digest', digest_card(card)),
                          ('evidence_digest', evidence_digest(card)), ('dataset_snapshot', snapshot),
                          ('decision', 'accept')):
        if review.get(key) != expected:
            errors.append('missing or stale ' + key)
    reviewer = review.get('reviewer') or {}
    if (not isinstance(reviewer, dict) or reviewer.get('independent') is not True
            or not reviewer.get('id') or not review.get('extractor_id')
            or reviewer.get('id') == review.get('extractor_id')):
        errors.append('review must be independent of extractor')
    required = ('extends',) if 'extends' in card else ('name', 'description', 'kind', 'field')
    if 'extends' in card and (not isinstance(card['extends'], str) or not card['extends'].strip()):
        errors.append('extension requires an explicit existing discovery ID')
    for path in required:
        if not claim_supported(card, review, path):
            errors.append('unsupported required claim ' + path)
    sources = card.get('sources') or []
    usable = False
    for i, event in enumerate(card.get('events') or []):
        index = event.get('source')
        if not valid_source(index, sources):
            errors.append('invalid event source index ' + str(i))
            continue
        page = source_snapshot(sources[index].get('url', '')).get('text', '')
        if (exact_quote(page, event.get('quote', ''))
                and claim_supported(card, review, f'events.{i}.statement')
                and claim_supported(card, review, f'events.{i}.date')):
            usable = True
    for i, link in enumerate(card.get('links') or []):
        if not valid_source(link.get('source'), sources):
            errors.append('invalid link source index ' + str(i))
    if not usable:
        errors.append('no event with exact passage and accepted statement/date claims')
    return errors


def link_supported(card, review, index):
    link = card['links'][index]
    claim = (review.get('claims') or {}).get(f'links.{index}', {})
    sources = card.get('sources') or []
    source = link.get('source')
    return (valid_source(source, sources) and claim_supported(card, review, f'links.{index}')
            and source in claim.get('sources', [])
            and all(claim.get(key) is True for key in ('relation', 'direction', 'context'))
            and exact_quote(source_snapshot(sources[source].get('url', '')).get('text', ''), link.get('quote', '')))


def validate_review(card, review, snapshot):
    try:
        return _validate_review(card, review, snapshot)
    except (AttributeError, KeyError, IndexError, TypeError, ValueError):
        return ['malformed semantic artifact or card']
