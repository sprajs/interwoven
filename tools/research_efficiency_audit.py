#!/usr/bin/env python3
"""Audit local research logs without copying conversation text into the report.

Codex: count each token_usage_record response once, never cumulative counters.
Claude: count each (requestId, message.id) once, not once per content block.
The resulting usage is logged usage, not an invoice or a quality evaluation.
Only the standard library is required. See the dated review for invocation.
"""
import argparse
import collections
import csv
import datetime as dt
import hashlib
import json
import re
import sqlite3
import subprocess
from pathlib import Path


KEYS = ('input_tokens', 'cached_input_tokens', 'cache_write_input_tokens',
        'output_tokens', 'reasoning_output_tokens')


def rows(path):
    with path.open(errors='replace') as stream:
        for line, text in enumerate(stream, 1):
            try:
                yield line, json.loads(text)
            except json.JSONDecodeError:
                continue


def content_text(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return '\n'.join(x.get('text', '') for x in content if isinstance(x, dict))
    return ''


def quantile(values, q):
    values = sorted(values)
    if not values:
        return None
    index = (len(values) - 1) * q
    lo = int(index)
    return values[lo] + (values[min(lo + 1, len(values) - 1)] - values[lo]) * (index - lo)


def summarize_calls(calls):
    by = collections.defaultdict(list)
    for call in calls:
        by[(call['provider'], call['role'], call['model'])].append(call)
    result = []
    for (provider, role, model), group in sorted(by.items()):
        sums = {k: sum(c.get(k, 0) for c in group) for k in KEYS}
        result.append(dict(provider=provider, role=role, model=model, calls=len(group),
                           **sums, median_input=quantile([c['input_tokens'] for c in group], .5),
                           p95_input=quantile([c['input_tokens'] for c in group], .95),
                           max_input=max(c['input_tokens'] for c in group)))
    return result


def parse_codex(paths, root_id, start, end):
    sessions = []
    for path in paths:
        first = next(rows(path), None)
        if not first or first[1].get('type') != 'session_meta':
            continue
        meta = first[1]['payload']
        if not str(meta.get('cwd', '')).endswith('/big_idea'):
            continue
        source = meta.get('source', {})
        spawn = source.get('subagent', {}).get('thread_spawn', {}) if isinstance(source, dict) else {}
        sessions.append((path, meta['id'], spawn))
    campaign_ids = {root_id}
    for _ in range(len(sessions)):
        campaign_ids.update(sid for _, sid, spawn in sessions if spawn.get('parent_thread_id') in campaign_ids)
    calls, files, tool_counts = [], [], collections.Counter()
    signals = collections.Counter()
    examples = collections.defaultdict(list)
    seen = set()
    for path, sid, spawn in sessions:
        role = spawn.get('agent_path', '').rsplit('/', 1)[-1] or ('coordinator' if sid == root_id else 'other_project_chat')
        scope = 'campaign' if sid in campaign_ids else 'other_project_chat'
        model, effort = None, None
        n, compactions = 0, 0
        last_event, final_record = {}, {}
        times = []
        for line, record in rows(path):
            timestamp = record.get('timestamp', '')
            if not start <= timestamp < end:
                continue
            times.append(timestamp)
            typ, p = record.get('type'), record.get('payload', {})
            if typ == 'turn_context':
                model = p.get('model', model)
                effort = p.get('effort', p.get('reasoning_effort', effort))
            elif typ == 'compacted':
                compactions += 1
            elif typ == 'token_usage_record':
                key = p.get('response_id')
                if key in seen:
                    signals['duplicate_usage_records_skipped'] += 1
                    continue
                seen.add(key)
                usage = p['usage']
                calls.append(dict(provider='codex', session=sid, role=role, scope=scope,
                                  model=model, effort=effort, timestamp=timestamp, line=line,
                                  **{k: usage.get(k, 0) for k in KEYS}))
                n += 1
                final_record = p.get('thread_token_usage', {})
            elif typ == 'event_msg' and p.get('type') == 'token_count':
                last_event = (p.get('info') or {}).get('total_token_usage', {})
            elif typ == 'response_item':
                if p.get('type') in ('custom_tool_call', 'function_call'):
                    name = p.get('name', 'unknown')
                    tool_counts[(scope, role, name)] += 1
                    raw = p.get('input', p.get('arguments', ''))
                    text = raw if isinstance(raw, str) else json.dumps(raw)
                    for nested in re.findall(r'\btools\.([A-Za-z0-9_]+)\s*\(', text):
                        tool_counts[(scope, role, 'nested:' + nested)] += 1
                    for label, pattern in [('validation_commands', r'tools/validate\.py'),
                                           ('test_commands', r'npm test'),
                                           ('build_commands', r'npm run build'),
                                           ('dataset_inventory_commands', r'rglob\(.{0,25}json|Dataset\.load|tools/coverage\.py')]:
                        if re.search(pattern, text):
                            signals[label] += 1
                elif p.get('type') in ('custom_tool_call_output', 'function_call_output'):
                    text = str(p.get('output', ''))
                    if 'truncat' in text.lower():
                        signals['outputs_containing_truncation_marker'] += 1
                elif p.get('type') == 'message' and p.get('role') == 'user':
                    text = content_text(p.get('content', []))
                    if '<codex_internal_context source="goal">' in text:
                        signals['goal_continuations'] += 1
        if n:
            files.append(dict(provider='codex', file=path.name, session=sid, role=role,
                              scope=scope, bytes=path.stat().st_size,
                              sha256=hashlib.sha256(path.read_bytes()).hexdigest(), calls=n,
                              first=min(times), last=max(times), compactions=compactions,
                              last_event_totals=last_event, final_record_totals=final_record))
    return calls, files, tool_counts, signals, examples


def classify_claude(path, prompts):
    computed = '\n'.join(s for s in prompts if 'computed task' in s or s.startswith('Read and follow') or 'You are the curator' in s)
    if 'SUPERVISOR.md' in computed:
        return 'supervisor'
    if 'RESEARCHER.md' in computed:
        return 'researcher'
    if 'SCORER.md' in computed:
        return 'scorer'
    if 'CURATOR.md' in computed:
        return 'curator'
    text = '\n'.join(prompts[:5])
    if 'Dedupe' in text or 'dedupe' in text.lower() and '/expand/' in text:
        return 'dedupe'
    return 'coordinator' if '/subagents/' not in str(path) else 'other_agent'


def parse_claude(paths, start, end):
    calls, files, tool_counts = [], [], collections.Counter()
    signals, seen_tools = collections.Counter(), set()
    examples = collections.defaultdict(list)
    global_seen = set()
    for path in paths:
        groups, prompts, times = {}, [], []
        raw_usage = collections.Counter()
        valid_rows = []
        for line, record in rows(path):
            timestamp = record.get('timestamp', '')
            if not start <= timestamp < end:
                continue
            times.append(timestamp)
            msg = record.get('message', {})
            if not isinstance(msg, dict):
                continue
            typ = record.get('type')
            if typ == 'user':
                text = content_text(msg.get('content', ''))
                if text:
                    prompts.append(text)
                for item in msg.get('content', []) if isinstance(msg.get('content'), list) else []:
                    if item.get('type') != 'tool_result':
                        continue
                    text = content_text(item.get('content', ''))
                    if re.search(r'(web.?search|search).{0,100}(limit|exhaust|unavailable|not available)|(?:limit|exhaust).{0,100}(?:web.?search|search)', text, re.I | re.S):
                        signals['search_limit_tool_results'] += 1
                        if len(examples['search_limits']) < 5:
                            examples['search_limits'].append(dict(file=path.name, line=line))
                    if re.search(r'captcha|bot.?check|access denied|403 forbidden|verify you are human', text, re.I):
                        signals['blocked_page_tool_results'] += 1
                continue
            if typ != 'assistant' or msg.get('model') == '<synthetic>' or not msg.get('usage'):
                continue
            key = (record.get('requestId'), msg.get('id'))
            if not all(key):
                signals['assistant_rows_missing_request_or_message_id'] += 1
                continue
            usage = msg['usage']
            for k in ('input_tokens', 'cache_creation_input_tokens', 'cache_read_input_tokens', 'output_tokens'):
                raw_usage[k] += usage.get(k, 0)
            if key not in groups:
                groups[key] = dict(record=record, line=line, usage=usage.copy(), timestamp=timestamp)
            else:
                signals['repeated_assistant_content_blocks'] += 1
                old = groups[key]['usage']
                if any(old.get(k, 0) != usage.get(k, 0) for k in ('input_tokens', 'cache_creation_input_tokens', 'cache_read_input_tokens', 'output_tokens')):
                    signals['usage_changed_between_content_blocks'] += 1
                    for k in ('input_tokens', 'cache_creation_input_tokens', 'cache_read_input_tokens', 'output_tokens'):
                        old[k] = max(old.get(k, 0), usage.get(k, 0))
            valid_rows.append((line, record))
        if not groups:
            continue
        role = classify_claude(path, prompts)
        workflow = path.parent.name if '/workflows/' in str(path) else None
        for line, record in valid_rows:
            for item in record['message'].get('content', []):
                if item.get('type') != 'tool_use' or item.get('id') in seen_tools:
                    continue
                seen_tools.add(item['id'])
                name = item.get('name', '')
                tool_counts[('claude', role, name)] += 1
        for key, group in groups.items():
            if key in global_seen:
                signals['cross_file_duplicate_responses_skipped'] += 1
                continue
            global_seen.add(key)
            usage = group['usage']
            cached = usage.get('cache_read_input_tokens', 0)
            write = usage.get('cache_creation_input_tokens', 0)
            uncached = usage.get('input_tokens', 0)
            record = group['record']
            calls.append(dict(provider='claude', session=path.stem, role=role,
                              scope='project', workflow=workflow, model=record['message']['model'],
                              effort=record.get('effort'), timestamp=group['timestamp'], line=group['line'],
                              input_tokens=uncached + write + cached, cached_input_tokens=cached,
                              cache_write_input_tokens=write, output_tokens=usage.get('output_tokens', 0),
                              reasoning_output_tokens=usage.get('output_tokens_details', {}).get('thinking_tokens', 0)))
        files.append(dict(provider='claude', file=str(path.relative_to(path.parents[3])) if workflow else path.name,
                          role=role, workflow=workflow, bytes=path.stat().st_size,
                          sha256=hashlib.sha256(path.read_bytes()).hexdigest(), calls=len(groups),
                          first=min(times), last=max(times), raw_content_block_usage=dict(raw_usage)))
    return calls, files, tool_counts, signals, examples


def pipeline_results(scratch):
    base = scratch / 'expand' / 'research'
    result = {'batches': []}
    for path in sorted(base.glob('batch-*-input.json')):
        bid = path.stem.removesuffix('-input')
        row = {'batch': bid}
        value = json.loads(path.read_text())
        row['leads'] = len(value.get('leads', []))
        for suffix in ('cards', 'verified'):
            target = base / f'{bid}-{suffix}.json'
            if not target.exists():
                row[suffix] = None
                continue
            cards = json.loads(target.read_text()).get('cards', [])
            row[suffix] = len(cards)
            row[suffix + '_statuses'] = dict(collections.Counter(c.get('status', '') for c in cards))
            if suffix == 'verified':
                row['verdicts'] = dict(collections.Counter(c.get('verdict', '') for c in cards))
                row['rejections_mentioning_search_limit'] = sum(c.get('verdict') == 'reject' and bool(re.search(r'search.{0,80}(budget|allowance|unavailable)|no web searches|had no.{0,20}search', c.get('changes', '') + c.get('note', ''), re.I)) for c in cards)
        result['batches'].append(row)
    return result


def dataset_stats(root, revision=None):
    if revision:
        paths = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', revision, 'data'], cwd=root, text=True).splitlines()
        selected = [p for p in paths if p.startswith(('data/discoveries/', 'data/sources/')) and p.endswith('.json')]
        stream = subprocess.check_output(['git', 'cat-file', '--batch'], input=''.join(f'{revision}:{p}\n' for p in selected).encode(), cwd=root)
        objects, offset = [], 0
        for path in selected:
            newline = stream.index(b'\n', offset)
            size = int(stream[offset:newline].split()[-1])
            raw = stream[newline + 1:newline + 1 + size]
            objects.append((path, json.loads(raw)))
            offset = newline + size + 2
    else:
        objects = [(str(p.relative_to(root)), json.loads(p.read_text())) for sub in ('discoveries', 'sources') for p in (root/'data'/sub).rglob('*.json')]
    discoveries = [r for p, r in objects if p.startswith('data/discoveries/')]
    sources = [r for p, r in objects if p.startswith('data/sources/')]
    urls = collections.Counter(s.get('url') for s in sources if s.get('url'))
    return dict(revision=revision or 'working_tree', discoveries=len(discoveries), sources=len(sources),
                events=sum(len(r.get('events', [])) for r in discoveries),
                measures=sum(len(r.get('measures', [])) for r in discoveries),
                contributions=sum(len(e.get('contributions', [])) for r in discoveries for e in r.get('events', [])),
                links=sum(len(r.get('links', [])) for r in discoveries),
                exact_url_duplicate_groups=sum(n > 1 for n in urls.values()),
                exact_url_redundant_source_rows=sum(n-1 for n in urls.values()),
                facets_present={key: sum(key in r for r in discoveries) for key in ('origin', 'concept', 'impact', 'grain', 'measures', 'funding', 'why', 'links')},
                origin_basis=dict(collections.Counter(r.get('research', {}).get('basis', {}).get('origin', 'unassessed') for r in discoveries)),
                event_basis=dict(collections.Counter(r.get('research', {}).get('basis', {}).get('events', 'unassessed') for r in discoveries)))


def runtime_summary(path, files, start, end):
    ids = [f['session'] for f in files if f['provider'] == 'codex']
    bounds = [int(dt.datetime.fromisoformat(t.replace('Z', '+00:00')).replace(tzinfo=dt.timezone.utc).timestamp()) for t in (start, end)]
    with sqlite3.connect('file:' + str(path) + '?mode=ro', uri=True) as database:
        result = database.execute('SELECT level,target FROM logs WHERE ts>=? AND ts<? AND thread_id IN (' + ','.join('?' for _ in ids) + ')', [*bounds, *ids]).fetchall()
    return dict(rows=len(result), levels=dict(collections.Counter(r[0] for r in result)),
                warning_error_targets=dict(collections.Counter(r[1] for r in result if r[0] in ('WARN', 'ERROR'))),
                interpretation='Four stream-retry warnings, six plugin-icon warnings, one nonexistent agent-path error. Pattern mentions in DEBUG/INFO are not error counts.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--codex-dir', type=Path, required=True)
    parser.add_argument('--root-thread', required=True)
    parser.add_argument('--claude-dir', type=Path, required=True)
    parser.add_argument('--scratch', type=Path, required=True)
    parser.add_argument('--runtime-db', type=Path)
    parser.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--start', default='2026-11-09T19:00:00')
    parser.add_argument('--end', default='2026-11-10T09:40:00')
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    codex = parse_codex(sorted(args.codex_dir.glob('*.jsonl')), args.root_thread, args.start, args.end)
    claude = parse_claude(sorted(args.claude_dir.rglob('*.jsonl')), args.start, args.end)
    calls = codex[0] + claude[0]
    assert all(0 <= c['cached_input_tokens'] + c['cache_write_input_tokens'] <= c['input_tokens'] for c in calls)
    assert all(c['reasoning_output_tokens'] <= c['output_tokens'] for c in calls)
    calls.sort(key=lambda c: (c['timestamp'], c['provider'], c['session'], c['line']))
    summary = dict(window=dict(start=args.start, end_exclusive=args.end, timezone='UTC (Europe/London on these dates)'),
                   source_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=args.repo, text=True).strip(),
                   accounting=dict(codex='Unique response_id, usage only; input includes cached input; output includes reasoning.',
                                   claude='Unique (requestId, message.id); maximum counters across repeated content blocks; input includes cache creation and cache reads.',
                                   limits='Local logged usage; missing provider/invoice/hidden advisor usage cannot be recovered. No cumulative usage, goal totals, or workflow totals added.'),
                   groups=summarize_calls(calls), files=codex[1]+claude[1],
                   codex_signals=dict(codex[3]), claude_signals=dict(claude[3]),
                   tools=[dict(scope=s, role=r, tool=t, count=n) for (s, r, t), n in sorted((codex[2]+claude[2]).items())],
                   pipeline=pipeline_results(args.scratch),
                   dataset=[dataset_stats(args.repo, rev) for rev in ('eed7790','32cf878','a51b7e9',None)])
    if args.runtime_db:
        summary['runtime'] = runtime_summary(args.runtime_db, summary['files'], args.start, args.end)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out/'audit.json').write_text(json.dumps(summary, indent=2, ensure_ascii=False)+'\n')
    fields = sorted(set().union(*(r.keys() for r in calls)))
    with (args.out/'calls.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fields, lineterminator='\n')
        writer.writeheader(); writer.writerows(calls)
    print(json.dumps(dict(files=len(summary['files']), calls=len(calls), groups=summary['groups'],
                          codex_signals=summary['codex_signals'], claude_signals=summary['claude_signals'],
                          dataset=summary['dataset']), indent=2))


if __name__ == '__main__':
    main()
