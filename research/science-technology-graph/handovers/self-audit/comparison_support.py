"""Read-only Stage 1 comparison inputs and source excerpts.

This helper never writes canonical graph data or review decisions. Historical
adjudications are recorded separately in COMPARISON.md, not inferred by code.
"""
from pathlib import Path
import collections
import hashlib
import json
import re
import subprocess
import sys
import tempfile

OUT = Path(__file__).resolve().parent
REPO = OUT.parents[3]
GRAPH = 'research/science-technology-graph/'
BASE = '30df3e79face637299ca26c88fdd2b1872725894'
MAIN = 'c388b6d9a9bbc936f6cab7646c246c38b3913f63'
INDEPENDENT = REPO / '.claude/worktrees/competent-lumiere-24494e' / GRAPH / 'handovers/independent-review'
CACHE = Path(tempfile.gettempdir()) / 'big-idea-stage1-source-text'

def git_text(rev, path):
    return subprocess.check_output(['git','show',rev+':'+path],cwd=REPO,text=True)

def records(name, rev=BASE):
    return {x['id']:x for x in map(json.loads,git_text(rev,GRAPH+'data/'+name+'.jsonl').splitlines())}

def rows(path):
    return list(map(json.loads,path.read_text().splitlines()))

def sources():
    return records('sources',MAIN)

def source_text(sid):
    from audit_support import Text
    s=sources()[sid]
    copy=s.get('local_copy',{})
    if not copy.get('path'): return s, None
    p=REPO/GRAPH/copy['path'];raw=p.read_bytes()
    assert hashlib.sha256(raw).hexdigest()==copy['sha256'],sid
    if p.suffix.lower() in ('.png','.jpg','.jpeg'):return s,None
    if p.suffix.lower()=='.pdf':
        text=subprocess.check_output(['pdftotext','-layout',str(p),'-']).decode('utf8',errors='replace')
    else:
        text=raw.decode('utf8',errors='replace')
        if p.suffix.lower() in ('.html','.xml'):
            parser=Text();parser.feed(text);text=''.join(parser.parts)
    CACHE.mkdir(exist_ok=True);(CACHE/(sid+'.txt')).write_text(text)
    return s,text

def inventory():
    self_rel={x['id']:x for x in rows(OUT/'connection-verdicts.jsonl')}
    other_rel={x['id']:x for x in rows(INDEPENDENT/'connection-verdicts.jsonl')}
    self_ent={x['id']:x for x in rows(OUT/'entry-verdicts.jsonl')}
    other_ent={x['id']:x for x in rows(INDEPENDENT/'entry-verdicts.jsonl')}
    changed={}
    for f in ['nodes','events','relationships','sources']:
        a=records(f);b=records(f,MAIN)
        changed[f]={'base_count':len(a),'main_count':len(b),'added':sorted(b.keys()-a.keys()),'removed':sorted(a.keys()-b.keys()),'changed':sorted(k for k in a.keys()&b.keys() if a[k]!=b[k])}
    cross=collections.Counter((self_rel[k]['verdict'],other_rel[k]['verdict']) for k in self_rel)
    result={'base_commit':BASE,'main_compared':MAIN,'independent_files':{f:hashlib.sha256((INDEPENDENT/f).read_bytes()).hexdigest() for f in ['REVIEW.md','connection-verdicts.jsonl','entry-verdicts.jsonl','gaps.jsonl']},'connection_cross_tab':[{'self':k[0],'independent':k[1],'count':v} for k,v in sorted(cross.items())],'changes_since_audited_snapshot':changed,'comparison_connection_ids':[k for k in other_rel if self_rel[k]['verdict']!='agree' or other_rel[k]['verdict']!='agree']}
    result['entry_comparison_ids']=[]
    for k,b in other_ent.items():
        a=self_ent[k];bt=b['tier'] if b.get('proposed_tier') is None else b['proposed_tier'];bk=b.get('proposed_kind') or b['kind']
        if (a['proposed_kind'],a['proposed_tier'],a['identity_verdict'])!=(bk,bt,b['identity_verdict']):result['entry_comparison_ids'].append(k)
    prior=OUT/'comparison-inputs.json'
    result['untracked_preservation']=json.loads(prior.read_text()).get('untracked_preservation',{}) if prior.exists() else {}
    if not result['untracked_preservation']:
        for path in subprocess.check_output(['git','ls-files','--others','--exclude-standard','--',GRAPH+'evidence/acquired/','web/tsconfig.tsbuildinfo'],cwd=REPO,text=True).splitlines():
            result['untracked_preservation'][path]=hashlib.sha256((REPO/path).read_bytes()).hexdigest()
    (OUT/'comparison-inputs.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ['untracked_preservation','changes_since_audited_snapshot','entry_comparison_ids','comparison_connection_ids']},indent=2))
    print('Preserved untracked inputs:',len(result['untracked_preservation']))

if __name__=='__main__':
    if sys.argv[1]=='inventory':inventory()
    elif sys.argv[1]=='source':
        sid=sys.argv[2];pattern=sys.argv[3] if len(sys.argv)>3 else '.'
        s,text=source_text(sid);print(sid,s.get('url'),s.get('local_copy',{}).get('path'))
        if text is None:print('NO LOCAL TEXT; live access or image inspection required')
        else:
            matches=list(re.finditer(pattern,text,re.I));print('text characters',len(text),'matches',len(matches))
            for m in matches[:5]:print(text[max(0,m.start()-280):m.end()+1000])
