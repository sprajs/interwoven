// Source-level evaluation of pure URL and HTML-string helpers only.
// No browser, DOM engine, page load, HTTP request, interaction or visual rendering.
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),crypto=require('node:crypto');
const audit=path.resolve(__dirname,'..'),root=path.join(audit,'r3-snapshot');
const html=fs.readFileSync(path.join(root,'index.html'),'utf8');
const payload=html.match(/<script id="research-data" type="application\/json">([\s\S]*?)<\/script>/)[1];
const scripts=[...html.matchAll(/<script>([\s\S]*?)<\/script>/g)];
const code=scripts.at(-1)[1].split('const counts=d.validation.counts;')[0];
function context(hash=''){
 const box={URLSearchParams,location:{hash},document:{getElementById:id=>{if(id==='research-data')return{textContent:payload};throw new Error('Unexpected DOM access: '+id)}},history:{replaceState:(_a,_b,url)=>box.location.hash=url}};
 vm.createContext(box);vm.runInContext(code,box);return box;
}
const box=context(),checks=[];
function test(name,expression){const result=vm.runInContext(expression,box);checks.push({check:name,passed:!!result});if(!result)throw new Error(name)}
test('separate case and section state',`href({view:'case',id:'MED-C07',section:'relations'})==='#view=case&id=MED-C07&section=relations'`);
box.location.hash='#view=case&id=MED-C07&section=relations';test('parse stored case and section',`parseState().id==='MED-C07'&&parseState().section==='relations'`);
const fresh=context(box.location.hash);checks.push({check:'fresh function context preserves URL identity',passed:vm.runInContext(`parseState().id==='MED-C07'&&parseState().section==='relations'`,fresh)});
box.location.hash='#relations';test('ambiguous old section is explicit, not substituted case',`parseState().view==='legacy-section'&&!parseState().id`);
box.location.hash='#MED-C07';test('legacy case mapped explicitly',`parseState().id==='MED-C07'&&location.hash.includes('id=MED-C07')`);
test('case section link contains both identifiers',`renderCase(byId.case['MED-C07'],{view:'case',id:'MED-C07'}).includes('#view=case&amp;id=MED-C07&amp;section=relations')`);
test('edge links exact supporting claim and preserves hypothesis',`(()=>{const s=renderEdge(byId.edge['IND-E14'],{view:'edge',id:'IND-E14',case:'IND-C04',section:'relations'});return s.includes('#view=claim&amp;id=IND-K10&amp;case=IND-C04&amp;section=relations')&&s.includes('hypothesis')&&s.includes('not measured recruitment effects')})()`);
test('claim links claim-specific source locator',`renderClaim(byId.claim['IND-K10'],{view:'claim',id:'IND-K10',case:'IND-C04',section:'relations'}).includes('#view=source&amp;id=IND-S08&amp;case=IND-C04&amp;section=relations&amp;claim=IND-K10')`);
test('source view preserves locator and case context',`(()=>{const s=renderSource(byId.source['IND-S08'],{view:'source',id:'IND-S08',case:'IND-C04',section:'relations',claim:'IND-K10'});return s.includes('Evidence used for')&&s.includes('accepted-manuscript pp. 15–16, 25–32 and 37–41')&&s.includes('Scope Limit')===false&&s.includes('scope limit')})()`);
test('node exposes exact incident edges',`(()=>{const s=renderNode(byId.node['IND-T33'],{view:'node',id:'IND-T33'});return ['IND-E09','IND-E10','IND-E11'].every(id=>s.includes('#view=edge&amp;id='+id))&&s.includes('3 recorded incident relations')})()`);
test('comparison preserves analogy boundary and onward case link',`(()=>{const s=renderComparison(byId.comparison['SYN-X02'],{view:'comparison',id:'SYN-X02',case:'MAT-C05',section:'comparisons'});return s.includes('An analytical comparison, not a causal edge')&&s.includes('#view=case&amp;id=NET-C02&amp;via=SYN-X02')&&s.includes('does not establish')})()`);
const pathRows=[];
function record(view,id,criteria){
 const html=vm.runInContext(`render${view[0].toUpperCase()+view.slice(1)}(byId[${JSON.stringify(view)}][${JSON.stringify(id)}],{view:${JSON.stringify(view)},id:${JSON.stringify(id)}})`,box);
 const texts=criteria.map(x=>({text:x,present:html.includes(x)}));pathRows.push({view,id,criteria:texts,passed:texts.every(x=>x.present)});
}
record('case','MAT-C05',['SYN-X02','modern experiments','observation limits']);
record('comparison','SYN-X02',['NET-C02','IND-C07','not a causal edge','not independent corroborations']);
record('case','NET-C02',['NET-X01','Counterevidence','Inference limit']);
record('comparison','NET-X01',['NET-C04','Potential transmission is not proven by chronology','script-sensitive cost models']);
record('case','NET-C04',['NET-E10','NET-K14','source']);
record('case','IND-C07',['CTX-X01','1949']);
record('comparison','CTX-X01',['CTX-C01','EXACT SAME','No backward projection']);
record('case','CTX-C01',['CTX-K02','unpaid','observation limits']);
const routeHtml=vm.runInContext(`renderChronology({view:'chronology',route:'medieval-networks'})`,box);
checks.push({check:'chronology links path start and retains noncausal/uncertain dates',passed:routeHtml.includes('#view=case&amp;id=MAT-C05')&&routeHtml.includes('route order is not a causal or transmission claim')&&routeHtml.includes('Case period:')&&routeHtml.includes('Episode interval:')});
const out={scope:'Source-level pure helper evaluation. No browser, DOM, external request, click, reload or visual rendering; fresh-context URL parsing is not a live-browser reload.',html_sha256:crypto.createHash('sha256').update(html).digest('hex'),checks,reading_path:pathRows,all_checks_passed:checks.every(x=>x.passed),all_path_checks_passed:pathRows.every(x=>x.passed),interpretation:'The test follows comparisons across Andean metallurgy, Chinese/European printing and two Chinese textile periods. These are labelled analogy/comparison transitions, not documented developmental ancestry.'};
fs.writeFileSync(path.join(__dirname,'source-navigation-verification.json'),JSON.stringify(out,null,2)+'\n');console.log(JSON.stringify(out,null,2));
