#!/usr/bin/env python3
"""Build the self-contained research explorer; allow isolated preview outputs."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

HTML = r'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Technology in use · Research atlas</title>
<style>
:root{--ink:#192e3a;--muted:#536570;--paper:#f5f3ed;--white:#fff;--line:#cfd7d8;--accent:#075a70;--pale:#e7eff0;--warn:#865b12}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:16px/1.55 system-ui,-apple-system,sans-serif}
header{padding:30px max(24px,5vw) 24px;border-bottom:1px solid var(--line)}
.kicker{text-transform:uppercase;letter-spacing:.1em;font-size:12px;font-weight:700;color:var(--accent)}
h1{font:clamp(32px,5vw,48px)/1.12 Georgia,serif;margin:10px 0}h2{font:30px/1.22 Georgia,serif;margin:8px 0 18px}h3{font-size:19px;margin:26px 0 12px}h4{font-size:16px;margin:0 0 8px}p{margin:0 0 14px}
a{color:var(--accent);text-underline-offset:3px}a:hover{text-decoration-thickness:2px}a:focus-visible,input:focus-visible,select:focus-visible,button:focus-visible,summary:focus-visible{outline:3px solid #d3a52f;outline-offset:3px}
.intro{max-width:900px;color:var(--muted)}.metrics{display:flex;flex-wrap:wrap;gap:10px 22px;font-size:13px;margin:16px 0}.metrics b{font-size:20px}.mode-note{max-width:1000px;font-size:13px;color:var(--muted)}
nav{display:flex;flex-wrap:wrap;gap:10px 20px}.layers{margin-top:20px;gap:8px}.layers a{display:block;border:1px solid var(--accent);padding:7px 14px;border-radius:4px;text-decoration:none;font-size:14px;font-weight:650}.layers a[aria-current=page]{background:var(--accent);color:white}
.reading-links{max-width:1050px;margin-top:15px}.reading-links summary{font-size:13px}.reading-links nav{font-size:13px;margin-top:12px}
.layout{display:grid;grid-template-columns:minmax(270px,325px) minmax(0,1fr);max-width:1600px;margin:auto}
.sidebar{border-right:1px solid var(--line);padding:24px 20px;align-self:start;position:sticky;top:0;max-height:100vh;overflow:auto}
.case-picker>summary{display:none}.controls{display:grid;gap:14px;margin-bottom:18px}.id-form{padding-bottom:16px;border-bottom:1px solid var(--line)}.input-row{display:flex;gap:6px}.input-row input{min-width:0}
label{display:block;font-size:13px;font-weight:700;margin-bottom:5px}input,select,button{background:white;border:1px solid #899ba2;border-radius:4px;padding:9px;color:var(--ink);font:inherit;font-size:14px}input,select{width:100%}button{cursor:pointer}button:hover{background:var(--pale)}
.case-link{display:block;text-decoration:none;border-top:1px solid var(--line);padding:13px 9px;color:var(--ink)}.case-link:hover{background:#eceded}.case-link[aria-current=true]{background:var(--pale);border-left:4px solid var(--accent);padding-left:5px}
.record-id{font-size:12px;font-weight:700;color:var(--accent)}.case-title{display:block;font-weight:650;font-size:14px;line-height:1.4}.case-period{font-size:12px;color:var(--muted)}.count{font-size:12px;color:var(--muted);margin-bottom:10px}
.detail{padding:30px clamp(22px,4vw,62px) 65px;min-width:0;overflow-wrap:anywhere}.detail:focus,section:focus{outline:none}.breadcrumbs{font-size:13px;margin-bottom:18px}.subnav{font-size:13px;gap:9px 17px;margin:20px 0 24px}.detail section{scroll-margin-top:18px}
.tag{display:inline-block;background:var(--pale);padding:3px 8px;font-size:12px;margin:0 6px 6px 0;border-radius:3px}.chip{display:inline-block;background:white;border:1px solid var(--line);border-radius:4px;padding:4px 8px;font-size:13px;margin:0 7px 7px 0}
.scope{background:#fff;border-left:4px solid var(--accent);padding:18px 20px;margin:18px 0}.small{font-size:13px;color:var(--muted)}.caution{border-left-color:var(--warn);background:#fffaf0}.caution p:last-child,.scope p:last-child{margin-bottom:0}
dl{margin:0}dt{font-size:13px;font-weight:700;color:var(--muted);margin-top:14px;text-transform:capitalize}dd{margin:4px 0 10px}dd dl{padding-left:14px;border-left:2px solid var(--line)}.values{margin:0;padding-left:20px}.values li{margin-bottom:6px}
details:not(.case-picker){border-top:1px solid var(--line);padding:12px 0}summary{cursor:pointer;font-weight:650;font-size:15px}details p{margin-top:12px}
.claim{padding:18px 0;border-top:1px solid var(--line)}.evidence{margin:12px 0;padding-left:20px;font-size:14px}.evidence li{margin-bottom:14px}.source-locator{display:block;margin-top:4px}
.card,.edge{background:white;padding:18px;margin:14px 0;border:1px solid var(--line);border-radius:3px}.card h3{margin:5px 0 12px;font-size:19px}.card p:last-child{margin-bottom:0}.relation{color:var(--accent);font-weight:700;font-size:13px;margin:7px 0}.edge-endpoint{font-weight:650}.empty{padding:22px 0;color:var(--muted)}
.layer-note{max-width:850px}.list-search{max-width:600px;margin:20px 0}.route-date{margin:7px 0;font-size:13px}.backlinks{margin-top:22px;padding-top:16px;border-top:1px solid var(--line)}footer{border-top:1px solid var(--line);padding:22px 5vw;color:var(--muted);font-size:12px}
.skip-link{position:fixed;top:-100px;left:12px;padding:10px;background:white;z-index:10}.skip-link:focus{top:10px}
@media(max-width:800px){.layout{display:block}.sidebar{position:static;max-height:none;border-right:0;border-bottom:1px solid var(--line);padding:14px 22px}.case-picker>summary{display:list-item}.case-picker[open]>.controls{margin-top:18px}#case-list{max-height:300px;overflow:auto}.detail{padding:26px 22px 48px}header{padding:25px 22px 20px}.metrics{gap:8px 16px}.case-link{padding:12px 6px}.layers a{padding:7px 11px}.reading-links nav{gap:10px 18px}h2{font-size:27px}}
@media print{.sidebar,nav,.subnav,.reading-links,.skip-link{display:none}.layout{display:block}.detail{padding:20px}header{padding:20px}body{background:white}}
</style>
</head>
<body>
<a class="skip-link" href="#" id="skip-detail">Skip to current record</a>
<header>
 <div class="kicker">Big Idea · Revised research edition · 5 November 2026</div>
 <h1>Technology in use</h1>
 <p class="intro">A comparative history of how working objects become operating systems—and why people, institutions and environments produce different patterns of use.</p>
 <div class="metrics" id="metrics"></div>
 <p class="mode-note">A purposive research collection. Counts describe its contents, not historical prevalence or independent confirmations. Source access, rival explanations and uncertainty remain visible.</p>
 <nav class="layers" aria-label="Explore the research">
  <a id="cases-layer" href="#view=case">Cases</a>
  <a id="chronology-layer" href="#view=chronology">Chronology</a>
  <a id="comparisons-layer" href="#view=comparisons">Comparisons</a>
 </nav>
 <details class="reading-links"><summary>Longer reading and research files</summary><nav aria-label="Reading routes">
  <a href="README.md">Start here</a><a href="analysis/SYNTHESIS.md">Synthesis</a><a href="analysis/GLOBAL_MAP.md">Full historical route</a><a href="analysis/FUTURE_ROLES.md">Human roles: conditional implications</a><a href="reviews/RESPONSE_LOG.md">Criticism and repairs</a><a href="data/graph.json">Graph data</a>
 </nav></details>
</header>
<main class="layout">
 <aside class="sidebar" aria-label="Find a case or record">
  <details class="case-picker" id="case-picker" open><summary>Find a case or record</summary>
   <div class="controls">
    <form id="id-form" class="id-form"><label for="record-id">Open a record ID</label><div class="input-row"><input id="record-id" name="record" placeholder="e.g. IND-E14" autocomplete="off"><button type="submit">Open</button></div><p class="small" style="margin:6px 0 0">Case, claim, source, node, edge or comparison.</p></form>
    <div><label for="search">Search cases, actors and mechanisms</label><input id="search" type="search" placeholder="e.g. maintenance, Ghana, printing"></div>
    <div><label for="strand">Research strand</label><select id="strand"><option value="">All strands</option></select></div>
   </div>
   <div class="count" id="count" role="status" aria-live="polite"></div><div id="case-list"></div>
  </details>
 </aside>
 <article class="detail" id="detail" tabindex="-1"></article>
</main>
<footer>This browser is generated from the JSON ledgers. It makes no automatic external requests and needs no account. Chronological routes and comparisons are navigation layers, not causal edges. Inspect each relation's scope and evidence; no transitive causal closure is warranted.</footer>
<script id="research-data" type="application/json">__DATA__</script>
<script>
'use strict';
const d = JSON.parse(document.getElementById('research-data').textContent);
const records = {case:d.cases, claim:d.claims, source:d.sources, node:d.graph.nodes, edge:d.graph.edges, comparison:d.comparisons};
const byId = Object.fromEntries(Object.entries(records).map(([kind,rows]) => [kind,Object.fromEntries(rows.map(row => [row.id,row]))]));
const kindOf = Object.fromEntries(Object.entries(records).flatMap(([kind,rows]) => rows.map(row => [row.id,kind])));
const routes = d.chronology?.routes || [];
const routeById = Object.fromEntries(routes.map(route => [route.id,route]));
const el = id => document.getElementById(id);
const owns = (object,key) => Object.prototype.hasOwnProperty.call(object,key);
const knownKind = id => owns(kindOf,id)?kindOf[id]:undefined;
const h = value => String(value ?? '').replace(/[&<>"']/g, character => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[character]));
const sectionNames = {episode:'Episode and actors',stages:'Stages',evidence:'Evidence and rivals',relations:'Graph relations',comparisons:'Comparisons',sources:'Sources and lineage'};
const strandNames = {MAT:'Materials and metallurgy',ANC:'Ancient infrastructure',NET:'Knowledge and navigation',IND:'Industrial production',AGR:'Agriculture and households',MED:'Health and public goods',MOB:'Transport and large systems',DIG:'Digital and consumer systems',LBR:'Labour transitions',OCE:'Indigenous and Oceanian systems',POL:'State, military and administration',SKL:'Precision, repair and skills',PSY:'Behaviour, identity and access',ENE:'Energy and manufacturing',SYN:'Cross-case synthesis',CTX:'Household textiles and institutions',GHA:'Ghana: roads, labour and local initiative'};
let state;

function href(next) {
 const params = new URLSearchParams();
 for (const key of ['view','id','case','section','via','claim','route']) if (next[key]) params.set(key,next[key]);
 return '#'+params.toString();
}
function anchor(url,label,extra='') {
 return '<a href="'+h(url)+'"'+(/^https?:/.test(url)?' target="_blank" rel="noopener noreferrer"':'')+extra+'>'+h(label)+'</a>';
}
function contextFor(current=state) {
 return {case:current.view==='case'?current.id:current.case,section:current.section,via:current.via};
}
function recordLink(id,label=id,context={},extra={}) {
 const kind = knownKind(id);
 if (!kind) return h(label);
 const next = kind==='case' ? {view:kind,id,via:extra.via||context.via} : {view:kind,id,...context,...extra};
 return anchor(href(next),label);
}
function rich(value,context={}) {
 const text = String(value ?? '');
 let result='', start=0;
 for (const match of text.matchAll(/\b[A-Z][A-Z0-9]{1,7}-[A-Z]\d{2,}\b/g)) {
  result += h(text.slice(start,match.index))+recordLink(match[0],match[0],context);
  start=match.index+match[0].length;
 }
 return result+h(text.slice(start));
}
function valueHtml(value,context={}) {
 if (Array.isArray(value)) return value.length?'<ul class="values">'+value.map(item=>'<li>'+valueHtml(item,context)+'</li>').join('')+'</ul>':'<span class="small">None recorded.</span>';
 if (value && typeof value==='object') return pairs(value,context);
 return rich(value,context);
}
function pairs(object,context={}) {
 return '<dl>'+Object.entries(object||{}).map(([key,value])=>'<dt>'+h(key.replaceAll('_',' '))+'</dt><dd>'+valueHtml(value,context)+'</dd>').join('')+'</dl>';
}
const tags = values => (values||[]).map(value=>'<span class="tag">'+h(value)+'</span>').join('');
function caseLinks(ids,context={},via) {
 return (ids||[]).map(id=>'<span class="chip">'+recordLink(id,id+' · '+(byId.case[id]?.title||'Unavailable case'),context,{via})+'</span>').join('');
}
function scopedCases(ids,context={}) {
 return '<div class="scope"><h4>Cases in scope</h4>'+caseLinks(ids,context)+'</div>';
}
function recordHeading(kind,record,title,context={}) {
 return '<div class="kicker">'+h(kind)+' · '+recordLink(record.id,record.id,context)+'</div><h2>'+h(title)+'</h2>';
}
function contextTrail(current) {
 let result='';
 if (current.view!=='case' && owns(byId.case,current.case)) result+=anchor(href({view:'case',id:current.case,section:current.section,via:current.via}),'Back to '+current.case+(owns(sectionNames,current.section)?' · '+sectionNames[current.section]:''));
 if (current.via && owns(byId.comparison,current.via)) result+=(result?' · ':'')+recordLink(current.via,'From comparison '+current.via,{case:current.view==='case'?current.id:current.case,section:'comparisons'});
 return result?'<nav class="breadcrumbs" aria-label="Record context">'+result+'</nav>':'';
}
function caseSection(id,caseRecord) {
 return '<section id="'+h(id)+'" tabindex="-1"><p class="record-id">'+recordLink(caseRecord.id)+' · '+h(caseRecord.title)+'</p>';
}

function sourceReference(reference,context={},claimId) {
 const source=byId.source[reference.source_id];
 if (!source) return '<li>'+h(reference.source_id)+' · Source record unavailable.</li>';
 return '<li>'+recordLink(source.id,source.id+' · '+source.title,context,{claim:claimId})+' · '+anchor(source.url,'Open original')+
  '<span class="source-locator"><b>Locator:</b> '+rich(reference.locator,context)+' · '+h(source.access)+'</span><span>'+rich(reference.supports,context)+'</span></li>';
}
function claimCard(claim,context={},expanded=false) {
 let result='<div class="claim" data-record-id="'+h(claim.id)+'"><div class="record-id">'+recordLink(claim.id,claim.id,context)+'</div><p>'+rich(claim.statement,context)+'</p>'+tags([claim.confidence+' confidence',claim.causal_status,claim.evidence_type]);
 result+='<ul class="evidence">'+(claim.sources||[]).map(reference=>sourceReference(reference,context,claim.id)).join('')+'</ul>';
 result+='<details'+(expanded?' open':'')+'><summary>Test, strongest rival and remaining ambiguity</summary>'+pairs(claim.test,context)+'<p><b>Counterevidence:</b> '+rich(claim.counterevidence,context)+'</p><p><b>Inference limit:</b> '+rich(claim.inference_limits,context)+'</p></details></div>';
 return result;
}
function edgeCard(edge,context={},expanded=false) {
 const from=byId.node[edge.from],to=byId.node[edge.to];
 let result='<div class="edge" data-record-id="'+h(edge.id)+'"><div class="record-id">'+recordLink(edge.id,edge.id,context)+' · '+h(edge.confidence)+' confidence</div>';
 result+='<p class="edge-endpoint">'+recordLink(edge.from,edge.from+' · '+(from?.label||''),context)+'</p><div class="relation">'+h(edge.relation)+' →</div><p class="edge-endpoint">'+recordLink(edge.to,edge.to+' · '+(to?.label||''),context)+'</p>';
 result+='<p><b>Basis:</b> '+h(edge.basis)+'</p>'+pairs({scope:edge.scope},context)+'<p>'+rich(edge.qualification,context)+'</p>';
 result+='<p class="small"><b>Supporting claims:</b> '+(edge.claim_ids||[]).map(id=>recordLink(id,id,context)).join(', ')+'<br><b>Source records:</b> '+(edge.source_ids||[]).map(id=>recordLink(id,id,context)).join(', ')+'</p>';
 result+='<details'+(expanded?' open':'')+'><summary>Alternatives, joint inputs, necessity and dispute</summary>'+pairs({alternatives:edge.alternatives,joint_inputs:edge.joint_inputs,necessity_rationale:edge.necessity_rationale,dispute:edge.dispute},context)+'</details></div>';
 return result;
}
function comparisonCard(comparison,context={}) {
 return '<div class="card" data-record-id="'+h(comparison.id)+'"><div class="record-id">'+recordLink(comparison.id,comparison.id,context)+'</div><h3>'+recordLink(comparison.id,comparison.question,context)+'</h3>'+caseLinks(comparison.case_ids,context,comparison.id)+'<p class="small">'+rich(comparison.conclusion_limit,context)+'</p></div>';
}
function caseCard(caseRecord,via) {
 return '<div class="card"><div class="record-id">'+recordLink(caseRecord.id,caseRecord.id,{}, {via})+'</div><h3>'+recordLink(caseRecord.id,caseRecord.title,{}, {via})+'</h3><p class="route-date"><b>Case period:</b> '+h(caseRecord.period)+'</p><p class="route-date"><b>Episode interval:</b> '+h(caseRecord.episode?.interval||'Not recorded')+'</p><details><summary>Observation limits</summary><p>'+rich(caseRecord.episode?.observation_limits)+'</p></details></div>';
}
function sourceDetails(source,context={}) {
 const {id,title,url,contribution,...fields}=source;
 return '<p>'+anchor(url,'Open original source')+'</p>'+pairs(fields,context);
}

function renderCase(caseRecord,current) {
 const context=contextFor(current), claims=(caseRecord.claim_ids||[]).map(id=>byId.claim[id]).filter(Boolean);
 const edges=d.graph.edges.filter(edge=>edge.case_ids.includes(caseRecord.id));
 const nodes=d.graph.nodes.filter(node=>node.case_ids.includes(caseRecord.id));
 const comparisons=d.comparisons.filter(comparison=>comparison.case_ids.includes(caseRecord.id));
 let result=recordHeading('case',caseRecord,caseRecord.title,context)+'<p class="small">'+h(caseRecord.period)+' · '+h((caseRecord.region||[]).join('; '))+'</p>'+tags(caseRecord.outcome)+'<p>'+rich(caseRecord.summary,context)+'</p><p>'+anchor('contributions/'+caseRecord.contribution+'/report.md','Read the substantive research dossier')+'</p>';
 const historicalRoutes=routes.filter(route=>route.case_ids.includes(caseRecord.id));
 if (historicalRoutes.length) result+='<p class="small"><b>Historical routes:</b> '+historicalRoutes.map(route=>anchor(href({view:'chronology',route:route.id}),route.title)).join(' · ')+'</p>';
 result+='<nav class="subnav" aria-label="Case sections">'+Object.entries(sectionNames).map(([section,label])=>anchor(href({view:'case',id:caseRecord.id,section,via:current.via}),label,current.section===section?' aria-current="location"':'')).join('')+'</nav>';
 if (current.section && !owns(sectionNames,current.section)) result+='<div class="scope caution"><p>The section '+h(current.section)+' is not available. The requested case is shown below.</p></div>';
 result+=caseSection('episode',caseRecord)+'<h3>What was actually observed?</h3><div class="scope">'+pairs(caseRecord.episode,context)+'</div><details><summary>Who chose, paid, worked and could refuse?</summary>'+pairs(caseRecord.actors,context)+'</details><details><summary>Tasks, livelihoods and entry barriers</summary>'+pairs(caseRecord.labour,context)+'</details></section>';
 result+=caseSection('stages',caseRecord)+'<h3>Stages and outcomes</h3>'+pairs(caseRecord.stages,context)+'<div class="scope caution"><h4>Counterevidence and limits</h4>'+valueHtml(caseRecord.counterevidence,context)+'</div></section>';
 result+=caseSection('evidence',caseRecord)+'<h3>Evidence and rival explanations</h3>'+claims.map(claim=>claimCard(claim,{...context,section:'evidence'})).join('')+'</section>';
 result+=caseSection('relations',caseRecord)+'<h3>Scoped graph relations</h3><p class="small">These are recorded relationships within stated episodes. Multiple inputs do not imply joint necessity; a path across cases is not proof of causation.</p><h4>Nodes in this case</h4><p>'+nodes.map(node=>'<span class="chip">'+recordLink(node.id,node.id+' · '+node.label,{...context,section:'relations'})+'</span>').join('')+'</p>';
 result+=edges.length?edges.map(edge=>edgeCard(edge,{...context,section:'relations'})).join(''):'<p class="empty">No graph edges are asserted for this case.</p>';
 result+='</section>'+caseSection('comparisons',caseRecord)+'<h3>Why these comparisons?</h3><p class="small">Comparisons test explanations across different cases. They do not assert causal or transmission links.</p>'+(comparisons.length?comparisons.map(comparison=>comparisonCard(comparison,{...context,section:'comparisons'})).join(''):'<p class="empty">No structured comparison is attached to this case.</p>')+'</section>';
 result+=caseSection('sources',caseRecord)+'<h3>Source access and lineage</h3>';
 for (const id of caseRecord.source_ids||[]) {
  const source=byId.source[id];
  if (source) result+='<details><summary>'+h(source.id+' · '+source.title)+'</summary><p>'+recordLink(source.id,'Inspect '+source.id+' and its linked claims',{...context,section:'sources'})+'</p>'+sourceDetails(source,{...context,section:'sources'})+'</details>';
 }
 return result+'</section>';
}
function renderClaim(claim,current) {
 const context=contextFor(current);
 const supportingEdges=d.graph.edges.filter(edge=>edge.claim_ids.includes(claim.id));
 return recordHeading('claim',claim,'Evidence claim',context)+scopedCases(claim.case_ids,context)+claimCard(claim,context,true)+'<h3>Relations citing this claim</h3>'+(supportingEdges.length?supportingEdges.map(edge=>'<p>'+recordLink(edge.id,edge.id+' · '+edge.relation,context)+'</p>').join(''):'<p class="small">No graph relation cites this claim.</p>');
}
function renderEdge(edge,current) {
 const context=contextFor(current);
 return recordHeading('edge',edge,'Scoped graph relation',context)+scopedCases(edge.case_ids,context)+edgeCard(edge,context,true)+'<div class="scope caution"><p>This view contains one recorded relation. Its scope, alternatives and evidence do not license an inferred chain of causes.</p></div>';
}
function renderNode(node,current) {
 const context=contextFor(current), incident=d.graph.edges.filter(edge=>edge.from===node.id||edge.to===node.id);
 return recordHeading('node',node,node.label,context)+tags([node.kind])+scopedCases(node.case_ids,context)+'<h3>'+incident.length+' recorded incident relation'+(incident.length===1?'':'s')+'</h3><p class="small">All relations attached to this exact node are shown, each with its own case scope. Similar labels are not merged.</p>'+(incident.length?incident.map(edge=>'<p class="small">'+caseLinks(edge.case_ids,context)+'</p>'+edgeCard(edge,context)).join(''):'<p class="empty">This node has no recorded incident relation.</p>');
}
function renderSource(source,current) {
 const context=contextFor(current), claims=d.claims.filter(claim=>claim.sources.some(reference=>reference.source_id===source.id));
 const selected=claims.find(claim=>claim.id===current.claim);
 const cases=d.cases.filter(caseRecord=>caseRecord.source_ids.includes(source.id)).map(caseRecord=>caseRecord.id);
 let result=recordHeading('source',source,source.title,context)+tags([source.access,source.source_type]);
 if (selected) result+='<div class="scope" id="source-locator"><h3>Evidence used for '+recordLink(selected.id,selected.id,context)+'</h3><p>'+rich(selected.statement,context)+'</p><ul class="evidence">'+selected.sources.filter(reference=>reference.source_id===source.id).map(reference=>sourceReference(reference,context,selected.id)).join('')+'</ul></div>';
 result+=sourceDetails(source,context)+scopedCases(cases,context)+'<h3>Claims citing this source</h3>';
 return result+(claims.length?claims.map(claim=>'<div class="card"><p>'+recordLink(claim.id,claim.id+' · '+claim.statement,context)+'</p><ul class="evidence">'+claim.sources.filter(reference=>reference.source_id===source.id).map(reference=>sourceReference(reference,context,claim.id)).join('')+'</ul></div>').join(''):'<p class="empty">No claim in this build cites this source.</p>');
}
function renderComparison(comparison,current) {
 const context=contextFor(current),{id,question,case_ids,contribution,...fields}=comparison;
 return recordHeading('comparison',comparison,question,context)+'<p class="layer-note small">An analytical comparison, not a causal edge or a claim of independent observations.</p><p>'+anchor(href({view:'comparisons'}),'All comparisons')+'</p>'+caseLinks(case_ids,context,id)+pairs(fields,context)+'<h3>Cases in this comparison</h3>'+case_ids.map(caseId=>byId.case[caseId]?caseCard(byId.case[caseId],id):'<p>'+h(caseId)+' is unavailable.</p>').join('');
}
function renderComparisonIndex() {
 return '<div class="kicker">Comparison layer</div><h2>Compare cases</h2><p class="layer-note">These records test explanations across selected cases. They preserve differences, shared evidence and omitted countercases; they do not add causal edges.</p><div class="list-search"><label for="comparison-search">Find a comparison by question or case ID</label><input type="search" id="comparison-search" placeholder="e.g. SYN-X04, wages, IND-C04"></div><p class="count" id="comparison-count" role="status"></p><div id="comparison-list"></div>';
}
function renderChronology(current) {
 let result='<div class="kicker">Chronological navigation</div><h2>Historical routes</h2><p class="layer-note">Follow broad historical routes through the cases. Overlapping periods and episode differences remain explicit; route order is not a causal or transmission claim.</p>';
 if (!routes.length) return result+'<div class="scope caution"><p>Chronological route data are not included in this build. The case catalogue remains available.</p><p>'+anchor('analysis/GLOBAL_MAP.md','Read the full historical route and its date qualifications')+'</p></div>';
 result+='<div class="scope caution">'+valueHtml(d.chronology.caution||'Routes are broad, overlapping navigation bins, not precise invention dates.')+'</div><p class="small">'+h(d.chronology.edition_date||'')+' · '+anchor('analysis/GLOBAL_MAP.md','Full historical route, methods and qualifications')+'</p>';
 if (current.route && !owns(routeById,current.route)) return result+'<div class="scope caution"><p>The requested route '+h(current.route)+' is unavailable.</p><p>'+anchor(href({view:'chronology'}),'Show all historical routes')+'</p></div>';
 const selected=routeById[current.route];
 if (!selected) return result+routes.map(route=>'<div class="card"><div class="record-id">'+h(route.id)+'</div><h3>'+anchor(href({view:'chronology',route:route.id}),route.title)+'</h3>'+valueHtml(route.scope)+'<p class="small">'+route.case_ids.length+(route.case_ids.length===1?' case reference':' case references')+' · broad, overlapping route</p></div>').join('');
 result+='<p>'+anchor(href({view:'chronology'}),'All historical routes')+'</p><h3>'+h(selected.title)+'</h3><div class="scope">'+valueHtml(selected.scope)+'</div><p class="small">Dates below reproduce the case records, including contested ranges and separate experimental or observation episodes.</p>';
 return result+selected.case_ids.map(id=>byId.case[id]?caseCard(byId.case[id]):'<p>'+h(id)+' is unavailable.</p>').join('');
}

function parseState() {
 const raw=location.hash.slice(1);
 if (!raw) return {view:'case',id:d.cases[0]?.id};
 if (!raw.includes('=')) {
  let legacy;try{legacy=decodeURIComponent(raw)}catch{return {view:'record',id:raw}}
  if (knownKind(legacy)) {const next={view:knownKind(legacy),id:legacy};history.replaceState(null,'',href(next));return next;}
  if (owns(sectionNames,legacy)) return {view:'legacy-section',section:legacy};
  return {view:'record',id:legacy};
 }
 const current=Object.fromEntries(new URLSearchParams(raw));
 current.view=current.view||'case';
 if (current.view==='record' && knownKind(current.id)) current.view=knownKind(current.id);
 if (current.view==='case' && !current.id) current.id=d.cases[0]?.id;
 return current;
}
function renderCaseList() {
 const terms=el('search').value.toLowerCase().trim().split(/\s+/).filter(Boolean), strand=el('strand').value;
 const matches=d.cases.filter(caseRecord=>(!strand||caseRecord.contribution===strand)&&terms.every(term=>JSON.stringify(caseRecord).toLowerCase().includes(term)));
 const selected=state.view==='case'?state.id:state.case;
 el('count').textContent=matches.length+' of '+d.cases.length+' cases'+(selected&&!matches.some(caseRecord=>caseRecord.id===selected)?' · open case is outside these filters':'');
 el('case-list').innerHTML=matches.map(caseRecord=>'<a class="case-link" href="'+h(href({view:'case',id:caseRecord.id}))+'" aria-current="'+String(caseRecord.id===selected)+'"><span class="record-id">'+h(caseRecord.id)+'</span><span class="case-title">'+h(caseRecord.title)+'</span><span class="case-period">'+h(caseRecord.period)+'</span></a>').join('')||'<p class="empty">No cases match these filters. Try a broader term.</p>';
}
function renderComparisonList() {
 const terms=el('comparison-search').value.toLowerCase().trim().split(/\s+/).filter(Boolean);
 const matches=d.comparisons.filter(comparison=>terms.every(term=>JSON.stringify(comparison).toLowerCase().includes(term)));
 el('comparison-count').textContent=matches.length+' of '+d.comparisons.length+' comparisons';
 el('comparison-list').innerHTML=matches.map(comparison=>comparisonCard(comparison)).join('')||'<p class="empty">No comparisons match. Try a broader term.</p>';
}
function render(initial=false) {
 state=parseState();
 const renderers={case:renderCase,claim:renderClaim,source:renderSource,node:renderNode,edge:renderEdge,comparison:renderComparison};
 let result=contextTrail(state), title='Technology in use';
 if (owns(renderers,state.view) && owns(byId[state.view],state.id)) {
  const record=byId[state.view][state.id];result+=renderers[state.view](record,state);title=state.id+' · '+(record.title||record.label||record.question||state.view);
 } else if (state.view==='chronology') {result+=renderChronology(state);title='Historical routes';}
 else if (state.view==='comparisons') {result+=renderComparisonIndex();title='Compare cases';}
 else if (state.view==='legacy-section') result+='<h2>This section link needs a case</h2><p>Older links such as #'+h(state.section)+' do not identify a case. Select a case, then use its section links to create a complete URL.</p>';
 else result+='<h2>Record not found</h2><p>The requested '+h(state.view)+' '+h(state.id||'')+' is not available in this build. No other case has been substituted.</p><p>Choose a case or open an existing record ID.</p>';
 el('detail').innerHTML=result;
 document.title=title+' · Technology in use';
 const selected=state.view==='case'?state.id:state.case;
 el('cases-layer').href=href({view:'case',id:owns(byId.case,selected)?selected:d.cases[0]?.id});
 for (const layer of ['cases','chronology','comparisons']) {
  const active=layer==='chronology'?state.view==='chronology':layer==='comparisons'?['comparison','comparisons'].includes(state.view):!['chronology','comparison','comparisons'].includes(state.view);
  if(active) el(layer+'-layer').setAttribute('aria-current','page');else el(layer+'-layer').removeAttribute('aria-current');
 }
 renderCaseList();
 if (state.view==='comparisons') {el('comparison-search').addEventListener('input',renderComparisonList);renderComparisonList();}
 if (!initial || location.hash) requestAnimationFrame(()=>{
  const target=state.view==='case' && owns(sectionNames,state.section)?el(state.section):el('detail');
  target?.focus({preventScroll:true});target?.scrollIntoView({block:'start'});
 });
}

const counts=d.validation.counts;
el('metrics').innerHTML=[['cases',counts.cases],['evidence claims',counts.claims],['source records',counts.sources],['scoped graph edges',counts.edges]].map(([label,count])=>'<span><b>'+h(count)+'</b> '+h(label)+'</span>').join('');
for (const strand of [...new Set(d.cases.map(caseRecord=>caseRecord.contribution))].sort()) {const option=document.createElement('option');option.value=strand;option.textContent=strand+' · '+(strandNames[strand]||strand);el('strand').append(option);}
if (matchMedia('(max-width:800px)').matches) el('case-picker').open=false;
el('id-form').addEventListener('submit',event=>{event.preventDefault();const id=el('record-id').value.trim().toUpperCase();if(id){location.hash=href({view:knownKind(id)||'record',id}).slice(1);if(matchMedia('(max-width:800px)').matches)el('case-picker').open=false;}});
el('case-list').addEventListener('click',event=>{if(event.target.closest('a')&&matchMedia('(max-width:800px)').matches)el('case-picker').open=false;});
el('search').addEventListener('input',renderCaseList);
el('strand').addEventListener('change',renderCaseList);
el('skip-detail').addEventListener('click',event=>{event.preventDefault();el('detail').focus();el('detail').scrollIntoView({block:'start'});});
window.addEventListener('hashchange',()=>render());
render(true);
</script>
</body></html>'''


def build(data_dir: Path, output: Path) -> None:
    payload = {
        kind: json.loads((data_dir / f'{kind}.json').read_text())
        for kind in ['cases', 'claims', 'sources', 'graph', 'comparisons', 'validation']
    }
    if payload['validation'].get('errors'):
        raise SystemExit('Refusing explorer generation: collection validation contains errors')
    chronology_path = data_dir / 'chronology.json'
    payload['chronology'] = json.loads(chronology_path.read_text()) if chronology_path.exists() else None
    if payload['chronology'] is not None:
        chronology = payload['chronology']
        if not isinstance(chronology, dict) or not isinstance(chronology.get('routes'), list):
            raise SystemExit('Refusing explorer generation: chronology must contain a routes array')
        known_cases = {case['id'] for case in payload['cases']}
        route_ids = set()
        for route in chronology['routes']:
            if (not isinstance(route, dict) or not isinstance(route.get('id'), str)
                    or not route['id'] or route['id'] in route_ids
                    or not isinstance(route.get('title'), str)
                    or not isinstance(route.get('case_ids'), list)
                    or any(not isinstance(case_id, str) or case_id not in known_cases for case_id in route['case_ids'])):
                raise SystemExit('Refusing explorer generation: invalid, duplicate or unknown chronology route reference')
            route_ids.add(route['id'])
    jsdata = json.dumps(payload, ensure_ascii=False).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(HTML.replace('__DATA__', jsdata))
    print('Wrote', output)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', type=Path, default=ROOT / 'data', help='Compiled data directory (defaults to programme data)')
    parser.add_argument('--output', type=Path, default=ROOT / 'index.html', help='Output HTML path; use a temporary path for previews')
    args = parser.parse_args()
    build(args.data_dir.resolve(), args.output.resolve())
