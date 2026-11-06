"""Repair bounded functions, explicit development and noncausal families."""
from common import *

records=load();before=deepcopy(records);decisions={};nodes=index(records['nodes']);events=index(records['events'])
def ep(nid):
    eid=nodes[nid]['graph_anchor'].get('event_id')
    return {'node_id':nid,**({'event_id':eid} if eid else {})}
def add(rid,a,b,relation,statement,sid,locator,limit):
    assert rid not in index(records['relationships'])
    r=link(rid,ep(a),ep(b),relation,statement,[evidence(sid,locator,statement)],
        'The relation concerns the scoped events and functions; no transmission inferred from chart placement.',limit)
    # Noncausal links carry no historical event-order assertion.
    records['relationships'].append(r)
    decisions[rid]='Reopened retained cited source at the specified passage. '+limit+' Confidence concerns this bounded statement; influence is not assessed.'

add('revision-oxide-mask-to-planar','elec-oxide-diffusion-mask-1955','elec-hoerni-planar-transistor-1959','bounded-technical-requirement',
    'The planar configuration uses oxide masking and retains oxide over the junction edges rather than removing that protective layer.',
    'elec-chm-planar-process','Main narrative: oxide masking and Hoerni’s retained-oxide process',
    'A bounded process-function connection, not proof that Hoerni read a particular Bell paper or acquired Atalla’s work. That knowledge route remains a historian question.')
add('revision-mos-to-4004','elec-atalla-kahng-mos-1959','elec-intel-4004-cpu-1971','bounded-technical-requirement',
    'The 4004 is a MOS integrated implementation; its transistor function belongs to the insulated-gate MOS architecture.',
    'elec-chm-4004-cpu','1971 milestone, MOS LSI and silicon-gate implementation narrative',
    'Device-class function, not use of Atalla and Kahng’s physical prototype or a demonstrated personal transmission route.')
add('revision-volta-to-ampere','elec-volta-batteries-1800','elec-ampere-parallel-currents-1820','bounded-technical-requirement',
    'Ampère’s electrodynamic account explicitly uses the voltaic pile as a sustained-current source in discussing closed conducting circuits.',
    'elec-ampere-1820','Opening treatment of electromotive action, Volta’s pile and closed circuits',
    'A power-source capability connection; it does not settle the distinct Volta-to-Ørsted trough-construction history.')
add('revision-induction-to-lauffen','elec-faraday-ring-induction-1831','entry-electronics-lauffen-frankfurt-1891','bounded-technical-requirement',
    'The Lauffen–Frankfurt system used transformers at both ends of its alternating-current transmission, requiring electromagnetic induction between circuits.',
    'entry-elec-lauffen','Contemporary report: three transformers at Lauffen and three at Frankfort',
    'Bounded physical-function synthesis; not documentary descent from Faraday’s particular ring apparatus.')
add('revision-induction-to-pearl-street','elec-faraday-moving-magnet-1831','entry-electronics-pearl-street-1882','bounded-technical-requirement',
    'Pearl Street’s steam-driven dynamos generated current through electromagnetic induction, the phenomenon represented by the moving-magnet experiment.',
    'entry-elec-pearl-street','Six steam-driven Jumbo dynamos paragraph',
    'The particular Faraday apparatus was not an ancestor machine copied by Edison. A bounded induction requirement does not fill the missing dynamo-development history.')
add('revision-condenser-to-old-bess','mech-condenser-specification-1769','mech-soho-old-bess-returning','bounded-technical-requirement',
    'Old Bess embodied Watt’s separate-condenser arrangement, keeping condensation separate from the working cylinder.',
    'entry-mech-oldbess-smg','Object description: engine embodied the separate condenser',
    'The arrangement is a scoped functional input, not proof that a particular later printed edition instructed the builders.')
add('revision-expansion-and-double-expansive','mech-expansion-specification-1782','mech-soho-double-expansive','same-principle',
    'The double-expansive arrangement and Watt’s 1782 specification share expansive working; the museum account places the design in that patent programme.',
    'entry-mech-double-expansive','Description: 1781 attention to expansion and 12 March 1782 patent',
    'Noncausal affinity/programme relation. This does not settle whether Shadwell actually operated expansively.')
add('revision-nine-chapters-and-fangcheng','math-nine-chapters-text','math-nine-chapters-fangcheng','companion-of',
    'Fangcheng is the simultaneous-equation procedure presented in chapter eight of the Nine Chapters.',
    'entry-exp-calculation-nine','Chapter eight description, simultaneous linear equations',
    'Noncausal text/procedure membership, not proof that the completed handbook caused the procedure’s invention.')
for rid,a,b in [('revision-hierapolis-gerasa-family','mech-hierapolis-geared-stone-saw','mech-gerasa-water-stone-saw'),
                ('revision-gerasa-ephesos-family','mech-gerasa-water-stone-saw','mech-ephesos-water-stone-saw')]:
    add(rid,a,b,'same-family','The named sites provide related evidence for water-powered reciprocating stone-saw configurations.',
        'entry-mech-ritti-2007','Opening comparison and sections on Hierapolis, Ephesos and Gerasa',
        'Documented technical family, not established geographical diffusion or direct machine-to-machine ancestry.')

def derived_event(nid,eid,year,kind,sid,locator,statement):
    n=nodes[nid];e=deepcopy(events[n['event_ids'][0]])
    e.update(id=eid,node_id=nid,event_type=kind,statement=statement,
        date={'status':'known','precision':'year','calendar':'historical-BCE-CE','label':str(year),
              'basis':'Explicitly dated episode in the reopened cited account.','earliest':{'year':year},'latest':{'year':year}},
        evidence=[evidence(sid,locator,statement)],uncertainty='The source supports this recorded episode; it does not authenticate every statement as part of an earlier oral presentation.')
    e['provenance']={'method':'source-evidence','source_ids':[sid],'note':'Freshly separated event for exact relationship timing.'}
    records['events'].append(e);n['event_ids'].append(eid);events[eid]=e
    if kind in n['lifecycle']:
        state=n['lifecycle'][kind];state['status']='documented';state['event_ids'].append(eid);state['evidence']+=e['evidence'];state['rationale']='Distinct source-supported events, without treating later print as proof of earlier spoken content.'
    decisions[eid]=decisions[nid]='Reopened cited source and separated the receiving/publication episode; original community event retained. No date invented.'
    return e

e=derived_event('entry-electronics-edsac-program-service-1950','revision-edsac-lyons-exchange-1947',1947,'documented_description',
    'entry-elec-edsac','LEO section: In July 47 Lyons made an agreement',
    'Lyons agreed in July 1947 to contribute funds and a technician in exchange for EDSAC experience for its commercial computer project.')
n=nodes[e['node_id']];a=n['graph_anchor'];a.update(event_id=e['id'],scope=deepcopy(e['scope']),evidence=e['evidence'],
    rationale='The July 1947 exchange agreement records knowledge of the EDSAC project before its 1949 logged run; the 1950 service entry remains separate.',uncertainty='The year of the source’s “July 47” episode is recorded without inventing a day; this is project knowledge, not a claim that EDSAC already ran in 1947.')
for r in records['relationships']:
    if r['id']=='entry-electronics-edsac-informs-leo':
        r['from']={'node_id':n['id'],'event_id':e['id']};r['temporal_note']='The July 1947 exchange of EDSAC experience precedes the 1951 LEO job; it is distinct from EDSAC’s 1950 formal service.'
        decisions[r['id']]='Reopened Cambridge LEO section; bound the source contribution to the actual 1947 exchange rather than the later service anchor.'
e=derived_event('mech-thomson-dynamical-heat-1851','revision-thomson-dynamical-printed-1852',1852,'publication',
    'mech-s2-thomson-1851','Paper bibliographic header and §§14,29',
    'The printed dynamical-heat account acknowledges Clausius and reports Joule’s refined equivalent while using a rounded constant.')
for r in records['relationships']:
    if r['id']=='mech-clausius-to-thomson-dynamical':
        r['from']={'node_id':'mech-clausius-heat-work-1850','event_id':'mech-clausius-heat-work-1850--publication'}
        r['to']={'node_id':e['node_id'],'event_id':e['id']}
        r['temporal_note']='Clausius’s 1850 memoir precedes the printed 1852 account. The printed acknowledgement is not independently dated to an oral presentation.'
        decisions[r['id']]='Reopened printed §14; bind the evidenced acknowledgement to print rather than retroactively authenticating oral content.'
    if r['id']=='mech-joule-refined-to-thomson-dynamical':
        r['statement']='Thomson quotes Joule’s refined equivalent as 772.69 and uses the rounded value 772 in the numerical calculation.'
        r['to']={'node_id':e['node_id'],'event_id':e['id']}
        decisions[r['id']]='Reopened printed §29: distinguish the reported measurement from the rounded working constant.'

finish('stage6',before,records,decisions,'Ten source-confirmed function/development/family links and exact event bindings. No historian question or refused speculative long-range edge was settled.')
