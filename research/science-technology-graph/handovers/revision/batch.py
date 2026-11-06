"""Construct ranked, source-bounded additions without inventing lifecycle facts."""
from common import *
from urllib.request import Request, urlopen
from urllib.parse import urlparse

def capture_note(sid,title,url,locator,note):
    """Explicit live-read note when raw capture fails; never labelled original."""
    path=ROOT/'evidence/acquired'/f'{sid}.read-note.txt'
    path.write_text('Attributed research note, 6 November 2026\n'+title+'\n'+url+'\nLocator: '+locator+'\n\n'+note+'\n\nLive source was reopened and read. This is a researcher’s bounded paraphrase, not an original-source capture.\n')
    return {'schema_version':1,'id':sid,'title':title,'url':url,'authors':[urlparse(url).hostname],'year':'Undated web source; see original attribution','accessed':'2026-11-06','access':'partial-text',
        'version':'Live-read attributed research note; original web response could not be retained.',
        'inspected_passages':[{'locator':locator,'assessment':'Live passage read; bounded paraphrase retained separately.'}],
        'evidence_lineage':'Live source was inspected directly. Local bytes are an attributed research note, not the source itself or independent corroboration.',
        'local_copy':{'path':str(path.relative_to(ROOT)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}}

def capture_source(sid,title,url,locator,checked,access='full-text'):
    path=ROOT/'evidence/acquired'/f'{sid}.html'
    if not path.exists():
        try:
            raw=urlopen(Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=45).read()
        except Exception as exc:
            raise RuntimeError(sid+': '+str(exc)) from exc
        if len(raw)<200:raise ValueError('No substantive retained source: '+sid)
        path.write_bytes(raw)
    raw=path.read_bytes()
    assert checked.casefold() in raw.decode('utf8',errors='replace').casefold(),('Expected passage absent',sid,checked)
    return {'schema_version':1,'id':sid,'title':title,'url':url,'authors':[urlparse(url).hostname],'year':'Undated web source; see original attribution','accessed':'2026-11-06','access':access,
        'version':'Retained web response; claims limited to the named inspected passage.',
        'inspected_passages':[{'locator':locator,'assessment':'Read directly; historical content and dates checked against the scoped addition.'}],
        'evidence_lineage':'Original website response retained. Source authorship and any retrospective dating are distinguished from the historical event.',
        'local_copy':{'path':str(path.relative_to(ROOT)),'sha256':hashlib.sha256(raw).hexdigest(),'representation':'full_source'}}

def year_date(year,label,basis,known_by=False,approximate=False,earliest=None):
    d={'status':'approximate' if approximate else 'bounded' if known_by or earliest is not None else 'known',
       'precision':'range' if earliest is not None else 'year','calendar':'historical-BCE-CE','label':label,'basis':basis,'latest':{'year':year}}
    if known_by:d['earliest_status']='unknown'
    else:d['earliest']={'year':year if earliest is None else earliest}
    return d

def add_entry(records,decisions,rid,label,kind,configuration,regions,labels,tier,tier_reason,
              record_date,record_ev,community_date,community_ev,community,basis='public_awareness',uncertainty=''):
    assert rid not in index(records['nodes']),rid
    common_uncertainty=uncertainty+' Earliest means earliest source-supported record established for this scoped referent here, not certified global priority.'
    scope={'regions':regions,'configuration':configuration,'applications':[], 'market':{'status':'not_yet_researched'},'population':{'status':'specified','value':community}}
    events=[]
    for eid,etype,date,ev,statement in [(rid+'--record','archaeological_evidence' if record_date['latest']['year']<0 else 'documented_description',record_date,record_ev,configuration),
         (rid+'--community',{'public_awareness':'publication','practical_use':'practical_use','recognition':'recognition','public_availability':'public_availability'}[basis],community_date,community_ev,configuration+' This event supports the specified community-entry claim only.')]:
        e={'schema_version':1,'id':eid,'node_id':rid,'event_type':etype,'date':date,'scope':deepcopy(scope),'statement':statement,
           'evidence':ev,'uncertainty':common_uncertainty,'provenance':{'method':'source-evidence','source_ids':list(dict.fromkeys(x['source_id'] for x in ev)),'note':'Read source, bounded proposition; no lifecycle inference from fame.'}}
        events.append(e);decisions[eid]='Freshly read source at stated locator. Date and referent checked; '+common_uncertainty
    lifecycle={stage:{'status':'not_yet_researched','event_ids':[],'rationale':'This distinct question is not established by this batch.','evidence':[]} for stage in ['invention','first_commercial_availability','practical_deployment','adoption','discovery','observation','formulation','publication','experimental_confirmation','acceptance','decline','withdrawal','end_of_use','abandonment','revival']}
    if kind in {'science','mathematics'}:
        for stage in ['invention','first_commercial_availability','practical_deployment']:
            lifecycle[stage].update(status='not_applicable',rationale='Knowledge content, not a commercial artifact or manufacturing milestone.')
    if events[1]['event_type'] in lifecycle:
        lifecycle[events[1]['event_type']]={'status':'documented','event_ids':[events[1]['id']],'rationale':'Only the sourced community event is established.','evidence':community_ev}
    interpretation=lambda d:'event_date' if 'earliest' in d else 'known_by'
    n={'schema_version':1,'id':rid,'label':label,'kind':kind,'configuration':configuration,'regions':regions,'labels':labels,
       'tier':tier,'tier_reason':tier_reason,'event_ids':[e['id'] for e in events],'lifecycle':lifecycle,
       'commercial_applicability':{'status':'not_applicable' if kind in {'science','mathematics'} else 'not_yet_assessed',
          'rationale':'Knowledge content.' if kind in {'science','mathematics'} else 'Commercial scope has not been established by this historical batch.','evidence':[]},
       'graph_anchor':{'status':'selected','policy':'earliest_record','event_id':events[0]['id'],'date_interpretation':interpretation(record_date),
          'scope':deepcopy(scope),'evidence':record_ev,'rationale':record_date['basis'],'uncertainty':common_uncertainty},
       'community_entry':{'status':'selected','policy':'community_entry','event_id':events[1]['id'],'entry_basis':basis,
          'date_interpretation':interpretation(community_date),'evidence_strength':'awareness_proxy' if basis=='public_awareness' else 'direct',
          'community':community,'scope':deepcopy(scope),'evidence':community_ev,'rationale':community_date['basis'],'uncertainty':common_uncertainty},
       'witnesses':[],'uncertainty':common_uncertainty,
       'provenance':{'method':'source-evidence','source_ids':list(dict.fromkeys(e['source_id'] for e in record_ev+community_ev)),'note':'Ranked Stage 7 gap admission after direct source reading. Inclusion is selective; no independent historian endorsement claimed.'}}
    if basis=='public_awareness':n['community_entry']['proxy_justification']='Dated publication provides an explicit awareness opportunity; no acceptance or widespread adoption is inferred.'
    records['nodes'].append(n);records['events']+=events
    decisions[rid]='Fresh scoped historical/date/topic review from the identified passages. Tier is an explicit consequence judgement: '+tier_reason+' No automatic ancestry, commercial availability or global first is asserted.'
    return n
