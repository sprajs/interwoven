"""Apply only passage-confirmed Stage 2 corrections. Run once on Stage 1."""
from common import *

records = load(); before = deepcopy(records); nodes = index(records['nodes']); events = index(records['events'])
decisions = {}
rejected = {'chem-ph-scale-to-oxford-penicillin':'Production pH evidence does not support the specifically anchored clinical treatment endpoint.',
            'entry-regional-link-tirta-waterworks-irrigation':'The inscription co-documents dam repair and irrigation but does not establish the drawn hydraulic route.'}
records['relationships'] = [r for r in records['relationships'] if r['id'] not in rejected]
decisions.update(rejected)

def endpoint(nid, eid):
    assert events[eid]['node_id'] == nid
    return {'node_id':nid, 'event_id':eid}

def add(r, reason):
    assert r['id'] not in index(records['relationships'])
    records['relationships'].append(r); decisions[r['id']] = reason

add(link('revision-regnault-to-clausius',
    endpoint('mech-regnault-steam-data-1847','mech-regnault-steam-data-1847--event-01'),
    endpoint('mech-clausius-heat-work-1850','mech-clausius-heat-work-1850--publication'),
    'documented-development', 'Clausius used Regnault’s steam measurements in the numerical evaluation of his heat-work argument.',
    [evidence('mech-s2-clausius-1850','First Memoir, printed pp. 53–54, equations 23–24','Explicit attribution and numerical use of Regnault’s latent-heat results.')],
    'The 1847 published data precede Clausius’s 1850 memoir; publication month remains unresolved.',
    'This is a particular numerical input, not a claim that Regnault supplied the whole theory.'),
    'Reopened First Memoir pp. 53–54: explicit use, not mere bibliographic co-occurrence. Other components unchanged.')
add(link('revision-joule-first-to-revised-apparatus',
    endpoint('mech-joule-magnetocalorimeter-1843','mech-joule-magnetocalorimeter-1843--event-01'),
    endpoint('mech-joule-series-two-apparatus-1843','mech-joule-series-two-apparatus-1843--experimental-use'),
    'documented-adaptation','Joule retained the revolving electromagnet while replacing the inducing arrangement for his second experimental series.',
    [evidence('mech-s2-joule-1843','1843 paper, printed pp. 124–131, first apparatus and second series','Describes the initial reused engine magnets and subsequent newly constructed magnet around the revolving apparatus.')],
    'Both are reported in 1843; the paper orders the experimental series without assigning an invented day.',
    'The configurations are distinct roles in one experimental programme, not independently invented complete instruments.'),
    'Reopened apparatus description and second-series paragraph: new magnet fixed around existing revolving electromagnet. Preserve deliberate split.')
add(link('revision-polymerase-to-plus-minus',
    endpoint('bio-dna-polymerase-preparation-1957','bio-dna-polymerase-preparation-1957--event-01'),
    endpoint('bio-plus-minus-sequencing-1974','bio-plus-minus-sequencing-1974--publication-entry'),
    'bounded-technical-requirement','Sanger and Coulson’s plus/minus sequencing method used DNA polymerase I as a synthesis reagent.',
    [evidence('bio-sanger-coulson-1975','Principle of the method, printed pp. 442–443','Explicit use of DNA polymerase I in the described method.')],
    'The enzyme-preparation capability is recorded by 1957, before the 1975 published method.',
    'Enzyme-class capability is the source referent. No use of Kornberg’s original physical preparation or unique transmission route is asserted.'),
    'Reopened the Principle section: polymerase I is an actual functional input. Historical method-use only; no new experimental instructions.')
add(link('revision-induction-to-joule-calorimeter',
    endpoint('elec-faraday-moving-magnet-1831','elec-faraday-moving-magnet-1831--event-01'),
    endpoint('mech-joule-magnetocalorimeter-1843','mech-joule-magnetocalorimeter-1843--event-01'),
    'bounded-technical-requirement','The magneto-electric operation measured by Joule uses electromagnetic induction, the phenomenon demonstrated by Faraday’s moving-magnet experiment.',
    [evidence('mech-s2-joule-1843','1843 paper, printed pp. 124–126, apparatus introduction','Identifies induction of magneto-electricity in Joule’s arrangement.'),
     *events['elec-faraday-moving-magnet-1831--event-01']['evidence']],
    'The 1831 demonstration precedes the apparatus reported in 1843.',
    'A bounded physical-function synthesis, not proof that Joule copied this particular apparatus or read a specific report.'),
    'Reopened Joule’s initial inducing-magnet description and retained Faraday experiment. Bounded phenomenon requirement, not documentary personal transmission.')

def add_event(nid, eid, kind, date, statement, ev, uncertainty):
    n=nodes[nid]; original=events[n['event_ids'][0]]
    e=deepcopy(original);e.update(id=eid,node_id=nid,event_type=kind,date=date,statement=statement,evidence=ev,uncertainty=uncertainty)
    e['provenance']={'method':'source-evidence','source_ids':list(dict.fromkeys(x['source_id'] for x in ev)), 'note':'Reopened source; distinct historical event, not a display-date conflation.'}
    records['events'].append(e);n['event_ids'].append(eid)
    if kind in n['lifecycle']:
        n['lifecycle'][kind]={'status':'documented','event_ids':[eid],'rationale':statement,'evidence':ev}
    decisions[eid]=decisions[nid]='Reopened cited source; added only the separate dated event. Community entry and chart anchor are handled in Stage 3. '+uncertainty

add_event('entry-electronics-edsac-program-service-1950','revision-edsac-first-logged-program','demonstration',
    {'status':'known','precision':'day','calendar':'historical-BCE-CE','label':'6 May 1949','basis':'Cambridge relics chronology, First logged program entry.','earliest':{'year':1949,'month':5,'day':6},'latest':{'year':1949,'month':5,'day':6}},
    'EDSAC ran its first logged program on 6 May 1949.',[evidence('entry-elec-edsac','First logged program: May 6 49','Complete computer working, input from paper tape and output by teleprinter.')],
    'The first logged run is distinct from formal research service in 1950 and does not date the earlier design agreement.')
add_event('entry-regional-musawwarat-great-hafir','revision-great-hafir-construction','production',
    {'status':'bounded','precision':'century','calendar':'historical-BCE-CE','label':'Sixth–fourth centuries BCE','basis':'Project chronology explicitly reports the radiocarbon-constrained construction interval.','earliest':{'year':-600},'latest':{'year':-301}},
    'The Musawwarat project dates construction of the Great Hafir between the sixth and fourth centuries BCE.',
    [evidence('entry-regional-source-musawwarat-chronology','Chronology, Great Hafir paragraph','Radiocarbon-based construction interval, distinct from later Meroitic occupation.')],
    'Century bounds express the reported interval, not exact construction endpoints. This does not date every inlet, duct or subsequent use.')
finish('stage2',before,records,decisions,'Owner-authorized Stage 2: remove unsupported drawn associations, add four passage-confirmed links, and separate two confirmed dated facts. Historian questions remain open.')
