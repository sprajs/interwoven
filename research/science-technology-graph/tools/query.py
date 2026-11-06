#!/usr/bin/env python3
"""Inspect and traverse the local graph without flattening lifecycle dates."""
from pathlib import Path
import argparse,json,collections
R=Path(__file__).resolve().parents[1]
def records(name):return [json.loads(s) for s in (R/'data'/f'{name}.jsonl').read_text().splitlines() if s.strip()]
def unresolved_commercial(nodes):
 return [n for n in nodes if n['kind']=='technology' and n['lifecycle']['first_commercial_availability']['status'] in ['unknown','not_yet_researched']]
def main():
 p=argparse.ArgumentParser(description=__doc__);s=p.add_subparsers(dest='command',required=True)
 s.add_parser('stats');n=s.add_parser('node');n.add_argument('id');t=s.add_parser('traverse');t.add_argument('id');t.add_argument('--depth',type=int,default=1);t.add_argument('--direction',choices=['incoming','outgoing','both'],default='both');t.add_argument('--include-candidates',action='store_true');s.add_parser('unresolved-commercial')
 args=p.parse_args();nodes={n['id']:n for n in records('nodes')};events={e['id']:e for e in records('events')};edges=records('relationships');sources={s['id']:s for s in records('sources')}
 if args.command=='stats':
  result={'nodes':len(nodes),'events':len(events),'relationships':len(edges),'sources':len(sources),'historical_review':dict(collections.Counter(n['review']['historical_claim'] for n in nodes.values())),'lifecycle_review':dict(collections.Counter(n['review']['lifecycle_classification'] for n in nodes.values())),'commercial_availability':dict(collections.Counter(n['lifecycle']['first_commercial_availability']['status'] for n in nodes.values() if n['kind']=='technology')),'graph_anchors':dict(collections.Counter(n['graph_anchor']['status'] for n in nodes.values()))}
 elif args.command=='unresolved-commercial':
  result=[{'id':n['id'],'label':n['label'],'applicability':n['commercial_applicability']['status'],'status':n['lifecycle']['first_commercial_availability']['status'],'rationale':n['lifecycle']['first_commercial_availability']['rationale']} for n in unresolved_commercial(nodes.values())]
 elif args.id not in nodes:p.error('Unknown node ID: '+args.id)
 elif args.command=='node':
  related=[e for e in edges if args.id in [e['from']['node_id'],e['to']['node_id']]];owned=[events[k] for k in nodes[args.id]['event_ids']];sourceids={ref['source_id'] for item in owned+related for ref in item['evidence']};result={'node':nodes[args.id],'events':owned,'incoming':[e for e in related if e['to']['node_id']==args.id],'outgoing':[e for e in related if e['from']['node_id']==args.id],'sources':[sources[k] for k in sorted(sourceids)]}
 else:
  if not 0<=args.depth<=20:p.error('depth must be 0..20')
  allowed=[e for e in edges if args.include_candidates or e['review']['historical_claim']=='accepted'];seen={args.id};frontier={args.id};selected={}
  for _ in range(args.depth):
   following=set()
   for e in allowed:
    a,b=e['from']['node_id'],e['to']['node_id']
    if (args.direction in ['outgoing','both'] and a in frontier) or (args.direction in ['incoming','both'] and b in frontier):selected[e['id']]=e;following.update([a,b])
   frontier=following-seen;seen|=following
  result={'nodes':[nodes[k] for k in sorted(seen)],'relationships':list(selected.values()),'note':'Traversal follows typed historical relationships, not graph-anchor chronology. Candidate edges excluded unless explicitly requested; disconnected nodes remain valid.'}
 print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
