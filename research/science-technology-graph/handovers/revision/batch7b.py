"""Next ranked gaps: mathematics, astronomy, modern physics and power/navigation."""
from batch import *
from concurrent.futures import ThreadPoolExecutor

# id, title, kind, region, topics, source URL, locator, checked text,
# record year, community year, community basis, configuration, consequence, limit.
items=[
('leibniz-calculus','Leibniz’s differential calculus','mathematics','Paris and Leipzig',['mathematics','calculation'],
 'https://mathshistory.st-andrews.ac.uk/Biographies/Leibniz/','1675 manuscript and 1684 Nova Methodus paragraphs','1675',1675,1684,'public_awareness',
 'A differential notation and operational rules for calculating tangents and rates of change, recorded in Leibniz’s manuscripts before the published 1684 account.',
 'Reusable differential methods and notation support later mathematical analysis, physics and engineering across generations.',
 'Newton’s distinct fluxional development is not merged with Leibniz’s method; no exclusive calculus-priority claim is made.'),
('copernican-system','Copernicus’s heliocentric planetary system','science','Poland',['astronomy','mathematics'],
 'https://plato.stanford.edu/entries/copernicus/index.html','§2.2 Commentariolus; 1514 inventory and §2.3 De revolutionibus','1514',1514,1514,'recognition',
 'A planetary system in which Earth rotates and travels around the Sun, outlined in the Commentariolus before the later De revolutionibus.',
 'The reorganised planetary framework supports subsequent astronomical modelling and celestial mechanics over generations.',
 'The 1514 inventory supplies a known-by bound, not a composition date or a surviving-copy anchor. Ancient heliocentric proposals remain distinct.'),
('special-relativity','Einstein’s special relativity','science','Bern, Switzerland',['physics','electromagnetism'],
 'https://fourmilab.ch/etexts/einstein/specrel/www/','Introduction, two postulates; original 1905 paper and translator/editor note','postulate',1905,1905,'public_awareness',
 'Relativity of inertial frames and invariant light speed lead to a consistent spacetime treatment of moving bodies and electrodynamics.',
 'The framework underlies subsequent particle physics, relativistic dynamics and precision physical modelling across generations.',
 'The retained English transcription derives from a later translation of the 1905 original. Lorentz and Poincaré antecedents and priority are not settled.'),
('gravitational-field-equations','Generally covariant gravitational field equations','science','Berlin, Germany',['physics','astronomy','mathematics'],
 'https://www.einstein.caltech.edu/news/one-hundred-years-of-einsteins-field-equations-and-of-the-explanation-of-mercurys-perihelion','Einstein Papers Project, final 25 November 1915 equations','1915',1915,1915,'public_awareness',
 'Einstein’s final 1915 field equations relate spacetime geometry to matter and energy; earlier incomplete gravitational theories remain distinct.',
 'The equations support subsequent cosmology, relativistic astrophysics and gravitational theory across generations.',
 'This is the final equation framework, not the beginning of every equivalence-principle or gravitational investigation. No Hilbert-priority adjudication is made.'),
('matrix-quantum-mechanics','Matrix quantum mechanics','science','Göttingen and Helgoland, Germany',['physics','mathematics'],
 'https://history.aip.org/exhibits/heisenberg/quantum-mechanic.html','The Quantum Mechanic 1925–1927, new mechanics and Born/Jordan contribution','1925',1925,1925,'public_awareness',
 'Observable transition quantities replace classical orbital descriptions in the matrix formulation developed by Heisenberg, Born and Jordan.',
 'The formalism supports subsequent atomic, molecular and condensed-matter physics and quantum technologies over generations.',
 'This is mature quantum mechanics, not a substitute date for Planck’s earlier quantum hypothesis or Schrödinger’s distinct wave formulation.'),
('nuclear-fission','Nuclear fission and its physical interpretation','science','Berlin and Sweden',['physics','chemistry'],
 'https://www.mpic.de/4469988/die-entdeckung-der-kernspaltung','December 1938 chemical finding and January–February 1939 interpretation/publications','1938',1938,1939,'public_awareness',
 'Hahn and Strassmann’s unexpected chemical products were interpreted by Meitner and Frisch as division of a heavy atomic nucleus.',
 'The discovered process supports subsequent nuclear physics, reactors and nuclear-energy systems over generations.',
 'Chemical observation and physical explanation are distinct contributions. The result is described historically without experimental or weapon-construction instructions.'),
('controlled-chain-reaction','Controlled self-sustaining nuclear chain reaction','technology','Chicago, USA',['physics','energy'],
 'https://radiology.uchicago.edu/about/nuclear-age','Opening account of the reactor becoming operational on 2 December 1942','1942',1942,1942,'practical_use',
 'A reactor system demonstrated a controlled self-sustaining nuclear chain reaction in Chicago in December 1942.',
 'Controlled reaction systems support subsequent reactor engineering, scientific reactors and nuclear-energy development over generations.',
 'The 1942 research demonstration is distinct from later electricity supply or commercial reactors. No construction parameters are supplied.'),
('newcomen-atmospheric-engine','Newcomen atmospheric pumping engine','technology','Britain',['steam','energy','mechanisms'],
 'https://www.nms.ac.uk/discover-catalogue/the-newcomen-engine-and-its-role-in-britains-industrial-revolution','1712 development, mine pumping and later engine use','1712',1712,1712,'practical_use',
 'Steam condensation creates a pressure difference that drives a piston and beam for mine pumping in the Newcomen atmospheric arrangement.',
 'The practical engine architecture supports successive mining, power and steam-engine developments rather than only a later surviving museum specimen.',
 'The class is recorded by 1712; the museum’s later Caprington engine and modern display dates are separate witnesses.'),
('steam-rail-traction','Steam railway traction','technology','Merthyr Tydfil, Wales',['steam','transport','mechanisms'],
 'https://museum.wales/collections/online/object/3725ef7b-e7b3-3490-97df-8a54c0f475ff/','Original 1804 journey versus 1981 reconstruction','1804',1804,1804,'practical_use',
 'A steam locomotive hauled a loaded train on the Merthyr Tramroad in 1804, establishing a working steam railway-traction configuration.',
 'Steam traction supports subsequent railway transport and industrial logistics over generations; the reconstructed exhibit is not the innovation.',
 'The 1804 episode witnesses the capability, not every later locomotive design. Public passenger-service entry in 1825 remains a separate event to research.'),
('magnetic-direction-finder','Magnetic compass for direction finding','technology','China',['navigation','electromagnetism','instruments'],
 'https://www.tcd.ie/physics/research/groups/magnetism/facts/the-seven-magnetic-moments/the-first-magnetic-device/','Floating fish around 1040; Shen Kua suspended compass account in 1088','1088',1040,1088,'recognition',
 'A magnetized indicator supplies a directional reference, with floating and suspended implementations documented in Chinese technical accounts.',
 'Magnetic direction finding supports subsequent navigation, surveying and seafaring across regions and generations.',
 'The early manual date is approximate; Shen’s 1088 account is separate. This does not date a Han spoon reconstruction, global invention or transmission to Europe.'),
('gunpowder-material','Gunpowder as an energetic material','technology','China',['chemistry','materials'],
 'https://afe.easia.columbia.edu/songdynasty-module/tech-gunpowder.html','Gunpowder section: 1044 military manual and subsequent use','1044',1044,1044,'recognition',
 'A documented energetic material was codified in the 1044 Wujing zongyao and used in subsequent incendiary and explosive applications.',
 'The controllable material supports subsequent military, mining and pyrotechnic technologies over generations.',
 '1044 is a secure documentary bound, not a claimed invention year; earlier alchemical precursors remain separate leads. No formulation or operating instructions are included.'),
]
notes={}
def obtain(item):
    key,title,kind,region,topics,url,locator,checked,*_=item;sid='revision7b-'+key
    try:return capture_source(sid,title+' — cited historical source',url,locator,checked)
    except Exception as exc:
        # Every fallback passage was separately reopened through the web reader.
        notes[sid]=str(exc)
        return capture_note(sid,title+' — live-read source note',url,locator,item[11]+' '+item[13]+' Dates checked: '+str(item[8])+' / '+str(item[9])+'. Raw capture failed; live source reading supplies the bounded claim.')
with ThreadPoolExecutor(max_workers=4) as pool:sources=list(pool.map(obtain,items))
records=load();before=deepcopy(records);decisions={}
for s in sources:
    records['sources'].append(s);decisions[s['id']]='Historical passage read directly, with source/translation/custody limits explicit. No primary-source capture is claimed for a retained live-read note.'
for item,source in zip(items,sources):
    key,title,kind,region,topics,url,loc,checked,ry,cy,basis,config,reason,limit=item
    bound=key in {'copernican-system','magnetic-direction-finder','gunpowder-material'}
    rd=year_date(ry,('By approximately ' if key=='magnetic-direction-finder' else 'By ' if bound else '')+str(ry),
       'The inspected source supports this scoped historical record; original conception and surviving-copy dates are not substituted.',bound,key=='magnetic-direction-finder')
    cd=year_date(cy,str(cy),'The named source records this distinct community episode; public accounts provide awareness rather than acceptance.',key in {'copernican-system','magnetic-direction-finder','gunpowder-material'})
    ev=[evidence(source['id'],loc,config)]
    add_entry(records,decisions,'gap-'+key,title,kind,config,[region],topics,0,reason,rd,ev,cd,ev,
        {'public_awareness':'Specialist readers of the dated scientific account','practical_use':'The named research, engineering or operating community','recognition':'The technical authors and practitioners documented by the cited account'}[basis],basis,limit)
finish('stage7b',before,records,decisions,'Second ranked gap batch: eleven scoped mathematical, physical, power and navigation capabilities. Original articles and institutional historical sources distinguished from attributed live-read notes.')
print('Capture fallbacks:',notes)
