#!/usr/bin/env python3
"""Freeze 100 retained genuine candidates without network or model calls."""
import argparse, collections, hashlib, json, re, subprocess, unicodedata
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
RETAINED = ROOT.parent / 'big_idea-research-state/workflow-20261110/retained/expand'
PRIVATE = ROOT.parent / 'big_idea-research-state/workflow-20261110/comparison/evidence'
OUT = ROOT / 'docs/reviews/2026-11-10-workflow-comparison'
SEED = 'workflow-comparison-2026-11-10-v1'
SELECTION = {
'ordinary_institutional':'201:0 201:5 202:0 202:1 202:5 203:1 203:2 204:4 205:0 205:1 205:2 205:4 205:5 206:0 206:3 206:5 207:0 207:5 208:2 208:3 208:4 208:5 209:0 209:1 210:1',
'archaeology_uncertainty':'201:1 202:3 203:0 203:3 203:4 203:5 204:0 204:1 209:2 209:3 209:5 210:3 213:3 213:5 214:0',
'contested_origin_transmission':'201:2 201:3 204:2 206:1 206:2 207:1 207:2 207:3 207:4 208:0 208:1 210:2 211:0 217:0 218:1',
'underrepresented_regions':'202:4 204:3 204:5 205:3 206:4 210:0 210:5 211:2 211:3 212:1 212:5 213:1 214:1 214:2 214:5 216:4 218:0 218:2 218:4 219:0',
'duplicate_extension':'101:1 101:3 103:0 103:1 104:0 104:1 104:3 104:4 105:3 106:0 106:1 106:2 106:3 108:0 108:1',
'retrieval_failures':'201:4 202:2 211:1 212:3 213:2 217:4 217:5 218:3 219:2 219:3'}
CALIBRATION = dict(zip(SELECTION, [5,3,3,4,3,2]))
def sha(value):
    return hashlib.sha256(value if isinstance(value,bytes) else value.encode()).hexdigest()
def quote_offset(full, quote):
    """Locate retained extraction despite PDF whitespace/diacritic differences."""
    if not quote:
        return -1, 'no_retained_quotation'
    exact = full.find(quote)
    if exact >= 0:
        return exact, 'exact_substring'
    def normalized(text):
        chars, offsets = [], []
        for offset, char in enumerate(text):
            for letter in unicodedata.normalize('NFKD', char).lower():
                if letter.isalnum():
                    chars.append(letter); offsets.append(offset)
        return ''.join(chars), offsets
    haystack, offsets = normalized(full)
    needle, _ = normalized(quote)
    position = haystack.find(needle)
    if needle and position >= 0:
        return offsets[position], 'normalized_substring'
    # Context is only a navigation aid, never proof that the quote is exact.
    position = haystack.find(needle[:60]) if len(needle) >= 60 else -1
    return (offsets[position], 'partial_navigation_anchor') if position >= 0 else (-1, 'requires_original_check')
def split_cases(cases):
    for stratum,count in CALIBRATION.items():
        group=sorted((c for c in cases if c['stratum']==stratum),key=lambda c:sha(SEED+':'+c['id']))
        for i,c in enumerate(group): c['split']='calibration' if i<count else 'held_out'
def match_context(record):
    """Snapshot context for scope comparison, not fresh evidence of its claims."""
    context={key:record[key] for key in ('id','name','summary','concept','origin','societies','places') if key in record}
    context['events']=[{key:event[key] for key in ('type','date','label','earliest_year','latest_year','statement','place','societies') if key in event} for event in record.get('events',[])]
    context['status']='Committed snapshot assertions; compare scope and seek source support independently'
    return context
def validate(cases):
    assert len(cases)==100 and len({c['id'] for c in cases})==100
    assert collections.Counter(c['split'] for c in cases)=={'calibration':20,'held_out':80}
    for s,selection in SELECTION.items():
        group=[c for c in cases if c['stratum']==s]
        assert len(group)==len(selection.split())
        assert sum(c['split']=='calibration' for c in group)==CALIBRATION[s]
        assert all(bool(c['evidence'])==(s!='retrieval_failures') for c in group)
def prepare(retained=RETAINED,private=PRIVATE):
    commit=subprocess.check_output(['git','rev-parse','38dfdb6'],cwd=ROOT,text=True).strip()
    paths=subprocess.check_output(['git','ls-tree','-r','--name-only',commit,'data/discoveries'],cwd=ROOT,text=True).splitlines()
    records=[json.loads(subprocess.check_output(['git','show',f'{commit}:{p}'],cwd=ROOT)) for p in paths if p.endswith('.json')]
    private.mkdir(parents=True,exist_ok=True)
    cases=[]; words=collections.Counter()
    for stratum,selectors in SELECTION.items():
        for selector in selectors.split():
            batch,index=map(int,selector.split(':'))
            path=retained/f'research/batch-{batch}-cards.json'
            card=json.loads(path.read_text())['cards'][index]
            leads=json.loads((retained/f'research/batch-{batch}-input.json').read_text())['leads']
            lead=next(l for l in leads if l['title']==card['lead'])
            cid='candidate-'+sha(lead['title'])[:16]
            exact=[r['id'] for r in records if r['name']==card.get('name')]
            related=[r['id'] for r in records if card.get('concept') and r.get('concept')==card['concept'] and r['id'] not in exact]
            evidence=[]
            for i,source in enumerate(card.get('sources',[])):
                url=source['url']; filename=re.sub(r'[^a-zA-Z0-9]+','_',url)[:150]+'.txt'
                saved=retained/'pages'/filename
                if not saved.exists(): saved=ROOT/'.cache/pages'/filename
                raw=saved.read_bytes() if saved.exists() else b''; full=raw.decode('utf-8','replace')
                page_sha=sha(raw); dest=private/(page_sha+'.txt')
                if raw and not dest.exists(): dest.write_bytes(raw)
                events=[e for e in card.get('events',[]) if e.get('source')==i and e.get('quote')]
                quote=events[0]['quote'] if events else ''; pos, quote_status=quote_offset(full,quote)
                text=' '.join(quote.split()[:min(80,max(0,200-words[url]))]); words[url]+=len(text.split())
                start=max(0,pos-800) if pos>=0 else 0
                evidence.append({'id':f'{cid}-source-{i+1}','url':url,'title':source.get('title'),'sha256':page_sha if raw else None,'text':text,'text_sha256':sha(text),'locator':events[0].get('locator','Retained quotation') if events else 'Saved source text','context':{'private_path':str(dest) if raw else None,'start':start,'end':min(len(full),start+3200),'quotation_exact_offset':pos if quote_status=='exact_substring' else -1,'navigation_anchor_offset':pos,'encoding':'utf-8'},'access_status':'saved_page' if raw else 'retained_quotation_only','quotation_status':quote_status,'retained_card_locator':f'{path.name}#/cards/{index}/sources/{i}'})
            case={'id':cid,'stratum':stratum,'candidate':{'name':lead['title'],'community':lead.get('where'),'question':lead.get('verify'),'hypothesis':{k:lead[k] for k in ('concept','kind','field','region','date','year','origin') if k in lead},'hypothesis_status':'Unverified retained lead, not reference truth'},'dataset_snapshot':commit,'screen':{'decision':'review_existing_scope' if exact or related else 'research','matches':[{'id':i,'basis':'exact_retained_card_name'} for i in exact]+[{'id':i,'basis':'same_concept_only'} for i in related],'rationale':'Mechanical screening only. Exact retained card name or shared concept does not prove historical duplication; compare community, events and scope.'},'evidence':evidence,'source_access_status':'saved_evidence' if evidence and all(e['sha256'] for e in evidence) else 'missing_or_incomplete','provenance':{'retained_file':str(path),'retained_file_sha256':sha(path.read_bytes()),'card_index':index}}
            case['screen']['match_context']=[match_context(r) for r in records if r['id'] in exact+related]
            if not evidence: case['access_failure']={'retained_note':card.get('note',''),'kind':'recorded_no_source_or_unresearched','not_a_synthetic_outage':True}
            cases.append(case)
    split_cases(cases);validate(cases);OUT.mkdir(parents=True,exist_ok=True)
    payload={'schema_version':1,'cases':sorted(cases,key=lambda c:c['id'])}
    encoded=(json.dumps(payload,ensure_ascii=False,indent=2)+'\n').encode();(OUT/'cases.json').write_bytes(encoded)
    registration={'schema_version':1,'registered_before_model_calls':True,'benchmark_calls_made_by_preparation':0,'seed':SEED,'dataset_snapshot':commit,'cases_sha256':sha(encoded),'candidate_ids':sorted(c['id'] for c in cases),'strata':{s:{'total':len(v.split()),'calibration':CALIBRATION[s],'held_out':len(v.split())-CALIBRATION[s]} for s,v in SELECTION.items()},'selection':'85 next-wave real leads and 15 earlier exact-name identity/scope controls; mutually exclusive primary sampling strata are not reference judgments. Earlier controls intentionally overlap the committed dataset.','evidence_policy':'Identical frozen payloads for both arms. No card decisions or reference answers. Content-addressed private original saved pages plus bounded 3200-character windows; public excerpts <=200 words per URL across fixture. Missing evidence stays missing. Up to three shared frozen retrieval requests per candidate; no post-registration live evidence replacement.','model_presets':{'source':'Runner must use user-requested model presets without silent substitution','answer_token_target':[1000,2000],'total_reasoning_token_ceiling':25000,'max_search_requests':3},'calibration_policy':'Only 20 calibration cases may guide prompt changes. Freeze prompts/settings before 80 held-out runs; never tune against held-out outputs/reference decisions.','reference_policy':'Independent blinded source-reading review after registration, using originals rather than retained card decisions. Review community, event/date scope, origin and every proposed link; resolve disagreements separately. Unresolved evidence is excluded from false-reject denominator and reported separately. No model judgment is reference truth.','quality_gate':{'held_out_false_admissions_max':0,'held_out_unsupported_links_max':0,'false_reject_rate_max_among_resolved_reference_admissions':0.05,'unsupported_facet_policy':'Every asserted date/place/person/origin/link must have source support; unsupported admissions fail.','uncertainty_policy':'Abstention or request-more-evidence is appropriate for unresolved references; report separately with coverage.','winner_policy':'No winner if independent resolved reference coverage or quality evidence is insufficient. Among arms passing gates compare paired correctness, then latency/cost; report uncertainty and stratum counts without implying statistical certainty from 80 cases.'}}
    registration['model_presets']={
        'arm_A':{'researcher':{'model':'gpt-6-luna','effort':'low'},'supervisor':{'model':'gpt-6.1-terra','effort':'medium'}},
        'arm_B':{'researcher':{'model':'gpt-6.1-terra','effort':'low'},'supervisor':{'model':'gpt-6.1-sol','effort':'medium'}},
        'proposal_generation':[{'model':'gpt-6.1-sol','effort':'medium'},{'model':'gpt-6-astra','effort':'low'},{'model':'gpt-6-astra','effort':'medium'}],
        'answer_token_target':[1000,2000], 'proposal_visible_token_target':1800,
        'total_reasoning_token_ceiling':None,
        'reasoning_ceiling_limitation':'The documented Codex CLI does not expose a strict 25,000 reasoning-token ceiling. Effort presets are not token caps. Do not claim this ceiling was enforced.',
        'max_search_requests':3,'capability_checks':'All named settings passed genuine capability calls before benchmark calls; capability probes are not comparison results.'}
    registration['finite_guards']={'max_calls':650,'max_elapsed_seconds':7200,'max_input_tokens':12000000,'max_output_tokens':1500000,'max_standard_api_equivalent_usd':60,'request_timeout_seconds':150,'retry_count':0,'workers':4,'enforcement':'Check cumulative token/cost/call/time guards between calls. Up to four in-flight requests may overshoot token or cost limits; request timeout is separate from total elapsed guard.'}
    registration['proposal_generation_policy']={'candidates_per_preset':12,'web_access':False,'same_input_context':True,'visible_token_target':1800,'separate_metrics':['count','uniqueness','scope_novelty_after_snapshot_screening','sourceability_requires_later_research','latency','tokens','standard_api_equivalent_cost'],'admission_policy':'Suggestions are assessed separately; none enters the preregistered 100-case admission benchmark or the dataset.'}
    registration['reference_policy']='Astra medium creates a blinded, source-based reference-only review independently of both arms, with no arm outputs in its prompt. This is a model reference, not independent historical truth. Root selectively reviews disputes against originals. Disclose model correlation and selective verification; report unresolved cases and sensitivity to reference uncertainty. No model judgment alone establishes historical truth.'
    (OUT/'preregistration.json').write_text(json.dumps(registration,ensure_ascii=False,indent=2)+'\n')
    return payload
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--retained',type=Path,default=RETAINED);parser.add_argument('--private-evidence',type=Path,default=PRIVATE);args=parser.parse_args()
    print(f"Registered {len(prepare(args.retained,args.private_evidence)['cases'])} candidates; no model calls.")
