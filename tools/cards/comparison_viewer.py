#!/usr/bin/env python3
"""Generate canonical Data viewer source from real comparison artifacts only.

Stdlib; no model calls, runtime scaffolding, preview server or publication.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[2]
DEFAULT=ROOT/'docs/reviews/2026-11-10-workflow-comparison'
JUDGMENT_FIELDS=('resolved','reference_admit','false_admission','false_reject','unsupported_facets','unsupported_links','unresolved_admitted_claims','useful_reviewed_record','supported_claims','date_errors','uncertainty_errors','duplicate_work','substantive_corrections','unresolved_source_access')
def sha(raw):return hashlib.sha256(raw).hexdigest()
def strip_markdown_tables(text):
    """RichNarrative does not implement GFM tables; native tables own their rows."""
    lines=text.splitlines();kept=[];i=0
    while i<len(lines):
        if i+1<len(lines) and '|' in lines[i] and re.match(r'^\s*\|?\s*:?-{3,}',lines[i+1]):
            i+=2
            while i<len(lines) and '|' in lines[i] and lines[i].strip():i+=1
            continue
        kept.append(lines[i]);i+=1
    return '\n'.join(kept)
def case_rows(cases):
    rows=[]
    for case in cases:
        judgments=case.get('judgments',[])
        if isinstance(judgments,dict):judgments=[dict(value,arm=arm) for arm,value in judgments.items()]
        for arm in ('A','B'):
            stages={r['stage']:r for r in case.get('calls',[]) if r.get('arm')==arm}
            extracted=stages.get('extract',{});reviewed=stages.get('review',{})
            ep=extracted.get('parsed') or {};rp=reviewed.get('parsed') or {}
            judgment=next((r for r in judgments if r.get('arm')==arm),{})
            counts=lambda parsed:len(parsed['claims']) if isinstance(parsed.get('claims'),list) else None
            row={'rowId':case['id']+'-'+arm,'caseId':case['id'],'name':case['name'],'arm':arm,'split':case['split'],'stratum':case['stratum'],'extractStatus':extracted.get('status','unavailable'),'reviewStatus':reviewed.get('status','unavailable'),'reviewDecision':rp.get('decision','unavailable'),'extractedClaims':counts(ep),'reviewedClaims':counts(rp),'modelCorrections':len(rp['corrections']) if isinstance(rp.get('corrections'),list) else None,'judgmentStatus':'provisional model reference' if judgment else 'unavailable'}
            checks=reviewed.get('mechanical_checks')
            row.update({'mechanicalPass':checks.get('pass') if isinstance(checks,dict) else None,'mechanicalFailures':', '.join(checks.get('failure_categories',[])) if isinstance(checks,dict) else None})
            row.update({key:judgment.get(key) for key in JUDGMENT_FIELDS})
            rows.append(row)
    return rows

def source(label,files,hashes,definitions=None):
    return {'label':label,'files':files,'caveats':['API-equivalent pricing is not observed billing or subscription credits.','Same-family model references are provisional, not independent historical truth. Missing quality remains unavailable.','Raw prompts, quotations, original source context and stderr remain private.'],'metricDefinitions':definitions or [],'evidenceFlow':[{'title':'Reproduce','detail':'Run tools/cards/analyze_comparison.py using private calls/judgments, then tools/cards/comparison_viewer.py using the generated report directory.'},{'title':'Input content hashes','detail':json.dumps(hashes,sort_keys=True)}]}
def prepare(base=DEFAULT):
    base=Path(base);names=('analysis.json','sanitized-results.json','report.md')
    raw={name:(base/name).read_bytes() for name in names};hashes={name:sha(value) for name,value in raw.items()}
    analysis=json.loads(raw['analysis.json']);sanitized=json.loads(raw['sanitized-results.json'])
    if not analysis['accounting']['totals']['calls']:raise ValueError('No actual calls; refusing placeholder viewer')
    cases=sanitized['cases']
    if len(cases)!=100 or len({c['id'] for c in cases})!=100:raise ValueError('Expected exactly 100 fixed cases')
    costs=[];overhead=[]
    for key,values in sorted(analysis['accounting']['groups'].items()):
        arm,split,stage=key.split('|')
        row={'arm':arm,'split':split,'stage':stage,'apiEquivalentUsd':values['api_equivalent_usd'],'calls':values['calls'],'inputTokens':values['input_tokens'],'cachedInputTokens':values['cached_input_tokens'],'cacheWriteInputTokens':values['cache_write_input_tokens'],'outputTokens':values['output_tokens'],'reasoningOutputTokens':values['reasoning_output_tokens']}
        (costs if arm in ('A','B') else overhead).append(row)
    quality=[{'arm':arm,**values} for arm,values in analysis['quality']['arms'].items()]
    proposal_path=base/'proposal-summary.json'
    proposal_rows=json.loads(proposal_path.read_text())['models'] if proposal_path.exists() else []
    if proposal_path.exists():hashes['proposal-summary.json']=sha(proposal_path.read_bytes())
    auxiliary_path=base/'auxiliary-usage.json'
    if auxiliary_path.exists():
        auxiliary=json.loads(auxiliary_path.read_text());token=auxiliary['tokens']
        overhead.append({'arm':'overhead','split':'overhead','stage':'secondary_source_review','apiEquivalentUsd':auxiliary['api_equivalent_usd'],'calls':auxiliary['unique_responses'],'inputTokens':token['input_tokens'],'cachedInputTokens':token['cached_input_tokens'],'cacheWriteInputTokens':token['cache_write_input_tokens'],'outputTokens':token['output_tokens'],'reasoningOutputTokens':token['reasoning_output_tokens']})
        hashes['auxiliary-usage.json']=sha(auxiliary_path.read_bytes())
    queries={
      'arm_costs':{'rows':costs,'source':source('Deduplicated arm accounting',['analysis.json','calls.csv'],hashes,[{'label':'API-equivalent USD','definition':'Unique response IDs repriced using compare.RATES; output includes reasoning. Overhead excluded.','componentIds':['arm-stage-cost']}])},
      'overhead':{'rows':overhead,'source':source('Reference, adjudication, proposal and targeted secondary-review overhead',['analysis.json','calls.csv','auxiliary-usage.json'],hashes)},
      'held_out_quality':{'rows':quality,'source':source('Provisional held-out source-reading judgments',['analysis.json'],hashes)},
      'case_results':{'rows':case_rows(cases),'source':source('Sanitized case outputs and provisional judgments',['sanitized-results.json'],hashes)},
      'proposal_quality':{'rows':proposal_rows,'source':source('Tool-free proposal generation; text quality only',['proposal-summary.json'],hashes)}}
    report_text=raw['report.md'].decode()
    paragraphs=report_text.split('\n\n')
    sections=[{'id':'comparison-decision-summary','title':'Decision','text':paragraphs[1]+'\n\nQuality labels come from same-family source-reading models. Disagreements are preserved; no confident passing winner is established.'}]
    for i,chunk in enumerate(raw['report.md'].decode().split('\n## ')):
        if i==0:continue
        title,_,body=chunk.partition('\n');body=re.sub(r'^!\[[^\]]*\]\([^\n]*\)\s*$', '',body,flags=re.M)
        body=re.sub(r'\[([^\]]+)\]\((?!https?://)([^)]+)\)',r'\1 (`\2`, saved report artifact)',body)
        body=strip_markdown_tables(body)
        sections.append({'id':f'comparison-report-section-{i}','title':title,'text':'## '+title+'\n'+body.strip()})
    snapshot={'title':report_text.splitlines()[0].removeprefix('# '),'surface':'report','description':'Fixed 100-candidate comparison; model-only references do not establish a historical winner.','status':'reviewed','buildStatus':'creating','report':{'asOf':'2026-11-10'},'filters':[],'exportPreferences':{'selected':None,'destinations':[]},'queries':queries,'comparisonMetadata':{'sourceCommit':analysis['source_commit'],'inputHashes':hashes,'referenceStandard':analysis['quality']['reference_standard'],'adequateIndependentReference':False,'winner':None}}
    viewer=base/'viewer';viewer.mkdir(exist_ok=True)
    for name,value in [('snapshot.json',snapshot),('sections.json',sections)]:
        (viewer/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
    (viewer/'ReportContent.jsx').write_text(COMPONENT)
    return {'viewer':str(viewer),'caseRows':len(queries['case_results']['rows']),'armCostRows':len(costs),'overheadRows':len(overhead),'inputHashes':hashes}
COMPONENT = r'''import React, { useState } from "react";
import { DataComponent, DataTable, Dropdown, EvidenceChart, ReportSection, RichNarrative, useDataApp } from "../../data-app-public.jsx";
import sections from "./sections.json";

const show = (value) => value === null || value === undefined ? "Unavailable" : typeof value === "boolean" ? (value ? "Yes" : "No") : String(value);
const columns = (fields) => fields.map(([field,label]) => ({field,label,renderCell:show}));
const percent = (value) => value === null || value === undefined ? "Unavailable" : (value*100).toLocaleString("en-GB",{maximumFractionDigits:4})+"%";
const dollars = (value) => value === null || value === undefined ? "Unavailable" : value.toLocaleString("en-US",{style:"currency",currency:"USD",minimumFractionDigits:4,maximumFractionDigits:6});
const label = (value) => value.replaceAll("_", " ");
export function ReportContent() {
  const { reviewedRows, visible, appTitle, setAppTitle, canEdit, mode } = useDataApp();
  const [costSplit,setCostSplit] = useState("All");
  const [arm,setArm] = useState("All");
  const [split,setSplit] = useState("All");
  const [stratum,setStratum] = useState("All");
  const [selectedId,setSelectedId] = useState(null);
  const armSources = reviewedRows("arm_costs").filter(r => costSplit === "All" || r.split === costSplit);
  const accumulated = new Map();
  armSources.forEach(r => {
    const key = r.arm+"|"+r.stage;
    const previous = accumulated.get(key);
    accumulated.set(key,{arm:r.arm,stage:r.stage,apiEquivalentUsd:(previous?.apiEquivalentUsd ?? 0)+r.apiEquivalentUsd});
  });
  const armCosts = [...accumulated.values()];
  const overheadSources = reviewedRows("overhead");
  const overheadTotals = new Map();
  overheadSources.forEach(r => overheadTotals.set(r.stage,(overheadTotals.get(r.stage) ?? 0)+r.apiEquivalentUsd));
  const overhead = [...overheadTotals].map(([stage,apiEquivalentUsd]) => ({stage,apiEquivalentUsd}));
  const allCases = reviewedRows("case_results");
  const cases = allCases.filter(r => (arm === "All" || r.arm === arm) && (split === "All" || r.split === split) && (stratum === "All" || r.stratum === stratum));
  const selected = cases.find(r => r.rowId === selectedId);
  const caseControls = <>
    <Dropdown label="Arm" showLabel value={arm} choices={["All","A","B"]} onChange={setArm}/>
    <Dropdown label="Split" showLabel value={split} choices={["All","calibration","held_out"]} formatChoice={label} onChange={setSplit}/>
    <Dropdown label="Stratum" showLabel value={stratum} choices={["All",...new Set(allCases.map(r => r.stratum))]} formatChoice={label} onChange={setStratum}/>
  </>;
  const quality = reviewedRows("held_out_quality");
  const proposals = reviewedRows("proposal_quality");
  const accounting = [...reviewedRows("arm_costs"),...overheadSources];
  const details = selected ? [
    ["Candidate",selected.name],["Arm",selected.arm],["Split",label(selected.split)],["Stratum",label(selected.stratum)],
    ["Reviewed decision",selected.reviewDecision],["Mechanical validation passed",selected.mechanicalPass],["Mechanical failure categories",selected.mechanicalFailures],["Extraction claims",selected.extractedClaims],["Reviewed claims",selected.reviewedClaims],
    ["Source-judged supported claims",selected.supported_claims],["Reference resolved",selected.resolved],
    ["False admission",selected.false_admission],["False reject",selected.false_reject],
    ["Unsupported facets",selected.unsupported_facets],["Unsupported links",selected.unsupported_links],
    ["Unresolved admitted claims",selected.unresolved_admitted_claims],["Useful reviewed record",selected.useful_reviewed_record],
    ["Substantive corrections",selected.substantive_corrections],["Unresolved source access",selected.unresolved_source_access],
  ].map(([metric,value]) => ({metric,value:show(value)})) : [];
  return <article className="report-content" aria-label="Workflow comparison">
    <header className="report-hero">
      <h1 data-data-app-title contentEditable={canEdit && mode === "edit"} suppressContentEditableWarning
        onBlur={canEdit && mode === "edit" ? event => setAppTitle(event.currentTarget.textContent.trim() || appTitle) : undefined}>{appTitle}</h1>
      <RichNarrative id="comparison:limits" className="report-deck" value={sections.find(s => s.id === "comparison-decision-summary")?.text ?? "Quality judgments are provisional source readings, not historical truth."}/>
    </header>
    {visible("arm-stage-cost") && <EvidenceChart id="arm-stage-cost" queryId="arm_costs" title="Extraction and review cost by arm" description="Selected split only. Standard API-equivalent USD, not observed billing. Reference, adjudication and proposal overhead is separate." headerControls={<Dropdown label="Cost split" showLabel value={costSplit} choices={["All","calibration","held_out"]} formatChoice={label} onChange={setCostSplit}/>} spec={{type:"horizontalStackedBar",x:"arm",y:"apiEquivalentUsd",series:"stage",currency:"USD",valueDecimals:4}} rows={armCosts} sourceRows={armSources} height={300}/>}
    {visible("overhead-cost") && <EvidenceChart id="overhead-cost" queryId="overhead" title="Reference and other overhead across the full run" description="All recorded splits and overhead jobs. This population is independent of the arm-cost split selector above." spec={{type:"horizontalBar",x:"stage",y:"apiEquivalentUsd",currency:"USD",valueDecimals:4,stackable:false}} rows={overhead} sourceRows={overheadSources} height={300}/>}
    {proposals.length > 0 && visible("proposal-comparison") && <DataComponent id="proposal-comparison" queryId="proposal_quality" kind="table" title="Proposal generation is cheaper with Sol in this bounded sample" sourceRows={proposals} displayRows={proposals} description="Same inventory, 12 proposals and answer target; realized reasoning/spend could not be equalized. Text usefulness is model-judged; historical correctness and source-verified novelty are unmeasured.">
      <DataTable rows={proposals} searchable={false} compactNumbers={false} caption="Tool-free proposal comparison" columns={[...columns([["model","Model"],["effort","Effort"],["generated","Proposals"],["textUseful","Text useful"]]),{field:"genCostUsd",label:"Generation USD equivalent",renderCell:dollars},{field:"genSeconds",label:"Seconds",renderCell:value => value == null ? "Unavailable" : value.toFixed(1)},...columns([["verifiedCandidates","Source verified"]])]}/>
    </DataComponent>}
    {visible("accounting-detail") && <DataComponent id="accounting-detail" queryId="arm_costs" queryIds={["arm_costs","overhead"]} sourceRowsByQuery={{arm_costs:reviewedRows("arm_costs"),overhead:overheadSources}} displayRows={accounting} kind="table" title="Accounting by arm, split and stage" description="Full-run accounting, independent of the chart split control. Output already includes the reasoning subset.">
      <DataTable rows={accounting} compactNumbers={false} caption="Detailed accounting" columns={[...columns([["arm","Arm / overhead"],["split","Split"],["stage","Stage"],["calls","Calls"],["inputTokens","Input"],["cachedInputTokens","Cache reads"],["cacheWriteInputTokens","Cache writes"],["outputTokens","Output"],["reasoningOutputTokens","Reasoning subset"]]),{field:"apiEquivalentUsd",label:"Estimated USD",renderCell:dollars}]}/>
    </DataComponent>}
'''
COMPONENT += r'''
    {visible("quality-summary") && <DataComponent id="quality-summary" queryId="held_out_quality" kind="table" title="Provisional held-out quality" sourceRows={quality} displayRows={quality} description="All 80 held-out cases per arm. Missing checks remain unavailable. Correct source deferrals can remain historically unresolved; unsupported admitted claims still fail.">
      <DataTable rows={quality} searchable={false} compactNumbers={false} caption="Provisional held-out quality by arm" columns={[...columns([["arm","Arm"],["judged_cases","Judged"],["unresolved_cases","Unresolved reference"],["false_admissions","False admissions"]]),{field:"false_reject_rate",label:"False-reject rate",renderCell:percent},...columns([["unsupported_facets","Unsupported facets"],["unsupported_links","Unsupported links"],["mechanical_failure_count","Mechanical failures"],["mechanical_unknown_cases","Unknown mechanical"],["provisional_quality_gate","Provisional gate"]])]}/>
    </DataComponent>}
    {visible("quality-unit-cost") && <DataComponent id="quality-unit-cost" queryId="held_out_quality" sourceRows={quality} displayRows={quality} kind="table" title="Useful records, supported claims and unit cost" description="Held-out extraction/review cost only; overhead excluded. Usable records and claims require both explicit provisional source support and the original mechanical gate. Format failures do not relabel historical facts. Unavailable is not zero.">
      <DataTable rows={quality} searchable={false} compactNumbers={false} caption="Provisional usefulness and unit cost" columns={[...columns([["arm","Arm"],["raw_semantic_useful_records","Source-judged useful"],["mechanical_blocked_useful_records","Mechanically blocked useful"],["useful_reviewed_records","Usable reviewed records"],["source_judged_supported_claims","Source-judged claims"],["usable_supported_claims","Usable supported claims"]]),{field:"cost_per_useful_reviewed_record_usd",label:"USD / useful record",renderCell:dollars},{field:"cost_per_supported_claim_usd",label:"USD / supported claim",renderCell:dollars}]}/>
    </DataComponent>}
    {visible("case-explorer") && <DataComponent id="case-explorer" queryId="case_results" kind="table" title="Inspect the fixed candidates" sourceRows={cases} displayRows={cases} description="One row per candidate and arm. Select a row for scalar claim/support details. No original quotations or source text are embedded.">
      <DataTable rows={cases} rowKey="rowId" selectedRowKey={selected?.rowId} onRowSelect={row => setSelectedId(row.rowId)} rowActionLabel={row => "Inspect "+row.name+", Arm "+row.arm} toolbarControls={caseControls} compactNumbers={false} caption="Candidate decisions and claim counts" columns={columns([["name","Candidate"],["arm","Arm"],["split","Split"],["stratum","Primary stratum"],["reviewDecision","Reviewed decision"],["reviewedClaims","Claims"],["supported_claims","Supported"],["judgmentStatus","Reference status"]])}/>
    </DataComponent>}
    {visible("case-detail") && <DataComponent id="case-detail" queryId="case_results" kind="table" title={selected ? "Candidate detail: "+selected.name+" · Arm "+selected.arm : "Select a candidate to inspect"} sourceRows={selected ? [selected] : []} displayRows={details} description="Provisional scalar judgments and output counts. Unavailable means no supplied judgment, not zero.">
      <DataTable rows={details} searchable={false} compactNumbers={false} caption="Selected candidate scalar details" columns={columns([["metric","Measure"],["value","Observed or judged value"]])}/>
    </DataComponent>}
    {sections.filter(s => s.id !== "comparison-decision-summary").map(section => visible(section.id) && (section.title === "Accounting" ? <ReportSection key={section.id} id={section.id} queryId="arm_costs" queryIds={["arm_costs","overhead"]} sourceRowsByQuery={{arm_costs:reviewedRows("arm_costs"),overhead:overheadSources}} title={section.title} showHeading={false}>
      <RichNarrative id={section.id+":body"} value={section.text}/>
    </ReportSection> : section.title === "Held-out quality" ? <ReportSection key={section.id} id={section.id} queryId="held_out_quality" sourceRows={quality} title={section.title} showHeading={false}>
      <RichNarrative id={section.id+":body"} value={section.text}/>
    </ReportSection> : <section key={section.id}><RichNarrative id={section.id+":body"} value={section.text}/></section>))}
  </article>;
}
'''
def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('review_directory',type=Path,nargs='?',default=DEFAULT)
    args=parser.parse_args();print(json.dumps(prepare(args.review_directory),sort_keys=True))
if __name__=='__main__':main()
