"""Materialize the bounded ENE research ledgers; no external writes."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parent
ACCESSED = '2026-11-05'
def write(name, obj):
    (ROOT/name).write_text(json.dumps(obj, ensure_ascii=False, indent=2)+'\n')
def ids(prefix, *nums): return [f'ENE-{prefix}{n:02d}' for n in nums]

sources=[]
def source(n,title,authors,year,url,kind,access,locator,limit,lineage):
    sources.append(dict(id=f'ENE-S{n:02d}',title=title,authors=authors,year=year,url=url,
      source_type=kind,access=access,locator=locator,scope_limit=limit,accessed=ACCESSED,
      evidence_lineage=lineage))

source(1,'Beyond the learning curve: factors influencing cost reductions in photovoltaics',
 ['Gregory F. Nemet'],2006,
 'https://wikis.mit.edu/confluence/download/attachments/21139745/Nemet_BeyondtheLearningCurve_EP_06.pdf?api=v2',
 'scholarly-analysis','full-text',
 'Energy Policy 34, 3218–3232; inspected pp. 3221, 3224–3228, especially Tables 2–3 and §§3.1–4.4; cached PDF pages 4, 7–11.',
 'Engineering decomposition of crystalline-silicon module costs/prices, 1975–2001, not system electricity costs or identified policy effects; early market-quality changes leave a large residual.',
 'Author reconstructs technical/cost inputs from Maycock industry series, laboratory efficiency histories, company and institutional reports. Kavlak et al. subsequently reuse some of this evidence and revise the decomposition; they are not wholly independent corroboration.')
source(2,'Evaluating the causes of cost reduction in photovoltaic modules',
 ['Goksin Kavlak','James McNerney','Jessika E. Trancik'],2018,
 'https://static1.squarespace.com/static/56afb881e321406be6160228/t/5bff10822b6a2884d7267f17/1543442566890/Evaluating%2Bthe%2Bcauses%2Bof%2Bcost%2Breduction%2Bin%2Bphotovoltaic%2Bmodules.pdf',
 'scholarly-analysis','full-text',
 'Energy Policy 123, 700–710; inspected §§2–4.2, pp. 701–707, Table 3, Figures 3–5 and conclusion; local PDF.',
 'Cost-equation decomposition and judgment-based allocation to R&D, learning and scale; the 60% market-policy attribution additionally assumes a public/private R&D split and equal effectiveness. Supplemental data were not independently re-estimated.',
 'Reconstructed industry technical/cost observations, including Nemet (2006), NREL efficiency records and materials/industry studies. Same research group and conceptual method as ENE-S11; recurrence across those models is not independent causal identification.')
source(3,'Innovation and international technology transfer: The case of the Chinese photovoltaic industry (CERNA Working Paper 2010-12; HAL version 1)',
 ['Arnaud de la Tour','Matthieu Glachant','Yann Ménière'],2010,
 'https://minesparis-psl.hal.science/hal-00498578v1/document',
 'scholarly-analysis','full-text',
 'Inspected working-paper pp. 1–11, 17–18 and Appendices 1–2; PDF pp. 3–13, 19–20, 24–28. Published version appeared in Energy Policy 39 (2011), 761–770; that version was not silently substituted.',
 'Interviews and patent/equipment proxies cover early Chinese PV entry, principally 2003–2009; patent counts miss tacit and secret process innovation. Small, producer-centered interview sample cannot represent workers or all firms.',
 'Authors combine 79,642 patent records, equipment-provider listings, ten interviews including a university institute (Appendix 1 lists nine companies), company biographies and inherited EPIA/REDP/industry output statistics. Abstract calls these ten companies; this discrepancy is retained rather than harmonized.')
source(4,'Historical construction costs of global nuclear power reactors',
 ['Jessica R. Lovering','Arthur Yip','Ted Nordhaus'],2016,
 'https://core.ac.uk/download/pdf/82188133.pdf',
 'scholarly-analysis','partial-text',
 'Web-parsed full article available; inspected §§2–4.4, §5, Table 1, especially pp. 373–375, 378–381. Local direct PDF request returned 403; inspected extracts retained in cache/web-inspections.json.',
 '349-reactor, seven-country overnight-cost compilation centered on completed reactors as of 2015; missing major countries, cancelled projects and some experimental routes. Interest during construction excluded. Source text says 26 Korean reactor records while Table 1 cohort counts imply a different total; no subgroup count is reproduced here.',
 'Reuses US Koomey–Hultman/EIA/early AEC evidence; French Cour des Comptes 2012 data; Korean utility inquiry with KHNP/NABO/KPX checks; other national compilations. Not independent of the earlier nuclear cost literature for reused reactors. Underlying reactor files were not re-audited here.')
source(5,'The French Pressurized Water Reactor Program',
 ['Arnulf Grubler'],2012,
 'https://pure.iiasa.ac.at/id/eprint/11077/1/The%20French%20Pressurised%20Water%20Reactor%20Programme.pdf',
 'scholarly-analysis','full-text',
 'Historical case study for Global Energy Assessment Chapter 24; inspected pp. 2–3, 5–10, Table 1 and §§2–4.',
 'Author synthesis of his 2009/2010 reconstruction, not a second independent French dataset. Its broad assertion of universal negative learning is not adopted; later national comparisons contest it.',
 'Uses Grubler 2009/2010 reconstructions from French public/parliamentary accounts, IAEA dates and institutional histories including Jasper and Finon–Staropoli. French cost data precede the reactor-level Cour des Comptes series used by ENE-S04.')
source(6,'Sources of Cost Overrun in Nuclear Power Plant Construction Call for a New Approach to Engineering Design',
 ['Philip Eash-Gates','Magdalena M. Klemun','Goksin Kavlak','James McNerney','Jacopo Buongiorno','Jessika E. Trancik'],2020,
 'https://dspace.mit.edu/bitstream/handle/1721.1/133049/Jacopo%27s%20and%20Jessika%27s%20paper%20on%20nuclear%20cost%20Sep%202020.pdf',
 'scholarly-analysis','partial-text',
 'Author manuscript web text; inspected abstract, §§2.1–2.2 and §4.4, manuscript pp. 1–5, 10–11; publication Joule 4, 2348–2373. Direct download returned 429; extracts cached.',
 'Detailed 1976–1987 cost-account model concerns a Westinghouse four-loop plant; 2017 containment data concern a narrow recent US project context. Indirect-cost reallocations and counterfactual component costs require assumptions; no labour-income panel.',
 'Combines IAEA, EIA and published reactor histories with Department of Energy EEDB accounts and construction/engineering reports. Some underlying US reactor history overlaps ENE-S04; the component-account decomposition contributes additional evidence, not a wholly independent national history.')
source(7,'US3025589A: Method of manufacturing semiconductor devices',
 ['Jean A. Hoerni'],1962,
 'https://patents.google.com/patent/US3025589A/en',
 'historical-primary','full-text',
 'Filed 1 May 1959; issued 20 March 1962. Inspected specification opening and claim 1 in hosted patent transcription; local HTML/text retained.',
 'A patent discloses and claims a technical process; it does not demonstrate factory yields, licensing uptake, commercial success or a unique first inventor. Host metadata priority chains are not used to date the planar demonstration.',
 'US patent record as transcribed by Google Patents, assigned to Fairchild. Patent also cited by ENE-S14, so the latter is not independent corroboration of the same disclosed process.')
source(8,'Computers in Spaceflight: The NASA Experience — Chapter 2, Evolution of the hardware',
 ['James E. Tomayko'],1988,
 'https://www.nasa.gov/wp-content/uploads/static/history/computers/Ch2-4.html',
 'institutional-synthesis','full-text',
 'NASA history, printed pp. 31–34; inspected entire supplied subsection, especially NOR-gate standardization, procurement and note references 30–35.',
 'Retrospective official history with participant disagreement. Its estimate that Apollo used 60% of US microcircuit output in summer 1963 is a narrow-period claim, not the whole decade or all semiconductor output. Underlying note 34 was not separately retrieved.',
 'NASA-commissioned historical reconstruction using program documents and interviews identified in endnotes. We inspected the historical account, not the original procurement invoices. No reliance on its possibly ambiguous Block I/Block II labeling or cycle-time units.')
source(9,'Learning-by-Doing Spillovers in the Semiconductor Industry',
 ['Douglas A. Irwin','Peter J. Klenow'],1994,
 'https://gwern.net/doc/economics/experience-curve/1994-irwin.pdf',
 'scholarly-analysis','full-text',
 'Journal of Political Economy 102(6), 1200–1227; inspected pp. 1200–1203, 1210–1215, 1219–1224, Tables 1, 4–7; local PDF.',
 'Quarterly Dataquest merchant DRAM shipments/prices, 1974Q1–1992Q4, 32 firms; firm costs and plant yields not directly observed. Cournot behavior, demand elasticity and instruments matter; vertically integrated internal producers excluded.',
 'Original econometric analysis of proprietary Dataquest prices and firm shipments; earlier qualitative yield examples are inherited OECD/industry evidence. Seven DRAM generations plus a distinct 16K voltage variant; not eight independent technology histories.')
source(10,'Brief History and Future of the Lithium-Ion Battery — Nobel Lecture',
 ['Akira Yoshino'],2019,
 'https://www.nobelprize.org/uploads/2019/10/yoshino-lecture.pdf',
 'historical-primary','partial-text',
 'Inspected historical §§1.1–1.5 and opening of §2, printed pp. 207–217, via web text. Direct PDF returned 403. Forecast passages excluded from this contribution.',
 'Inventor retrospective emphasizing his team; patent chronology and qualitative impact-test account are not an independently audited safety dataset or complete commercialization history. No claim that lithium-ion cells are hazard-free.',
 'First-person account referring to Whittingham 1976, Mizushima/Goodenough 1980, Yoshino patents and 2012 retrospective. Original laboratory notebooks and full commercial qualification records not inspected.')
source(11,'Determinants of lithium-ion battery technology cost decline',
 ['Micah S. Ziegler','Juhyun Song','Jessika E. Trancik'],2021,
 'https://pubs.rsc.org/en/content/articlepdf/2021/ee/d1ee01313k',
 'scholarly-analysis','partial-text',
 'Energy & Environmental Science 14, 6074–6098; inspected data/method sections pp. 6076–6078 and results pp. 6085–6091, Figures 5–9, Table 4, via web text. Direct download returned 403; extracts retained.',
 'Representative high-energy-density cylindrical 18650 cell configurations for 1995–2000 and 2010–2015, not all battery chemistries or EV packs. Sparse historical inputs, estimated manufacturing parameters and assumed allocations limit causal attribution.',
 'Authors assemble literature measurements, technical reports, materials prices and production estimates into a new cell-cost model. Shares conceptual method and some authors with ENE-S02; price validation draws on their separate compiled price series, not independent factory accounts.')
source(12,'The future of electric two-wheelers and electric vehicles in China',
 ['Jonathan Weinert','Joan Ogden','Dan Sperling','Andrew Burke'],2008,
 'https://escholarship.org/content/qt0d05f8v9/qt0d05f8v9.pdf',
 'scholarly-analysis','partial-text',
 'Energy Policy 36, 2544–2555; inspected §§1.2–2.4, §3 and historical parts of §6, particularly pp. 2545–2550 and 2553. Web-parsed text retained; direct request returned empty 202.',
 'Mixed industry estimates, observations in ten cities, manufacturer/user interviews and six assembly-plant visits; descriptive force-field rankings are subjective. Forecasts excluded; samples not nationally representative.',
 'Builds on authors’ 2007 studies and 2006–2007 fieldwork plus CMIC/CNBS/Jamerson industry series. Shares authors, survey evidence and underlying transport/lead research with ENE-S13; not independent replication.')
source(13,'Comparative environmental impacts of electric bikes in China',
 ['Christopher R. Cherry','Jonathan X. Weinert','Yang Xinmiao'],2009,
 'https://itspubs.ucdavis.edu/download_pdf.php?id=1289',
 'scholarly-analysis','full-text',
 'Transportation Research Part D 14, 281–290; inspected §§2–4, Tables 2 and 6, especially pp. 283–284 and 287–289; local PDF.',
 'Partial life-cycle inventory, regional grid assumptions and passenger-load/lifespan scenarios; not measured health damages or a full lifecycle account. Several bus/car factors borrowed from non-Chinese or earlier studies. Battery-price comparison approximate.',
 'Combines authors’ field/transport work, industrial statistical intensities, regional grid factors and Mao et al. 2006 lead-flow estimates based on 1999 data. Shares earlier user evidence with ENE-S12. No independent blood-lead cohort is established by this analysis.')
source(14,'1959: Invention of the “Planar” Manufacturing Process',
 ['Computer History Museum'],None,
 'https://www.computerhistory.org/siliconengine/invention-of-the-planar-manufacturing-process/',
 'institutional-synthesis','full-text',
 'The Silicon Engine timeline entry; inspected main account and references; downloaded HTML/text.',
 'Museum synthesis provides commercial chronology and failure-mode context, not a production-yield series. Its expansive significance claims are not repeated.',
 'Explicitly draws on Hoerni patent/1960 paper, Lécuyer 2006, Moore 1998, Riordan 2007 and oral history; same patent as ENE-S07. Those underlying works, apart from the patent, were not independently read here.')

claims=[]
def ref(n,loc,support): return dict(source_id=f'ENE-S{n:02d}',locator=loc,supports=support)
def descriptive(reason): return dict(status='descriptive-only',reason=reason)
def test(chain,rival,obs,found,ambiguity,timing='pre-search candidate',status='underdetermined'):
    return dict(status=status,mechanism_chain=chain,strongest_rival=rival,
      discriminating_observation=obs,evidence_sought_found=found,
      remaining_ambiguity=ambiguity,hypothesis_timing=timing)
def claim(n,cs,statement,etype,conf,status,refs,counter,limits,tst):
    claims.append(dict(id=f'ENE-K{n:02d}',case_ids=ids('C',*cs),statement=statement,
      evidence_type=etype,confidence=conf,causal_status=status,sources=refs,
      counterevidence=counter,inference_limits=limits,test=tst))

claim(1,[1],'For US PV in the 1970s, the shift from a space-program buyer toward terrestrial users changed product requirements, standardization and market structure; the early fall in module prices cannot be read wholly as factory learning.',
 'scholarly-analysis','medium','mechanism-supported',
 [ref(1,'§§3.1.1–3.1.4, pp. 3224–3225','Large unexplained early cost/price residual; differing quality and willingness to pay; move from custom space panels to standard terrestrial products.')],
 'Manufacturing improvements also occurred; terrestrial government purchases remained substantial.',
 'No causal allocation of the 1975–1979 residual to quality, markups or standardization; niche procurement is not evidence of grid competitiveness.',
 test('New terrestrial tasks and customers -> less customized products and altered markups -> observed prices change with production practice.','Repeated output alone lowers an unchanged product’s factory cost.','Do prices fall faster than the engineering model explains while customers/product requirements change?','ENE-S01 §§3.1–3.2: early residual and market changes found; later period better explained.','Quality, competition and manufacturing changed together; no matched unchanged-product counterfactual.'))
claim(2,[1],'PV cost decomposition is model-sensitive: for 1980–2001 Nemet assigns 43% of decline to plant size, whereas Kavlak et al. assign 8%; the latter assigns 36% for 2001–2012 and separates efficiency, material use, prices and yield. Their reconstructions also identify early silicon supply/process benefits inherited from the semiconductor industry rather than generated entirely by PV output.',
 'scholarly-analysis','high','descriptive',
 [ref(1,'Table 3 and §4.3, p. 3227','43% plant-size allocation and semiconductor silicon-supply spillover.'),ref(2,'§§4.1–4.2, Table 3, pp. 705–707','8% and 36% plant-size allocations; revised cost equation; semiconductor supply/know-how before the mid-2000s transition.')],
 'Both studies support several improvement channels, but their shared historical evidence is not two independent estimates of the same causal policy effect.',
 'These are allocated contributions under engineering models; neither percentage is a universal learning coefficient, electricity-price effect or welfare estimate.',
 descriptive('Reports and compares published model allocations, without treating them as identified causal effects.'))
claim(3,[1],'China’s emergence as a PV producer in the late 2000s did not imply similarly large domestic deployment: the inspected 2010 study reports over one-third of world production in 2008 with over 95% exported, and about 2.2% of global demand in 2009.',
 'scholarly-analysis','medium','descriptive',
 [ref(3,'Abstract and §1.1, working-paper pp. 1, 4–5','Production/export estimates and separate 2009 domestic-demand share.')],
 'The production and demand numbers concern different years and inherited industry estimates; domestic installations were not zero.',
 'No current market claim and no subtraction of nonmatching denominators; production capacity, annual output and deployment must remain distinct.',
 descriptive('Dated production/export and demand observations establish a stage/geographic mismatch, not its causal magnitude.'))
claim(4,[1],'Interviews and supply-chain evidence from early Chinese PV entry support imported production equipment plus skilled personnel as important channels; upstream process secrecy and sparse equipment markets constrained entry despite downstream success.',
 'scholarly-analysis','medium','mechanism-supported',
 [ref(3,'§§1.2, 2.1–2.3, working-paper pp. 7–11; conclusion pp. 17–18','Turnkey lines, vendor training, diaspora recruitment and segment-specific entry barriers.')],
 'Low wages, energy prices, finance and foreign deployment incentives also mattered; firms’ retrospective accounts may exaggerate chosen channels.',
 'Small producer-centered sample, rough equipment competition measure and imperfect patent proxies; no estimate of independent policy or labour contribution.',
 test('Equipment purchases plus recruited expertise -> process operation/adaptation -> cell/module entry; upstream tacit processes remain harder to acquire.','Cheap factors alone explain entry uniformly across supply-chain stages.','Downstream/upstream entry should differ with accessible equipment and tacit knowledge even within the same country.','ENE-S03 contrasts stages, documents vendor training and returning executives, and reports later FDI following pioneer firms.','Stages also differ in capital intensity, energy use and market concentration; no controlled isolation.'))
claim(5,[2],'The 2016 seven-country reactor-cost compilation records differing within-country overnight-cost trajectories, including declines across Korean construction cohorts and escalation in later US/French cohorts; it does not identify a universal sign of nuclear learning.',
 'scholarly-analysis','medium','descriptive',
 [ref(4,'§§3.1–3.2, §4.3, Table 1, pp. 373–379','Country/cohort construction-start comparisons and local-currency cost normalization.')],
 'Countries adopted different designs in different eras; data quality and coverage vary, and some prototype routes are excluded.',
 'The 349-reactor sample is not all proposed projects. Korean cohort-count inconsistency is not resolved here; no precise Korean cohort total is asserted. No international cost ranking is inferred.',
 descriptive('Describes variation in the published construction-cost sample, without attributing it solely to standardization or state structure.'))
claim(6,[2],'France’s coordinated PWR programme combined bulk ordering, licensed designs, regulatory continuity and EDF engineering capacity with rapid deployment, yet its later construction cohorts still experienced real cost escalation.',
 'scholarly-analysis','medium','mechanism-supported',
 [ref(5,'§2, Table 1 and §§3–4, pp. 2–8','Institutional organization, deployment timing, design changes and estimated escalation.'),ref(4,'§3.1 and French results, pp. 374–376','Later reactor-level series also shows escalation, with different magnitudes/coverage.')],
 'French cost magnitudes differ by reconstruction and cohort; national coordination did not mean unchanged designs or citizen consent.',
 'The coordinated setting supports an enabling account, not proof of necessity or sufficiency. Grubler’s universal negative-learning generalization is rejected here.',
 test('Concentrated ordering and engineering authority -> repeatable build programme -> rapid capacity deployment.','Falling unit costs are the necessary cause of rapid deployment.','Can deployment expand under coordinated procurement while real construction costs rise?','ENE-S05 documents both rapid programme expansion and escalation; ENE-S04 supplies later, differently constructed French cost series.','Oil security, political priorities, financing and grid demand coincide; comparison does not identify each institutional contribution.'))
claim(7,[2],'In Eash-Gates et al.’s US four-loop-plant reconstruction for 1976–1987, indirect accounts contribute 72% of the modeled cost increase, placing engineering, supervision and construction organization alongside hardware and regulatory requirements.',
 'scholarly-analysis','medium','mechanism-supported',
 [ref(6,'§2.2, manuscript pp. 3–5; §4.4, pp. 10–11','61 EEDB accounts; 72% indirect contribution; model/data limits.')],
 'Indirect accounts can themselves include responses to regulation, changed scope or schedules; the allocation does not establish a separate regulation-free cause.',
 'Account attribution is not a causal estimate that management alone explains 72%; it covers one modeled configuration and interval, not every reactor or worker productivity level.',
 test('Complex site activities and changing execution conditions -> more engineering/support and installation burden -> higher constructed cost.','Cost escalation is entirely additional reactor hardware demanded by safety rules.','Do indirect service accounts account for large changes beyond direct hardware expenditure?','ENE-S06 EEDB decomposition found the majority in indirect accounts and acknowledges proportional-allocation assumptions.','Regulation, redesign and site interference can generate indirect costs jointly; ultimate causal shares remain underdetermined.'))
claim(8,[2],'Overnight reactor construction cost excludes interest during construction, and completed-project cost trajectories omit the outcome of cancellation; they cannot by themselves establish investor affordability or system welfare.',
 'synthesis-inference','high','descriptive',
 [ref(4,'§3.2, pp. 374–375 and §5.2, p. 381','Explicit exclusion of IDC; distinction from electricity cost and coverage frame.'),ref(6,'Introduction, manuscript p. 1','Reports 2017 abandonment of VC Summer as a separate project outcome.')],
 'Overnight costs remain useful for an explicitly restricted question about construction resource cost.',
 'No claim that every omitted cost reverses any national ranking; social damages and avoided pollution are not estimated.',
 descriptive('States accounting and sampling boundaries, including an observed cancellation, without estimating their aggregate causal effect.'))
claim(9,[3],'Hoerni’s 1959 patent application specifies retaining a nonconducting surface coating over exposed junction edges; the museum history dates a working planar transistor to March 1959 and commercial introduction to April 1960.',
 'historical-primary','high','mechanism-supported',
 [ref(7,'Specification and claim 1','Protected-junction process architecture.'),ref(14,'Main account, paragraphs 1–4','Demonstration and commercialization chronology; subsequent reliability problems.')],
 'The process still needed complementary masking, diffusion, contacts and packaging; later bonding/interconnect failures continued.',
 'Patent and retrospective chronology do not measure yield or prove that planar technology alone caused the semiconductor industry’s expansion.',
 test('Surface coating retained during fabrication -> junction protection -> reproducible planar-device architecture.','A patent idea alone demonstrates commercially satisfactory production.','Is there separate evidence of functioning hardware and a later marketed device, as well as unresolved failure modes?','ENE-S07 describes process; ENE-S14 records demonstration, commercial device and subsequent reliability issues.','Factory qualification and independent yield series were not inspected; museum history inherits the patent record.','pre-search candidate','evaluated'))
claim(10,[3],'The Apollo computer programme supported an early IC production niche through a large, standardized NOR-gate purchase, while its engineers valued size, power, timing and reliability rather than the lowest initial component price.',
 'institutional-synthesis','medium','mechanism-supported',
 [ref(8,'Printed pp. 33–34; notes 30–35','Single-gate choice, initially higher cost, large 1963 production share and participant disagreement over perceived risk.')],
 'Other military and commercial customers existed; NASA history alone cannot establish its share of total industry cost decline.',
 'Procurement volume supports demand creation in a specific niche, not a claim that NASA invented ICs or alone financed semiconductor diffusion; historical 60% estimate is not extrapolated.',
 test('Mission constraints plus financed programme -> standardized purchase and qualification effort -> early IC production at volume.','Unsubsidized component cheapness already made the choice automatic.','Did designers choose higher-priced components for nonprice capabilities and create a large early order?','ENE-S08 records higher initial IC cost, single NOR type and intensive 1963 purchasing.','Reliability choices and procurement size are jointly determined; no no-Apollo industry counterfactual.'))
claim(11,[3],'Irwin and Klenow’s 1974–1992 merchant-DRAM model estimates stronger own-firm than external learning contributions and finds no systematic faster learning rate for Japanese firms; it does not support a simple national-learning-superiority explanation.',
 'scholarly-analysis','medium','mechanism-supported',
 [ref(9,'§IV, pp. 1210–1221, Tables 2–6','32-firm shipment/price dataset; own/external and Japanese-rate tests; ambiguous Japanese within-country spillover difference.')],
 'Tests of stronger within-Japan spillovers are inconclusive; international cooperation, investment and equipment differences may matter through other channels.',
 'Costs and yields are not observed directly; structural competition assumptions and sample selection qualify the interpretation. Results concern merchant DRAM, not all chips or all eras.',
 test('Repeated firm production and some external knowledge -> lower inferred marginal cost -> product-generation price/output patterns.','Japanese firms inherently learn faster, or domestic-only spillovers dominate.','Allow country-specific learning slopes and separate same-country from cross-country cumulative production.','ENE-S09 estimates these alternatives, reporting similar country slopes and own-firm contribution about three times external contribution in baseline.','Unobserved investment, R&D and selection can covary with shipments; some spillover parameters are imprecise.'))
claim(12,[3],'The same DRAM study finds economically important spillovers between adjacent product generations in only two of seven tested transitions, so experience in one generation cannot be treated as a guaranteed permanent entry barrier.',
 'scholarly-analysis','medium','mechanism-supported',
 [ref(9,'§IV.D and conclusion, pp. 1223–1224, Table 7','Weak cross-generation effects and entry/exit examples.')],
 'Some spillovers are statistically detectable but economically tiny; capital, design skills, equipment and customer relationships can still deter entry.',
 'Weak estimated spillovers are not evidence that experience or incumbency has no value; the underlying proprietary data were not re-estimated.',
 test('Design-generation change -> partial obsolescence of specific production knowledge -> limited transferable learning advantage.','An early lead guarantees cumulatively increasing advantage across every generation.','Does previous-generation production strongly predict subsequent-generation cost, and do entrants appear despite little prior production?','ENE-S09 Table 7 identifies only two economically meaningful transitions and discusses contemporaneous entry.','Model imposes a particular knowledge-depreciation structure; entry is selected and requires other assets.'))
claim(13,[4],'Yoshino’s account separates a rechargeable laboratory configuration from saleable batteries: polyacetylene’s heat/volume limitations motivated a carbon anode, and comparative impact testing supported continued development before Japanese commercialization in 1991.',
 'historical-primary','medium','mechanism-supported',
 [ref(10,'§§1.1, 1.4–1.5, pp. 207–217','PA limitations, carbon/lithiated-cathode combination, 1985 patent, impact comparison and 1991 commercialization.')],
 'This is a retrospective inventor narrative, not the whole industry’s development record or statistical safety certification.',
 'A passed impact test does not establish general safety; commercial process yields, warranties, financing terms and all intervening qualification work remain unknown.',
 test('Portable-device demand and metallic-lithium/PA limitations -> paired material changes and safety tests -> candidate suitable for commercialization.','Electrochemical charge/discharge demonstration alone suffices for market entry.','Are working configurations rejected on heat, size or abuse performance, followed by separate commercialization steps?','ENE-S10 gives those rejected configurations and contrast tests, followed by commercialization date.','Narrative selection and retrospective credit cannot establish independent necessity of every contribution.','emerged during research'))
claim(14,[4],'For representative high-energy-density 18650 cells, Ziegler et al. compare 1995–2000 with 2010–2015 and allocate 38% of modeled cost decline to charge-density improvements; reduced material prices and nonmaterial costs also contribute.',
 'scholarly-analysis','medium','mechanism-supported',
 [ref(11,'pp. 6076–6078, 6085–6087; Figures 5–6 and Table 4','Fixed-size cell definition, reconstructed costs and density/material decomposition.')],
 'Historical data are sparse and unequal across variables; some parameter values represent selected high-energy cells or prototypes, not a census.',
 'USD per energy capacity differs from price per cell, pack cost, cycle life and power capability. The result does not cover LFP vehicle packs or all battery uses.',
 test('More active capacity in a fixed cell volume plus lower input cost -> overhead and components spread over more stored energy -> lower modeled USD/Wh.','Raw-material cheapness or factory replication alone explains the decline.','Does a fixed-configuration component model require large energy-density changes as well as input-price changes?','ENE-S11 separates those variables and finds a substantial charge-density contribution.','Component interactions and representative-cell selection mean decomposition is not intervention identification.'))
claim(15,[4],'The battery model’s baseline assigns about 54% of cost decline to broadly defined R&D, 30% to scale and 2% to learning-by-doing; these shares depend on classifications that include pilot-line and process work within R&D.',
 'scholarly-analysis','medium','contested',
 [ref(11,'pp. 6088–6091, Figures 7–9','Definitions, baseline shares, alternative-assignment sensitivity and proprietary information limits.')],
 'The authors’ alternative assignments retain the broad ranking, but routine and nonroutine improvements can be complementary rather than mutually separable activities.',
 'No inference that factory workers contributed only 2%, or that a public R&D programme caused 54%. Public/private R&D and endogenous demand are not independently identified.',
 test('Recorded component/process changes -> literature-based assignment to research, routine learning or scale -> estimated mechanism shares.','A different classification of intertwined process work changes apparent research versus learning contributions.','Does the ranking survive plausible reassignments, and are records available to separate overlapping activities?','ENE-S11 tests several extreme assignments and reports robust ranking but sparse/proprietary process evidence.','The method cannot identify a counterfactual public/private funding effect or labour’s social contribution.','emerged during research'))
claim(16,[5],'In China’s mid-2000s electric-two-wheeler market, lead-acid remained the dominant battery despite commercially available lithium-ion alternatives; a contemporary comparison estimated roughly fourfold upfront Li-ion battery cost with a longer assumed life.',
 'scholarly-analysis','medium','descriptive',
 [ref(12,'§2.1.1, pp. 2547–2548','VRLA dominance and limited advanced-battery availability; export mix uncertainty.'),ref(13,'Conclusion, p. 289','Approximate power-equivalent fourfold purchase price and two-to-threefold lifespan comparison.')],
 'Advanced-battery sales were increasing; estimated production shares include exports and are not domestic-use shares.',
 'Does not prove low income or credit constraints caused individual choices. Historical price comparison is not a current specification, a universal lifetime ratio or a fully normalized lifecycle estimate.',
 descriptive('Establishes coexistence/continued older practice and reported price trade-off, leaving buyer-level causal attribution open.'))
claim(17,[5],'E-bike adoption in the surveyed Chinese cities combined component-based assembly with a policy-shaped choice set: motorcycle restrictions favored some electric use, while other cities restricted e-bikes; available surveys mainly observed substitution from bicycles and public transport.',
 'scholarly-analysis','medium','mechanism-supported',
 [ref(12,'§1.2, pp. 2545–2546; §§2.1.2–2.4 and §3, pp. 2547–2551','Field methods, standardized components, six factory visits, motorcycle/e-bike bans, previous-mode observations.')],
 'Urban distance, incomes, transit quality and enforcement differed with policy; modular architecture did not eliminate entry/quality barriers.',
 'Ten-city observations and three-city prior-mode surveys are not a national causal estimate. No inference that all Chinese adoption was voluntary or that bans alone explain it.',
 test('Standard components and permissive local classification amid motorcycle constraints -> accessible vehicle supply and usable road space -> adoption by some urban travellers.','Uniform technical superiority or a uniform national mandate explains uptake.','Are rival modes and local restrictions heterogeneous, and are assemblers observed using standardized prefabricated parts?','ENE-S12 documents opposing city rules, survey choice sets and six assembly-plant observations.','Policy adoption is endogenous to congestion and demand; force-field rankings do not identify effects.'))
claim(18,[5],'The 2009 partial lifecycle analysis finds that e-bike comparisons depend on regional electricity and the displaced mode; lead emissions arise upstream in battery production/recycling, so zero tailpipe emissions do not demonstrate zero pollution or a quantified health benefit.',
 'scholarly-analysis','medium','mechanism-supported',
 [ref(13,'§§2.1–2.3, §§3.1–4, Tables 2 and 6, pp. 282–289','Production/grid inventories, lead pathways, excluded lifecycle processes, absence of direct population health measures.')],
 'E-bikes compare favorably with some motorized alternatives on several modeled emissions metrics; emissions relocation can reduce urban exposure while imposing burdens elsewhere.',
 'Mass emissions are not absorbed dose, disease or money damages. Old lead-flow factors, borrowed vehicle factors, load/lifespan assumptions and omitted processes prevent a full welfare estimate.',
 test('Battery manufacture/recycling and electricity use -> geographically redistributed pollution -> different lifecycle comparisons than tailpipe accounting.','A vehicle without exhaust has negligible pollution regardless of energy/material supply chain or displaced travel.','Include lead flows and region-specific electricity; compare bicycle, bus, motorcycle and car rather than one favorable alternative.','ENE-S13 performs a partial inventory and explicitly states missing health and lifecycle evidence.','Magnitude and exposure depend on process controls, region, service life and counterfactual travel; some inputs predate rapid e-bike expansion.'))

cases=[]
def case(n,title,region,period,domain,outcome,summary,stages,mechanisms,counter,ks,ss,episode,actors,labour):
    cases.append(dict(id=f'ENE-C{n:02d}',title=title,region=region,period=period,domain=domain,
      outcome=outcome,summary=summary,stages=stages,mechanisms=mechanisms,
      counterevidence=counter,claim_ids=ids('K',*ks),source_ids=ids('S',*ss),
      episode=episode,actors=actors,labour=labour))

case(1,'Crystalline-silicon PV: changing markets and production capabilities',
 ['United States','Japan','Germany','China','International supply chain'],'1970–2012',
 ['energy','industrial manufacturing'],['niche-to-expanded-production','international-diffusion','cost-decline'],
 'A linked set of episodes distinguishes early terrestrial-market formation, later module process improvements, and Chinese producer entry from domestic deployment. The evidence tests learning-only and cheap-labour-only explanations.',
 {'invention':'Prehistory; no single invention date established here.',
  'feasibility':'Repeatable crystalline-silicon cell/module production existed before the sampled expansion; subsequent yield and material improvements measured in reconstructed models.',
  'deployment':'US space and off-grid terrestrial tasks in the 1970s; later policy-supported grid markets in Japan/Europe.',
  'diffusion':'Dated Chinese production/export shares and qualitative supplier/worker knowledge circulation; no household adopter census.',
  'scaling':'Factory size, efficiency, material use/prices and process yield changed during 1980–2012.',
  'non-adoption/niche':'Early terrestrial niches and very small Chinese domestic-demand share despite major export manufacturing.',
  'displacement/reversal':'No general displacement of fossil generation or quantification of net welfare established.'},
 ['Procurement and demand composition','R&D and process control','Equipment trade plus tacit skill','Investment risk and factory scale','Supply-chain entry barriers'],
 'Decomposition allocations differ strongly by model; low wages, energy cost, finance, foreign incentives and technology transfer covary.',
 [1,2,3,4],[1,2,3],
 dict(technology_configuration='Crystalline-silicon modules; subepisodes: US terrestrial market formation (1970s), worldwide production-cost changes (1980–2012), Chinese downstream entry (2003–2009).',
 task='Provide electrical energy in remote/space tasks and later grid-connected installations; produce saleable modules meeting market quality.',
 population='Module manufacturers/industry averages in cost studies; selected Chinese firms and equipment suppliers in interview/patent study; installations are only indirectly observed.',
 interval='1970–2012, with nonidentical subepisode windows explicitly separated.',
 contemporary_alternatives=['Spacecraft primary batteries for finite missions','Remote diesel or extending electricity connections where feasible','Conventional grid electricity','Other PV chemistries; not cost-equivalent in every sampled period'],
 adoption_measure='Module production/cost series; 2008 Chinese world-production/export shares; separate 2009 global-demand share. No common adopter denominator across subepisodes.',
 observation_limits='Module manufacture is not installed-system service; nominal output is not lifetime energy; model variables mix sources and interviews select producers.'),
 dict(chooser='Space/remote-system purchasers, later system owners under national support regimes, and firms choosing production investment.',
 payer='Government procurement/public research; private firm capital; tariff/tax-supported customers in later grid markets; individual financing shares not identified.',
 operator_maintainer='Manufacturing engineers, technicians and production workers; system installers and owners. Vendor training is documented.',
 affected_nonchooser='Ratepayers/taxpayers, production communities and workers; their net burdens/benefits were not measured in these studies.',
 ability_to_refuse='Producer entry is a firm choice; downstream buyers face task and connection constraints. Foreign recruitment/no-poach arrangements are reported, but worker consent, legal enforceability and household ability to decline support costs are not established.'),
 dict(tasks='Vendor training, line operation/adaptation, quality control, manual/automated module assembly, recruitment of experienced managers.',
 entry_barriers='Skilled process knowledge and capital; accessible downstream turnkey equipment reduced some firm-entry barriers, while upstream secrecy and limited suppliers impeded entry.',
 bargaining_ownership='Firms controlled equipment and hiring. Interviews report poaching disputes and agreements not to recruit rivals’ skilled staff; wage/bargaining effects unmeasured.',
 transition='Some executive migration histories documented; no longitudinal worker transition or retraining cohort.',
 distribution='Distinct opportunities for internationally trained managers versus assembly tasks; no reliable wages, gender, working-condition or displaced-worker distribution.',
 evidence_limit='Reduced labour cost per module cannot establish fewer total jobs, better livelihoods or who retained gains.'))

case(2,'Nuclear construction: coordinated programmes, cost variation and finance boundaries',
 ['United States','France','South Korea'],'Construction cohorts 1954–2008; French programme 1970–2000; US accounting 1976–1987 and cancellation context 2017',
 ['energy','large-scale construction'],['deployment','cost-escalation-and-decline','cancellation'],
 'National completed-project cost histories and component accounts challenge both automatic learning and inevitable escalation. Rapid coordinated construction can coexist with rising unit costs; finance and cancellations remain outside overnight-cost trends.',
 {'invention':'Nuclear fission/reactor invention precedes this construction comparison; no invention claim made.',
  'feasibility':'Commercial reactor configurations were imported, licensed, standardized and revised; feasibility did not settle project cost.',
  'deployment':'France built a large PWR fleet under concentrated procurement; South Korea adopted commercial imports and domestic derivatives.',
  'diffusion':'Installed fleets and construction cohorts, not individual electricity-user choices.',
  'scaling':'Bulk orders, domestic manufacturing/engineering and multi-unit projects; cost effects differ by cohort and site.',
  'non-adoption/niche':'Completed-reactor datasets omit cancelled proposals and selected experimental designs.',
  'displacement/reversal':'VC Summer expansion abandoned in 2017 in the inspected US account; no systematic cancellation rate estimated.'},
 ['Programme coordination','Licensed designs and standardization','Site-specific construction execution','Capital commitment and interest exposure','Scope and safety changes'],
 'Cross-country trajectories are not matched experiments; interest excluded, cancellations missing, and later French data revise earlier estimates.',
 [5,6,7,8],[4,5,6],
 dict(technology_configuration='Commercial power-reactor cohorts; France PWR programme; Korea imported and domestic designs; US Westinghouse four-loop cost accounts, with 2017 cancellation as a separate outcome.',
 task='Construct and operate grid-connected bulk electricity supply under national security, economic and regulatory objectives.',
 population='349 reactors in seven-country compilation (focus US/France/Korea), completed-project selection; EEDB representative US plant accounts are a different population.',
 interval='Country construction-start cohorts through 2008 in the historical compilation; US accounting 1976–1987; historical cancellation observed in 2017.',
 contemporary_alternatives=['Coal/oil/gas generation under period-specific fuel prices','Hydroelectricity where sites available','Different reactor designs, imported or domestic','Delayed construction or cancellation'],
 adoption_measure='Completed reactor capacity/cohorts and construction time; overnight currency per kW in 2010 domestic prices. No uniform whole-project adoption hazard.',
 observation_limits='Missing proposed/cancelled projects, financing, some experimental routes and major countries; different technologies, periods, deflators and record quality.'),
 dict(chooser='Government/utility planners, regulators, reactor vendors and financing authorities; households generally did not choose the generation fleet.',
 payer='Utility capital, lenders and state-backed programmes, ultimately allocated through rates/taxes or losses; precise incidence not quantified.',
 operator_maintainer='Engineering organizations, construction contractors, plant operators and fuel-cycle workers.',
 affected_nonchooser='Electricity customers, site communities, construction workers, waste/fuel-cycle communities and taxpayers.',
 ability_to_refuse='France’s history describes concentrated technocratic decisions and weak public influence; this is not consent. Korean community/worker refusal channels and US project-level bargaining are unestablished in inspected cost records.'),
 dict(tasks='Engineering design, scheduling, purchasing, on-site supervision, construction and quality assurance; operation continues after construction.',
 entry_barriers='Large capital commitments, engineering capability, qualified vendors and safety requirements; individual credential thresholds not reconstructed.',
 bargaining_ownership='Utility/vendor/state control of project choices; cost accounts reveal expenditure rather than worker bargaining or who absorbs overruns.',
 transition='No worker/cohort tracking across construction pauses or cancelled plants; costs cannot establish retraining outcomes.',
 distribution='Higher indirect spending is observed in a model; no supported wage, employment-security or regional-income distribution.',
 evidence_limit='Cost and completion histories cannot settle occupational gains, welfare, accident risk or benefits from avoided fossil pollution.'))

case(3,'Planar silicon and merchant DRAM: reproducibility, procurement and bounded learning',
 ['United States','Japan','Other merchant DRAM producer countries'],'1957–1969 and 1974–1992',
 ['industrial manufacturing','digital hardware'],['commercialization','production-learning','entry-and-exit'],
 'Two explicitly distinct episodes connect protected-junction manufacturing and Apollo procurement to later tests of generation-specific DRAM learning. The evidence rejects patent-equals-diffusion and simple national-learning-superiority stories.',
 {'invention':'Hoerni’s coating-retention method disclosed in 1959 patent application; no claim to exclusive invention of the transistor or IC.',
  'feasibility':'Working planar transistor recorded in March 1959; repeatability and continuing failure mechanisms distinguished from a patent.',
  'deployment':'Commercial planar transistor in April 1960; Apollo NOR-gate purchases in the early 1960s.',
  'diffusion':'Commercial licensing described qualitatively; later 32-firm merchant-DRAM shipment panel.',
  'scaling':'Standardized procurement and inferred within-generation production learning; direct yield panel absent.',
  'non-adoption/niche':'High-value spacecraft niche precedes broad consumer affordability; core/transistor alternatives were considered.',
  'displacement/reversal':'DRAM generation transitions include entry and exit; they do not establish whole-firm disappearance.'},
 ['Surface protection and process control','Standardized high-value procurement','Within-firm learning with international spillovers','Partial knowledge obsolescence'],
 'Later DRAM evidence does not identify what Apollo caused; patent, museum and official history share inherited records and lack full factory data.',
 [9,10,11,12],[7,8,9,14],
 dict(technology_configuration='Episode A: silicon planar transistor process and Apollo NOR logic, 1957–1969. Episode B: merchant DRAM generations 4K through 16M, 1974–1992. No transitive causal proof is asserted between episodes.',
 task='Manufacture reliable compact switching/logic devices and, separately, inexpensive merchant memory.',
 population='Fairchild/process-history and Apollo engineering records; separate Dataquest panel of 32 merchant firms, excluding internal-only producers.',
 interval='1957–1969; 1974Q1–1992Q4.',
 contemporary_alternatives=['Mesa/discrete transistors and core-transistor logic','Different gates and redundant/repairable computer designs','Prior or rival memory generations','Internal rather than merchant memory production'],
 adoption_measure='Documented prototype/product introduction and NASA purchase episode; later quarterly DRAM shipments/prices, not direct costs or plant yields.',
 observation_limits='Patent is not proof of uptake; procurement share is narrow in time; structural model infers cost from price/output and market assumptions.'),
 dict(chooser='Device firms, NASA/MIT system designers and merchant-memory producers; buyers chose different performance/cost trade-offs.',
 payer='Corporate investment and publicly financed Apollo procurement; later merchant sales and investment, exact R&D/procurement shares unknown.',
 operator_maintainer='Process engineers, fabrication and test workers, equipment/quality specialists and system designers.',
 affected_nonchooser='Taxpayers and manufacturing workers/communities; hazardous-material exposure and labour allocation are not quantified here.',
 ability_to_refuse='System designers evaluated alternatives; firms could enter/exit merchant product lines. Workers’ employment alternatives, compelled transfers and local community voice unknown.'),
 dict(tasks='Protective coating/masking/diffusion, contact and packaging work, qualification tests, defect diagnosis, production-process monitoring.',
 entry_barriers='Precision/cleanliness, equipment, process knowledge and capital. Cross-generation spillover estimates do not measure every entry barrier.',
 bargaining_ownership='Patent assigned to Fairchild and rights licensed according to museum account; firms own production assets. Worker bargaining evidence absent.',
 transition='Firm-level product entry/exit observed; no individual transitions from wiring/assembly to fabrication quantified.',
 distribution='Model tests country-level learning rates; it does not measure wage inequality, gendered assembly work or ownership returns.',
 evidence_limit='No claim that semiconductor learning automatically creates accessible work or that 20% inferred cost learning means a 20% labour-productivity gain.'))

case(4,'Lithium-ion cells: feasible chemistry, qualification and manufacturing improvement',
 ['Japan','International battery manufacturing and research'],'1981–1991; manufacturing comparison 1995–2000 versus 2010–2015',
 ['energy storage','materials','industrial manufacturing'],['commercialization','cost-decline','application-specific-scaling'],
 'A first-person development account and later fixed-format cell model distinguish rechargeable chemistry from saleable qualification and from the sources of cost improvement. No universal battery-replacement or safety claim follows.',
 {'invention':'Several electrode discoveries and configurations; Yoshino’s carbon/lithiated-cathode patent in 1985 is one development, not a sole-inventor story.',
  'feasibility':'Laboratory rechargeable operation faced heat, volume and abuse-performance constraints; paired material selection and testing mattered.',
  'deployment':'Commercial manufacture/sales in Japan in 1991 reported by Yoshino.',
  'diffusion':'Portable-electronics use is described qualitatively; no independently audited adopter count.',
  'scaling':'Cost and component changes for representative high-energy 18650 cells between two multi-year windows.',
  'non-adoption/niche':'Rejected PA and metallic-lithium configurations in the described pathway; application-specific needs persist.',
  'displacement/reversal':'No assertion that Li-ion displaced every rechargeable chemistry; ENE-C05 records continued lead-acid use.'},
 ['Complementary electrode chemistry','Qualification and reliability','Interdivision knowledge transfer','Energy density and manufacturing scale','R&D/process classification'],
 'Inventor selection and incomplete process records; cell format, power, safety and cycle-life trade-offs limit aggregation.',
 [13,14,15],[10,11],
 dict(technology_configuration='Episode A: carbon/LiCoO2 nonaqueous rechargeable configuration in Yoshino’s development account. Episode B: representative high-energy cylindrical 18650 cells, not every chemistry.',
 task='Store rechargeable energy in small/light packages for portable devices; lower manufacturing cost per energy capacity while meeting application requirements.',
 population='One corporate research pathway; separate reconstructed representative cell datasets assembled from publications/reports.',
 interval='1981–1991; 1995–2000 and 2010–2015 comparison windows.',
 contemporary_alternatives=['Nickel-cadmium and nickel-metal-hydride rechargeables','Lead-acid batteries where mass/volume tolerable','Primary lithium batteries','Rejected metallic-lithium/PA rechargeable designs in the studied pathway'],
 adoption_measure='Commercialization date and qualitative use; modelled cost per Wh of representative cells, not a complete production or user adoption census.',
 observation_limits='Retrospective inventor report; sparse early components/process data; choice of high-energy 18650 excludes applications optimized for other characteristics.'),
 dict(chooser='Corporate research and manufacturing teams, device designers and end purchasers with different constraints.',
 payer='Company research/manufacturing investment and downstream device buyers; public research contributions acknowledged but exact incidence not reconstructed.',
 operator_maintainer='Materials researchers, process/quality engineers and factory workers; testing drew on another corporate division’s facilities.',
 affected_nonchooser='Workers and communities involved in materials supply and disposal; mining/waste distribution not investigated by these two sources.',
 ability_to_refuse='Research teams could reject material routes; consumers faced device offerings. Worker and supply-community refusal evidence unknown.'),
 dict(tasks='Electrode/material development, cell assembly and formation, inspection, manufacturing-process optimization and qualification testing.',
 entry_barriers='Materials knowledge, controlled processes, equipment and quality/safety capability; exact skill credentials and employment access not established.',
 bargaining_ownership='Corporate patents/assets and proprietary process formulations matter; ownership of gains and worker bargaining not measured.',
 transition='No longitudinal labour or mining-community evidence; dates describe technology work, not individual retraining duration.',
 distribution='Modeled labour/overhead costs aggregated; no supported distribution of compensation, health risk or returns.',
 evidence_limit='A small assigned learning-by-doing share is not an estimate of factory labour’s value; battery-cost decline is not a worker welfare estimate.'))

case(5,'Chinese electric two-wheelers: lead-acid persistence and shifted externalities',
 ['China; sampled urban markets and regional electricity systems'],'1999–2009, principally observations 2006–2007',
 ['energy storage','transport manufacturing'],['rapid-use-growth','continued-older-technology','uneven-local-permission'],
 'Lead-acid storage supported a growing electric vehicle category while newer batteries remained costly alternatives. City rules, modular component supply, actual substituted modes and upstream lead flows complicate a clean/newer-is-better story.',
 {'invention':'Lead-acid chemistry predates the episode; the innovation here is a configured vehicle/supply system.',
  'feasibility':'Standardized batteries, motors, controllers and chargers assembled into useful low-speed vehicles.',
  'deployment':'Observed use and sales expansion in Chinese cities during the 2000s.',
  'diffusion':'Industry sales estimates and limited city surveys; no nationally representative household diffusion panel.',
  'scaling':'Decentralized supplier/assembler networks; routine assembly observed at six plants.',
  'non-adoption/niche':'Li-ion/NiMH available but limited in domestic stores; lead-acid continued. Some cities restricted e-bikes.',
  'displacement/reversal':'Prior bicycle/bus use common in surveyed cities; not evidence of universally replacing cars or motorcycles.'},
 ['Upfront price and performance trade-offs','Standardized components and assembly entry','Policy-shaped transport alternatives','Supply-chain externalities'],
 'Battery choice motives not causally observed; advanced-battery production includes exports; environmental inventory omits important pathways and dose-response evidence.',
 [16,17,18],[12,13],
 dict(technology_configuration='Chinese bicycle-style and scooter-style electric two-wheelers, mostly VRLA batteries, with Li-ion/NiMH comparators.',
 task='Affordable urban/regional personal mobility under local road rules; assemble/maintain a saleable vehicle.',
 population='Users, dealers and manufacturers in selected cities/plants; national industry estimates and a separate partial emissions model.',
 interval='1999–2009, field observations principally 2006–2007; some upstream lead inputs refer to 1999.',
 contemporary_alternatives=['Bicycles','Buses/public transport','Gasoline motorcycles where permitted','Cars for households able to afford them','Li-ion/NiMH electric two-wheelers, available but more costly'],
 adoption_measure='Industry annual-sales estimates, city roadside shares, prior-mode surveys; chemical-market shares do not cleanly distinguish exports from domestic use.',
 observation_limits='Nonrandom cities/plants, shifting regulations and inconsistent estimates; emissions model uses borrowed factors and scenario service life/load assumptions.'),
 dict(chooser='Users selecting among affordable/legal modes; city authorities setting access; assemblers selecting components.',
 payer='Purchasers and replacement-battery buyers; external pollution costs partly borne elsewhere and unpriced in purchase comparison.',
 operator_maintainer='Riders/households charge vehicles, dealers/repairers replace components, assembly workers build vehicles and battery workers/recyclers handle materials.',
 affected_nonchooser='Pedestrians, road users, workers and communities near electricity generation, lead production and recycling.',
 ability_to_refuse='Motorcycle/e-bike bans remove particular options in different cities; surveyed users retained bicycle/bus alternatives but access varied. Communities exposed to upstream pollution did not choose each vehicle; effective refusal rights unestablished.'),
 dict(tasks='Prefabricated-component assembly using pneumatic tools, battery manufacture/replacement, charging and recycling; low machining requirement in visited assembly plants.',
 entry_barriers='Modular components lowered some assembler technical requirements; capital, supplier access, legal registration and quality control remained. User purchase price and local legal access constrain uptake.',
 bargaining_ownership='Many small assemblers and competitive supplier networks documented; wages, ownership profits and recycler bargaining not established.',
 transition='No tracked transitions from bicycle manufacture or displaced transport jobs; plant visits provide task snapshots.',
 distribution='Pollution shifted to supply/recycling locations; actual worker doses, health outcomes and income distribution not measured.',
 evidence_limit='Low task-entry requirements are not proof of decent work, and cheap transport is not sufficient evidence of net social benefit.'))

nodes=[]
def node(n,label,kind,cs): nodes.append(dict(id=f'ENE-T{n:02d}',label=label,kind=kind,case_ids=ids('C',*cs)))
node(1,'Electronic-grade silicon supply and semiconductor process know-how','resource',[1,3])
node(2,'Crystalline-silicon PV module manufacture, 1980–2001','technology',[1])
node(3,'International PV equipment suppliers and vendor training, 2003–2009','complement',[1])
node(4,'Chinese downstream PV production, 2003–2009','technology',[1])
node(5,'Experienced PV engineers and returning managers','resource',[1])
node(6,'Foreign policy-supported PV demand, late 2000s','institution',[1])
node(7,'Bulk procurement and licensed French PWR series','practice',[2])
node(8,'French PWR construction programme, 1970–2000','technology',[2])
node(9,'EDF engineering and programme coordination','institution',[2])
node(10,'US site-specific construction interference and support burden','practice',[2])
node(11,'US four-loop reactor construction, 1976–1987','technology',[2])
node(12,'Long-lived construction finance and interest exposure','complement',[2])
node(13,'Permanent junction-protecting surface coating','practice',[3])
node(14,'Planar silicon devices, 1959–1960s','technology',[3])
node(15,'Apollo standardized NOR-gate procurement and qualification','institution',[3])
node(16,'Within-generation DRAM production/process learning','practice',[3])
node(17,'Merchant DRAM production, 1974–1992','technology',[3])
node(18,'Prior-generation DRAM production experience','resource',[3])
node(19,'Suitable carbonaceous anode in Yoshino configuration','resource',[4])
node(20,'Carbon/LiCoO2 rechargeable cell configuration, 1980s','technology',[4])
node(21,'Lithium-bearing oxide cathode in Yoshino configuration','resource',[4])
node(22,'Qualification tests and process development','practice',[4])
node(23,'High-energy 18650 cell manufacture, 1995–2015','technology',[4])
node(24,'Improved charge density and materials/process research','practice',[4])
node(25,'Lead-acid electric two-wheelers in China, mid-2000s','technology',[5])
node(26,'Higher-priced Li-ion/NiMH two-wheeler alternatives','technology',[5])
node(27,'Standardized electric two-wheeler components and suppliers','complement',[5])
node(28,'City-specific motorcycle and e-bike access rules','institution',[5])
node(29,'Lead production, battery replacement and recycling','practice',[5])
node(30,'Regional electricity supply for two-wheelers','resource',[5])

edges=[]
def edge(n,fr,to,rel,c,ks,ss,conf,qual,basis,stage,config,alts,joint,dispute):
    edges.append(dict(id=f'ENE-E{n:02d}',**{'from':f'ENE-T{fr:02d}','to':f'ENE-T{to:02d}'},
      relation=rel,case_ids=ids('C',c),claim_ids=ids('K',*ks),source_ids=ids('S',*ss),
      confidence=conf,qualification=qual,basis=basis,
      scope=dict(case_id=f'ENE-C{c:02d}',stage=stage,configuration=config),
      alternatives=alts,joint_inputs=ids('T',*joint),necessity_rationale='No necessity claim',dispute=dispute))
edge(1,1,2,'enables',1,[2],[1,2],'medium','Observed supply and know-how spillover before PV dominated silicon demand; not a timeless dependency.','documented-transmission','scaling','Crystalline-silicon modules before mid-2000s supply transition',
 ['Dedicated solar-grade silicon supply','Different thin-film chemistries with different inputs'],[],
 'Transmission is documented in reviewed histories; its quantitative contribution differs by model and changes after silicon shortages.')
edge(2,3,4,'enables',1,[4],[3],'medium','Equipment purchase carried training and complementary know-how.','observed-contribution','diffusion','Chinese cell/module producer entry, 2003–2009',
 ['In-house process development','Joint ventures or licensing where accessible'],[5],
 'Interviews and supplier counts are not controlled causal evidence; finance and factor prices covary.')
edge(3,5,4,'complements',1,[4],[3],'medium','Experienced personnel helped operate and adapt production processes alongside equipment.','observed-contribution','diffusion','Chinese downstream PV entry',
 ['Local training and accumulated process experience'],[3],
 'Manager biographies overrepresent successful firms; ordinary worker outcomes are unknown.')
edge(4,6,4,'enables',1,[3,4],[3],'medium','Export-oriented demand supported orders for Chinese production, without implying domestic deployment.','observed-contribution','scaling','Exporting Chinese PV manufacturers, late 2000s',
 ['Domestic grid support','Off-grid/private niches'],[],
 'No isolated estimate of feed-in tariffs, capital subsidies or factor-cost effects.')
edge(5,7,8,'enables',2,[6],[5],'medium','Bulk series and licensed designs formed part of the coordinated French programme.','observed-contribution','scaling','French PWR programme, 1970–2000',
 ['More fragmented utility orders','Other reactor series or nonnuclear generation'],[9],
 'Rapid deployment coexisted with rising unit costs and design change; this is not necessity or guaranteed cheapness.')
edge(6,9,8,'complements',2,[6],[5],'medium','In-house engineering complemented concentrated orders.','observed-contribution','scaling','French PWR programme',
 ['External engineering/constructor coordination'],[7],
 'Political support, financing and security objectives are not separately identified; public voice was constrained.')
edge(7,10,11,'constrains',2,[7],[6],'medium','Indirect-account growth and site execution burden raised modeled construction cost.','observed-contribution','scaling','US representative four-loop plant cost accounts, 1976–1987',
 ['Different construction designs and execution organization'],[],
 'Indirect burdens may themselves be responses to regulation/redesign; 72% is an accounting allocation, not a management causal effect.')
edge(8,12,11,'complements',2,[8],[4,6],'high','Construction requires financing arrangements in practice, but no specific finance route is declared necessary.','observed-contribution','deployment','Financed construction with interest excluded from OCC metric',
 ['Public balance-sheet funding','Different debt/equity arrangements'],[],
 'Cost of capital and risk incidence differ; no completed-project cost curve measures cancelled-project losses.')
edge(9,13,14,'enables',3,[9],[7,14],'high','Coating protects surface junction edges in the patented local process.','technical-possibility','feasibility','Hoerni planar device process, 1959–1960',
 ['Mesa/discrete transistor routes with different protection and packaging'],[],
 'Patent is not a yield record; other fabrication and packaging inputs required but no complete necessity bundle is claimed.')
edge(10,15,14,'enables',3,[10],[8],'medium','Procurement supported a qualified IC niche; not all planar-device demand.','observed-contribution','deployment','Apollo early-1960s NOR-gate orders',
 ['Other military/commercial purchasers','Discrete/core logic at system-design level'],[],
 'No independent reconstruction of invoices or no-Apollo counterfactual; does not prove NASA caused later DRAM learning.')
edge(11,16,17,'enables',3,[11],[9],'medium','Within-firm experience has stronger estimated contribution than external experience in structural DRAM model.','observed-contribution','scaling','Merchant DRAM generations, 1974–1992',
 ['R&D and equipment improvements','Knowledge obtained from other firms'],[],
 'Observed contribution is model-inferred from shipments/prices, not measured factory yield or randomized production.')
edge(12,18,17,'complements',3,[12],[9],'medium','Limited transfer in particular adjacent generations, not universal prerequisite.','observed-contribution','diffusion','Two economically meaningful generation transitions in the published model',
 ['New-entrant investment and new-generation process development'],[],
 'Weak/absent estimated transfer in other transitions and model assumptions limit a general cumulative-advantage claim.')
edge(13,19,20,'enables',4,[13],[10],'medium','Carbon anode combined with a lithium-bearing cathode in the described configuration.','technical-possibility','feasibility','Yoshino carbon/LiCoO2 nonaqueous cell, 1980s',
 ['Other rechargeable chemistries','Different carbon materials only after suitable process/electrolyte development'],[21],
 'Joint input means local electrode pairing, not complete sufficiency; retrospective account lacks all process/qualification details.')
edge(14,21,20,'complements',4,[13],[10],'medium','Lithium-bearing cathode supplies the needed ions when the described anode lacks metallic lithium.','technical-possibility','feasibility','Same carbon/LiCoO2 configuration',
 ['Other compatible lithiated cathodes','Metallic-lithium routes with different safety constraints'],[19],
 'Local paired chemistry is not proof these exact materials are necessary for every lithium-ion battery.')
edge(15,22,20,'complements',4,[13],[10],'medium','Abuse tests informed progression toward commercialization after workable chemistry.','observed-contribution','deployment','Yoshino development pathway before 1991 sales',
 ['Other valid qualification protocols; no complete period standard catalog established'],[],
 'Inventor reports tests; no universal safety guarantee or independent statistical qualification dataset.')
edge(16,24,23,'enables',4,[14,15],[11],'medium','Higher stored energy per fixed-size cell and materials changes lower modeled cost per Wh.','observed-contribution','scaling','High-energy 18650 comparison, 1995–2000 versus 2010–2015',
 ['Cheaper inputs or larger plants','Other cell formats/chemistries optimized for different services'],[],
 'Model decomposition and R&D assignments are not counterfactual public-policy effects.')
edge(17,26,25,'competes-with',5,[16],[12,13],'medium','Commercial alternatives coexist; lead-acid persists despite lower mass of advanced chemistries.','observed-contribution','non-adoption/niche','Chinese mid-2000s electric-two-wheeler battery choices',
 ['Bicycle/bus','Gasoline motorcycle where permitted'],[],
 'Price/lifetime comparison approximate; buyer-level reasons and export-adjusted shares remain unknown.')
edge(18,27,25,'enables',5,[17],[12],'medium','Prefabricated modules supported low-machining assembly in observed plants.','observed-contribution','scaling','Six visited plants and related component network, mid-2000s',
 ['More integrated vehicle production'],[],
 'Site visits establish tasks; modularity’s independent cost/adoption effect and work quality are not identified.')
edge(19,28,25,'constrains',5,[17],[12],'medium','City rules could restrict e-bikes or remove motorcycle alternatives; the sign depends on the local rule.','observed-contribution','diffusion','Chinese city-specific vehicle access, 2006–2007',
 ['Permissive treatment','Bicycle/bus choices under local rules'],[],
 'This edge records constraints, not a uniform national anti-adoption effect; enforcement and policy endogeneity matter.')
edge(20,29,25,'complements',5,[18],[13],'medium','Battery production/replacement/recycling supported vehicle service while distributing upstream lead losses.','observed-contribution','deployment','Lead-acid two-wheelers in partial lifecycle inventory',
 ['Other rechargeable batteries','Improved controlled lead production/recycling'],[],
 'Emissions are modeled material flows, not directly measured population doses or net welfare.')
edge(21,30,25,'complements',5,[18],[13],'medium','Charging service links vehicle use to regional generation emissions.','observed-contribution','deployment','Regional-grid scenarios in 2009 partial lifecycle study',
 ['Cleaner electricity configurations','Nonelectric mobility'],[],
 'Average grid factors need not equal marginal dispatch; no causal health estimate or universal emissions ranking.')

comparisons=[
 dict(id='ENE-X01',question='Does more production necessarily make a technology cheaper?',case_ids=ids('C',1,2,3,4),
 useful_similarities='All require capital, repeatable processes and accumulated operational knowledge; all have historical cost evidence.',
 important_differences='PV and cell factory output are not site-built nuclear projects; DRAM costs are structurally inferred; product performance and cohort intervals differ.',
 evidence_comparability='Compare proposed mechanisms and measurement boundaries, not numerical learning rates. Nuclear OCC omits finance; battery USD/Wh differs from module USD/W.',
 connections_nonindependence='PV, nuclear decomposition and battery studies share some authors/methods; DRAM and PV share semiconductor inputs; nuclear datasets reuse reactor records.',
 omitted_countercases='Wind turbines, chemical plants, cement and shipbuilding would test granularity and complexity beyond this selection.',
 conclusion_limit='Evidence rejects a universal automatic-cost-decline rule; it does not estimate how often learning dominates or prove modularity is sufficient.'),
 dict(id='ENE-X02',question='Why does a newer chemistry coexist with an older one?',case_ids=ids('C',4,5),
 useful_similarities='Rechargeable storage serves portable/mobile loads; both combine cells, product design and user charging/maintenance.',
 important_differences='High-energy electronics prize volume and mass; low-speed two-wheelers face upfront purchase and road-access constraints. Historical comparison uses different services/windows.',
 evidence_comparability='Contemporary e-bike accounts directly document availability and dominance; cell-cost reconstruction is not an e-bike lifetime-cost panel.',
 connections_nonindependence='Shared battery producers/knowledge possible but not individually traced; Weinert coauthors both e-bike sources and reuses survey evidence.',
 omitted_countercases='Japanese/European premium e-bikes, off-grid storage and lead-acid vehicle starter batteries would test whether price, serviceability or performance dominates.',
 conclusion_limit='Continued lead-acid use contradicts inevitable immediate replacement; household credit constraints and lifetime expectations remain hypotheses.'),
 dict(id='ENE-X03',question='Does state involvement have one consistent effect on diffusion?',case_ids=ids('C',1,2,3,5),
 useful_similarities='Procurement, permissions and finance alter feasible choices rather than merely respond to a preexisting price.',
 important_differences='Apollo purchased specialized components; French utilities organized construction; PV demand support crossed borders; cities both favored and prohibited e-bikes.',
 evidence_comparability='Different actors, interventions and outcomes prevent pooling as a single treatment called government.',
 connections_nonindependence='International trade connects national PV policies to Chinese output; licensed reactor designs connect programme histories.',
 omitted_countercases='Comparable unsupported firms/cities and abandoned procurement programmes not systematically sampled.',
 conclusion_limit='Useful institutional distinctions survive; no estimate of net state-versus-market contribution or welfare follows.'),
 dict(id='ENE-X04',question='When is specialized knowledge an entry barrier and when can it travel?',case_ids=ids('C',1,3,5),
 useful_similarities='Manufacturing relies on complementary equipment, routines, skilled people and component interfaces.',
 important_differences='PV upstream secrecy contrasts with downstream turnkey supply; DRAM generation changes can erode prior learning; e-bike assembly uses prefabricated components.',
 evidence_comparability='Interview histories, structural estimates and factory visits reveal different aspects; they do not measure the same worker or firm entry probability.',
 connections_nonindependence='PV inherits semiconductor materials/process knowledge; mobility of staff and vendor feedback can link nominally separate firms.',
 omitted_countercases='Failed entrants, women/migrant production workers, financing-constrained firms and proprietary chemical processes remain undersampled.',
 conclusion_limit='Observed transferable know-how and lower assembly requirements do not establish equitable access, high wages or absence of capital barriers.')
]

write('sources.json',sources)
write('claims.json',claims)
write('cases.json',cases)
write('graph.json',dict(nodes=nodes,edges=edges))
write('comparisons.json',comparisons)
print(f'Wrote {len(cases)} cases, {len(sources)} sources, {len(claims)} claims, {len(nodes)} nodes, {len(edges)} edges and {len(comparisons)} comparisons.')
