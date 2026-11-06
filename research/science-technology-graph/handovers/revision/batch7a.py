"""Ranked gaps 1–6: printing, maize, writing, microbial causation, vaccination, selection."""
from batch import *
from concurrent.futures import ThreadPoolExecutor

specs=[
 ('revision7-gutenberg-mainz','Gutenberg and his time: Mainz museum chronology','https://www.gutenberg.de/zeit/zeitleiste_gutenberg','1439; Vor 1450; 1452–1454 and 1454/55 entries','1450'),
 ('revision7-gutenberg-loc','Library of Congress Gutenberg guide','https://guides.loc.gov/gutenberg/introduction','Production and Piccolomini letter, 12 March 1455','1455'),
 ('revision7-maize-piperno-europepmc','Piperno et al. 2009, Central Balsas maize evidence','https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=EXT_ID:19307570&format=json&resultType=core','Abstract, Xihuatoxtla maize by 8,700 cal BP','8,700','abstract'),
 ('revision7-writing-met','Ira Spar: The Origins of Writing, Metropolitan Museum','https://www.metmuseum.org/essays/the-origins-of-writing','Uruk economic records; proto-cuneiform and 3200–3000 BCE stages','3200'),
 ('revision7-koch-foundation','Robert Koch Foundation: portrait and contribution','https://www.robert-koch-stiftung.de/en/about-the-foundation/portrait-of-robert-koch','Opening historical overview, specific microbial causation in 1876','1876'),
 ('revision7-koch-dhm','Deutsches Historisches Museum: Robert Koch chronology','https://www.dhm.de/lemo/biografie/robert-koch','1876 result and publication entry','1876'),
 ('revision7-jenner-rcpe','Royal College of Physicians of Edinburgh: Edward Jenner','https://www.rcpe.ac.uk/heritage/physicians-database/edward-jenner','1796 documented vaccination; 1798–1800 publications and adoption','1796'),
 ('revision7-darwin-cambridge','Darwin Correspondence Project: Natural selection','https://www.darwinproject.ac.uk/commentary/evolution/natural-selection','September 1838 formulation; 1842 sketch','1838'),
 ('revision7-darwin-wallace-1858','Darwin and Wallace joint 1858 paper, scholarly transcription','https://darwin-online.org.uk/converted/published/1858_species_F350.html','Read-date header; extracts and joint selection account','1858'),
]
notes={'revision7-writing-met':'The museum account describes Uruk administrative needs leading to economic records on clay. It dates early cuneiform stages to 3200–3000 BCE and distinguishes later consistent phonetic writing. Earlier tentative systems elsewhere are not treated as a dated Uruk origin. Raw capture returned HTTP 429; the live page was read successfully.'}
with ThreadPoolExecutor(max_workers=4) as pool:sources=list(pool.map(lambda a:capture_note(*a[:4],notes[a[0]]) if a[0] in notes else capture_source(*a),specs))
metadata={'revision7-gutenberg-mainz': {'authors': ['Gutenberg-Museum / Landeshauptstadt Mainz'], 'year': 'Undated web chronology'}, 'revision7-gutenberg-loc': {'authors': ['Library of Congress'], 'year': 'Undated resource guide'}, 'revision7-maize-piperno-europepmc': {'authors': ['Dolores R. Piperno', 'Anthony J. Ranere', 'Irene Holst', 'Jose Iriarte', 'Ruth Dickau'], 'year': 2009}, 'revision7-writing-met': {'authors': ['Ira Spar'], 'year': 2004}, 'revision7-koch-foundation': {'authors': ['Robert Koch Foundation'], 'year': 'Undated institutional portrait'}, 'revision7-koch-dhm': {'authors': ['Susanne Eckelmann / Deutsches Historisches Museum'], 'year': 2014}, 'revision7-jenner-rcpe': {'authors': ['Royal College of Physicians of Edinburgh'], 'year': 'Undated institutional biography'}, 'revision7-darwin-cambridge': {'authors': ['Darwin Correspondence Project, University of Cambridge'], 'year': 'Undated scholarly commentary'}, 'revision7-darwin-wallace-1858': {'authors': ['Charles Darwin', 'Alfred Russel Wallace'], 'year': 1858}}
for source in sources:source.update(metadata[source["id"]])
records=load();before=deepcopy(records);decisions={}
for s in sources:
    assert s['id'] not in index(records['sources']);records['sources'].append(s)
    decisions[s['id']]='Read the named passage directly; retained response hashed. Source scope/access distinguished from a global first or full lifecycle claim.'

ev=lambda sid,loc,claim:[evidence(sid,loc,claim)]
add_entry(records,decisions,'gap-gutenberg-metal-type-printing','Gutenberg’s metal-type printing system','technology',
    'Reusable cast-metal type combined with press printing in Gutenberg’s European production system; the Bible is a witness to the process, not the invention of all printing.',
    ['Mainz and Strasbourg, present-day Germany and France'],['printing','materials','mechanisms'],0,
    'The reproducible production system supported later publishing, religious debate, administration and scientific exchange over generations.',
    year_date(1450,'By approximately 1450','Mainz chronology places an attributed early print before 1450; exact fragment attribution and dating remain qualified.',True,True),
    ev('revision7-gutenberg-mainz','1439; Vor 1450 entries','Early practice is reconstructed before the Bible; the fragment’s exact date and place remain unresolved.'),
    year_date(1455,'By 12 March 1455','Piccolomini’s dated letter establishes examples offered and already sold by this date.',True),
    ev('revision7-gutenberg-loc','Piccolomini letter discussion','Printed quires and sales were reported by March 1455.'),
    'Frankfurt/Mainz book buyers and correspondents',basis='public_availability',
    uncertainty='The earlier chronology is a qualified institutional reconstruction, not a surviving dated press. Asian printing traditions precede it; no direct Asian-to-Mainz transmission is asserted.')
add_entry(records,decisions,'gap-domesticated-maize','Domesticated maize','technology',
    'Human-selected maize as a cultivated crop, evidenced by starch and phytolith remains at Xihuatoxtla; distinct from later alkaline cooking.',
    ['Central Balsas Valley, Mexico'],['agriculture'],0,
    'The domestic crop supports subsequent food production, settlement economies and crop systems across generations; rank concerns the crop capability, not one excavation.',
    year_date(-6750,'By approximately 6750 BCE','Reported 8,700 cal BP converted using the 1950 reference epoch and rounded; a known-by attestation, not a domestication onset.',True,True),
    ev('revision7-maize-piperno-europepmc','Abstract','Maize present by 8,700 cal BP; domestication is an earlier process, not dated by an exact first day.'),
    year_date(-6750,'By approximately 6750 BCE','Archaeological remains attest use in the named local community by the source-reported horizon.',True,True),
    ev('revision7-maize-piperno-europepmc','Abstract and grinding-stone figure descriptions','Local crop use is evidenced; no universal first cultivation claim.'),
    'Early Holocene Balsas food-processing communities',basis='practical_use',
    uncertainty='Abstract and figure descriptions were read; the full excavation chronology was not audited. The claim is a bound and does not represent all plant/animal domestication.')
add_entry(records,decisions,'gap-proto-cuneiform-recording','Proto-cuneiform economic recording','practice',
    'A structured system of signs and quantities recorded economic transactions on clay in the Uruk cultural setting; later phonetic writing is a separate development.',
    ['Southern Mesopotamia, present-day Iraq'],['accounting','knowledge-transmission'],0,
    'External written records support later administration, textual transmission and mathematical record keeping across generations; no single tablet inherits this consequence.',
    year_date(-3000,'Approximately 3200–3000 BCE','Museum account dates early proto-cuneiform stages to this interval; it is not a precise invention year.',False,True,-3200),
    ev('revision7-writing-met','Uruk economic records and early cuneiform stages','Early administrative sign systems precede consistent phonetic writing.'),
    year_date(-3000,'Approximately 3200–3000 BCE','Economic recording attests administrative practice in the named community, not later museum discovery.',False,True,-3200),
    ev('revision7-writing-met','Uruk estates and recording economic data','Clay records served economic administration.'),
    'Uruk administrative record keepers',basis='practical_use',
    uncertainty='This represents one independently scoped early writing history. Other early systems and tentative earlier finds are not claimed to descend from it.')
add_entry(records,decisions,'gap-specific-microbial-causation','Specific microbial causation of disease','science',
    'Koch’s 1876 evidence tied a particular infectious disease to a specific microorganism, contributing to experimental microbial causation rather than merely associating microbes with illness.',
    ['Wollstein, present-day Wolsztyn, Poland'],['medicine'],0,
    'Specific microbial causation supports successive diagnostic, preventive and therapeutic research programmes; it is not the whole history of germ theory.',
    year_date(1876,'1876','Foundation historical account explicitly dates the specific-causation result to 1876.'),
    ev('revision7-koch-foundation','Opening scientific contribution paragraph','Specific microbial causation was demonstrated in 1876.'),
    year_date(1876,'1876 publication','The museum chronology explicitly records publication of the results in Beiträge zur Biologie der Pflanzen in 1876.'),
    ev('revision7-koch-dhm','1876 entry, publication sentence','The result was published in 1876; public awareness is distinct from acceptance.'),
    'Nineteenth-century bacteriological readers',
    uncertainty='High-level historical result only. Pasteur’s fermentation and Lister’s earlier antiseptic reasoning are independent missing parts; no anachronistic Koch-to-earlier-Lister link is drawn.')
add_entry(records,decisions,'gap-jenner-vaccination','Jenner’s cowpox-based vaccination','technology',
    'A preventive vaccination approach documented by Jenner in 1796 and published from 1798; distinct from earlier smallpox variolation and other earlier cowpox practices.',
    ['Berkeley, Gloucestershire, England'],['medicine'],0,
    'The preventive approach underlies later vaccination programmes and generations of infectious-disease prevention, beyond a single experimental recipient.',
    year_date(1796,'1796','RCPE dates Jenner’s documented vaccination result to 1796; no worldwide first vaccination is inferred.'),
    ev('revision7-jenner-rcpe','Main biography, first documented 1796 and subsequent publications','Dates the documented approach and its later published dissemination.'),
    year_date(1798,'1798','The first of Jenner’s 1798–1800 publications provided a public medical awareness opportunity.'),
    ev('revision7-jenner-rcpe','1798–1800 publications and translation paragraph','Published dissemination is distinct from the 1796 episode.'),
    'Medical readers of Jenner’s published accounts',uncertainty='This is historical description, not medical instructions or current clinical guidance. Earlier practitioners and later vaccine identities are not merged into one origin.')
add_entry(records,decisions,'gap-natural-selection','Natural selection as an evolutionary mechanism','science',
    'Heritable variation and differential survival/reproduction provide a natural mechanism of adaptive change; Darwin’s recorded formulation and Wallace’s later independent account are distinguished.',
    ['Britain','Malay Archipelago'],['evolution'],0,
    'The explanatory mechanism underlies subsequent evolutionary biology, ecology and population research across generations, independently of a particular surviving notebook.',
    year_date(1838,'September 1838 (recorded formulation)','Cambridge’s correspondence project dates Darwin’s formulation to September 1838; no universal priority over every earlier proposal is asserted.'),
    ev('revision7-darwin-cambridge','Natural selection, September 1838 paragraph','Dated formulation rather than the later 1859 book or modern custody of a notebook.'),
    year_date(1858,'1 July 1858 presentation','Joint Darwin–Wallace paper records its reading on 1 July and subsequent August publication.'),
    ev('revision7-darwin-wallace-1858','Record header and Lyell/Hooker introduction','Joint public presentation and distinct prior formulations.'),
    'Linnean Society naturalists',uncertainty='The private formulation is retrospectively reconstructed. Earlier independent selection proposals and the detailed chronology of individual notebook pages are not settled by this entry.')

finish('stage7a',before,records,decisions,'First ranked gap batch: six separate achievements from priorities 1, 3–6. Paper was already supplied. All source passages read; no speculative new connections.')
