"""Compile independently reviewed cards, then optionally apply the staged records.

Usage: python3 tools/cards/admit.py cards.json [...] [--apply]
The envelope must contain semantic_reviews keyed by gates.digest_card(card).
Old supervisor verdicts and quotation-match flags alone never authorize writes.
Explicit ``extends`` cards append reviewed events to an existing ID and require
review of the target. Existing facts and research status remain intact.
Optional --concepts/--concept-map retain the existing curated-concept interface.
"""
import argparse
import collections
import copy
import datetime
import json
import re
import sys
import unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(HERE))
import dataset as ds
from fetch_page import norm, source_snapshot
from gates import (claim_supported, dataset_snapshot, digest_card, exact_quote,
                   link_supported, locate_span, valid_source, validate_review)


def slug(value, maxwords=None):
    value = value.replace('Ø', 'O').replace('ø', 'o').replace('ʻ', '').replace('’', '').replace("'", '').replace('æ', 'ae').replace('ß', 'ss').replace('ł', 'l').replace('đ', 'd')
    value = ''.join(c for c in unicodedata.normalize('NFKD', value) if not unicodedata.combining(c)).lower()
    words = re.sub(r'[^a-z0-9]+', ' ', value).split()
    return '-'.join(words[:maxwords] if maxwords else words)


def source_id(source):
    from gates import digest
    return slug(source['title'], 5) + '-' + digest(source.get('url'))[:16]


def locate(text, quote):
    span = locate_span(text, quote)
    return span[0] if span else None


def event_signature(event):
    """Repeated historical event excludes IDs, citation formatting and review prose."""
    date = event.get('date') or {}
    return json.dumps({'type': event.get('type'), 'statement': norm(event.get('statement', '')),
                       'date': {key: date.get(key) for key in ('earliest', 'latest', 'status', 'precision')}},
                      sort_keys=True, separators=(',', ':'))


def merge_extension(original, addition):
    """Append reviewed information without changing preexisting facts or status."""
    merged = copy.deepcopy(original)
    merged.setdefault('events', []).extend(addition['events'])
    research = merged.setdefault('research', {'status': 'draft', 'basis': {}})
    basis = research.setdefault('basis', {})
    if not original.get('events'):
        basis['events'] = 'reviewed'
    for facet in ('summary', 'why', 'origin', 'advance', 'prompted_by', 'known_from', 'fate', 'concept', 'places', 'people'):
        if facet not in addition:
            continue
        if facet not in merged or merged[facet] in (None, [], {}):
            merged[facet] = copy.deepcopy(addition[facet])
            if facet in addition['research']['basis']:
                basis[facet] = addition['research']['basis'][facet]
        elif isinstance(merged[facet], list) and isinstance(addition[facet], list):
            merged[facet].extend(copy.deepcopy(value) for value in addition[facet] if value not in merged[facet])
    old_note = research.get('note')
    research['note'] = (old_note + '\n' if old_note else '') + addition['research']['note']
    for question in addition['research'].get('unresolved', []):
        if question not in research.get('unresolved', []):
            research.setdefault('unresolved', []).append(copy.deepcopy(question))
    # Move the bounded event anchor only when a newly reviewed event is earlier.
    old_anchor = next((event for event in original.get('events', [])
                       if event['id'] == (original.get('earliest_record') or {}).get('event')), None)
    candidate = min(addition['events'], key=lambda event: event['date']['latest']['year'])
    if old_anchor is None or candidate['date']['latest']['year'] < old_anchor['date']['latest']['year']:
        merged['earliest_record'] = {'event': candidate['id'], 'rationale':
            'New reviewed evidence gives an earlier supported event for this community record; no claim of global priority.'}
    return merged


class SourceRows(dict):
    def __init__(self):
        super().__init__()
        self.expected_content = {}
        self.reviewed_quotes = {}


def compile_cards(envelopes, data, snapshot, concepts=None, concept_map=None):
    """Build records in memory; no requests or filesystem mutations occur here."""
    concepts, concept_map = concepts or {}, concept_map or {}
    vocab = {key: set(value['values']) for key, value in data.vocab.items()}
    records, sources, new_concepts = {}, SourceRows(), {}
    report, problems = collections.Counter(), []
    existing = {slug(row['name']): row['id'] for row in data.discoveries.values()}
    pending_links = {}
    today = datetime.date.today().isoformat()
    for envelope in envelopes:
        for card in envelope.get('cards', []):
            if card.get('verdict') not in ('accept', 'accept_with_changes'):
                report['rejected'] += 1
                continue
            review = (envelope.get('semantic_reviews') or {}).get(digest_card(card))
            errors = validate_review(card, review, snapshot)
            if errors:
                report['semantic gate blocked'] += 1
                problems.append(f"{card.get('name', '?')}: {'; '.join(errors)}")
                continue
            supported = lambda path: claim_supported(card, review, path)
            try:
                extension = card.get('extends')
                original = None
                if extension:
                    if extension not in data.discoveries:
                        raise ValueError('extension target is not an existing discovery ID')
                    if extension in records:
                        raise ValueError('one extension per target per staged batch; combine reviewed cards first')
                    original = data.discoveries[extension]
                name = original['name'] if original else card['name'].strip()
                rid = extension if original else slug(name)
                if not original and (rid in data.discoveries or rid in records or slug(name) in existing):
                    report['duplicate'] += 1
                    continue
                field = original['domain'] if original else card['field']
                kind = original['kind'] if original else card['kind']
                if field not in data.fields or kind not in vocab['kind']:
                    raise ValueError('invalid field or kind')
                srcs = card.get('sources') or []
                sids = []
                staged_sources = {}
                for source in srcs:
                    sid = next((key for key, row in data.sources.items()
                                if row.get('url') == source.get('url')), source_id(source))
                    sids.append(sid)
                    if sid in sources:
                        staged_sources[sid] = copy.deepcopy(sources[sid])
                    elif sid in data.sources:
                        staged_sources[sid] = copy.deepcopy(data.sources[sid])
                        staged_sources[sid].setdefault('passages', [])
                    else:
                        staged_sources[sid] = {
                            'id': sid, 'title': source['title'],
                            'authors': [a for a in source.get('authors', []) if a] or [source.get('publisher') or 'Unknown'],
                            'year': source.get('year') if type(source.get('year')) is int else None,
                            'url': source.get('url'), 'access': 'full-text', 'accessed': today,
                            'passages': []}
                events, event_ids = [], {}
                occupied = {event['id'] for event in original.get('events', [])} if original else set()
                previous_events = {event_signature(event) for event in original.get('events', [])} if original else set()
                repeated_events = 0
                reviewed_quotes = {}
                for i, event in enumerate(card.get('events') or []):
                    index = event.get('source')
                    if (not valid_source(index, srcs) or not supported(f'events.{i}.statement')
                            or not supported(f'events.{i}.date')
                            or event.get('type') not in vocab['event']):
                        continue
                    # Statement/date review must refer to the source cited by this event.
                    claims = review['claims']
                    if any(index not in claims[f'events.{i}.{part}']['sources'] for part in ('statement', 'date')):
                        continue
                    page = source_snapshot(srcs[index]['url'])
                    if not exact_quote(page.get('text', ''), event.get('quote', '')):
                        continue
                    latest, earliest = event.get('latest_year'), event.get('earliest_year')
                    if type(latest) is not int or latest == 0:
                        continue
                    if earliest is not None and (type(earliest) is not int or earliest == 0 or earliest > latest):
                        raise ValueError('invalid reviewed event date range')
                    if event.get('status') not in vocab['date_status'] or event.get('precision') not in vocab['date_precision']:
                        raise ValueError('reviewed date must retain explicit status and precision')
                    base = f"{event['type'].replace('_', '-')}-{i + 1}"
                    eid = base
                    suffix = 2
                    while eid in occupied:
                        eid = f'{base}-{suffix}'
                        suffix += 1
                    record = {'id': eid, 'type': event['type'],
                              'date': {'earliest': {'year': earliest} if earliest is not None else None,
                                       'latest': {'year': latest}, 'status': event['status'],
                                       'precision': event['precision'], 'label': event.get('label') or str(latest),
                                       'basis': claims[f'events.{i}.date']['rationale']},
                              'statement': event['statement'],
                              'evidence': [{'source': sids[index], 'supports': event['quote']}]}
                    if event.get('locator'):
                        record['evidence'][0]['locator'] = event['locator']
                    signature = event_signature(record)
                    if signature in previous_events:
                        repeated_events += 1
                        continue
                    previous_events.add(signature)
                    occupied.add(eid)
                    event_ids[i] = eid
                    events.append(record)
                    reviewed_quotes.setdefault(sids[index], set()).add(event['quote'])
                    if sids[index] in staged_sources:
                        staged_sources[sids[index]]['passages'].append({'quote': event['quote'], **({'locator': event['locator']} if event.get('locator') else {})})
                if not events:
                    if original and repeated_events:
                        report['extension unchanged'] += 1
                        continue
                    raise ValueError('no usable reviewed event')
                anchor = min(events, key=lambda event: event['date']['latest']['year'])
                record = {'id': rid, 'name': name, 'description': original['description'] if original else card['description'],
                          'kind': kind, 'domain': field, 'events': events,
                          'earliest_record': {'event': anchor['id'], 'rationale':
                              'Earliest supported event in this reviewed card; no claim of global priority.'}}
                basis = {'domain': 'reviewed', 'events': 'reviewed'}
                # Optional facets appear only after their own semantic acceptance.
                for facet in ('summary', 'why', 'origin'):
                    if card.get(facet) and supported(facet):
                        if facet == 'origin' and card[facet] not in vocab['origin']:
                            continue
                        record[facet] = card[facet]
                        if facet != 'why':
                            basis[facet] = 'reviewed'
                for facet in ('advance', 'prompted_by', 'known_from'):
                    if card.get(facet) and supported(facet):
                        values = [value for value in card[facet] if value in vocab[facet]]
                        if values:
                            record[facet], basis[facet] = values, 'reviewed'
                if record.get('why') and 'prompted_by' not in record:
                    record.pop('why')
                if card.get('fate') in vocab['fate'] and supported('fate'):
                    record['fate'], basis['fate'] = card['fate'], 'reviewed'
                concept = concept_map.get(card.get('concept'), card.get('concept'))
                if concept and supported('concept') and (concept in data.registers['concepts'] or concept in concepts):
                    record['concept'], basis['concept'] = concept, 'reviewed'
                    if concept not in data.registers['concepts']:
                        candidate = concepts[concept]
                        # Curated definitions need their own review; the card's concept assignment cannot attest them.
                        if supported('concept_definition'):
                            new_concepts[concept] = {key: candidate[key] for key in ('id', 'name', 'summary', 'field') if candidate.get(key)}
                        else:
                            record.pop('concept'); basis.pop('concept')
                # Reuse registered places/people only. New register facts need a separate reviewed import.
                for facet, register, target in (('places', 'places', 'place'), ('people', 'people', 'person')):
                    rows = []
                    for i, item in enumerate(card.get(facet) or []):
                        match = next((key for key, value in data.registers[register].items()
                                      if slug(value['name']) == slug(item.get('name', ''))), None)
                        if not match or not supported(f'{facet}.{i}'):
                            continue
                        row = {target: match}
                        if facet == 'people':
                            if item.get('role') not in vocab['person_role']:
                                continue
                            row['role'] = item['role']
                        rows.append(row)
                    if rows:
                        record[facet], basis[facet] = rows, 'reviewed'
                # The status covers only retained, independently reviewed claims.
                record['research'] = {'status': 'sourced', 'basis': basis,
                                      'note': 'Independent semantic review ' + str(review['reviewer']['id']) +
                                              '; card ' + digest_card(card) + '; evidence ' + review['evidence_digest'] +
                                              '; dataset ' + snapshot + '.'}
                questions = [value for value in card.get('open_questions', []) if isinstance(value, str) and value.strip()]
                if questions:
                    record['research']['unresolved'] = [{'about': 'open question', 'note': value} for value in questions]
                if original:
                    record = merge_extension(original, record)
                records[rid] = record
                for sid, quotes in reviewed_quotes.items():
                    sources.reviewed_quotes.setdefault(sid, set()).update(quotes)
                for sid, row in staged_sources.items():
                    sources.expected_content[sid] = source_snapshot(row['url']).get('content_sha256')
                sources.update(staged_sources)
                pending_links[rid] = (card, review, sids)
                report['extended' if original else 'accepted'] += 1
            except (KeyError, TypeError, ValueError) as error:
                report['error'] += 1
                problems.append(f"{card.get('name', '?')}: {error}")
    names = dict(existing, **{slug(row['name']): rid for rid, row in records.items()})
    for rid, (card, review, sids) in pending_links.items():
        old_links = copy.deepcopy(records[rid].get('links', []))
        links = []
        for i, link in enumerate(card.get('links') or []):
            target = names.get(slug(link.get('to', '')))
            if (not target or target == rid or link.get('type') not in vocab['link']
                    or not link_supported(card, review, i)):
                report['unsupported link omitted'] += 1
                continue
            if any(old.get('type') == link['type'] and old.get('from') == target for old in old_links + links):
                report['existing link preserved'] += 1
                continue
            links.append({'type': link['type'], 'from': target, 'status': 'established',
                          'statement': link['statement'], 'evidence': [
                              {'source': sids[link['source']], 'supports': link['quote']}]})
            sources.reviewed_quotes.setdefault(sids[link['source']], set()).add(link['quote'])
            if sids[link['source']] in sources:
                sources[sids[link['source']]]['passages'].append({'quote': link['quote']})
        if links:
            records[rid]['links'] = old_links + links
            if not old_links:
                records[rid]['research']['basis']['links'] = 'reviewed'
    return records, sources, new_concepts, report, problems


def apply_records(records, sources, concepts, data, root=ROOT, *, queue=None, lease=None):
    """Preflight every saved excerpt before the first dataset write. No fetching here."""
    if queue is None or lease is None:
        raise ValueError('apply requires the global workflow integrator lease')
    queue.check_integrator(lease)
    staged_data = copy.deepcopy(data)
    staged_data.discoveries.update(records)
    staged_data.sources.update(sources)
    staged_data.registers['concepts'].update(concepts)
    staged_data.paths.update({'discoveries/' + key: ds.discovery_path(row) for key, row in records.items()})
    staged_data.paths.update({'sources/' + key: ds.source_path(key) for key in sources})
    validation = staged_data.validate(check_files=False)
    if validation:
        raise ValueError('staged dataset invalid: ' + '; '.join(validation[:10]))
    used = {evidence['source'] for record in records.values()
            for item in record['events'] + record.get('links', []) for evidence in item.get('evidence', [])}
    staged = []
    for sid, source in sources.items():
        if sid not in used or not sources.reviewed_quotes.get(sid):
            continue
        saved = source_snapshot(source['url'])
        if saved.get('content_sha256') != getattr(sources, 'expected_content', {}).get(sid):
            raise ValueError('saved source version changed since review: ' + sid)
        text = saved.get('text', '')
        excerpts = []
        cited_quotes = sources.reviewed_quotes[sid]
        for quote in cited_quotes:
            span = locate_span(text, quote)
            if span is None:
                raise ValueError('saved source changed or complete quotation missing: ' + sid)
            excerpts.append(text[max(0, span[0] - 500):span[1] + 500].strip())
        if not excerpts:
            raise ValueError('no saved source context: ' + sid)
        body = (f"Excerpts from: {source['title']}\nAddress: {source['url']}\n"
                f"Saved: {datetime.date.today().isoformat()}\n\n" + '\n\n----\n\n'.join(excerpts) + '\n')
        relative = f'evidence/{sid[0]}/{sid}.txt'
        previous = source.get('file') or {}
        if previous:
            old_path = (Path(root) / previous.get('path', '')).resolve()
            if not old_path.is_relative_to(Path(root).resolve()) or not old_path.is_file():
                raise ValueError('existing saved evidence unavailable: ' + sid)
            if ds.sha256(old_path) != previous.get('sha256'):
                raise ValueError('existing saved evidence hash changed: ' + sid)
            if old_path.suffix != '.txt' or previous.get('representation') != 'excerpt':
                raise ValueError('preserve existing full/binary source through a separate reviewed source version: ' + sid)
            body = old_path.read_text(encoding='utf-8') + '\n\nAdditional reviewed passages:\n\n' + body
        staged.append((sid, source, relative, body))
    for sid, source, relative, body in staged:
        queue.check_integrator(lease)
        path = Path(root) / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding='utf-8')
        source['file'] = {'path': relative, 'sha256': ds.sha256(path),
                          'representation': 'excerpt', 'method': 'Complete normalized quotation with surrounding source context.'}
        ds.write_json(ds.source_path(sid), source)
    for record in records.values():
        queue.check_integrator(lease)
        ds.write_json(ds.discovery_path(record), record)
    if concepts:
        queue.check_integrator(lease)
        ds.write_jsonl(ds.DATA / 'concepts.jsonl', list(data.registers['concepts'].values()) + list(concepts.values()))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('files', nargs='+')
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--concepts')
    parser.add_argument('--concept-map')
    parser.add_argument('--queue', help='private workflow SQLite database for the single integrator')
    parser.add_argument('--owner', help='explicit integration lease owner')
    args = parser.parse_args(argv)
    if args.apply and (not args.queue or not args.owner):
        parser.error('--apply requires --queue and --owner for the single integrator')
    load = lambda path: json.loads(Path(path).read_text()) if path else {}
    data = ds.Dataset.load()
    snapshot = dataset_snapshot(ROOT)
    envelopes = [load(path) for path in args.files]
    records, sources, concepts, report, problems = compile_cards(
        envelopes, data, snapshot, load(args.concepts), load(args.concept_map))
    print(dict(report))
    for problem in problems[:40]:
        print('  ' + problem)
    if args.apply:
        from workflow import Queue
        queue = Queue(args.queue)
        lease = queue.claim_integrator(args.owner)
        if lease is None:
            raise SystemExit('apply blocked: another integrator owns the workflow lease')
        try:
            queue.check_integrator(lease)
            if dataset_snapshot(ROOT) != snapshot:
                raise SystemExit('dataset advanced; reviews require a fresh snapshot')
            for envelope in envelopes:
                for card in envelope.get('cards', []):
                    if card.get('verdict') in ('accept', 'accept_with_changes'):
                        errors = validate_review(card, (envelope.get('semantic_reviews') or {}).get(digest_card(card)), snapshot)
                        if errors:
                            raise SystemExit('apply blocked: evidence/review changed: ' + '; '.join(errors))
            if problems:
                raise SystemExit('apply blocked: resolve all semantic/compilation errors first')
            apply_records(records, sources, concepts, data, queue=queue, lease=lease)
            print('written', len(records))
        finally:
            try:
                queue.release_integrator(lease)
            except ValueError:
                pass  # Expired/replaced owners must never release a newer integrator's lock.
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
