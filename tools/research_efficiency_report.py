#!/usr/bin/env python3
"""Regenerate reviewed chart inputs and authored viewer source (stdlib only).

Usage: python3 tools/research_efficiency_report.py REVIEW_DIRECTORY
The Data plugin builds viewer/ReportContent.jsx in its standard report runtime.
"""
import collections
import html
import json
import sys
from pathlib import Path

RATES = {'gpt-6-astra': (10, 1, 50), 'gpt-6.1-sol': (2, .1, 10),
         'gpt-6.1-terra': (1, .05, 5), 'gpt-6-luna': (.1, .01, .5)}


def main():
    base = Path(sys.argv[1])
    audit = json.loads((base/'audit.json').read_text())
    groups = collections.defaultdict(collections.Counter)
    for row in audit['groups']:
        if row['provider'] != 'codex' or row['role'] == 'other_project_chat':
            continue
        role = row['role']
        label = ('Astra coordinator' if role == 'coordinator' else
                 'Six Terra research lanes' if role.endswith('_research') else
                 'Terra schema / panels' if role == 'research_schema' else
                 'Luna inventories' if row['model'] == 'gpt-6-luna' else 'Initial Astra reviews')
        a, b, c = RATES[row['model']]
        cost = ((row['input_tokens']-row['cached_input_tokens'])*a + row['cached_input_tokens']*b + row['output_tokens']*c)/1e6
        groups[label].update(dict(inputMillions=row['input_tokens']/1e6,
                                 outputMillions=row['output_tokens']/1e6,
                                 cachedMillions=row['cached_input_tokens']/1e6,
                                 standardApiUsd=cost, responses=row['calls']))
    cost_rows = [dict(role=label, **dict(values)) for label, values in groups.items()]
    cost_rows.sort(key=lambda r: r['standardApiUsd'], reverse=True)
    total = sum(r['standardApiUsd'] for r in cost_rows)
    assert abs(total-257.61753974) < 1e-7
    sections = []
    for n, text in enumerate((base/'review.md').read_text().split('\n## ')):
        if n == 0:
            continue
        title, _, body = text.partition('\n')
        sections.append(dict(id='review-section-'+str(n), title=title, text='## '+title+'\n'+body.strip()))
    snapshot = dict(title='Research more efficiently without weakening the evidence', surface='report',
                    description='Evidence from the 9–10 November 2026 research runs',
                    status='reviewed', buildStatus='creating', report=dict(asOf='2026-11-10'),
                    generatedAt='2026-11-10T09:40:00Z', filters=[],
                    exportPreferences=dict(selected=None, destinations=[]),
                    queries={'campaign_roles': dict(rows=cost_rows, source=dict(
                        label='Logged Codex campaign usage; modeled standard API token cost',
                        files=['audit.json','calls.csv','review.md'],
                        links=[dict(label='Official OpenAI pricing', url='https://developers.openai.com/api/docs/pricing')],
                        caveats=['API-equivalent comparison, not an invoice. Excludes search/tools, long-context adjustments, plan-specific pricing and any missing usage.',
                                 'Token presentations include cached history. Output includes reasoning. Initial design/review work and schema/panels remain included.'],
                        metricDefinitions=[dict(label='Standard API equivalent (USD)', definition='Sum over responses of (input minus cached input) × standard input price + cached input × cached price + output × standard output price, divided by one million. No reasoning double count.'),
                                           dict(label='Input token presentations (millions)', definition='Per-response input, including cached history, summed once per unique response ID and divided by one million.')],
                        evidenceFlow=[dict(title='Scope',detail='Root research chat 01a1c22c-8838-7cf1-aa46-90b17270fab5 and recorded descendant sessions, 9 November 19:00 to 10 November 09:40 UTC.'),
                                      dict(title='Reproduce',detail='Run tools/research_efficiency_audit.py using reproduce.txt, then tools/research_efficiency_report.py. Source log hashes are in audit.json.')]))})
    usage_rows = []
    for provider, scope, label in [('codex', 'campaign', 'Codex research campaign'), ('codex', 'other_project_chat', 'Other Codex project chats'), ('claude', 'all', 'Claude project activity')]:
        selected = [g for g in audit['groups'] if g['provider'] == provider and (provider == 'claude' or (g['role'] == 'other_project_chat') == (scope == 'other_project_chat'))]
        usage_rows.append(dict(scope=label, **{key:sum(g[key] for g in selected) for key in ('calls','input_tokens','cached_input_tokens','output_tokens')}))
    pipeline_rows = []
    for prefix, label in [('batch-000','Pilot'),('batch-1','First screened wave'),('batch-2','Next wave')]:
        batches = [b for b in audit['pipeline']['batches'] if b['batch'].startswith(prefix)]
        reviewed = sum(b['verified'] or 0 for b in batches)
        verdicts = sum((collections.Counter(b.get('verdicts', {})) for b in batches), collections.Counter())
        pipeline_rows.append(dict(stage=label, leads=sum(b['leads'] for b in batches), researcherCards=sum(b['cards'] or 0 for b in batches), reviewedCards=reviewed,
                                  accepted=verdicts['accept_with_changes'] if reviewed else None,
                                  rejected=verdicts['reject'] if reviewed else None))
    queries = {'run_usage':usage_rows, 'pipeline':pipeline_rows,
               'checkpoints':audit['dataset'], 'model_roles':audit['groups'],
               'diagnostics':[dict(signal=k, count=v) for k,v in audit['claude_signals'].items()]}
    for key, values in queries.items():
        snapshot['queries'][key] = dict(rows=values, source=dict(label='Reviewed local research audit: '+key,
            files=['audit.json','calls.csv','review.md'],
            caveats=['Fixed evidence window 9 November 19:00 to 10 November 09:40 UTC. Missing reviews are not failed reviews. No invoice data.',
                     'Workflow outcomes are not independently measured historical error rates. Diagnostic text matches can overlap.'],
            evidenceFlow=[dict(title='Reproduce', detail='tools/research_efficiency_audit.py with arguments from reproduce.txt. Inspect source hashes in audit.json; raw messages remain local.')]))
    viewer = base/'viewer'
    viewer.mkdir(exist_ok=True)
    (viewer/'snapshot.json').write_text(json.dumps(snapshot, indent=2)+'\n')
    (viewer/'sections.json').write_text(json.dumps(sections, indent=2, ensure_ascii=False)+'\n')
    # A persistent figure for the repository's Markdown source.
    width, height, left, right = 1000, 380, 255, 105
    scale = (width-left-right)/180
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="Codex campaign standard API equivalent by role, excluding tools; coordinator dominates">',
           '<rect width="100%" height="100%" fill="#ffffff"/>',
           '<g font-family="sans-serif" font-size="16" fill="#162126">',
           '<text x="24" y="30" font-size="22">The coordinator dominates modeled token cost</text>',
           '<text x="24" y="56" fill="#526268">Codex campaign · standard API equivalent USD · excludes tools and plan billing</text>']
    for tick in (0,50,100,150):
        x=left+tick*scale
        svg.extend([f'<line x1="{x}" x2="{x}" y1="79" y2="305" stroke="#dfe5e7"/>',f'<text x="{x}" y="329" text-anchor="middle">${tick}</text>'])
    for i,row in enumerate(cost_rows):
        y=85+i*43
        svg.extend([f'<text x="{left-12}" y="{y+20}" text-anchor="end">{html.escape(row["role"])}</text>',
                    f'<rect x="{left}" y="{y}" width="{row["standardApiUsd"]*scale:.3f}" height="28" fill="{("#156c88" if i==0 else "#8baeb8")}"/>',
                    f'<text x="{left+row["standardApiUsd"]*scale+9:.2f}" y="{y+20}">${row["standardApiUsd"]:.2f}</text>'])
    svg.append('<text x="24" y="367" font-size="14" fill="#526268">Observed usage repriced at 10 November 2026 rates. This is not actual billed spend.</text></g></svg>')
    (base/'coordination-cost.svg').write_text('\n'.join(svg)+'\n')
    print(json.dumps(dict(standardApiEquivalentUsd=total, sourceCommit=audit['source_commit'], sections=len(sections))))


if __name__ == '__main__':
    main()
