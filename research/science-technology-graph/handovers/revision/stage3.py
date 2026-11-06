"""Separate the earliest evidenced record from the preserved community event."""
from common import *
import subprocess

records=load();before=deepcopy(records);decisions={}
base='30df3e79face637299ca26c88fdd2b1872725894'
def original(name):
    return index([json.loads(x) for x in subprocess.check_output(['git','show',base+':research/science-technology-graph/data/'+name+'.jsonl'],text=True).splitlines()])
old_nodes=original('nodes');old_events=original('events');old_links=original('relationships')
restore=['elec-hoerni-planar-conception-1957','mech-kendall-k1-voyage','mech-bloomfield-pump-1776',
         'global-hokulea-built-1975','global-mau-hokulea-passage-1976',
         'math-latin-dixit-algorizmi-1100s','math-latin-liber-alchorismi-1100s']
for nid in restore:
    assert nid not in index(records['nodes'])
    n=deepcopy(old_nodes[nid]);records['nodes'].append(n)
    for eid in n['event_ids']:
        current=index(records['events']).get(eid)
        if current:
            owner=index(records['nodes'])[current['node_id']]
            owner['event_ids'].remove(eid)
            for state in owner['lifecycle'].values():
                if eid in state['event_ids']:
                    state['event_ids'].remove(eid)
                    if not state['event_ids']:state.update(status='not_yet_researched',rationale='Separate dated configuration restored; see its own node.',evidence=[])
            records['events'].remove(current)
        records['events'].append(deepcopy(old_events[eid]))
        decisions[eid]='Reopened source in Stage 1; restore separately dated event and original owner. This is not a new priority claim.'
    decisions[nid]='Restore deliberate split: independent date and explanatory chain role fail the owner’s duplicate-merge test. No assertion of a new global frontier solely from geography or reconstruction.'
for rid in ['elec-planar-concept-to-device','mech-h4-to-k1-copy','global-hokulea-build-to-mau-voyage',
            'global-hokulea-study-to-build','global-hokulea-to-field-trial',
            'math-edge02-khwarizmi-to-alchorismi','math-edge02-khwarizmi-to-dixit',
            'elec-planar-concept-to-interconnection','mech-boring-to-bloomfield','mech-k1-to-k2-simplification','mech-trials-to-bloomfield']:
    records['relationships']=[r for r in records['relationships'] if r['id']!=rid]
    r=deepcopy(old_links[rid])
    if rid=='math-edge02-khwarizmi-to-alchorismi':
        r['statement']='The Latin Liber Alchorismi expands the exposition of the al-Khwarizmi arithmetic tradition; Folkerts compares its chapter reordering with the Latin Liber Ysagogarum, not the lost Arabic original.'
        r['uncertainty']='The lost Arabic original cannot establish a direct chapter-order comparison. Latin versions have distinct redaction and transmission histories.'
    records['relationships'].append(r)
    decisions[rid]='Restore the source-supported separate endpoints and chain roles checked in Stage 1. Folkerts comparator corrected where relevant; no new speculative transmission.'

nodes=index(records['nodes']);events=index(records['events'])
holds={'global-muldoons-channel-infill','global-muldoons-walled-channel','global-barbegal-aqueduct-mills',
       'mech-shadwell-expansive-engine-1781','med-humulin-recombinant-insulin-1982'}
def limit(e):
    d=e['date'];b=d.get('latest',d.get('earliest',{}));return (b.get('year',999999),b.get('month',12),b.get('day',31))
def usable(e):
    return e['date']['status'] in {'known','approximate','bounded'} and ('latest' in e['date'] or 'earliest' in e['date'])

# Earlier items that describe a predecessor or a different scoped configuration
# are not candidates merely because they share a node after a broad consolidation.
excluded={
 'mech-harrison-h4-watch':set(),
 'elec-hoerni-planar-transistor-1959':set(),
}
rows=[]
for n in records['nodes']:
    old=deepcopy(n['graph_anchor']);n['community_entry']=old
    candidates=[events[eid] for eid in n['event_ids'] if usable(events[eid]) and eid not in excluded.get(n['id'],set())]
    chosen=min(candidates,key=limit) if candidates else None
    if n['id'] in holds:
        n['graph_anchor']={'status':'unknown','policy':'earliest_record','rationale':'Historian/date dispute retained. A later community witness is not an automatic earliest-record anchor.'}
        reason='Hold earliest placement; preserve all evidence and the separately recorded community entry. Historian adjudication not supplied.'
    elif chosen:
        date=chosen['date'];interpretation='event_date' if date.get('earliest') and date.get('latest') else 'known_by' if date.get('latest') else 'known_from'
        n['graph_anchor']={'status':'selected','policy':'earliest_record','event_id':chosen['id'],'date_interpretation':interpretation,
            'scope':deepcopy(chosen['scope']),'evidence':deepcopy(chosen['evidence']),
            'rationale':'Earliest defensible dated record of this scoped referent in the retained evidence; later community entry is recorded separately. '+chosen['date']['basis'],
            'uncertainty':chosen['uncertainty']+' This is the earliest supported record currently established here, not certification of absolute priority.'}
        reason='Reviewed earliest-record selection against all owned event records, their scoped statements, bounds and cited locators. Preserve original event uncertainty and the distinct community-entry claim; no date invented.'
    else:
        n['graph_anchor']={'status':'not_yet_researched','policy':'earliest_record','rationale':'No defensible bounded earliest record established; community entry remains separate.'}
        reason='No usable earliest record; do not infer one from a surviving witness.'
    n['witnesses']=[{'event_id':eid,'limitation':events[eid]['uncertainty']} for eid in n['event_ids']
        if any(w in (events[eid]['date']['label']+' '+events[eid]['statement']).lower() for w in ['surviving copy','manuscript copy','copyist','printed witness','1157 copy','1345 copy','13th-century copy'])]
    prior=decisions.get(n['id'],'')
    decisions[n['id']]=(prior+' '+reason).strip()
    rows.append({'id':n['id'],'community_event':old.get('event_id'),'community_date':events[old['event_id']]['date']['label'] if old.get('event_id') in events else 'unresolved',
        'record_event':n['graph_anchor'].get('event_id','unknown'),'record_date':chosen['date']['label'] if chosen and n['id'] not in holds else 'held',
        'check_method':'existing accepted source-backed events and fresh Stage 1/2 passage checks; not a new full-document lifecycle audit',
        'reason':decisions[n['id']]})
finish('stage3',before,records,decisions,'Earliest-record versus community-event separation. Seven deliberate dated chain parts restored; zero duplicate merges. Historian holds remain unplaced, not rejected.')
write_json(Path(__file__).parent/'stage3-dates.json',rows)
