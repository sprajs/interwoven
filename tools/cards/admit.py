"""Turn supervised research cards into records, sources, places and people.

    python3 tools/cards/admit.py verified.json [...]            # report what would be admitted
    python3 tools/cards/admit.py verified.json [...] --apply    # write it
    python3 tools/cards/admit.py verified.json --concepts curated.json --concept-map map.json --apply

Only cards with the verdict "accept" or "accept_with_changes" are admitted. Run
tools/cards/check_quotes.py on the same files first: an event whose quotation was found on its page
is admitted as checked, with the passage saved under evidence/, and any other event carries a
caveat. A record whose every quotation was found is marked sourced; otherwise it is a draft.

--concepts names a JSON object of concept records (id, name, summary, field) that cards may use
before they exist in the register. --concept-map names a JSON object that renames a card's concept
to one already in the register. docs/research-agents/ describes the cards.
"""
import collections, datetime, json, re, sys, unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(HERE))
import dataset as ds

def option(name):
    return json.loads(Path(sys.argv[sys.argv.index(name) + 1]).read_text()) if name in sys.argv else {}

APPLY = '--apply' in sys.argv
OPTIONS = {sys.argv[i + 1] for i, a in enumerate(sys.argv[:-1]) if a in ('--concepts', '--concept-map')}
FILES = [a for a in sys.argv[1:] if not a.startswith('--') and a not in OPTIONS]
TODAY = datetime.date.today().isoformat()
data = ds.Dataset.load()
V = {k: set(v['values']) for k, v in data.vocab.items()}
FIELDS = set(data.fields)
CHECKS = ROOT / '.cache' / 'quote-checks.json'
checks = json.loads(CHECKS.read_text()) if CHECKS.exists() else {}
curated_concepts = option('--concepts')
CONCEPT_MAP = option('--concept-map')
report = collections.Counter()
problems = []

def slug(s, maxwords=None):
    s = s.replace('Ø', 'O').replace('ø', 'o').replace('ʻ', '').replace('’', '').replace("'", '').replace('æ', 'ae').replace('ß', 'ss').replace('ł', 'l').replace('đ', 'd')
    s = unicodedata.normalize('NFKD', s)
    s = ''.join(c for c in s if not unicodedata.combining(c)).lower()
    words = re.sub(r'[^a-z0-9]+', ' ', s).split()
    return '-'.join(words[:maxwords] if maxwords else words)

STOP = set('a an the of on in and for to with by from at as its their this that into de la le des du der die das und el los las von van di da del e y et en new'.split())
def source_id(src):
    author = (src.get('authors') or [src.get('publisher') or 'anon'])[0] or 'anon'
    words = re.sub(r'\(.*?\)', '', author).split()
    key = slug(words[-1]) if 1 <= len(words) <= 3 and not re.search(r'(?i)museum|university|society|institut|press|editor|staff|britannica|unesco|smithsonian|library|nasa|national|department|magazine|news', author) else slug(' '.join(w for w in words if w.lower() not in STOP), 3)
    year = src.get('year')
    title = [w for w in slug(src['title']).split('-') if w not in STOP and not w.isdigit()][:3]
    base = '-'.join(x for x in [key or 'anon', str(year) if isinstance(year, int) else 'nd', *title] if x)
    return base

place_by_name = {}
for p in data.registers['places'].values():
    place_by_name[slug(p['name'])] = p['id']
    for a in p.get('aliases', []): place_by_name.setdefault(slug(a), p['id'])
new_places, new_people, new_societies, new_concepts, new_sources, new_records = {}, {}, {}, {}, {}, {}
existing_names = {slug(r['name']): r['id'] for r in data.discoveries.values()}

def place_id(p, card_places):
    key = slug(p['name'])
    if key in place_by_name: return place_by_name[key]
    pid = key
    if pid in data.registers['places'] or pid in new_places: pid = f"{key}-{slug(p.get('within') or p.get('country') or 'place')}"
    kind = p.get('kind') if p.get('kind') in V['place_kind'] else 'area'
    region = p.get('region') if p.get('region') in V['world_region'] else None
    if region is None or not isinstance(p.get('lat'), (int, float)) or not isinstance(p.get('lon'), (int, float)):
        return None
    rec = {'id': pid, 'name': p['name'], 'kind': kind, 'lat': round(float(p['lat']), 2), 'lon': round(float(p['lon']), 2),
           'country': p.get('country') if isinstance(p.get('country'), str) and re.fullmatch('[A-Z]{2}', p.get('country') or '') else None,
           'region': region, 'within': None, 'basis': 'recalled'}
    w = p.get('within')
    if w and slug(w) in place_by_name and place_by_name[slug(w)] != pid: rec['within'] = place_by_name[slug(w)]
    new_places[pid] = rec; place_by_name[key] = pid
    return pid

def point(year):
    return {'year': int(year)}

for path in FILES:
    for card in json.load(open(path)).get('cards', []):
        if card.get('verdict') not in ('accept', 'accept_with_changes'):
            report['rejected'] += 1; continue
        try:
            name = card['name'].strip()
            rid = slug(name)
            if rid in data.discoveries or rid in new_records or slug(name) in existing_names:
                report['duplicate'] += 1; problems.append(f'duplicate: {name}'); continue
            field = card['field']
            assert field in FIELDS, f'field {field}'
            assert card['kind'] in V['kind']
            srcs = card.get('sources') or []
            sids = []
            for s in srcs:
                base = source_id(s); sid = base; i = 2
                while (sid in data.sources or sid in new_sources) and (new_sources.get(sid, data.sources.get(sid, {})).get('url') != s.get('url')):
                    sid = f'{base}-{i}'; i += 1
                if sid not in data.sources and sid not in new_sources:
                    rec = {'id': sid, 'title': s['title'], 'authors': [a for a in (s.get('authors') or []) if a] or [s.get('publisher') or 'Unknown'],
                           'year': s.get('year') if isinstance(s.get('year'), int) else None, 'url': s.get('url')}
                    if s.get('publisher'): rec['version'] = s['publisher']
                    rec['access'] = s.get('access') if s.get('access') in V['access'] else 'partial-text'
                    rec['accessed'] = TODAY
                    rec['passages'] = []
                    new_sources[sid] = rec
                sids.append(sid)
            cplaces = card.get('places') or []
            pids = {}
            for p in cplaces:
                pid = place_id(p, cplaces)
                if pid: pids[p['name']] = pid
            events = []; used = set(); all_verified = True
            for e in card.get('events') or []:
                if e.get('type') not in V['event'] or not isinstance(e.get('source'), int) or e['source'] >= len(sids) or not e.get('quote'): continue
                ly = e.get('latest_year'); ey = e.get('earliest_year')
                if not isinstance(ly, int) or ly == 0: continue
                if isinstance(ey, int) and (ey == 0 or ey > ly): ey = None
                status = e.get('status') if e.get('status') in V['date_status'] else 'approximate'
                precision = e.get('precision') if e.get('precision') in V['date_precision'] else 'year'
                base = f"{e['type'].replace('_', '-')}-{abs(ly)}{'bce' if ly < 0 else ''}"; eid = base; i = 2
                while eid in used: eid = f'{base}-{i}'; i += 1
                used.add(eid)
                check = checks.get(srcs[e['source']]['url'] + ' || ' + e['quote'], 'unchecked')
                if e.get('checked') == 'tool' and check not in ('exact', 'near'): check = 'tool'
                report[f'quote {check}'] += 1
                if check not in ('exact', 'near'): all_verified = False
                ev = {'id': eid, 'type': e['type'],
                      'date': {'earliest': point(ey) if isinstance(ey, int) else None, 'latest': point(ly), 'precision': precision, 'status': status,
                               'label': e.get('label') or str(ly), 'basis': 'As the cited source gives it.'},
                      'statement': e['statement']}
                if e.get('place') in pids: ev['places'] = [pids[e['place']]]
                evid = {'source': sids[e['source']], 'supports': e['quote']}
                if e.get('locator'): evid['locator'] = e['locator']
                ev['evidence'] = [evid]
                if check in ('exact', 'near'):
                    new_sources.get(sids[e['source']], {}).get('passages', []).append({k: v for k, v in (('locator', e.get('locator')), ('quote', e['quote'])) if v})
                else:
                    ev['caveats'] = 'The quotation was read by the researcher and the supervisor in their own tools. It has not been re-checked against the page by machine.' if check in ('unreachable', 'unchecked', 'tool') else 'The quotation was not found on the cited page when re-checked. Verify before relying on this event.'
                events.append((e, ev))
            if not events:
                report['no usable event'] += 1; problems.append(f'no event: {name}'); continue
            events.sort(key=lambda x: x[1]['date']['latest']['year'])
            er = card.get('earliest_record')
            orig = card.get('events') or []
            anchor = next((ev for e, ev in events if isinstance(er, int) and er < len(orig) and e is orig[er]), events[0][1])
            anchor = min((ev for _, ev in events), key=lambda ev: ev['date']['latest']['year']) if anchor['date']['latest']['year'] > min(ev['date']['latest']['year'] for _, ev in events) else anchor
            imp = card.get('impact') or {}
            impact = {k: int(imp[k]) for k in ('reach', 'depth', 'generativity')}
            assert all(0 <= v <= 3 for v in impact.values())
            if imp.get('note'): impact['note'] = imp['note']
            basis = {'summary': 'sourced', 'domain': 'sourced', 'tier': 'recalled', 'impact': 'recalled', 'grain': 'recalled', 'events': 'sourced'}
            rec = {'id': rid, 'name': name, 'summary': card['summary'], 'description': card['description'], 'kind': card['kind'], 'domain': field,
                   'tier': ds.tier_from(impact), 'impact': impact, 'grain': 'capability'}
            adv = [a for a in card.get('advance') or [] if a in V['advance']]
            if adv: rec['advance'] = adv; basis['advance'] = 'recalled'
            if card.get('origin') in V['origin']:
                rec['origin'] = card['origin']; basis['origin'] = 'sourced' if card.get('origin_note') else 'recalled'
            concept = CONCEPT_MAP.get(card.get('concept'), card.get('concept'))
            if concept and (concept in data.registers['concepts'] or concept in curated_concepts):
                rec['concept'] = concept; basis['concept'] = 'recalled'
                if concept not in data.registers['concepts']:
                    c = curated_concepts[concept]
                    new_concepts[concept] = {k: c[k] for k in ('id', 'name', 'summary', 'field') if c.get(k) and (k != 'field' or c[k] in FIELDS)}
            pb = [a for a in card.get('prompted_by') or [] if a in V['prompted_by']]
            if pb:
                rec['prompted_by'] = pb; basis['prompted_by'] = 'sourced'
                if card.get('why'): rec['why'] = card['why']
            if pids: rec['places'] = [{'place': p} for p in dict.fromkeys(pids.values())]; basis['places'] = 'sourced'
            ppl = []
            for p in card.get('people') or []:
                if not p.get('name') or p.get('role') not in V['person_role']: continue
                pid = slug(p['name'])
                if pid not in data.registers['people'] and pid not in new_people:
                    row = {'id': pid, 'name': p['name'], 'basis': 'sourced'}
                    for k in ('born', 'died'):
                        if isinstance(p.get(k), int): row[k] = p[k]
                    new_people[pid] = row
                ppl.append({'person': pid, 'role': p['role']})
            if ppl: rec['people'] = ppl; basis['people'] = 'sourced'
            soc = card.get('society')
            if isinstance(soc, dict) and soc.get('name'):
                sid_ = slug(soc['name'])
                if sid_ not in data.registers['societies'] and sid_ not in new_societies:
                    new_societies[sid_] = {'id': sid_, 'name': soc['name'], 'kind': soc.get('kind') if soc.get('kind') in V['society_kind'] else 'people', 'basis': 'recalled'}
                rec['societies'] = [sid_]; basis['societies'] = 'recalled'
            kf = [a for a in card.get('known_from') or [] if a in V['known_from']]
            if kf: rec['known_from'] = kf; basis['known_from'] = 'sourced'
            if card.get('fate') in V['fate']: rec['fate'] = card['fate']; basis['fate'] = 'recalled'
            rec['events'] = [ev for _, ev in events]
            rec['earliest_record'] = {'event': anchor['id'], 'rationale': 'The earliest dated evidence found for this capability in this community. No review has yet confirmed that nothing earlier exists.'}
            research = {'status': 'sourced' if all_verified else 'draft', 'basis': basis}
            oq = [q for q in card.get('open_questions') or [] if isinstance(q, str) and q.strip()]
            if oq: research['unresolved'] = [{'about': 'open question', 'note': q} for q in oq]
            if card.get('origin_note'): research['note'] = card['origin_note']
            rec['_links'] = card.get('links') or []
            rec['_sids'] = sids; rec['_srcs'] = srcs
            rec['research'] = research
            new_records[rid] = rec
            report['accepted'] += 1
        except Exception as e:
            report['error'] += 1; problems.append(f"error {card.get('name')}: {type(e).__name__} {e}")

# links between records, by name
names = {slug(r['name']): r['id'] for r in list(data.discoveries.values()) + list(new_records.values())}
for rec in new_records.values():
    links = []
    for l in rec.pop('_links'):
        to = names.get(slug(l.get('to') or ''))
        sids = rec['_sids']; srcs = rec['_srcs']
        if not to or to == rec['id'] or l.get('type') not in V['link'] or not isinstance(l.get('source'), int) or l['source'] >= len(sids) or not l.get('quote'):
            if l.get('to') and l.get('statement'):
                rec['research'].setdefault('missing_prerequisites', []).append(f"{l['to']}: {l['statement']}")
            continue
        check = checks.get(srcs[l['source']]['url'] + ' || ' + l['quote'], 'unchecked')
        link = {'type': l['type'], 'from': to, 'status': 'established' if check in ('exact', 'near') else 'candidate', 'statement': l['statement']}
        if link['status'] == 'established': link['evidence'] = [{'source': sids[l['source']], 'supports': l['quote']}]
        links.append(link); report['links'] += 1
    rec.pop('_sids'); rec.pop('_srcs')
    if links:
        r = rec.pop('research'); rec['links'] = links; r['basis']['links'] = 'sourced'; rec['research'] = r

print(dict(report)); print('new places', len(new_places), 'people', len(new_people), 'societies', len(new_societies), 'concepts', len(new_concepts), 'sources', len(new_sources))
for p in problems[:40]: print('  ', p)
if APPLY:
    for rec in new_records.values(): ds.write_json(ds.discovery_path(rec), rec)
    used_sources = {e['source'] for r in new_records.values() for ev in r['events'] for e in ev['evidence']} | {e['source'] for r in new_records.values() for l in r.get('links', []) for e in l.get('evidence', [])}
    from fetch_page import page_text, norm
    for sid, s in new_sources.items():
        if sid not in used_sources: continue
        # Keep the words around each checked quotation as evidence, so the check can be repeated.
        text = page_text(s['url']) if s.get('url') else ''
        excerpts = []
        for p in s['passages']:
            words = norm(p['quote']).split()
            probe = re.compile(r'\W+'.join(re.escape(w) for w in words[:6]), re.I)
            m = probe.search(text)
            if m: excerpts.append(text[max(0, m.start() - 500):m.start() + len(p['quote']) + 500].strip())
        if excerpts:
            body = f"Excerpts from: {s['title']}\nAddress: {s['url']}\nSaved: {TODAY}\nThese are the passages around each quotation cited in the dataset, copied from the page as fetched.\n\n" + '\n\n----\n\n'.join(excerpts) + '\n'
            rel = f'evidence/{sid[0]}/{sid}.txt'
            (ROOT / rel).parent.mkdir(parents=True, exist_ok=True)
            (ROOT / rel).write_text(body, encoding='utf-8')
            s['file'] = {'path': rel, 'sha256': ds.sha256(ROOT / rel), 'representation': 'excerpt', 'method': 'Passages of about 500 characters either side of each cited quotation, cut from the fetched page text.'}
        if not s['passages']: del s['passages']
        ds.write_json(ds.source_path(sid), s)
    for name, rows in (('places', new_places), ('people', new_people), ('societies', new_societies), ('concepts', new_concepts)):
        if rows: ds.write_jsonl(ds.DATA / f'{name}.jsonl', list(data.registers[name].values()) + list(rows.values()))
    print('written', len(new_records))
