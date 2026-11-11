import json,pathlib,hashlib
out=pathlib.Path(__file__).resolve().parent
snap=out.parent/'r1-snapshot'
selected=json.loads((out/'selection.json').read_text())['claims']
contexts={d:json.loads((out/(d+'-selected-context.json')).read_text()) for d in ['MAT','ANC']}
sources={s['id']:s for d in contexts.values() for s in d['sources']}
access={
'MAT-S01':('full-text relevant passages via author-upload OCR','Science pp. 1697–1699; pottery-bearing strata, associated dates, 45 samples/13 resampled, micromorphology; table captions. Numerical calibration and supplement not reanalysed.',None),
'MAT-S06':('preserved full article text, relevant sections inspected','Tables 2–3 and Research Following the Campaign / Lessons Learned / Conclusion, pp. 404–405, 411–415; preserved text lines 432–450 and 735–944. Table 4 numerical rows not independently checked.','contributions/MAT/evidence/meroe_experiment.txt'),
'MAT-S11':('publisher abstract','Abstract: two proposed transmission phases and local reinterpretation. Main text/object catalogue not accessed.',None),
'MAT-S13':('full-text OCR, relevant sections inspected','Sections 4.2–4.3 and conclusion; pp. 103–104 raw-material comparisons and mixed local/imported context.',None),
'MAT-S14':('repository accepted manuscript text','PDF pp. 2–4, Semi-finished glass, Laboratory analysis, Implications; museum provenance and reaction phases.',None),
'ANC-S03':('preserved full original XML, relevant sections inspected','Results: Stable isotope composition and Fig. 4 caption; Discussion, especially market alternatives. Live PMC open returned a browser check, so original preserved XML was used.','contributions/ANC/working/barbegal2018.xml'),
'ANC-S05':('preserved HTML translation','Book II §§116–117; reported ownership, counts, functions, and diversion to private work. Ancient manuscript and Greek/Latin critical apparatus not inspected.','contributions/ANC/working/frontinus.html'),
'ANC-S08':('full chapter OCR, relevant sections inspected','§17.1/Fig.17.1 caption; al-Madam §17.2 and §17.2.2; §17.4.2. Underlying excavation reports and figure images not reanalysed.',None),
'ANC-S09':('preserved HTML translation','Histories X.28.1–7, especially X.28.3–4; no explicit tax exemption in this English text. Greek/critical apparatus not inspected.','contributions/ANC/working/polybius.html')}
ledger=[]
for sid,(mode,loc,local) in access.items():
 row={'source_id':sid,'claimed_access':sources[sid]['access'],'audit_actual_access':mode,'passages_inspected':loc,'url':sources[sid]['url'],'accessed':'2026-11-05','original_lineage_assessment':sources[sid]['evidence_lineage'],'access_discrepancy_found':False}
 if local:
  p=snap/local; row.update({'preserved_file':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
 ledger.append(row)
(out/'source_access.json').write_text(json.dumps(ledger,indent=2,ensure_ascii=False)+'\n')
rows=[]
def add(k,source_ids,finding,disposition,alignment,lineage,support,repair,edges):
 rows.append({'claim_id':k,'selection_reason':selected[k],'sources_passages_inspected_access':[next(s for s in ledger if s['source_id']==sid) for sid in source_ids],'finding':finding,'disposition':disposition,'population_measure_alignment':alignment,'source_lineage_check':lineage,'support_level':support,'repair_or_check':repair,'associated_edge_ids':edges})
add('MAT-K01',['MAT-S01'],
 'The associated-context chronology is accurately reported, with neither an invention date nor a diffusion denominator substituted for it.',
 'upheld',
 'One cave sequence and associated bone/charcoal dates; not direct dates on every vessel or a population adoption rate.',
 'Repeated sampling and multiple dating laboratories belong to one site/context study, as the source ledger states.',
 'Descriptive archaeological support; high confidence is defensible for what Wu et al. dated, conditional on their contextual association.',
 'No mandatory repair. A chronology replication would require the supplement, calibration and stratigraphic samples; that is outside this entailment audit.',[])
add('MAT-K12',['MAT-S06'],
 'The trials support workable combinations after operational changes. Neither individual input effects nor the ancient recipe is identified; the existing claim limits and test acknowledge both.',
 'upheld',
 'Modern replica smelts based on later/post-Meroitic workshops, not ancient output or livelihoods.',
 'One experimental programme; later poorly quantified runs do not become independent controlled replications.',
 'Mechanism-supported feasibility and operational learning, not causal identification of each parameter.',
 'Retain the explicit anecdotal-data and simultaneous-change limits when summarising high confidence. No mandatory claim repair.', ['MAT-E06','MAT-E07'])
add('MAT-K19',['MAT-S11'],
 'The abstract entails that Hosler proposed selective transmission and transformation. It cannot verify the route or catalogue. MAT-C06.outcome nevertheless says local transformation of transmitted techniques without a hypothesis qualifier.',
 'claim upheld; associated case wording repair (R1-MAT-01, low severity)',
 'Researcher-proposed regional sequence; adopters and object frequencies were not independently inspected.',
 'Hosler 1988 and 1995 are the same research programme, not independent witnesses; the existing ledger correctly records this.',
 'Attribution to scholarship is supported; historical transmission remains a hypothesis.',
 'Change MAT-C06.outcome[1] to proposed local transformation of transmitted techniques (or equivalent). Check exported case cards preserve the qualifier. Full-text inspection is needed only before strengthening the substantive transmission claim.',[])
add('MAT-K22',['MAT-S14','MAT-S13'],
 'Residual mineral phases and heterogeneous partly molten batch directly support primary glassmaking. The qualification separating manufacture from independent invention is warranted.',
 'upheld',
 'Three museum-store fragments with site attribution; the 52-bead study concerns another selected assemblage. Neither gives exact invention timing or annual output.',
 'Different specimens strengthen the inference but share site attribution and investigators. The ledger does not miscount them as independent traditions.',
 'Descriptive archaeological identification of a production process; no identified adoption mechanism.',
 'No mandatory repair. Keep museum provenance attached to the primary-production inference and keep exact quarry and intellectual origins unresolved.', ['MAT-E18'])
add('ANC-K05',['ANC-S03'],
 'The isotope/truncation evidence supports recurrent pauses; timing and harbour proximity do not identify purchasers. The claim and edge properly retain the biscuit market as unconfirmed.',
 'upheld; consequential rival checked',
 'Selected carbonate fragments record sampled machinery/years, not a census of all wheels or all operating years.',
 '2018/2024 papers share the carbonate archive and investigators. New rival source Leveau 1996 uses earlier excavation/context evidence but shares an author with 2018; neither is independent purchaser evidence.',
 'Descriptive operating proxy plus underdetermined market mechanism.',
 'Optional evidence strengthening: add Leveau 1996 p.149 as the explicit urban-market rival. Do not turn seasonal pauses into an exclusive customer identification.', ['ANC-E05'])
add('ANC-K08',['ANC-S05'],
 'The translation explicitly reports state/imperial enslaved gangs, about 240 and 460, and specialised functions. Reporting these as Frontinus’s account is accurate.',
 'upheld',
 'Reported staffing near 100 CE; not verified worker-days, compliance, a trend, or Barbegal workforce status.',
 'A single transmitted administrative account. Functional detail and counts are not separate corroborating witnesses.',
 'Descriptive historical-primary testimony, high for what the text reports.',
 'No mandatory repair. Preserve the author-attribution and separate the 537 episode.', ['ANC-E06'])
add('ANC-K14',['ANC-S09','ANC-S08'],
 'Paton’s translation gives five generations of cultivation rights. The claim correctly refuses an explicit tax-exemption reading and avoids assigning the channels a deep-aquifer source.',
 'upheld',
 'Local testimony reported by Polybius about earlier rulers, not a surviving grant, universal policy, or observed effect on investment.',
 'Boucharlat reinterprets the same Polybius passage; two citations are not two witnesses.',
 'Descriptive testimony; the incentive edge remains a hypothesis.',
 'No mandatory repair. A stronger fiscal claim would need a translation/Greek-text comparison; enforcement or incentive effects require different evidence.', ['ANC-E15'])
add('ANC-K15',['ANC-S08'],
 'The source distinguishes collecting from conveying galleries and documents altered depths. The physical claim holds for the explicitly groundwater-intercepting, passive configuration.',
 'upheld',
 'Condition on a type of hydraulic system, not proof that every early gallery had the same source, yield, or sustainability.',
 'Synthesis of excavation reports; al-Tikriti’s contrary aquifer classification is reported in the chapter, not independently rechecked here.',
 'First-principles physical necessity consistent with source geometry; not identified historical adoption causation.',
 'No mandatory repair. Keep the configuration restriction visible; require collecting-section and elevation evidence before assigning any disputed installation to the edge.', ['ANC-E13'])
(out/'claim_audit.json').write_text(json.dumps({'date':'2026-11-05','snapshot':str(snap),'audit_unique_claims':8,'eligible_unique_claims':46,'per_dossier':{'MAT':{'audited':4,'eligible':24},'ANC':{'audited':4,'eligible':22}},'ordinary_descriptive_sample':['MAT-K01','ANC-K08','ANC-K14'],'rows':rows},indent=2,ensure_ascii=False)+'\n')
edges=[]
explanations={
'MAT-E06':'Bounded necessity for new iron from ore reduction; alternative ore remains possible and purchased metal changes the task. No specific deposit necessity asserted.',
'MAT-E07':'Complement relationship stays within the modern replica scope. It must not be read as isolating bellows effects or proving the unique ancient arrangement.',
'MAT-E18':'Raw-batch contribution is supported by the reaction residues and compatible composition; quarry and exact calcium source remain unresolved.',
'ANC-E05':'Hypothesis basis, low confidence, and explicit market alternative prevent an inferred schedule from becoming a demonstrated purchaser link.',
'ANC-E06':'Text explicitly assigns specialists to service functions. The contribution is reported, not an independently measured performance effect.',
'ANC-E13':'Dependency is physically valid for a groundwater-intercepting gravity gallery; groundwater availability and compatible gradient are necessary, not sufficient.',
'ANC-E15':'Cultivation grant is reported; causal investment effect is only a hypothesis. No claim of necessary governance or tax exemption.'}
for d in contexts.values():
 for e in d['edges']:
  edges.append({'edge_id':e['id'],'claim_ids':e['claim_ids'],'disposition':'upheld within stated scope','assessment':explanations[e['id']],'repair_or_check':'No mandatory repair; preserve basis, scope and qualification in any rendering.'})
(out/'edge_audit.json').write_text(json.dumps({'audited_unique_edges':len(edges),'eligible_unique_edges':40,'edge_ids':[e['edge_id'] for e in edges],'rows':edges},indent=2,ensure_ascii=False)+'\n')
new={'source_id':'R1-MAT-SX01','title':'The Barbegal water mill in its environment: archaeology and the economic and social history of antiquity','authors':['Philippe Leveau'],'year':1996,'doi':'10.1017/S1047759400016536','publisher_metadata_url':'https://www.cambridge.org/core/journals/journal-of-roman-archaeology/article/abs/barbegal-water-mill-in-its-environment-archaeology-and-the-economic-and-social-history-of-antiquity/2178B7D2CEEF8E527F86660CB1EA5D11','inspected_url':'https://www.academia.edu/8397838/The_Barbegal_water_mill_in_its_environment_archaeology_and_the_economie_and_social_history_of_antiquity','actual_access':'full article OCR; relevant passages pp.142 and 149–152 inspected','relevance':'p.149 explicitly argues for an Arles-only flour market from revised chronology; the 2018 study instead proposes harbour provisions from seasonal deposits. Earlier context-based inference is a credible rival, not a refutation of subsequently measured pauses.','lineage':'Excavation/environment study by a later coauthor of ANC-S03. Shared site and researcher; different evidential subset. Sellin and Benoit arguments mentioned inside it were not separately read.','audit_disposition':'Supports keeping ANC-K05 underdetermined, as already recorded.','downloaded_file':None}
(out/'counterevidence.json').write_text(json.dumps({'sources':[new],'search_scope':'Targeted English/French searches for Barbegal hardtack/seasonality criticism and original urban-market scholarship. Also sought Ile-Ife autonomous-origin commentary; no separate contrary original was fully inspected there.','access_failures_or_limits':['PMC live article returned browser check; preserved original XML inspected instead.','Cambridge Leveau page initially exposed metadata only; article OCR subsequently inspected at Academia.','Comet 1999 Persée page exposed introductory text/metadata, not the full argument; not used as substantive evidence.','Sellin 1983 original not obtained; bibliographic lead and Leveau discussion not treated as independently inspected Sellin evidence.'],'no_new_source_downloads':True},indent=2,ensure_ascii=False)+'\n')
findings=[{'id':'R1-MAT-01','severity':'low','affected_claim_ids':['MAT-K19'],'affected_case_ids':['MAT-C06'],'affected_edge_ids':[],'locator':'contributions/MAT/cases.json: MAT-C06.outcome[1]','problem':'Outcome wording drops the transmission-hypothesis qualifier present in claim, report and source-access record.','evidence':'Hosler abstract proposes transmission and transformation; audit did not inspect its supporting catalogue. The research claim is expressly hypothesis/underdetermined.','repair':'Qualify the outcome itself as proposed and preserve that qualifier in rendered summaries.','closure_test':'Inspect revised outcome and any generated card/table; no unqualified assertion of proven transmission.','status':'open; reviewer did not edit snapshot'}]
(out/'findings.json').write_text(json.dumps(findings,indent=2,ensure_ascii=False)+'\n')
print(json.dumps({'claim_rows':len(rows),'edge_rows':len(edges),'source_rows':len(ledger),'findings':len(findings),'output':str(out)}))
