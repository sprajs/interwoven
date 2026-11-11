// Execute the frozen explorer's pure routing/render functions in Node.
// Deliberately not a browser, DOM, layout, focus, reload, or accessibility test.
import fs from 'node:fs';
import vm from 'node:vm';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const out=path.dirname(fileURLToPath(import.meta.url));
const html=fs.readFileSync(path.join(out,'../r3-snapshot/index.html'),'utf8');
const payloadText=html.match(/<script id="research-data" type="application\/json">([\s\S]*?)<\/script>/)[1];
const payload=JSON.parse(payloadText);
const script=[...html.matchAll(/<script>([\s\S]*?)<\/script>/g)][0][1];
const setup=script.slice(0,script.indexOf('const counts=d.validation.counts;'));
const context=vm.createContext({URLSearchParams,location:{hash:''},document:{getElementById(id){if(id==='research-data')return {textContent:payloadText};throw new Error('Unexpected DOM call '+id);}},history:{replaceState(a,b,url){context.location.hash=url;}}});
vm.runInContext(setup,context);
const run=code=>vm.runInContext(code,context);
const checks=[];
function check(name,pass,detail){checks.push({name,passed:!!pass,detail});}
function invoke(name,...args){return run(name+'('+args.map(x=>JSON.stringify(x)).join(',')+')');}
function parse(hash){context.location.hash=hash;return JSON.parse(JSON.stringify(run('parseState()')));}
function links(markup){return [...markup.matchAll(/href="([^"]+)"/g)].map(m=>m[1].replaceAll('&amp;','&').replaceAll('&quot;','"').replaceAll('&#39;',"'"));}
function hashParams(url){return Object.fromEntries(new URLSearchParams(url.slice(1)));}
const renderers={case:'renderCase',claim:'renderClaim',source:'renderSource',node:'renderNode',edge:'renderEdge',comparison:'renderComparison'};
const records={case:payload.cases,claim:payload.claims,source:payload.sources,node:payload.graph.nodes,edge:payload.graph.edges,comparison:payload.comparisons};
const allIds=Object.fromEntries(Object.entries(records).flatMap(([k,rows])=>rows.map(x=>[x.id,k])));
const allRoutes=new Set(payload.chronology.routes.map(r=>r.id));
const malformed=[];const unknown=[];let inspectedLinks=0;
for(const [kind,rows] of Object.entries(records)){
 for(const row of rows){
  const state={view:kind,id:row.id};
  const markup=invoke(renderers[kind],row,state);
  for(const url of links(markup)){
   if(!url.startsWith('#'))continue;inspectedLinks++;
   const p=hashParams(url);
   if(!p.view)malformed.push({record:row.id,url});
   if(['case','claim','source','node','edge','comparison'].includes(p.view)&&allIds[p.id]!==p.view)unknown.push({record:row.id,url});
   if(p.view==='chronology'&&p.route&&!allRoutes.has(p.route))unknown.push({record:row.id,url});
  }
 }
}
check('Every rendered record-link URL resolves to a known typed record or chronology route',!malformed.length&&!unknown.length,{record_count:Object.keys(allIds).length,hash_links_inspected:inspectedLinks,malformed,unknown});
const sections=['episode','stages','evidence','relations','comparisons','sources'];
const badSectionURLs=[];
for(const c of payload.cases)for(const section of sections){
 const url=invoke('href',{view:'case',id:c.id,section});
 const p=parse(url);
 if(p.view!=='case'||p.id!==c.id||p.section!==section)badSectionURLs.push({url,p});
}
check('All 528 case/section URLs preserve identity when reparsed from a fresh hash',!badSectionURLs.length,{count:payload.cases.length*sections.length,issues:badSectionURLs});
const legacy=parse('#MED-C07');
check('Legacy case ID redirects into explicit typed URL',legacy.view==='case'&&legacy.id==='MED-C07'&&context.location.hash==='#view=case&id=MED-C07',{parsed:legacy,hash:context.location.hash});
check('Ambiguous old section URL does not silently select the first case',parse('#relations').view==='legacy-section',parse('#relations'));
const missing=parse('#view=case&id=NO-C99&section=relations');
check('Unknown explicit case stays unknown instead of substituting another case',missing.id==='NO-C99',missing);

// Worked edge -> claim -> claim-specific source-locator route, retaining case context.
const current={view:'case',id:'MED-C07',section:'relations'};
const c=payload.cases.find(x=>x.id===current.id);
const caseMarkup=invoke('renderCase',c,current);
const edgeURL=links(caseMarkup).find(u=>u.startsWith('#')&&hashParams(u).view==='edge');
const edgeState=parse(edgeURL);const edge=payload.graph.edges.find(x=>x.id===edgeState.id);
const edgeMarkup=invoke('contextTrail',edgeState)+invoke('renderEdge',edge,edgeState);
const claimURL=links(edgeMarkup).find(u=>u.startsWith('#')&&hashParams(u).view==='claim');
const claimState=parse(claimURL);const claim=payload.claims.find(x=>x.id===claimState.id);
const claimMarkup=invoke('renderClaim',claim,claimState);
const sourceURL=links(claimMarkup).find(u=>u.startsWith('#')&&hashParams(u).view==='source'&&hashParams(u).claim===claim.id);
const sourceState=parse(sourceURL);const source=payload.sources.find(x=>x.id===sourceState.id);
const sourceMarkup=invoke('contextTrail',sourceState)+invoke('renderSource',source,sourceState);
check('MED-C07 relation -> exact claim -> claim-specific locator retains return context',edgeState.case==='MED-C07'&&claimState.case==='MED-C07'&&sourceState.case==='MED-C07'&&sourceState.claim===claim.id&&sourceMarkup.includes('id="source-locator"')&&links(sourceMarkup).includes('#view=case&id=MED-C07&section=relations'),{edgeURL,claimURL,sourceURL,locator:claim.sources.find(x=>x.source_id===source.id).locator});

const comparison=payload.comparisons.find(x=>x.id==='SYN-X07');
const origin={case:'SKL-C01',section:'comparisons'};
const comparisonURL=links(invoke('recordLink',comparison.id,comparison.id,origin))[0];
const comparisonState=parse(comparisonURL);
const comparisonMarkup=invoke('contextTrail',comparisonState)+invoke('renderComparison',comparison,comparisonState);
const destinationURL=links(comparisonMarkup).find(u=>u.startsWith('#')&&hashParams(u).id==='OCE-C01');
const destinationState=parse(destinationURL);
const destinationMarkup=invoke('contextTrail',destinationState)+invoke('renderCase',payload.cases.find(x=>x.id==='OCE-C01'),destinationState);
const returnURL=links(destinationMarkup).find(u=>u.startsWith('#')&&hashParams(u).view==='comparison'&&hashParams(u).id==='SYN-X07');
check('Precision/navigation comparison permits another case and return to the comparison',destinationState.id==='OCE-C01'&&destinationState.via==='SYN-X07'&&!!returnURL,{comparisonURL,destinationURL,returnURL});
const chronologyMarkup=invoke('renderChronology',{view:'chronology',route:'early-landscapes'});
check('Chronology route gives linked bounded cases with both period and episode interval',chronologyMarkup.includes('Episode interval:')&&links(chronologyMarkup).includes('#view=case&id=OCE-C02'),{route:'early-landscapes'});
const node=payload.graph.nodes.find(x=>x.id===edge.from);
const nodeMarkup=invoke('renderNode',node,{view:'node',id:node.id,case:'MED-C07',section:'relations'});
check('Node view exposes its exact incident edge and scoped cases',links(nodeMarkup).some(u=>u.startsWith('#')&&hashParams(u).id===edge.id),{node:node.id,edge:edge.id});

const result={method:'Node VM executes unchanged routing/render function source from the frozen HTML, with minimal JSON and location fixtures. No browser used; event, DOM, visual, scrolling, accessibility, reload/new-tab behavior remains unverified.',passed:checks.every(c=>c.passed),checks};
fs.writeFileSync(path.join(out,'navigation-verification.json'),JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify(result,null,2));
