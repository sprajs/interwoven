#!/usr/bin/env python3
"""Reproduce private comparison accounting without model calls or source exports."""
from __future__ import annotations
import argparse, collections, csv, hashlib, json
from pathlib import Path
import subprocess, sys
from xml.sax.saxutils import escape
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from compare import RATES, api_cost, mechanical, exact_quote
ROOT=HERE.parents[1]
DEFAULT_OUT=ROOT/'docs/reviews/2026-11-10-workflow-comparison'
DEFAULT_STATE=ROOT.parent/'big_idea-research-state/workflow-20261110/comparison'
TOKENS=('input_tokens','cached_input_tokens','cache_write_input_tokens','output_tokens','reasoning_output_tokens')
COUNTERS=('date_errors','uncertainty_errors','duplicate_work','substantive_corrections','unresolved_source_access')
def sha(raw):
    return hashlib.sha256(raw if isinstance(raw,bytes) else raw.encode()).hexdigest()
def classify(call):
    label=str(call.get('label',''))
    if label in ('A-extract','A-review','B-extract','B-review'):
        arm,stage=label.split('-');return arm,stage
    text=(label+' '+str(call.get('case_id',''))).lower()
    if 'adjudicat' in text:return None,'adjudication'
    if 'proposal' in text or 'generat' in text:return None,'proposal'
    if label=='reference' or 'reference' in text:return None,'reference'
    return None,'other'
def sanitize(value):
    """Quote hashes replace quote strings; never export prompts/source contexts."""
    if isinstance(value,list):return [sanitize(v) for v in value]
    if not isinstance(value,dict):return value
    result={}
    for key,item in value.items():
        if key in ('quote','quotation'):result[key+'_sha256']=sha(item) if isinstance(item,str) else None
        elif key not in ('prompt','raw_prompt','original_context','context','stderr','conversation','response'):result[key]=sanitize(item)
    return result
def checked_usage(value):
    row={key:value.get(key,0) for key in TOKENS}
    if any(type(v) is not int or v<0 for v in row.values()):raise ValueError('Invalid token scalar')
    if row['cached_input_tokens']+row['cache_write_input_tokens']>row['input_tokens']:raise ValueError('Cache tokens exceed input')
    if row['reasoning_output_tokens']>row['output_tokens']:raise ValueError('Reasoning is a subset of output')
    return row
def public_judgment(row):
    """Expose bounded judgment labels/scalars, without source or reasoning text."""
    fields=('arm','resolved','reference_admit','false_admission','false_reject','unsupported_facets','unsupported_links','unresolved_admitted_claims','useful_reviewed_record','supported_claims',*COUNTERS,'extraction_claims','reviewed_claims')
    result={k:row[k] for k in fields if k in row and isinstance(row[k],(str,bool,int,float,type(None)))}
    for key in ('error_types','claim_judgment_labels'):
        if isinstance(row.get(key),list):result[key]=[s[:100] for s in row[key] if isinstance(s,str)][:20]
    if isinstance(row.get('claim_judgments'),list):
        result['claim_judgments']=[{
            **{k:v for k,v in claim.items() if k in ('index','verdict','facet','supported','label','error_type') and isinstance(v,(str,bool,int,type(None)))},
            'error_types':[v for v in (claim.get('error_types') or []) if v in ('date','uncertainty','link','facet','duplicate','quotation','scope')]
        } for claim in row['claim_judgments'] if isinstance(claim,dict)]
    return result
def empty_metrics():
    return dict(calls=0,successful_calls=0,failed_calls=0,inflight_calls=0,calls_without_usage=0,observed_tool_calls=0,tool_observation_unknown_calls=0,unique_responses=0,duplicate_response_ids=0,**{k:0 for k in TOKENS},uncached_input_tokens=0,api_equivalent_usd=0.0,api_equivalent_12h_write_usd=0.0,elapsed_sum_seconds=0.0)
def observed_tools(call,audit,raw_sha):
    """Unknown observations remain distinct from an observed empty tool list."""
    observed=call.get('observed_tool_calls')
    if not isinstance(observed,list) and audit:
        fingerprint=call.get('fingerprint')
        if (isinstance(fingerprint,str) and audit.get('fingerprint')==fingerprint
                and audit.get('call_sha256')==raw_sha):
            observed=audit.get('observed_tool_calls')
    if not isinstance(observed,list):return None
    if any(not isinstance(r,dict) or not isinstance(r.get('name'),str)
           or type(r.get('count')) is not int or r['count']<0 for r in observed):return None
    return sum(r['count'] for r in observed)
def review_mechanical(call):
    """Recheck the immutable model-visible evidence; never export its context."""
    try:
        case=json.loads(call.get('prompt',''))['case']
        if case.get('id')!=call.get('case_id') or not isinstance(case.get('evidence'),list):return None
    except (ValueError,KeyError,TypeError,AttributeError):return None
    result=call.get('parsed');checks=mechanical(result,case,review=True);categories=set()
    if isinstance(result,dict):
        sources={s['id']:s for s in case['evidence']}
        for claim in result.get('claims',[]) if isinstance(result.get('claims'),list) else []:
            if not isinstance(claim,dict):continue
            quote=claim.get('quote');source=sources.get(claim.get('source_id'))
            if not isinstance(quote,str) or not 8<=len(quote.split())<=45:categories.add('quote_length')
            if not source or not isinstance(quote,str) or not exact_quote(source.get('original_context',''),quote):categories.add('quote_presence')
    for error in checks['errors']:
        if 'invalid year bounds' in error:categories.add('date')
        elif 'original quote/reference' not in error:categories.add('schema')
    return {**checks,'failure_categories':sorted(categories),'admission_proposal':isinstance(result,dict) and str(result.get('decision','')).startswith('admit')}

def quality_metrics(cases,judgments,groups,mechanical_results=None):
    rows=(judgments or {}).get('judgments',[]);seen=set()
    ids={c['id'] for c in cases}
    for row in rows:
        key=(row['case_id'],row['arm'])
        if key in seen:raise ValueError('Duplicate quality judgment')
        if row['case_id'] not in ids or row['arm'] not in ('A','B') or type(row.get('resolved')) is not bool:
            raise ValueError('Invalid quality judgment identity/status')
        if row['resolved']:
            if any(type(row.get(k)) is not bool for k in ('reference_admit','false_admission','false_reject','useful_reviewed_record')):
                raise ValueError('Resolved judgment requires explicit decision/support flags')
            if any(type(row.get(k)) is not int or row[k]<0 for k in ('unsupported_facets','unsupported_links','supported_claims')):
                raise ValueError('Resolved judgment requires nonnegative support/error counts')
        seen.add(key)
    by_arm={}
    for arm in ('A','B'):
        eligible={c['id'] for c in cases if c['split']=='held_out'}
        selected=[r for r in rows if r['arm']==arm and r['case_id'] in eligible]
        resolved=[r for r in selected if r.get('resolved') is True]
        refs=[r for r in resolved if r.get('reference_admit') is True]
        rejected=sum(r.get('false_reject') is True for r in refs)
        def known_sum(key, boolean=False):
            present=[r for r in selected if type(r.get(key)) is (bool if boolean else int)]
            return sum(r[key] for r in present) if selected and len(present)==len(selected) else None
        admits=known_sum('false_admission',True)
        facets=known_sum('unsupported_facets');links=known_sum('unsupported_links')
        unresolved_claims=known_sum('unresolved_admitted_claims')
        raw_useful=known_sum('useful_reviewed_record',True);raw_claims=known_sum('supported_claims')
        checks={cid:(mechanical_results or {}).get((cid,arm)) for cid in eligible}
        mechanical_failures=sum(c is not None and c['pass'] is False for c in checks.values())
        mechanical_unknown=sum(c is None for c in checks.values())
        blocked=sum(r.get('useful_reviewed_record') is True and checks[r['case_id']] is not None and not checks[r['case_id']]['pass'] for r in selected)
        useful=sum(r.get('useful_reviewed_record') is True and checks[r['case_id']]['pass'] for r in selected) if raw_useful is not None and not mechanical_unknown else None
        claims=sum(r['supported_claims'] for r in selected if checks[r['case_id']]['pass']) if raw_claims is not None and not mechanical_unknown else None
        ratio=rejected/len(refs) if refs else None
        cost=sum(g['api_equivalent_usd'] for key,g in groups.items() if key.startswith(arm+'|held_out|'))
        complete=len(selected)==len(eligible)
        # A known unsupported admission fails even when historical priority is unresolved.
        known_failure=any(r.get('false_admission') is True or any(r.get(k,0)>0 for k in ('unsupported_facets','unsupported_links','unresolved_admitted_claims') if type(r.get(k)) is int) for r in selected)
        checks_known=all(value is not None for value in (admits,facets,links,unresolved_claims))
        gate=False if known_failure or mechanical_failures or (ratio is not None and ratio>.05) else True if complete and checks_known and ratio is not None and not mechanical_unknown else None
        quality_keys=('false_admission','unsupported_facets','unsupported_links','unresolved_admitted_claims')
        unknown=sum(any(k not in r for k in quality_keys) for r in selected)
        by_arm[arm]={'eligible_cases':len(eligible),'judged_cases':len(selected),'judgment_coverage_complete':complete,'unknown_quality_cases':unknown,'resolved_cases':len(resolved),'unresolved_cases':len(selected)-len(resolved),'resolved_reference_admissions':len(refs),'false_admissions':admits,'false_rejects':rejected if refs else None,'false_reject_rate':ratio,'unsupported_facets':facets,'unsupported_links':links,'unresolved_admitted_claims':unresolved_claims,'raw_semantic_useful_records':raw_useful,'mechanical_blocked_useful_records':blocked if selected else None,'mechanical_failure_count':mechanical_failures if selected else None,'mechanical_unknown_cases':mechanical_unknown,'source_judged_supported_claims':raw_claims,'usable_supported_claims':claims,'useful_reviewed_records':useful,'supported_claims':claims,'provisional_quality_gate':gate,'cost_per_useful_reviewed_record_usd':cost/useful if useful else None,'cost_per_supported_claim_usd':cost/claims if claims else None,'judgment_counters':{k:sum(r.get(k,0) for r in selected) if selected and all(k in r for r in selected) else None for k in COUNTERS},'correction_summary':{'extraction_claims':known_sum('extraction_claims'),'reviewed_claims':known_sum('reviewed_claims')}}
    for arm,metrics in by_arm.items():
        selected=[r for r in rows if r['arm']==arm and r['case_id'] in {c['id'] for c in cases if c['split']=='held_out'}]
        metrics['unsupported_relation_assertions']=sum(
            c.get('verdict')=='unsupported' and 'link' in c.get('error_types',[])
            for r in selected for c in r.get('claim_judgments',[])
        ) if selected and all(isinstance(r.get('claim_judgments'),list) for r in selected) else None
    return {'reference_standard':(judgments or {}).get('reference_standard','not_supplied'),'adequate_independent_reference':False,'arms':by_arm,'winner':None,'winner_reason':'Same-family model references/adjudication are provisional; agreement is not truth and does not support a confident winner.'}
def analyze(state=DEFAULT_STATE,cases_path=DEFAULT_OUT/'cases.json',judgments_path=None):
    state=Path(state);cases_path=Path(cases_path)
    cases_raw=cases_path.read_bytes();cases=json.loads(cases_raw)['cases'];by_id={c['id']:c for c in cases}
    if len(cases)!=100 or len(by_id)!=100:raise ValueError('Expected frozen 100-case fixture')
    calls=[(p,json.loads(p.read_text())) for p in (state/'calls').glob('*.json')]
    if not calls:raise ValueError('No actual call artifacts; refusing placeholder report')
    calls.sort(key=lambda pair:(pair[1].get('started',0),pair[0].name))
    audit_path=state/'tool-audit.json'
    audit_raw=audit_path.read_bytes() if audit_path.exists() else None
    audit_rows=json.loads(audit_raw).get('calls',[]) if audit_raw else []
    audit={r['call']:r for r in audit_rows}
    if len(audit)!=len(audit_rows):raise ValueError('Ambiguous duplicate tool-audit call')
    ownership={};rows=[];groups={};provenance=[];mechanical_results={}
    outputs={c['id']:{'id':c['id'],'name':c['candidate']['name'],'split':c['split'],'stratum':c['stratum'],'calls':[]} for c in cases}
    starts=[];ends=[]
    for path,call in calls:
        arm,category=classify(call);case=by_id.get(call.get('case_id'));split=case['split'] if case else 'overhead'
        model=call.get('params',{}).get('model');status=call.get('status','unknown')
        row={'call_file':path.name,'raw_call_sha256':sha(path.read_bytes()),'case_id':call.get('case_id'),'arm':arm or '', 'split':split,'stage':category,'model':model,'effort':call.get('params',{}).get('effort'),'status':status,**empty_metrics()}
        row.update(calls=1,successful_calls=int(status=='success'),failed_calls=int(status=='failed'),inflight_calls=int(status=='inflight'))
        row['calls_without_usage']=int(not call.get('usage_records'))
        row['observed_tool_calls']=observed_tools(call,audit.get(path.name),row['raw_call_sha256'])
        row['tool_observation_unknown_calls']=int(row['observed_tool_calls'] is None)
        elapsed=call.get('elapsed_seconds');started=call.get('started')
        if isinstance(elapsed,(int,float)) and elapsed>=0:row['elapsed_sum_seconds']=elapsed
        if isinstance(started,(int,float)):
            starts.append(started);ends.append(started+(elapsed if isinstance(elapsed,(int,float)) else 0))
        for rid,raw_usage in call.get('usage_records',{}).items():
            usage=checked_usage(raw_usage)
            if rid in ownership:
                if ownership[rid]!=(model,usage):raise ValueError('Conflicting global response ID: '+rid)
                row['duplicate_response_ids']+=1;continue
            if model not in RATES:raise ValueError('Unknown rate model: '+str(model))
            ownership[rid]=(model,usage);row['unique_responses']+=1
            for key in TOKENS:row[key]+=usage[key]
            row['uncached_input_tokens']+=usage['input_tokens']-usage['cached_input_tokens']-usage['cache_write_input_tokens']
            row['api_equivalent_usd']+=api_cost(model,usage)
            row['api_equivalent_12h_write_usd']+=api_cost(model,usage,2)
        key='|'.join((arm or 'overhead',split,category));group=groups.setdefault(key,empty_metrics())
        for metric in group:
            if row[metric] is not None:group[metric]+=row[metric]
        provenance.append({'file':path.name,'sha256':row['raw_call_sha256'],'fingerprint':call.get('fingerprint')})
        if case and category=='review' and arm:
            mechanical_results[(case['id'],arm)]=review_mechanical(call)
        if case:outputs[case['id']]['calls'].append({'stage':category,'arm':arm,'status':status,'model':model,'effort':row['effort'],'raw_call_sha256':row['raw_call_sha256'],'parsed':sanitize(call.get('parsed')),'mechanical_checks':mechanical_results.get((case['id'],arm)) if category=='review' else None})
        rows.append(row)
    totals=empty_metrics()
    for group in groups.values():
        for key in totals:totals[key]+=group[key]
    totals['elapsed_wall_seconds']=max(ends)-min(starts) if starts else None
    judgments=json.loads(Path(judgments_path).read_text()) if judgments_path else None
    for judgment in (judgments or {}).get('judgments',[]):
        if judgment.get('case_id') in outputs:
            outputs[judgment['case_id']].setdefault('judgments',[]).append(public_judgment(judgment))
    try:
        commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True,stderr=subprocess.DEVNULL).strip()
        worktree_dirty=bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True,stderr=subprocess.DEVNULL))
    except (subprocess.CalledProcessError,FileNotFoundError):
        # A Git archive remains analyzable; hashes retain provenance, Git state is unknown.
        commit=None
        worktree_dirty=None
    analysis={'schema_version':1,'source_commit':commit,'input_hashes':{'cases_sha256':sha(cases_raw),'raw_calls':provenance,'judgments_sha256':sha(Path(judgments_path).read_bytes()) if judgments_path else None},'accounting':{'totals':totals,'groups':groups,'rates_per_million_tokens':RATES,'cost_status':'Standard short-context API-equivalent estimate; not observed billing, credits, or subscription usage. Base cache-write scenario and doubled write-rate sensitivity.','token_semantics':'Input includes cache reads/writes; uncached=input-cached-write. Output includes reasoning; reasoning is a subset, never added twice. Global response IDs deduplicated.','elapsed_semantics':'Sum is aggregate request duration, wall is earliest request start to latest observed request end. Inflight durations are incomplete.','observed_billing':None,'subscription_credits':None},'quality':quality_metrics(cases,judgments,groups,mechanical_results),'coverage':{'registered_cases':100,'cases_with_any_output':sum(bool(c['calls']) for c in outputs.values()),'completed_review_counts':{a:sum(any(r['stage']=='review' and r['arm']==a and r['status']=='success' for r in c['calls']) for c in outputs.values()) for a in ('A','B')}},'limitations':['Source-only model references are not independent historical truth.','No strict per-request 25k reasoning-token ceiling is available.','Four inflight calls may overshoot between-call budget guards.','Quote presence and decision agreement do not establish claim support.']}
    analysis['coverage']['completed_held_out_review_counts']={a:sum(c['split']=='held_out' and any(r['stage']=='review' and r['arm']==a and r['status']=='success' for r in c['calls']) for c in outputs.values()) for a in ('A','B')}
    summaries={}
    for arm in ('A','B'):
        for split in ('all','calibration','held_out'):
            expected=[c for c in cases if split=='all' or c['split']==split]
            checks=[mechanical_results.get((c['id'],arm)) for c in expected]
            known=[c for c in checks if c is not None]
            summaries[arm+'|'+split]={'expected_reviews':len(expected),'checked_reviews':len(known),'unknown_reviews':len(checks)-len(known),'passed_reviews':sum(c['pass'] for c in known),'failed_reviews':sum(not c['pass'] for c in known),'failed_admission_proposals':sum(not c['pass'] and c['admission_proposal'] for c in known),'failure_categories':{kind:sum(kind in c['failure_categories'] for c in known) for kind in ('quote_length','quote_presence','schema','date')}}
    analysis['mechanical_validation']={'groups':summaries,'rule':'Original compare.mechanical(review=True) applied to each immutable final-review prompt.case evidence; no new model calls. Category counts may overlap. Format/quotation failures do not relabel source-based historical judgments.','source':'Raw call SHA256 hashes listed in input_hashes.raw_calls; original context and prompts remain private.'}
    analysis['input_hashes']['tool_audit_sha256']=sha(audit_raw) if audit_raw else None
    analysis['accounting']['provider_reported_tool_search_usage']=None
    analysis['accounting']['tool_usage']=f"Observed tool calls: {totals['observed_tool_calls']}; {totals['tool_observation_unknown_calls']} calls have unknown tool observation coverage. Counts use raw saved observations or an audit bound to the exact raw file SHA256 and fingerprint; unknown is not an observed zero. Provider-reported tool/search usage and billing remain unavailable."
    analysis['accounting']['usage_coverage_note']=f"{totals['calls_without_usage']} call artifacts have no response usage. Token/cost sums cover observed response records only; missing accounting is not an observed zero."
    analysis['input_hashes']['analysis_script_sha256']=sha(Path(__file__).read_bytes())
    analysis['input_hashes']['runner_script_sha256']=sha((HERE/'compare.py').read_bytes())
    registration=cases_path.with_name('preregistration.json')
    if registration.exists():
        raw=registration.read_bytes()
        if json.loads(raw)['cases_sha256']!=sha(cases_raw):raise ValueError('Fixture hash differs from registration')
        analysis['input_hashes']['preregistration_sha256']=sha(raw)
    analysis['source_worktree_dirty']=worktree_dirty
    return analysis,rows,{'schema_version':1,'cases':list(outputs.values())}

def svg(analysis):
    groups=analysis['accounting']['groups'];quality=analysis['quality']['arms']
    costs={a:sum(v['api_equivalent_usd'] for k,v in groups.items() if k.startswith(a+'|')) for a in ('A','B')}
    maximum=max(costs.values()) or 1
    parts=['<svg xmlns="http://www.w3.org/2000/svg" width="960" height="480" viewBox="0 0 960 480" role="img" aria-labelledby="title desc">','<title id="title">Observed arm cost and provisional held-out quality</title>','<desc id="desc">Cost excludes reference, adjudication and proposal overhead. Quality uses model references and cannot establish a confident winner.</desc>','<rect width="960" height="480" fill="#ffffff"/>','<g font-family="Arial,sans-serif" fill="#172033">','<text x="40" y="40" font-size="24">Arm costs and provisional held-out quality</text>','<text x="40" y="68" font-size="14">Standard API-equivalent USD; not observed billing. Reference overhead excluded.</text>']
    for i,arm in enumerate(('A','B')):
        y=115+i*150;cost=costs[arm];q=quality[arm]
        parts.extend([f'<text x="40" y="{y}" font-size="20">Arm {arm}</text>',f'<rect x="145" y="{y-23}" width="{cost/maximum*550:.2f}" height="32" fill="{["#196c9c","#a24726"][i]}"/>',f'<text x="720" y="{y}" font-size="18">${cost:.4f}</text>'])
        value=lambda k:'unavailable' if q[k] is None else str(q[k])
        label=f"Held-out reviewed: {analysis['coverage']['completed_held_out_review_counts'][arm]}/80; resolved judgments: {q['resolved_cases']}/80"
        parts.append(f'<text x="145" y="{y+40}" font-size="15">{escape(label)}</text>')
        label=f"False admissions: {value('false_admissions')}; unsupported facets: {value('unsupported_facets')}; links: {value('unsupported_links')}"
        parts.append(f'<text x="145" y="{y+65}" font-size="15">{escape(label)}</text>')
    parts.append('<line x1="145" x2="695" y1="355" y2="355" stroke="#74808e"/>')
    for i in range(4):
        x=145+i*550/3
        parts.append(f'<text x="{x:.1f}" y="378" text-anchor="middle" font-size="14">${maximum*i/3:.2f}</text>')
    parts.append('<text x="145" y="402" font-size="14">Extraction + review standard API equivalent (USD)</text>')
    parts.extend(['<text x="40" y="430" font-size="15">Quality is provisional: same-family model references are not historical truth.</text>','<text x="40" y="455" font-size="15">No confident winner is inferred. Bars start at zero; both use the same scale.</text>','</g></svg>'])
    return '\n'.join(parts)+'\n'
def report(analysis):
    totals=analysis['accounting']['totals'];q=analysis['quality'];coverage=analysis['coverage']
    lines=['# Workflow comparison: observed costs and provisional quality','',f"The saved run contains {totals['successful_calls']} successful calls and {totals['failed_calls']} failed calls. Reviewed outputs cover {coverage['completed_review_counts']['A']}/100 cases for Arm A and {coverage['completed_review_counts']['B']}/100 for Arm B. No confident winner follows from same-family model references.",'','![Arm cost and provisional quality](comparison.svg)','','## Accounting','',f"The standard API-equivalent estimate is ${totals['api_equivalent_usd']:.6f}; the doubled cache-write-rate sensitivity is ${totals['api_equivalent_12h_write_usd']:.6f}. These are pricing scenarios, not an invoice, subscription-credit measurement or observed billing.",'','| Arm / split / stage | Calls | Input | Cache reads | Cache writes | Output incl. reasoning | Reasoning subset | Estimated USD |','| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    for key,g in sorted(analysis['accounting']['groups'].items()):
        key=key.replace('|',' / ')
        lines.append(f"| {key} | {g['calls']} | {g['input_tokens']} | {g['cached_input_tokens']} | {g['cache_write_input_tokens']} | {g['output_tokens']} | {g['reasoning_output_tokens']} | {g['api_equivalent_usd']:.6f} |")
    lines+=['',f"Global response-ID deduplication retained {totals['unique_responses']} responses and excluded {totals['duplicate_response_ids']} repeated IDs. Uncached input is {totals['uncached_input_tokens']} tokens. Reasoning is already inside output and is never added again.",'',f"Aggregate request duration is {totals['elapsed_sum_seconds']:.2f} seconds; observed wall span is {totals['elapsed_wall_seconds']:.2f} seconds. Their difference reflects overlap and gaps; it is not a causal efficiency estimate. Inflight requests have incomplete durations.",'','## Held-out quality','',f"Reference standard: `{q['reference_standard']}`. All reference and adjudication models are from the same family. Source-based model judgments, including selective dispute review, remain provisional and correlated; agreement is not historical truth.",'','| Arm | Judged / 80 | Resolved | Ref. admissions | False admits | False rejects | Unsupported facets / links | Provisional gate |','| --- | ---: | ---: | ---: | ---: | ---: | --- | --- |']
    show=lambda value:'unavailable' if value is None else str(value)
    for arm,row in q['arms'].items():
        lines.append(f"| {arm} | {row['judged_cases']} | {row['resolved_cases']} | {row['resolved_reference_admissions']} | {show(row['false_admissions'])} | {show(row['false_rejects'])} | {show(row['unsupported_facets'])} / {show(row['unsupported_links'])} | {show(row['provisional_quality_gate'])} |")
    lines+=['','The preregistered held-out gates require zero false admissions, zero unsupported facets/links and at most 5% false rejects among resolved reference admissions. Unresolved references are excluded from the false-reject denominator and reported separately. Unsupported or unresolved admitted claims still fail the gate even when reference priority is unresolved. Complete judgment coverage requires all 80 cases judged, including correct source deferrals; it does not require all reference histories resolved. Missing quality checks remain unavailable and prevent a provisional pass. Calibration cases do not count toward held-out gate outcomes.','','| Arm | Useful reviewed records | Supported claims | USD / useful record | USD / supported claim |','| --- | ---: | ---: | ---: | ---: |']
    for arm,row in q['arms'].items():
        lines.append(f"| {arm} | {show(row['useful_reviewed_records'])} | {show(row['supported_claims'])} | {show(row['cost_per_useful_reviewed_record_usd'])} | {show(row['cost_per_supported_claim_usd'])} |")
    for arm,row in q['arms'].items():
        lines.append(f"Arm {arm}: source-judged useful records {show(row['raw_semantic_useful_records'])}, mechanically blocked useful records {show(row['mechanical_blocked_useful_records'])}, raw source-supported claims {show(row['source_judged_supported_claims'])}, mechanically usable supported claims {show(row['usable_supported_claims'])}.")
        lines.append(f"Arm {arm}: {row['unresolved_cases']} unresolved reference cases, {row['unknown_quality_cases']} judged cases with missing quality checks, and {show(row['unresolved_admitted_claims'])} unresolved admitted claims.")
    lines+=['','These unit costs allocate held-out extraction/review cost only. Reference, adjudication and proposal-generation overhead is reported separately in the accounting table. Useful-record and supported-claim counts inherit the provisional reference limitation and require the original mechanical validation gate. Mechanical quote-length/presence, schema and date failures are formal validation failures; source-based false-admission/reject judgments remain unchanged.','','## Reproduction and limits','',f"Source commit: `{analysis['source_commit']}`. Fixture SHA256: `{analysis['input_hashes']['cases_sha256']}`. `analysis.json` contains input artifact hashes; raw prompts, conversations, original source context, quotations and stderr remain private. Public structured answers replace quotations with SHA256 hashes. `calls.csv` provides safe per-call accounting.",'','Reproduce with `python3 tools/cards/analyze_comparison.py --state /absolute/private/comparison --judgments /absolute/private/comparison/judgments.json`. Omit `--judgments` only to report unavailable quality. The script reads existing calls and never dispatches models.','','No strict 25,000 reasoning-token cap is available from the documented CLI. Finite guards are checked between calls and up to four inflight requests may overshoot. Provider-reported tool/search usage, observed billing and subscription-credit accounting remain unavailable. Proposal-generation outputs are separate from the fixed admission set.','']
    lines.extend(['','Mechanical review validation (original frozen rule; categories may overlap):',''])
    for key,values in analysis['mechanical_validation']['groups'].items():
        lines.append(f"{key.replace('|',' / ')}: {values['passed_reviews']} passed, {values['failed_reviews']} failed, {values['unknown_reviews']} unavailable; failed admission proposals {values['failed_admission_proposals']}; categories {values['failure_categories']}.")
    lines.extend([analysis['accounting']['usage_coverage_note'],'',analysis['accounting']['tool_usage'],''])
    return '\n'.join(lines)
def write_report(analysis,rows,sanitized,out=DEFAULT_OUT):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    (out/'analysis.json').write_text(json.dumps(analysis,ensure_ascii=False,indent=2)+'\n')
    (out/'sanitized-results.json').write_text(json.dumps(sanitized,ensure_ascii=False,indent=2)+'\n')
    with (out/'calls.csv').open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    (out/'comparison.svg').write_text(svg(analysis));(out/'report.md').write_text(report(analysis))
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state',type=Path,default=DEFAULT_STATE);parser.add_argument('--cases',type=Path,default=DEFAULT_OUT/'cases.json');parser.add_argument('--judgments',type=Path);parser.add_argument('--out',type=Path,default=DEFAULT_OUT)
    args=parser.parse_args();result=analyze(args.state,args.cases,args.judgments);write_report(*result,out=args.out)
    print(json.dumps({'output':str(args.out),'calls':result[0]['accounting']['totals']['calls']}))
if __name__=='__main__':main()
