#!/usr/bin/env python3
"""Preserve explicitly authored cross-case inference and comparison records."""
from pathlib import Path
import json
root=Path(__file__).resolve().parents[1]
allclaims={}
for p in (root/'contributions').glob('*/claims.json'):
 for c in json.loads(p.read_text()): allclaims[c['id']]=c
p=root/'contributions/SYN'
base=[c for c in json.loads((p/'claims.json').read_text()) if int(c['id'].split('K')[1])<10]
specs=[
 ('SYN-K10',['ANC-K01','DIG-K13','AGR-K18'],
  'In the selected cases, a described working principle, household device availability and equipment delivery do not establish operational scale, control of access or sustained beneficial use.',
  'Observed artifact/access -> distinct deployment and use constraints -> different downstream outcomes; no automatic stage transition.',
  'A simple technical-availability account predicts that providing an effective object is enough for the claimed downstream outcome.',
  'Find documented configurations with the object/principle present but the relevant downstream use unestablished or constrained.',
  'The cases observe different stages, not matched treatment effects; Hero’s absence of load is a source limit, not proof of no ancient application.'),
 ('SYN-K11',['MAT-K15','NET-K07','IND-K20'],
  'Material performance and production methods are task-dependent in these comparisons; older practices and newer inputs can coexist or combine rather than form a universal replacement sequence.',
  'Different required outputs and workflows -> different useful properties -> selective adoption or hybrid production.',
  'A single technical-superiority ranking predicts broadly uniform replacement once the newer option is available.',
  'Compare measured material trade-offs and documented mixed workflows or specialised uses.',
  'Coexistence alone does not prove optimal choice or consent; prices, exclusion and unavailable alternatives may also explain persistence.'),
 ('SYN-K12',['AGR-K07','ANC-K08','MED-K22'],
  'Chooser, payer, operator and affected person cannot be assumed identical: the selected cases show altered control over output, coerced maintenance work and provider revenue incentives.',
  'Decision rights/revenue/labour obligations -> actor-specific choices -> adoption and benefits/harms distributed across different people.',
  'A representative voluntary adopter with a common welfare objective is sufficient to explain observed uptake.',
  'Look for directly documented labour status, entitlement changes or an intervention altering one actor’s incentive.',
  'These cases establish heterogeneous interests, not a general effect size of coercion or a complete welfare balance.'),
 ('SYN-K13',['AGR-K18','ANC-K06','MED-K15'],
  'Recurring operating and maintenance arrangements matter in these cases, but the evidence does not isolate maintenance as the universal or unique cause of persistence or reversal.',
  'Recurring skill/supply/work changes -> usable service changes -> altered retention or effective operation.',
  'A durable installation or successful initial intervention alone secures continuing service; alternatively demand/ecology rather than upkeep explains decline.',
  'Trace equipment condition, recurring provision and service outcomes; distinguish continued inputs from actual operation.',
  'Multiple variables change together; retrospective decline explanations may share records and remain underdetermined.'),
 ('SYN-K14',['AGR-K15','AGR-K03','MOB-K03'],
  'Risk, labour over a full production cycle and complete-journey costs can change the relevant adoption comparison; acquisition price or one performance denominator is insufficient in these cases.',
  'Uncounted risk, recurring labour or transfer costs -> different feasible payoff for the task -> changed investment or comparative ranking.',
  'Nominal purchase price, initial yield per hectare or one transport-leg cost alone ranks the alternatives.',
  'Vary risk separately from cash, include full rotations, and compare complete journeys rather than isolated legs.',
  'The insurance experiment, contested labour model and archaeological cost inference have different identification strengths and cannot be pooled.'),
 ('SYN-K16',['LBR-K02','MOB-K22','MOB-K23'],
  'Aggregate opportunities or productivity gains do not establish accessible gains for displaced individuals: incumbent outcomes, task relocation and bargaining arrangements require separate evidence.',
  'Technology shifts tasks -> workers differ in exposure/entry rights -> compensation, reallocation and outcomes diverge.',
  'New work or aggregate employment resilience automatically compensates those whose tasks disappear.',
  'Track incumbents separately from entrants and identify how task jurisdiction and compensation actually changed.',
  'US labour cases are not global replications; bargaining records do not identify every worker’s realised transition or welfare.'),
 ('SYN-K17',['DIG-K18','MED-K21','MOB-K21'],
  'The source audits identify consequential differences between measures and causal claims: VR gaming reports, ORT episode definitions and container adoption-timing estimates cannot be treated as interchangeable general adoption evidence.',
  'Observation definition/identification strategy -> reported quantity -> permissible interpretation.',
  'Headline summaries preserve sufficient information for a cross-technology success ranking.',
  'Inspect original question wording, table denominators and published identification cautions.',
  'These purposively selected discrepancies do not estimate the error rate of the entire bibliography.'),
 ('SYN-K18',['DIG-K24','DIG-K09','DIG-K18'],
  'The acquired digital evidence leaves the universal portability-versus-performance ranking and the “most laptops cheaper than most smartphones” assertion unestablished; it supports only bounded task and use comparisons.',
  'Bundled device/service attributes and access -> observed preference/use -> insufficient identification of one dominant attribute.',
  'Pocketability alone explains market outcomes, or hardware price alone orders the relevant choices.',
  'Require dated price distributions and designs separating portability, connectivity, software, performance and ergonomics.',
  'Unestablished is not false; no current global VR or device-price verdict is claimed.')]
new=[]
for ident,refs,statement,chain,rival,obs,limit in specs:
 missing=[r for r in refs if r not in allclaims]
 if missing: raise SystemExit(f'Waiting for source claims {missing}')
 caseids=sorted({x for r in refs for x in allclaims[r]['case_ids']})
 supports=[];seen=set()
 for r in refs:
  for sup in allclaims[r]['sources']:
   key=(sup['source_id'],str(sup['locator']))
   if key in seen: continue
   seen.add(key);supports.append(dict(source_id=sup['source_id'],locator=sup['locator'],supports=f'Bounded evidence in {r}: '+sup['supports']))
 new.append(dict(id=ident,case_ids=caseids,statement=statement,evidence_type='synthesis-inference',confidence='medium',causal_status='mechanism-supported' if ident not in ['SYN-K17','SYN-K18'] else 'contested',sources=supports,counterevidence=rival,inference_limits=limit,test=dict(status='evaluated' if ident in ['SYN-K10','SYN-K11','SYN-K12','SYN-K16','SYN-K17'] else 'underdetermined',mechanism_chain=chain,strongest_rival=rival,discriminating_observation=obs,evidence_sought_found='Parent compared the inspected case claims '+', '.join(refs)+'. Source acquisition is documented by their authors; independent sample audits are recorded separately in reviews/.',remaining_ambiguity=limit,hypothesis_timing='retrospective synthesis')))
(p/'claims.json').write_text(json.dumps(base+new,indent=2,ensure_ascii=False)+'\n')
comparisons=[
 dict(id='SYN-X01',question='When does equipment presence fail to establish useful service?',case_ids=['ANC-C01','AGR-C07','DIG-C04','MED-C05'],useful_similarities='All distinguish an available object or principle from the user’s relevant outcome.',important_differences='Textual description, field trial, survey and institutional production history observe different stages and populations.',evidence_comparability='Diagnostic counterexamples to a universal sufficiency claim; not matched causal estimates or a failure-rate sample.',connections_nonindependence='Some complements and reporting traditions recur; modern programme research is better observed than ancient use.',omitted_countercases=['Simple tools usable with few external complements','Adoption after a single price/quality change','Non-users with adequate complements'],conclusion_limit='Names stage distinctions; does not show that complements are always the binding constraint.'),
 dict(id='SYN-X02',question='Does a newer technology necessarily displace older practice?',case_ids=['MAT-C05','NET-C02','NET-C03','IND-C07','MOB-C05'],useful_similarities='Observable coexistence, hybrid workflows or stable task-specific niches.',important_differences='Alloy properties, text workflows, textile inputs and vehicle duty cycles differ.',evidence_comparability='Can disprove a universal replacement narrative; cannot estimate how often coexistence is efficient.',connections_nonindependence='Printing cases share scholarship and linked East Asian histories; industrial cases belong to connected trade systems.',omitted_countercases=['Rapid near-complete replacement in a well-defined task','Persistence solely through enforced exclusion'],conclusion_limit='Coexistence does not establish optimality, autonomy or unchanged use intensity.'),
 dict(id='SYN-X03',question='Can uptake or output gains represent all actors’ welfare?',case_ids=['AGR-C03','ANC-C03','MED-C08','MOB-C03'],useful_similarities='Choice, payment, operation and exposure to harm can belong to different actors.',important_differences='Household gender relations, slavery, provider incentives and colonial finance have distinct institutions.',evidence_comparability='Actor decomposition is portable; institutional effects and welfare magnitudes are not pooled.',connections_nonindependence='Some cases lie within imperial/state systems, not isolated independent experiments.',omitted_countercases=['Worker-owned adoption','Voluntary collective provision with measured distribution','Effective veto/compensation by affected users'],conclusion_limit='No general net-benefit ranking or single sign for state/religious/market institutions.'),
 dict(id='SYN-X04',question='Does new work or aggregate recovery compensate displaced individuals?',case_ids=['LBR-C01','LBR-C02','MOB-C06','IND-C04','AGR-C08'],useful_similarities='Technological change reallocates tasks, control and measured work.',important_differences='Linked individuals, occupational-title aggregates, legal bargaining records and household histories have different units.',evidence_comparability='Only some sources directly observe transitions; absence of such evidence is retained.',connections_nonindependence='US studies share census traditions; industrial and household evidence may inherit overlapping scholarship.',omitted_countercases=['Non-US linked workers','Unpaid carers','Transitions with strong worker ownership or no growing substitute sector'],conclusion_limit='Historical tasks are candidate research directions, not forecasts of human comparative advantage or wages.')]
(p/'comparisons.json').write_text(json.dumps(comparisons,indent=2,ensure_ascii=False)+'\n')
print(f'Wrote {len(base)+len(new)} synthesis claims and {len(comparisons)} comparisons')
