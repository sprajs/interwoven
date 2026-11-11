# Historical drafting helper: canonical JSON contains later reviewed edits.
# Do not regenerate canonical records from this helper. Use tools/build_collection.py for exports.
"""Build IND's explicitly scoped research records; no network or external mutations."""
import json
from pathlib import Path

OUT = Path(__file__).parent
DATE = '2026-11-05'

def save(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')

def source(n, title, authors, year, url, source_type, access, locator, scope_limit):
    return dict(id=f'IND-S{n:02d}', title=title, authors=authors, year=year, url=url,
                source_type=source_type, access=access, locator=locator,
                scope_limit=scope_limit, accessed=DATE)

sources = [
source(1, 'De re metallica, translated from the 1556 Latin edition', ['Georgius Agricola', 'Herbert Clark Hoover (translator)', 'Lou Henry Hoover (translator)'], '1556; English translation 1912; reprint 1950',
'https://www.gutenberg.org/files/38015/38015-h/38015-h.htm', 'historical-primary', 'full-text',
'Book II, printed pp. 31–33 (water, roads, provisioning and rulers); Book VI, pp. 171–185 (pumping choices, replacement teeth, staged pumps). Selected text sections inspected; complete HTML available.',
'Technical treatise, not an installation census. Translation and editorial notes are later; claim uses authorial text rather than assigning the Hoovers’ historical annotations to Agricola. Illustrations do not establish prevalence.'),
source(2, 'Mine Pumping in Agricola’s Time and Later', ['Robert P. Multhauf'], 1959,
'https://www.gutenberg.org/cache/epub/31024/pg31024-images.html', 'scholarly-analysis', 'full-text',
'Printed pp. 114–120; especially pp. 117–120 and footnotes 13–22. Main text and relevant notes inspected in full HTML.',
'Smithsonian historical study based on treatises and depictions; some proposed dates conflict. Images are selective and sometimes internally inconsistent. Its hydraulic explanation for German steam delay is a conjecture, not an identified causal result.'),
source(3, 'Collective Invention during the British Industrial Revolution: The Case of the Cornish Pumping Engine', ['Alessandro Nuvolari'], 2004,
'https://pure.tue.nl/ws/portalfiles/portal/2343508/669221.pdf', 'scholarly-analysis', 'full-text',
'ECIS Working Paper 04.02, printed pp. 10–20, 22 (PDF pp. 12–22, 24); figure 1 located p. 32. Sections 3–4 inspected. Downloaded PDF and extracted text retained locally.',
'The inspected object is the 2004 working paper, not the journal pagination. Reconstructs published engineering evidence; Lean’s original reports and royalty contracts not independently inspected. Information sharing, investment and high-pressure engineering changed together.'),
source(4, 'Productivity Growth in the Industrial Revolution: A New Growth Accounting Perspective', ['Nicholas Crafts'], 2002,
'https://www.frbsf.org/wp-content/uploads/sites/4/crafts.pdf', 'scholarly-analysis', 'full-text',
'January 2002 version, pp. 13–19 and table 3 on p. 23. Downloaded full PDF; those analytic passages and table inspected.',
'Working-paper estimates, not silently substituted for either 2004 published article. Reconstructed horsepower, capital shares and social savings depend on assumptions; sectoral importance is not the same as aggregate growth contribution. No claim that the results settle later revisions to steam stocks.'),
source(5, 'Limited waterpower contributed to rise of steam power in British “Cottonopolis”', ['Tara N. Jonell', 'Peter Jones', 'Adam Lucas', 'Simon Naylor'], 2024,
'https://pmc.ncbi.nlm.nih.gov/articles/PMC11249955/', 'scholarly-analysis', 'partial-text',
'Abstract, introduction, “Impact on the British textile industry”, and methods passages on hydropower estimation and mill census retrieved and inspected. DOI 10.1093/pnasnexus/pgae251. Some later open attempts returned an access challenge.',
'Not all article sections or supplementary files were acquired. Physical reconstruction uses terrain, historical climate and assumed efficiency; modern marginal-cost thresholds are suggestive, not observed historical adoption prices. Does not independently identify labour-control motives or reservoir feasibility.'),
source(6, 'Fleeing the Flowing Commons: Robert Thom, Water Reservoir Schemes, and the Shift to Steam Power in Early Nineteenth-Century Britain', ['Andreas Malm'], 2014,
'https://portal.research.lu.se/en/publications/fleeing-the-flowing-commons-robert-thom-water-reservoir-schemes-a/', 'scholarly-analysis', 'abstract',
'Author-institution repository abstract and bibliographic record; journal reference Environmental History 19(1), pp. 55–77. Full text not acquired.',
'Only supports an attributed summary of Malm’s argument about proposed reservoirs and coordination. Scheme-level costs, archives and the article’s strong cheaper-water conclusion were not audited. Do not cite detailed pages as if read.'),
source(7, 'The British Industrial Revolution in Global Perspective: chapter 1 excerpt', ['Robert C. Allen'], 2009,
'https://assets.cambridge.org/97805218/68273/excerpt/9780521868273_excerpt.pdf', 'scholarly-analysis', 'partial-text',
'Publisher excerpt, chapter 1, pp. 1–10 available; pp. 1–5 inspected, especially pp. 1–3 on factor prices and engineering-led diffusion.',
'Introductory formulation only: underlying profitability computations, full wage series and later replies to critics were not inspected. Supports attribution of the thesis rather than a verified finding that technology was uneconomic everywhere outside Britain.'),
source(8, 'Spinning the Industrial Revolution', ['Jane Humphries', 'Benjamin Schneider'], '2019 (online 2018; accepted manuscript)',
'https://ora.ox.ac.uk/objects/uuid%3A4f321519-a0b7-4879-a521-139cbca81b25/download_file?safe_filename=Humphries_and_Schneider_Spinning_the_industrial_revolution.pdf&type_of_work=Journal+article', 'scholarly-analysis', 'full-text',
'Accepted-manuscript pp. 4, 15–16, 25–32, 37–41 and dataset table 6. These pages inspected in locally downloaded 58-page PDF; journal version is Economic History Review 72(1), pp. 126–155.',
'Archival research, but individual archive originals not independently inspected. Most reconstructed observations concern wool; pre-factory cotton data are scarce. Full-time work and daily earnings require inference. Challenges wage premise more directly than it identifies alternative invention motives.'),
source(9, 'The Philosophy of Manufactures (selected passages)', ['Andrew Ure'], 1835,
'https://sourcebooks.web.fordham.edu/mod/1835ure.asp', 'historical-primary', 'partial-text',
'Fordham extract inspected, identified as original pp. 5–8, 14–15, 20–21, 23, 29–31; especially paragraphs beginning “The principle of the factory system”, “By the infirmity”, and “In the infancy of mechanical engineering”.',
'Contemporary pro-factory advocacy, not neutral observation of workers’ welfare. The extract does not map each paragraph individually to a printed page. Page ranges are the compiler’s provenance, and paragraph incipits are the exact reading locators.'),
source(10, 'Connecting the Scientific and Industrial Revolutions: The Role of Practical Mathematics', ['Morgan Kelly', 'Cormac Ó Gráda'], 2020,
'https://www.econstor.eu/bitstream/10419/228197/1/1701742357.pdf', 'scholarly-analysis', 'full-text',
'UCD WP20/17, sections 2.1–2.3, printed pp. 13–18 (PDF pp. 15–20), and p. 27. Downloaded full PDF; specified passages inspected.',
'Working-paper historical mechanism argument drawing on technical biographies and earlier studies. Does not identify an exogenous skill-supply effect or establish that every machine depended on instrument-making. No numerical horsepower claim from its p. 16 is reused.'),
source(11, 'Cotton Textiles and the Great Divergence: Lancashire, India and Shifting Competitive Advantage, 1600–1850', ['Stephen N. Broadberry', 'Bishnupriya Gupta'], 2005,
'https://muslintrust.org/wp-content/uploads/2018/01/wrap_broadberry-cotton-textiles-and-the-great-diverge.pdf', 'scholarly-analysis', 'full-text',
'CEPR Discussion Paper 5183; printed pp. 2–4, 11, 15–25, 27, 32–33 and tables 7–13 located. Downloaded full 50-page PDF; relevant passages inspected. Printed pagination is three less than PDF page number.',
'This is the earlier discussion paper, not the 2009 journal version. Wage units and household assistants are imperfectly comparable; productivity partly inferred from prices and assumed Indian stagnation. Protection’s causal effect remains disputed.'),
source(12, 'Mughal Decline, Climate Change, and Britain’s Industrial Ascent: An Integrated Perspective on India’s 18th and 19th Century Deindustrialization', ['David Clingingsmith', 'Jeffrey G. Williamson'], 2005,
'https://www.nber.org/system/files/working_papers/w11730/w11730.pdf', 'scholarly-analysis', 'full-text',
'NBER Working Paper 11730; sections 2–7, especially printed pp. 15–19, 24–28 and model at p. 19. Selected sections inspected in downloaded PDF; published successor appeared in 2008.',
'The specified working paper models price evidence, with mobile labour, subsistence-linked wages and initially non-traded grain. Not causal identification of climate or Mughal decline; sparse employment evidence and inherited aggregate manufacturing estimates are not reproduced as fresh measurements.'),
source(13, 'Atlantic Slavery and the Rise of the Capitalist Global Economy', ['Joseph E. Inikori'], 2020,
'https://www.journals.uchicago.edu/doi/10.1086/709818', 'scholarly-analysis', 'full-text',
'Full HTML article; sections I–II on regional wages and Atlantic markets, section III and table 2 on commodity production, section IV paragraphs on Charles Grant and table 3 on Indian trade inspected.',
'Argument by a participating historian, including primary testimony quoted through other scholarship. Neither the parliamentary original nor underlying trade returns independently acquired. Broad claims of slavery’s necessity and colonial policy effects are not cleanly separated by an experiment.'),
source(14, 'National Leadership and Competing Technological Paradigms: The Globalization of Cotton Spinning, 1878–1933', ['Gary R. Saxonhouse', 'Gavin Wright'], 2010,
'https://drive.google.com/file/d/1T5GYPrNlqQ3QoJPo_vzEwlDRF7LhR7IG/view', 'scholarly-analysis', 'full-text',
'Journal of Economic History 70(3), pp. 535–566. Author-linked public PDF downloaded; pp. 535–542, 548–554, 558–561 and tables 1–3 inspected. Author index: https://gavin-wright.humsci.stanford.edu/recent-papers-and-publications',
'British supplier order records cover much world machinery trade, not every installed machine or realised mill outcome. Technical specification proxies, selective recorded cotton types and nonexperimental adoption models limit causal inference; explanations of Indian labour relations are qualified in the text.'),
source(15, 'Women’s Work and the Politics of Homespun in Socialist China, 1949–1980', ['Jacob Eyferth'], 2012,
'https://www.cambridge.org/core/services/aop-cambridge-core/content/view/1B4DC63727682F1EEC958A62A4126757/S0020859012000521a.pdf/div-class-title-womenandapos-s-work-and-the-politics-of-homespun-in-socialist-china-1949-1980-div.pdf', 'scholarly-analysis', 'full-text',
'International Review of Social History 57, pp. 365–391. Complete PDF retrieved through web; pp. 365–374 inspected. Claims in this contribution use historical background pp. 369–374, not later collectivisation episodes.',
'Major research focus is post-1949; pre-1949 quantities and history depend on earlier studies, especially Xu and Min, Kraus, Feuerwerker and rural surveys, not independently inspected. Reported handloom-output share is retained as an attributed estimate, not a census audit.'),
source(16, 'From Shafts to Wires: Historical Perspective on Electrification', ['Warren D. Devine, Jr.'], 1983,
'https://gwern.net/doc/economics/automation/1983-devine.pdf', 'scholarly-analysis', 'full-text',
'Journal of Economic History 43(2), pp. 347–372. Full PDF downloaded; pp. 353–363 and 368–372 inspected, especially drive configurations, equipment redesign and utility services.',
'Technical literature and reconstructed capacity series are stronger for engineering mechanisms than worker experience. No comprehensive unit-drive census exists; horsepower shares cannot be read as establishment adoption rates. Productivity interpretation is not an experimental estimate.')
]


def claim(n, cases, statement, evidence, confidence, causal, refs, counter, limits):
    return dict(id=f'IND-K{n:02d}', case_ids=[f'IND-C{x:02d}' for x in cases], statement=statement,
                evidence_type=evidence, confidence=confidence, causal_status=causal,
                sources=[dict(source_id=f'IND-S{s:02d}', locator=l, supports=p) for s,l,p in refs],
                counterevidence=counter, inference_limits=limits)

claims = [
claim(1,[1], 'Agricola’s 1556 account presents human, animal and hydraulic mine-work choices together and includes repairable components and site access among practical considerations.',
'historical-primary','high','descriptive', [(1,'Book II pp. 31–33; Book VI pp. 171–185, especially replacement teeth p. 173 and staged pump pp. 184–185','Documents explicit technical choices and maintenance provisions in the treatise.')],
'Texts and illustrations may describe exemplary arrangements rather than common practice.', 'Supports existence of described techniques and stated criteria, not measured prevalence, profitability or a universal choice rule.'),
claim(2,[1], 'In sixteenth- and seventeenth-century central European mining, rod transmission extended the use of waterpower to pumps distant from the stream; non-steam engineering continued to change.',
'scholarly-analysis','medium','mechanism-supported',[(2,'pp. 117–120, especially pp. 118–119 and notes 13–20','Compares crank-driven pumps, remote rods, balanced transmission and later depictions.')],
'Introduction dates vary; some depicted machinery is ambiguous. Some applications remained tied to local hydrology.', 'No region-wide diffusion denominator. Adequate hydraulics delaying German steam adoption is a further hypothesis, not established by this claim.'),
claim(3,[2], 'Nuvolari’s Cornish comparison links early Newcomen use to tolerable fuel costs and the uptake of more fuel-efficient Watt engines to the expense of imported coal in Cornwall.',
'scholarly-analysis','medium','mechanism-supported',[(3,'working-paper pp. 10–12','Contrasts fuel-intensive atmospheric engines and Cornish demand for fuel economy; documents Boulton and Watt deployments.')],
'Engine cost, drainage needs, labour, maintenance and royalties also entered investment decisions.', 'An historically supported pathway, not isolated identification of coal prices; cheap energy did not characterise every successful steam market.'),
claim(4,[2], 'From 1811, Cornish engine reporting made performance and practices comparable across installations; Nuvolari interprets this information sharing and overlapping investment as supports for incremental improvement.',
'scholarly-analysis','medium','mechanism-supported',[(3,'pp. 14–20; figure 1 p. 32','Describes Lean’s reporting, engineering competition and cost-book ownership.')],
'High-pressure designs and new investment arrived concurrently; a slack period followed patent expiry before reporting began.', 'Does not estimate the reporting effect separately from investment, engineers, fuel prices or design changes; original engine reports not directly audited.'),
claim(5,[2], 'Watt’s fuel-saving royalties and patent enforcement generated documented conflict in Cornwall; Nuvolari argues that broad exclusion also obstructed rival steam development.',
'scholarly-analysis','medium','contested',[(3,'pp. 12–14','Describes royalty formula, disputes, Hornblower and post-expiry withdrawal of Cornish orders.')],
'Patents and royalties may also have financed development and dissemination; cessation of monopoly was not followed by immediate technical progress.', 'The direction and magnitude of net patent effects remain disputed. Distinguish the documented dispute from the author’s wider innovation judgement.'),
claim(6,[2,3], 'In Crafts’s January 2002 reconstruction, steam contributed less than 0.01 percentage points per year to British labour-productivity growth before 1830, with a larger later contribution including railways.',
'scholarly-analysis','medium','descriptive',[(4,'pp. 13–19 and table 3 p. 23','Reports growth-accounting estimates and their stock/share assumptions.')],
'Early engine stocks are incomplete and unmeasured enabling effects may not be captured by aggregate accounting.', 'An estimate from the inspected version, not a timeless consensus or evidence that steam was unnecessary at individual sites. No cross-era forecast is made.'),
claim(7,[3], 'Jonell and colleagues reconstruct unused waterpower potential across much of Britain alongside local constraints around Greater Manchester, and describe supplementary steam use in water-powered mills.',
'scholarly-analysis','medium','mechanism-supported',[(5,'“Impact on the British textile industry”; hydropower and mill-census methods; abstract','Supports geographical heterogeneity and mixed-power operation.')],
'Reservoir construction, ownership, transmission and industrial location could alter usable supply; theoretical national potential is not economically deployable capacity.', 'Partial-text inspection only; underlying model and supplements not rerun. Local scarcity does not identify why factories originally clustered there.'),
claim(8,[3], 'Malm argues that large proposed reservoir schemes in the 1820s–1830s failed partly because their collective financing and coordination requirements conflicted with manufacturers’ arrangements.',
'scholarly-analysis','low','contested',[(6,'author-repository abstract','Explicitly attributes non-realisation of reservoir schemes to coordination and collective funding.')],
'Physical reliability, projected demand, land rights and cost assumptions are alternative or interacting explanations.', 'Abstract-only evidence: claim is about the author’s interpretation, not an independent finding that water was consistently cheaper or every proposed scheme feasible.'),
claim(9,[4], 'Allen’s explanation assigns British mechanisation to labour being expensive relative to capital and energy, and subsequent wider diffusion to improvements that reduced other input requirements.',
'scholarly-analysis','medium','contested',[(7,'chapter 1 excerpt pp. 1–3','States the factor-price and later engineering-diffusion thesis directly.')],
'Task-specific female wages, regional heterogeneity, skills, markets and political power complicate the aggregate comparison.', 'Attribution of a hypothesis; introductory excerpt does not validate Allen’s profitability calculations or universal foreign non-viability.'),
claim(10,[4], 'Humphries and Schneider’s reconstructed British hand-spinning pay does not show a general wage surge immediately before the spinning inventions; it challenges including these workers in an undifferentiated high-wage economy.',
'scholarly-analysis','medium','contested',[(8,'accepted-manuscript pp. 15–16, 25–32 and 37–41','Documents archival construction, source-type differences and absence of the proposed sharp wage increase.')],
'Cotton data are scarce, fibres and worker populations differ, and daily earnings involve time assumptions; Allen’s later rejoinders are not assessed here.', 'A challenge to a particular wage premise, not proof that factor prices never mattered or causal identification of quality control as the alternative motive.'),
claim(11,[4], 'In 1835 Ure publicly advocated factory mechanisation partly as a means to substitute cheaper labour and reduce dependence on independent skilled workers.',
'historical-primary','high','descriptive',[(9,'extract paragraphs beginning “The principle of the factory system”, “By the infirmity”, and “In the infancy of mechanical engineering”; compiler original-page ranges 20–23, 29–31','Records contemporary managerial advocacy for skill substitution and tractability.')],
'Skilled mechanics and machine operatives remained necessary; Ure is a partisan advocate whose welfare claims are not corroborated by this extract.', 'Shows a stated aspiration, not universal employer intention, successful complete deskilling or demonstrated worker benefit.'),
claim(12,[4], 'Kelly and Ó Gráda trace a pathway from instrument-making skill and precision measurement to complex textile machinery and the machine tools needed for repeated production and replacement parts.',
'scholarly-analysis','medium','mechanism-supported',[(10,'sections 2.1–2.3, printed pp. 13–18 (PDF pp. 15–20)','Identifies skill transfer, gauges and exact tools, and the demand for reproducible wearing components.')],
'The jenny and atmospheric engine could use less elaborate capabilities; cross-country tool histories have other routes and political contingencies.', 'A historically supported pathway rather than a universal prerequisite; no independent causal effect of national skill endowment is estimated.'),
claim(13,[5], 'Broadberry and Gupta’s reconstruction makes the timing of Lancashire’s competitive gains depend on raw-cotton and transport costs as well as wages and uneven productivity advances across spinning and weaving.',
'scholarly-analysis','medium','contested',[(11,'printed pp. 16–25, 27, 33; tables 7–13','Reconstructs comparative wages, productivity proxies, raw cotton prices and market-specific delivery costs.')],
'Indian productivity stagnation is assumed for key intervals, and household earnings and labour units are not directly comparable; political market access remains a rival/complement.', 'Applies to the inspected 2005 model and reconstruction, not directly measured productivity for all Indian textiles or proof of tariffs’ irrelevance.'),
claim(14,[5], 'Clingingsmith and Williamson propose that pre-1810 Indian textile decline involved domestic political/agricultural shocks, while later decline involved stronger international manufactured-price pressure.',
'scholarly-analysis','medium','contested',[(12,'sections 4–7, printed pp. 19–28','Uses a three-sector model and relative-price evidence to propose two phases.')],
'Regional political histories and data are uneven; colonial intervention, quality changes and capital constraints are not independently isolated by these prices.', 'Model assumptions include mobile labour, subsistence-linked pay and initially non-traded grain. This is an interpretation, not exogenous identification of drought or Mughal decline.'),
claim(15,[4,5], 'Inikori argues that Atlantic demand linked to slavery-based commodity production helped form the markets and regional expansion within which British cotton mechanisation developed.',
'scholarly-analysis','medium','contested',[(13,'sections I–III, especially section II paragraphs on Lancashire’s wages and Atlantic export sales','Connects regional protoindustry, Atlantic demand and later mechanisation.')],
'Factor prices, domestic demand, engineering and other trading regions also matter; regional wage rankings do not by themselves adjudicate international wage comparisons.', 'An attributed historical mechanism, not a quantified necessary contribution of slavery to each invention. Export demand is not the same variable as investment finance.'),
claim(16,[5], 'Inikori’s discussion of Charles Grant’s 1821 testimony identifies asymmetric British and Indian tariff power as a contemporary concern alongside improvements in machinery.',
'scholarly-analysis','medium','mechanism-supported',[(13,'section IV, Charles Grant paragraph immediately preceding table 3','Reproduces an explicit contemporary argument about protection at home and political power over Indian imports.')],
'The testimony does not establish a tariff counterfactual for each cloth quality or exclude cost-driven competitive shifts.', 'Primary testimony is accessed through Inikori’s quotation via Chaudhuri; original parliamentary record not independently inspected. No causal magnitude assigned.'),
claim(17,[6], 'Japanese mills in the 1890s adapted ring spinning through a package involving cotton imports, mixed fibres, more preparation labour and a changed labour force, rather than merely copying American operating conditions.',
'scholarly-analysis','medium','mechanism-supported',[(14,'pp. 549–551, table 2, and conclusion p. 561','Combines order specifications with historical accounts of cotton preparation and workforce change.')],
'Cotton prices, yarn markets and suppliers changed concurrently; order specifications are not direct measurements of realised mill productivity.', 'Does not establish the separate effect of each component, or that the labour arrangements were freely chosen or beneficial to workers.'),
claim(18,[6], 'Between 1878 and 1914 mule and ring spinning both continued to improve; Saxonhouse and Wright interpret British mule persistence as a choice supported by skills and product flexibility, not simply stagnant technology.',
'scholarly-analysis','medium','contested',[(14,'pp. 537–542 and 552–554','Documents coexisting technologies, skill requirements and adoption models using changing technical frontiers.')],
'Rings later gained capabilities and mule performance growth slowed; rationality at one time does not demonstrate optimal long-run investment.', 'Technical specification proxies and nonexperimental firm-choice models do not isolate learning, and the authors’ strong claim about unavoidable British decline is not adopted here.'),
claim(19,[6], 'India supplied the largest number of high-draft machinery orders in Saxonhouse and Wright’s 1929–1933 dataset, a bounded counterexample to equating low wages with non-adoption of labour-saving equipment.',
'scholarly-analysis','medium','descriptive',[(14,'pp. 558–559, high-draft discussion','Reports destination ordering and qualifications to the labour-relations explanation.')],
'Order count is not an installed-stock share or necessarily a comparable fraction of each country’s capacity.', 'Restricted to the supplier dataset and interval; the paper’s proposed male-workforce/labour-relations mechanism remains tentative.'),
claim(20,[7], 'In late Qing and Republican China, some handweavers combined machine-spun warp with hand-spun weft, and cheaper factory yarn also supported handloom weaving in new districts.',
'scholarly-analysis','medium','mechanism-supported',[(15,'pp. 373–374, notes 23–27','Describes mixed yarn use, Dingxian and geographical expansion of hand weaving.')],
'Hand spinning declined and factory cloth increased its share; hybrid persistence differed by region and product.', 'Earlier studies underlying Eyferth’s historical background were not independently acquired; no nationwide adoption rate is inferred from the examples.'),
claim(21,[7], 'Eyferth reports that handloom cloth accounted for about 70 percent of China’s cotton textile output in 1934–1936, despite the expansion of factory production.',
'scholarly-analysis','medium','descriptive',[(15,'p. 374, estimate and note 28','Provides the bounded period and output denominator for the reported estimate.')],
'Handloom market share was declining and aggregation may mask regional variation; the underlying estimation method was not audited.', 'An attributed estimate from earlier research, not a newly verified census; cannot equate output share with employment share or household welfare.'),
claim(22,[7], 'Eyferth documents moral and gendered classifications of textile work in late imperial and Republican China, including reform rhetoric that rendered household female production economically invisible.',
'scholarly-analysis','medium','descriptive',[(15,'pp. 369–373, “Imagining a new national economy”','Contrasts gendered household ideals, diverse practice and later reformist definitions of productive work.')],
'Actual household divisions were more varied than prescriptive discourse; beliefs alone need not explain persistence when cash, prices and employment differ.', 'Documents classifications and interpretation, not freely expressed worker preferences. Post-1949 rationing mechanisms are excluded from this pre-1950 case.'),
claim(23,[8], 'American factory electrification included distinct line-shaft, group-drive and unit-drive arrangements; replacing a prime mover with a motor did not automatically reorganise factory power distribution.',
'scholarly-analysis','high','descriptive',[(16,'pp. 353–363, figure 2 and line-shaft/group-drive sections','Documents the configurations, early retrofits and the functional differences.')],
'Group drive remained useful in some applications, and older configurations survived beyond the main transition.', 'The engineering distinction is well documented; it supplies neither an exact date for universal replacement nor proof that all firms benefited from unit drive.'),
claim(24,[8], 'Devine links effective unit-drive use to compatible machinery, production redesign, utility expansion and application services, with sunk onsite equipment differentiating retrofits from new plants.',
'scholarly-analysis','medium','mechanism-supported',[(16,'pp. 363, 368–371; machine redesign and Detroit Edison paragraphs','Describes indirect production benefits, compatibility constraints and services offered with electricity.')],
'Firms varied in load, process and existing capital; some group-drive choices remained justified. Expanding firms may have selected electrification.', 'Not causal identification of all postwar productivity gains; worker pace, discretion and welfare are not assessed by the engineering evidence.'),
claim(25,[8], 'Devine reports that electric motors represented roughly one-quarter of US manufacturing mechanical-drive horsepower in 1909 and over half in 1919; he separately infers unit-drive diffusion because comprehensive configuration statistics were unavailable.',
'scholarly-analysis','medium','descriptive',[(16,'pp. 368–370, “Market penetration”','Provides the capacity denominator and explains indirect evidence for unit-drive timing.')],
'Installed capacity is not utilisation, output, establishment adoption or the source of electricity generation.', 'Reuses the bounded historical series, not a reconstructed census; motor adoption must not be counted as complete factory redesign.')
]


def case(n,title,regions,period,domains,outcomes,summary,stages,mechanisms,counter,ks,ss):
    return dict(id=f'IND-C{n:02d}',title=title,region=regions,period=period,domain=domains,outcome=outcomes,
                summary=summary,stages=stages,mechanisms=mechanisms,counterevidence=counter,
                claim_ids=[f'IND-K{k:02d}' for k in ks],source_ids=[f'IND-S{s:02d}' for s in ss])

cases=[
case(1,'Central European mine pumping and remote mechanical power',['Erzgebirge','Harz','Central Europe'],'c. 1550–1700',['mining','hydraulic power','mechanical transmission'],['deployment','incremental improvement','coexistence'],
'Mines used a portfolio of human, animal and water power; remote rod transmission expanded the usable hydraulic choice set without requiring steam.',
{'invention':'Multiple devices predate the interval; exact priority for crank/rod combinations is disputed, not fixed here.',
'feasibility':'Agricola gives operating descriptions; later scholarship compares feasible direct and remote-drive arrangements.',
'deployment':'Named mine accounts and later depictions support installations; drawings alone are not a census.',
'diffusion':'Continued descriptions and installations provide qualitative evidence; no denominator established.',
'scaling':'Remote transmission allowed a stream to serve distant pumps; scale in total regional output unresolved.',
'non-adoption':'Site water, transmission expense and maintenance constrained individual choices; no general hydraulic absence inferred.',
'displacement':'Human, horse and hydraulic devices coexisted; no complete replacement date established.'},
['site-specific power access','transmission engineering','repairability','capital and operating costs','provisioning and political security'],
'First-use dates and prevalence are uncertain; celebratory images can be selective; adequate hydraulics delaying steam remains a hypothesis.',[1,2],[1,2]),
case(2,'Coalfield and Cornish steam pumping, fuel economy and collective improvement',['Britain','Cornwall'],'1712–1850',['steam power','mining','innovation organisation'],['deployment','diffusion','incremental improvement','contested patent effects'],
'A fuel-intensive drainage technology occupied an early niche; fuel economy, information sharing and local financing changed viable applications.',
{'invention':'Newcomen’s workable atmospheric engine and Watt’s condenser are distinct stages; later high-pressure designs were further changes.',
'feasibility':'Atmospheric operation fitted early engineering capability; improved economy mattered in high-coal-cost Cornwall.',
'deployment':'Boulton and Watt erected Cornish pumping engines; original installation records accessed through Nuvolari.',
'diffusion':'Mine district reporting from 1811 supported comparisons; not a national count of all engines.',
'scaling':'Incremental efficiency and expanded investment accompanied district improvements; aggregate early steam impact remained small in Crafts’s accounting.',
'non-adoption':'Fuel cost could make early engines unattractive away from cheap-coal locations; engineering and royalties also mattered.',
'displacement':'Alternative compound and single-cylinder designs persisted; no universal extinction of earlier pumps inferred.'},
['fuel-price incentives','engineering improvement','cost-book investment','comparative performance reporting','patent and royalty arrangements','maintenance'],
'Patent expiry, reporting, high-pressure engines and investment were not independent shocks; duty is not mine profit.',[3,4,5,6],[3,4]),
case(3,'British textile mills choosing water, steam and collective reservoirs',['Greater Manchester','Mersey Basin','Britain'],'c. 1780–1850',['textiles','water power','steam power','infrastructure coordination'],['coexistence','partial displacement','non-deployment'],
'Local water scarcity, mixed-power operation and unbuilt reservoir schemes challenge a single national energy-price account.',
{'invention':'The relevant choice involved existing prime movers and proposed infrastructure, not a new first invention.',
'feasibility':'Hydrological potential differs from dependable and legally accessible power; reservoir technical feasibility is not audited here.',
'deployment':'Steam sometimes supplemented or recirculated water before replacing it.',
'diffusion':'The 1838 factory return and mill-location reconstruction indicate geographical variation, not uniform British adoption.',
'scaling':'Concentrated mills could exceed convenient local water supply; collective reservoirs were a possible but contingent response.',
'non-adoption':'Malm attributes non-realisation of major reservoir proposals partly to coordination requirements; abstract-only attribution.',
'displacement':'Steam gained in cotton districts while water remained viable elsewhere; no single national replacement moment.'},
['local hydrology','seasonal reliability','industrial concentration','collective financing','water rights and coordination','sunk locations'],
'Run-of-river reconstruction does not price reservoirs or determine initial industrial geography. Abstract-only access limits the coordination account.',[6,7,8],[4,5,6]),
case(4,'British spinning, factory organisation and machine-tool complements',['Britain','Lancashire','English textile districts'],'c. 1760–1850',['textiles','machine tools','labour organisation'],['mechanisation','factory expansion','household income displacement','coexisting skills'],
'Task-specific pay, product demands, power, precision machinery and control over work need separation when explaining mechanisation.',
{'invention':'Jennies, water frames and later mules/tools are distinct inventions; exact firsts and all development costs not reconstructed.',
'feasibility':'Repeatable operation required appropriate craft and engineering capabilities; small devices and complex machinery differed.',
'deployment':'Factory machinery and outwork were contemporary alternatives; Ure records managerial advocacy rather than a deployment census.',
'diffusion':'Displacement of hand spinning is established qualitatively in scholarship, with different fibre and regional trajectories.',
'scaling':'Machine tools and replacement parts supported repeated machine supply; labour recruitment and organisation remained necessary.',
'non-adoption':'Extending outwork or importing yarn could address capacity needs without immediate factory concentration.',
'displacement':'Hand-spinning income contracted while engineering skill demand expanded; complete deskilling is not inferred.'},
['relative wages contested','female and child labour','quality and productivity','labour control','precision engineering','maintenance supply','capital organisation'],
'Most hand-spinning pay observations concern wool; cotton time-use data are scarce. An anti-high-wage finding does not identify one alternative motive.',[9,10,11,12,15],[7,8,9,10,13]),
case(5,'India–Lancashire competition, colonial markets and uneven displacement',['India','Bengal','Coromandel','Lancashire','Atlantic markets'],'c. 1700–1900',['cotton textiles','global trade','colonial institutions'],['competitive reversal','uneven deindustrialisation','partial reindustrialisation'],
'Productivity, cotton/freight prices, domestic political and agricultural shocks, slavery-linked demand and asymmetric policy power offer interacting explanations.',
{'invention':'This case evaluates competitive diffusion and displacement rather than identifying a first machine.',
'feasibility':'British machinery could be feasible without immediately undercutting every Indian product after input and delivery costs.',
'deployment':'British mechanised output reached different export markets at different times; Indian manufacture predated this competition.',
'diffusion':'Trade and price reconstructions track competitive shifts; they are not uniform adoption rates for Indian producers.',
'scaling':'Expanding markets and raw-material supply interacted with machine productivity; colonial market access was politically shaped.',
'non-adoption':'Low wages alone are not accepted as a sufficient explanation for Indian production choices; capital and policy constraints need further study.',
'displacement':'Hand-spinning, export production, handloom weaving and later mill growth require separate series; universal destruction of handicrafts is not claimed.'},
['relative productivity and wages','raw cotton and transport','colonial tariff power','Atlantic demand and coerced production','political/agricultural disruption','quality-specific markets'],
'National aggregate estimates and wage units are fragile; a cost advantage does not identify market formation, and a coercive policy does not identify every product’s counterfactual.',[13,14,15,16],[11,12,13]),
case(6,'Rings, mules and adaptation in Japan, India and Britain',['Japan','India','Britain','United States (technology origin)'],'1878–1933',['cotton spinning','technology transfer','labour organisation'],['adaptation','coexistence','delayed displacement'],
'Imported spinning equipment was recombined with local cotton preparation, labour and skills; machine rankings changed over time.',
{'invention':'Ring and mule lineages predate the main comparison; high drafting later changed fibre control.',
'feasibility':'Product count, fibre length, preparation and operatives affected workable use.',
'deployment':'Supplier orders establish purchases; installation and realised utilisation are incompletely observed.',
'diffusion':'The study follows major British exporters’ records across countries, with defined coverage limits.',
'scaling':'Japanese mixed-cotton preparation expanded ring capability; supplier improvements widened the range of adopters.',
'non-adoption':'Mule purchases continued where skill and flexibility conferred advantages; this need not indicate stagnation.',
'displacement':'Ring gains and high drafting eroded mule applications in the 1920s; specialised persistence continued and is not reduced to a single switch date.'},
['cotton preparation','imported capital and technical services','learning and prior experience','skill specificity','workforce organisation','changing engineering frontier'],
'Orders and specifications differ from output; adoption regressions are not exogenous identification; Indian labour-relations explanation is explicitly tentative.',[17,18,19],[14]),
case(7,'Chinese household weaving and factory-yarn hybrids',['China','Dingxian','Lower Yangzi','North China','Central and western China'],'c. 1870–1949',['cotton textiles','household production','gender and labour'],['partial displacement','hybrid adoption','handloom persistence'],
'Factory yarn could displace hand spinning and support handloom weaving; household work also carried gendered meanings and constraints.',
{'invention':'Neither factory yarn nor the handloom is a new invention in this interval.',
'feasibility':'Different yarn characteristics supported selective combination of factory warp and hand-spun weft.',
'deployment':'Named districts and historical accounts describe hybrid use; exact household installations are not enumerated.',
'diffusion':'Eyferth reports continuing handloom output and spread with yarn access; underlying original surveys were not audited.',
'scaling':'Machine intermediates could extend hand production geographically, rather than only displace it.',
'non-adoption':'Cash, alternative earnings, product requirements and gender arrangements are candidate constraints; preferences cannot be inferred from persistence alone.',
'displacement':'Spinning declined faster than hand weaving; reported 1934–1936 handloom output share remains substantial.'},
['modular input substitution','fabric properties','market access','household cash and labour allocation','gender norms','measurement exclusion'],
'Main source studies a later period and uses earlier scholarship for this background. National quantities are estimates; post-1949 mechanisms are not projected backward.',[20,21,22],[15]),
case(8,'US manufacturing electrification and factory redesign',['United States'],'c. 1880–1930',['electricity','factory organisation','power transmission'],['diffusion','complementary redesign','coexistence'],
'Line-shaft replacement, group drive and unit drive were distinct arrangements; electricity service and machine redesign shaped their value.',
{'invention':'Electric motors and generation preceded broad industrial reorganisation; exact first-use claims are not needed here.',
'feasibility':'Reliable motor operation did not establish machine compatibility or economic superiority in every factory.',
'deployment':'Early motors often retained existing shafts; group and unit configurations followed and coexisted.',
'diffusion':'Motor horsepower shares are documented; unit-drive prevalence is inferred from technical sources, not comprehensively counted.',
'scaling':'Utility networks, equipment suppliers, installation advice and new factory design helped expansion.',
'non-adoption':'Existing onsite generation and group operations could make immediate conversion unattractive.',
'displacement':'Mechanical distribution was reduced over time; electric motors could still rely on steam-generated electricity.'},
['distributed control','machine compatibility','factory layout','utility economies and services','sunk capital','maintenance and downtime'],
'Engineering-focused sources underrepresent workers; aggregate productivity gains are not all independently assigned to electrification.',[23,24,25],[16])
]

nodes=[]
def node(n,label,kind,cases):
    nodes.append(dict(id=f'IND-T{n:02d}',label=label,kind=kind,case_ids=[f'IND-C{c:02d}' for c in cases]))
for row in [
(1,'Mine water pumping','technology',[1,2]),(2,'Dependable accessible waterpower','resource',[1,3]),
(3,'Remote rod transmission and maintainable components','complement',[1]),(4,'Human and animal hauling','technology',[1]),
(5,'Fuel-intensive atmospheric steam engine','technology',[2]),(6,'Low delivered coal cost at an early mine site','resource',[2]),
(7,'Fuel-efficient Cornish pumping engines','technology',[2]),(8,'Comparative engine reporting','practice',[2]),
(9,'Cost-book investment and overlapping mine ownership','institution',[2]),(10,'Watt patent and royalty regime','institution',[2]),
(11,'Steam in British textile mills','technology',[3]),(12,'Collective reservoir schemes','technology',[3]),
(13,'Collective financing and water-use coordination','institution',[3]),(14,'Mechanised British spinning','technology',[4,5]),
(15,'Precision skills, gauges and machine tools','complement',[4]),(16,'Cheap and controlled labour recruitment','practice',[4]),
(17,'Indian and Lancashire cotton-market competition','practice',[5]),(18,'Raw cotton supply and delivery costs','resource',[5]),
(19,'Colonial tariff authority and Atlantic market formation','institution',[5]),(20,'Japanese ring-spinning package','technology',[6]),
(21,'Imported cotton mixtures and preparation work','complement',[6]),(22,'Mule spinning and specific operative skills','technology',[6]),
(23,'High-draft fibre control','technology',[6]),(24,'Factory-spun cotton yarn','technology',[7]),
(25,'Chinese handloom weaving','technology',[7]),(26,'Chinese hand spinning','technology',[7]),
(27,'Household allocation and gender norms','institution',[7]),(28,'Electric line-shaft or group drive','technology',[8]),
(29,'Electric unit drive','technology',[8]),(30,'Compatible machines and reorganised production','complement',[8]),
(31,'Utilities and application services','institution',[8]),(32,'Existing onsite generation and shafts','complement',[8])]:node(*row)

edges=[]
def edge(a,b,relation,cases,ks,ss,confidence,qualification):
    edges.append(dict(id=f'IND-E{len(edges)+1:02d}',**{'from':f'IND-T{a:02d}','to':f'IND-T{b:02d}'},relation=relation,
                      case_ids=[f'IND-C{c:02d}' for c in cases],claim_ids=[f'IND-K{k:02d}' for k in ks],
                      source_ids=[f'IND-S{s:02d}' for s in ss],confidence=confidence,qualification=qualification))
edge(2,1,'enables',[1],[1,2],[1,2],'high','Hydraulic configurations only; mine pumping also used human and animal power. No universal water prerequisite.')
edge(3,1,'complements',[1],[1,2],[1,2],'medium','Remote transmission and repair features extend workable use; dates and prevalence remain uncertain.')
edge(4,1,'enables',[1],[1],[1],'high','A documented alternative prime mover for selected hauling and pumping arrangements, not a developmental stage all mines passed through.')
edge(6,5,'enables',[2],[3],[3],'medium','Economic support for fuel-intensive early applications, not a physical necessity or an explanation of all steam deployment.')
edge(7,5,'competes-with',[2],[3],[3],'medium','Fuel efficiency altered choice under dear coal; not an immediate universal replacement.')
edge(8,7,'complements',[2],[4],[3],'medium','Reporting and improvement co-occurred; other engineering and investment changes confound separate causal identification.')
edge(9,8,'enables',[2],[4],[3],'medium','Nuvolari’s district-specific incentive interpretation; overlapping ownership may internalise benefits of disclosure.')
edge(10,7,'constrains',[2],[5],[3],'medium','Attributed effect on rival development before 1800, not a claim that all patent protection always retards innovation.')
edge(11,2,'competes-with',[3],[7,8],[5,6],'medium','Steam and usable water were alternative power sources at particular mill locations; national potential is not the choice denominator.')
edge(11,2,'complements',[3],[7],[5],'medium','Steam engines sometimes recirculated water or supplemented hydraulic operation; coexistence is explicit.')
edge(12,2,'enables',[3],[8],[6],'low','Proposed reservoirs could expand usable water supply; non-built projects are not demonstrated deployments.')
edge(12,13,'depends-on',[3],[8],[6],'low','Malm’s abstract attributes non-realisation to collective funding and coordination; not independently verified scheme economics.')
edge(15,14,'complements',[4],[12],[10],'medium','Complex later machinery and repeat production benefited from precision capability; simple jennies did not require the full package.')
edge(16,14,'complements',[4],[10,11],[8,9],'medium','Labour supply and control enter the organisation of mechanised work; advocacy does not prove complete realised deskilling.')
edge(14,17,'enables',[5],[13],[11],'medium','Productivity changes could improve Lancashire competitiveness conditional on input prices, product and market access.')
edge(18,17,'constrains',[5],[13],[11],'medium','Raw cotton and delivery costs delayed some competitive shifts; not identical for all markets or cloth qualities.')
edge(19,17,'constrains',[5],[15,16],[13],'medium','Political power structured which competition was permitted; does not quantify policy’s share of industrial decline.')
edge(21,20,'complements',[6],[17],[14],'medium','Japanese adaptation combined fibres, preparation and labour; not every ring installation needed the same recipe.')
edge(20,22,'competes-with',[6],[17,18],[14],'medium','Relative capability and skills changed over time; coexistence before 1914 is part of the claim.')
edge(23,22,'displaces',[6],[19,18],[14],'medium','High drafting eroded selected mule advantages in the 1920s; specialist mule uses survived.')
edge(23,20,'complements',[6],[19],[14],'medium','Later fibre control widened ring applications; India’s orders show this beyond Japan, with dataset limits.')
edge(24,25,'complements',[7],[20],[15],'medium','Machine yarn was an input to some hand weaving; not all handlooms used the same yarn mixture.')
edge(24,26,'displaces',[7],[20,21],[15],'medium','Partial and uneven hand-spinning decline; retained hand-spun weft and household production are counterexamples to total displacement.')
edge(26,25,'complements',[7],[20],[15],'medium','Homespun weft could coexist with machine-spun warp; product properties and locality matter.')
edge(27,25,'complements',[7],[22],[15],'medium','An interpretive relationship concerning household organisation and social meanings; not evidence of freely chosen preference or sole causation.')
edge(29,28,'competes-with',[8],[23,24],[16],'high','Different electric distribution configurations could remain appropriate in different plants; not a universal sequence.')
edge(30,29,'complements',[8],[24],[16],'medium','Reorganisation and compatible machinery condition indirect benefits; complete redesign is not necessary for every motor installation.')
edge(31,29,'enables',[8],[24],[16],'medium','Utilities and engineering services promoted deployment; onsite generation remained an alternative.')
edge(32,29,'constrains',[8],[24],[16],'medium','Sunk equipment could make immediate conversion unattractive; the equipment did not physically prevent every retrofit.')
edge(28,32,'complements',[8],[23],[16],'high','Early electrification could retain shafts and use onsite generated electricity, illustrating partial adoption.')

save('sources.json',sources)
save('claims.json',claims)
save('cases.json',cases)
save('graph.json',dict(nodes=nodes,edges=edges))
print(f'Wrote {len(cases)} cases, {len(sources)} sources, {len(claims)} claims, {len(nodes)} nodes and {len(edges)} edges.')
