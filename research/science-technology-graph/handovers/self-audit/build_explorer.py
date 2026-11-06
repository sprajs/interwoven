"""Build the in-chat, presentation-only verdict browser from the audit outputs.

Usage: python3 build_explorer.py /absolute/task-owned/path/graph-audit.html
"""
import json
from pathlib import Path
import sys
from audit_support import OUT, records

titles = {n['id']:n['label'] for n in records('nodes')}
rows=[]
for kind, file in [('connection','connection-verdicts.jsonl'),('entry','entry-verdicts.jsonl'),('label','label-verdicts.jsonl')]:
    for r in map(json.loads,(OUT/file).read_text().splitlines()):
        if kind=='connection':
            verdicts=[r['verdict'],r['severity']]; proposal=r['proposed_change']
        elif kind=='entry':
            verdicts=[key.removesuffix('_verdict')+': '+r[key] for key in ['kind_verdict','identity_verdict','tier_verdict']]
            proposal=f"kind {r['proposed_kind']}; tier {r['proposed_tier']}" if 'change' in [r[k] for k in ['kind_verdict','identity_verdict','tier_verdict']] else None
        else:
            verdicts=[r['verdict']];proposal=', '.join(r['proposed']) if r['verdict']=='change' else None
        rows.append({'type':kind,'id':r['id'],'title':titles.get(r['id'],r['id']),
            'verdicts':verdicts,'issue':r['issue'],'change':proposal,'method':r['basis']['method'],
            'sources':list(dict.fromkeys(s['source_id'] for s in r['basis'].get('sources',[])))})
raw=json.dumps(rows,ensure_ascii=False).replace('<','\\u003c')
target=Path(sys.argv[1]);target.parent.mkdir(parents=True,exist_ok=True)
target.write_text((OUT/'explorer.template.html').read_text().replace('__AUDIT_DATA__',raw))
assert target.stat().st_size<1_000_000
assert '__AUDIT_DATA__' not in target.read_text()
print(target)
