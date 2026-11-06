"""Presentation-only browser of Stage1 report judgements; no graph mutation."""
import json
from pathlib import Path
import re
import sys
from comparison_support import OUT,records,MAIN

def prose(t):
    t=re.sub(r'(?<=[A-Za-z])(?=(?:1\d{3}|20\d{2})\b)',' ',t)
    return re.sub(r'\b(Stage|stage|tier|decision)([0-9])\b',r'\1 \2',t)

titles={k:n['label'] for k,n in (records('nodes')|records('nodes',MAIN)).items()}
items=[]
for r in map(json.loads,(OUT/'comparison-findings.jsonl').read_text().splitlines()):
    section=r['section'];basis=r.get('basis',r.get('source_check',''))
    if isinstance(basis,dict):basis=basis['method']+' · '+', '.join(basis['source_ids'])+' · '+basis['limit']
    if section=='connection':verdicts=['self: '+r['self'],'independent: '+r['independent'],r['current_status']]
    elif section=='entry':verdicts=[f"tiers {r['self_tier']} / {r['independent_tier']} → {r['stage1_preferred_tier']}",r['stage1_preferred_kind'],r['current_status']]
    elif section=='removal':verdicts=[r['operation']]
    elif section=='added_entry':verdicts=[r['kind'],'tier '+str(r['tier']),r['current_anchor']]
    else:verdicts=[r['relation']]
    items.append({'section':section,'id':r['id'],'title':titles.get(r['id'],r['id']),'verdicts':verdicts,'finding':prose(r['finding']),'identity':prose(r.get('identity_resolution',r.get('reason_recorded',''))),'basis':prose(basis)})
meta=json.loads((OUT/'comparison-checks.json').read_text())
counts=f"40 connection cases · 120 entry cases · {meta['added_entries']} added entries · 11 removals · main {MAIN[:7]}"
target=Path(sys.argv[1]);target.parent.mkdir(parents=True,exist_ok=True)
template=(OUT/'comparison-explorer.template.html').read_text()
payload=json.dumps(items,ensure_ascii=False).replace('<','\\u003c')
target.write_text(template.replace('__COMPARISON_DATA__',payload).replace('__COMPARISON_COUNTS__',json.dumps(counts)))
assert target.stat().st_size<1_000_000
print(target)
