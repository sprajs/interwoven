"""Serialize this reviewer's assessments, preserving source and coverage limits.

This is report assembly, not an automatic historical fact checker. The prose
assessments below are the audit. Inputs are pinned in scope.json.
"""
import collections
import hashlib
import json
import re
from pathlib import Path

from audit_support import ROOT, OUT, records, pinned_text

sources = {x['id']: x for x in records('sources')}
nodes = records('nodes')
relationships = records('relationships')
events = {x['id']: x for x in records('events')}
web = ROOT.parents[1] / 'web'

# One distinct assessment per relationship, in the frozen input order.
NOTES = '''
Wyatt is actually cited alongside Chargaff; the compositional constraint is neither a structural proof nor an exclusive ancestry.
The original two-page scan distinguishes observed diffraction from the qualified inference of a helix and two chains.
The production account explicitly lists dye terminators and permits different centre-specific reagents.
The enzyme preparation and incorporation assay are real experimental tools; the later copying interpretation is a separate result.
The consortium describes mapped-clone production and the 7 October 2000 draft snapshot, with assembly and coverage limits.
Kornberg explicitly invokes complementary pairing to interpret synthesis; the enzyme search is not attributed exclusively to that model.
The phiX174 abstract explicitly names plus/minus; it does not assign every confirmation experiment to that method.
The 1977 opening describes the relation to plus/minus and also names inhibitor chemistry and competing methods.
The consortium explicitly credits four-colour fluorescence and Smith; it does not claim unchanged use of Smith's first machine.
Primer extension is a functional requirement of this assay, not a proof that knowledge of a particular lecture was historically necessary.
The Prober abstract describes modified dideoxy chemistry with four fluorescent terminators; independent transfer details remain unproved.
Last's chronology and the contemporary market notice distinguish prototype feasibility, sample availability and uncertain earliest sold isolation.
The planar prototype and later 2N1613 commercial product are connected without identifying them as the same die or polarity.
The original report identifies the twenty-trough supply and explicitly permits a sufficiently strong smaller supply.
Marconi explicitly names and modifies the Branly detector; this does not settle all priority claims.
Hertz's account identifies the dielectric problem, abandoned approaches and the contingent spark technique; theoretical guidance is qualified.
Hertz describes reinforced and extinguished secondary sparks near reflecting walls; the record excludes his problematic velocity estimates.
Marconi explicitly begins with a Hertz oscillator; borrowing a design tradition is distinguished from reusing Hertz's own object.
Maxwell names the induction investigations of Faraday and Felici; a ring experiment represents a programme, not its sole cause.
Marconi's retrospective sequence explicitly distinguishes the earlier trials from the August aerial-and-earth arrangement.
Faraday paragraph 83 explicitly connects magnet-current tests with adapting Arago's experiment; he warns that the report rearranges experiments.
Hertz connects the prize problem to Maxwell's hypotheses through Helmholtz; direct reading of the 1864 paper is not established.
The CHM narrative explicitly says Last's project was based on Noyce's patent and Hoerni's process, with further fabrication work.
Ampere's translated sections 1 and 4 and the institutional history support the stimulus and distinct current-current experiment.
Maxwell's printed page 534 explicitly names Oersted's current-magnet observation among several empirical foundations.
The Royal Institution account connects replication of Oersted with Faraday's new rotation apparatus; it is a retrospective, not a complete diary audit.
The CHM account explicitly describes photoresist patterning on the Frosch-Derick oxide layer; overlapping year bounds are not a reversal.
The MOS account and Moore's section IV identify the oxide-interface obstacle and its reduction; universal elimination of surface states is not asserted.
The two working isolation approaches belong to the same programme; Last's recollection differs from the exact later September chronology.
CHM explicitly distinguishes the December 1957 conception, January disclosure and March 1959 working device.
The Noyce patent really uses retained oxide as insulation under metal conductors; CHM supplies the connection to Hoerni's idea.
Last's project used the planar process; a commercial display anchor does not date the first technical availability of that process.
Faraday paragraph 39 explicitly tests whether formation of a magnet was essential; paragraph numbering is not treated as a laboratory calendar.
CHM distinguishes the 3708 circuit from silicon-gate expertise, Faggin's transfer and new logic-process features at Intel.
CHM connects Bardeen's surface-state explanation with the ensuing Bardeen-Brattain experiments without claiming full prediction of the amplifier.
Atalla's section 1.2 explicitly credits Bardeen's charge and space-charge framework; this is explanatory use, not transfer of a fabrication recipe.
The Barbegal studies explicitly describe detaching a previous city-supply branch and redirecting it to the mills.
Shen's translated item describes alternating forms and reheating for reuse within one reported operation, not a later independently dated invention.
The launched vessel and Mau's specific 1976 use are identified; the edge does not reverse the direction of Mau's learning.
Kane explicitly describes selection of widely distributed features for his conceptual design; this verifies use of a hypothesis, not its truth.
Kyselka's report describes the canoe as an experimental platform; it does not validate every navigational claim or the historical reconstruction.
Genz page 237 explicitly says Korent guided deployment sites; practical expertise affected sampling rather than being confirmed merely by co-presence.
Kyselka explicitly connects learning from Mau with testing at sea; the PVS history independently dates the teaching episode.
The DOI and publisher abstract could be reopened, but the cited construction-phase sections could not be inspected.
Kyselka connects planetarium latitude investigations to the voyage test; his reported performance is not independent experimental replication.
Procopius explicitly describes aqueduct failure, fodder constraints and installation of river-driven boat mills; physical reuse of specific hill-mill parts is unproved.
Procopius explicitly describes debris damage, chains and removal; defence against hostile boats was a major additional motive.
The translated Shen passage explicitly combines fired types, a coated iron board and a retaining frame; no surviving assembly is claimed.
Genz distinguishes recorded buoy spectra, navigation descriptions and inconclusive aspects of validation; this is not blanket validation of all wave concepts.
Dallinger explicitly distinguishes Powell and Lealand's own objective formula from eyepieces made on Abbe's plan.
The Blaenavon history identifies a changed lining for phosphorus-bearing feedstock, with further refinement and alternative ores.
The Jernkontoret account explicitly identifies practical application of the Bessemer method at Edsken; a particular licensing channel is not asserted.
Dallinger describes swapping compensating eyepieces onto his earlier objectives and qualifies the claimed advantage of the new objective alone.
Faraday's introduction dates the RI installation and the later focus on heavy glasses; it does not identify each individual firing.
The LD history explicitly describes contact with Gerlafingen and Durrer's advice before the separate Linz operating adjustment.
Faraday paragraph 2151 explicitly identifies his earlier heavy glass and its role in the first successful magnetic rotation observation.
The Zeiss catalogue scan explicitly joins new glass materials with new lens formulae; Abbe describes the research and industrial supply.
The ASME history connects successful converter trials with subsequent production-plant construction; it is a project sequence, not inevitability.
The Zeiss scan and Abbe pages 25-26 establish coordinated objective-eyepiece correction, not a chronological invention order between components.
The metallurgical analysis identifies the CB3 bronze head and treated iron shaft; the exact assembly process remains an interpretation.
Abbe explicitly connects systematic measurements with synthesis of glasses having desired optical properties and the supply operation.
Dallinger identifies the loaned objective and later supplied series and reports qualified comparisons with his existing optics.
Galileo reports Dutch news and Paris confirmation; Van Helden discusses other information channels and instrument circulation, not a proven personal Lipperhey contact.
Whipple explicitly describes two Gunter scales moved together and the elimination of dividers, with cautious dating.
The Briggs biography records reading, discussion, visits and the 1617 tables, preserving collaborative credit.
The museum accounts explicitly explain logarithmic distances embodied in Gunter's instrument; the original numerical normalization is not required.
The Whipple object record explicitly describes Allen's influence, fixed scales and paired radial arms; the separate Oxford witness is not conflated.
Newton explicitly says differential refrangibility prompted reflection and a built reflector; his general conclusion about refractors is not endorsed.
Galileo's January narrative distinguishes initial observation, repeated changing positions and the satellite inference.
Galileo's lunar passage explicitly distinguishes resolved light-shadow details from the inference of relief.
Al-Hawari's introduction and worked addition really elaborate his teacher's rules during a named teaching relationship.
Thomann pages 174-175 describe ink-and-paper methods using mixed numerals; broad later deployment remains unknown.
Leonardo's prologue connects learning at Bugia and later study with his book; no named Arabic teacher or exclusive text chain is established.
Folkerts distinguishes Liber Alchorismi from other related Latin redactions and describes expansion and reordering.
Folkerts explicitly distinguishes the lost Arabic work, a Latin translation and its later redactions and manuscript witnesses.
Andrew documents the supplier and reconstructs the machining arrangement with qualifications; the precise machine used on this cylinder is not established.
Joule describes the apparatus, thermometer calibration and correction measurements underlying the estimate, rather than treating digits as certified accuracy.
Clapeyron explicitly names Carnot and proposes mathematical reformulation; the retained caloric premise is correctly limited.
Clausius explicitly says he knew Carnot through Clapeyron and Thomson, including the later editorial distinction from subsequent direct reading.
Thomson's appendix explicitly compares Carnot and Clapeyron values with Regnault-derived numbers.
Thomson's 1848 footnote explicitly identifies his mediated access through Clapeyron and distinguishes the numerical input from Regnault.
Thomson credits Clausius while claiming an independently found proof; the print-versus-presentation endpoint needs tighter binding.
The specification connects alternate driving strokes and condensation passages within Watt's design; no working demonstration follows merely from a patent.
The expansion specification reuses the hot-cylinder and condenser arrangement while adding cutoff; this is not a universal requirement for expansion.
The Soho catalogue describes both double action and the particular gear arrangement; continuous expansive operation is not inferred.
Joule explicitly traces his refined programme through earlier electrical, gas and friction work in the opening historical account.
Thomson section 29 uses Joule's refined equivalent; the historical reference-temperature convention differs and is already disclosed.
Clausius explicitly invokes Joule's experiments and cites the earlier magneto-electric equivalent; converted historical units are qualified.
Thomson explicitly cites Joule's 1843 work while retaining doubts about heat accounting, rather than unconditionally accepting the full interpretation.
Joule explicitly describes the new stationary magnet, reused rotating apparatus and later falling-weight measurement; the two apparatus configurations are not identical.
The museum and specification accounts distinguish model development from patent formalization; a unique determining prototype is not claimed.
Thomson section 3 explicitly uses Regnault's data as the planned numerical basis of his account.
Thomson explicitly requires latent heat, pressure and missing density information in comparing scales; this is not the fully modern Kelvin scale.
The Papplewick catalogue explicitly identifies the named sun-and-planet engine application; a drawing date is not an exact installation date.
The Soho catalogue explicitly identifies internal sun-and-planet gearing and the 1781 patent, supported by the specification.
Joule's 1843 postscript explicitly discusses Rumford; no instrument-copying channel is inferred.
The Soho catalogue explicitly states reassignment from corn milling to lathes and drills and leaves the exact conversion date open.
The archive history and Andrew describe the transfer and rebuilding programme; the patent text is not by itself a performance cause.
Clausius explicitly answers Thomson's doubts by allowing both consumption and transfer of heat.
Thomson section 6 explicitly reuses earlier numerical results under a changed theoretical foundation.
Andrew identifies the Wilkinson replacement cylinder and promising trials; exact machine and dimensional accuracy remain unproved.
Andrew describes the trials and subsequent new Bloomfield installation; the experimental engine was not simply moved to that colliery.
Carnot's note explicitly reproduces and criticizes Watt's expansion calculation, including the pressure-law and condensation assumptions.
Maxwell's pages 531-532 explicitly use Faraday's optical rotation and Thomson's interpretation; the mechanical medium is Maxwell's historical argument.
The mathematical scholarship identifies Liu Hui's engagement with the received Nine Chapters, while the exact traditional year remains qualified.
Chemla page 21 explicitly describes extending the chapter 8 algorithm's application by interpreting the sequence of problems.
Chemla identifies the Li Chunfeng group and the subcommentary; the live 2020 paper also warns about blurred textual layers.
Djebbar explicitly identifies al-Qurashi's commentary on Abu Kamil and the indirect survival of fragments and testimony.
The archaeological project explicitly identifies the inlet as a component of the Great Hafir; independent component phasing is unresolved.
The project explicitly identifies ducts from both reservoirs to the Great Enclosure, without separately dating their full routes.
The water-history paragraph associates the repaired dam and irrigation in one inscriptional context; it does not establish a detailed hydraulic dependency.
The road scholarship and Smithsonian account identify chaski use of the road network; surviving installations are not all functionally homogeneous.
The accounts identify messenger exchange at replacement posts; distances and identification of individual archaeological buildings remain variable.
The Koh Ker study identifies the two outlets and their relationship to the reservoir; its failure modelling is not proof of political causation.
The Alcoa timeline explicitly identifies the supplier's aluminum in the Flyer engine; this corporate account is not a full metallurgical procurement record.
The museum account explicitly identifies DuPont nylon bristles in Dr West's toothbrush; production batches and first bulk supply are not established.
The Board of Longitude resource explicitly identifies the commissioned H4 copy and 1769 completion of K1.
The reopened RMG description calls K2 a simplified H4/K1 version, not proof that each part descended from K1 alone.
Smiles explicitly places expansive working at Shadwell before the patent; the 1781 letter separately mentions Shadwell and expansive experiments at Soho.
The reopened museum object description places the coaking machine within the Portsmouth machine sequence; it is component membership, not influence of a completed mill on its earlier parts.
The Cambridge chronology explicitly describes the 1947 agreement to use EDSAC experience for LEO; the later display anchors are not that transfer date.
Field describes technical investigation after failure, renewed companies and later construction improvements; continuity is of the enterprise, not a single unchanged legal company.
The reports support the current-needle mechanism used in this telegraph family; the discovery event and a physical law are distinct referents.
The electricity chronology explicitly says the exhibition gave impetus to Niagara; the detailed decision pathway is not independently documented here.
The National Academies chapter explicitly describes modified expression, scale-up, pilot plants and Lilly commercialization; its first-sale year differs from other accounts already disclosed in the node.
The original Smith exhibit could not be retrieved beyond the initial cached web page; its cited Strategy and reference passage could not be independently inspected.
The Ebola methods explicitly name a one-step RT-PCR system with Platinum Taq and subsequent MinION library preparation; the 1989 study is not a demonstrated personal transmission channel.
The 1941 report really uses pH in production and extraction research, but that is a broader referent than the particular clinical trial and treatment event.
The early acidimeter patent explicitly describes pH determination; requiring a pH convention for a pH reading is not requiring a particular textbook to build the electronics.
The court's account of the 1949 memo identifies a Bessemer converter and vertical oxygen blowing; this is vessel/process adaptation rather than evidence of unchanged original air-blowing practice.
Moore explicitly connects Fairchild's research response to the MOS presentation; CHM separately identifies the later silicon-gate multiplexer and intervening contributors.
'''.strip().splitlines()
assert len(NOTES) == len(relationships) == 131

CHANGES = {
 'bio-base-ratios-to-double-helix': ('medium', 'modelling_choice', 'The evidence is a compositional constraint used in model reasoning, not a physical combination of components.', 'Retain the connection, but distinguish evidential contribution to a model from physical used-together/part-of edges; do not reverse it.'),
 'bio-model-to-template-interpretation': ('low', 'modelling_choice', 'Documented-development does not distinguish theoretical interpretation from a technical development lineage.', 'Retain with an interpretation/evidential-role facet; do not recode as theory-informs-design because the target is a scientific interpretation.'),
 'elec-physical-to-junction-isolation': ('medium', 'evidence_limit', 'The sequence is supported, but the exact September date in the endpoint label differs from Last\'s tentative October/November recollection in src-chm-sector PDF pp. 84-85.', 'Keep the programme link. Reconcile the dated notebook/report chronology with the recollection before presenting the exact day as independently settled.'),
 'global-korent-to-buoy-placement': ('medium', 'modelling_choice', 'Observed-combination conceals the directional role of navigator expertise in choosing sampling sites.', 'Retain as practice-informs-investigation or an explicit sampling-design contribution facet, alongside any separate used-with relation.'),
 'mat-objectives-with-compensating-eyepieces': ('medium', 'modelling_choice', 'The supported relationship is coordinated use; arbitrary orientation must not be interpreted as an earlier invention causing a later one.', 'Mark as nonchronological used-with, or identify a named combined configuration with component roles. No chronological reversal is proposed.'),
 'mech-clausius-to-thomson-dynamical': ('high', 'evidence_limit', 'The source event is unresolved and the target is the 1851 presentation, whereas the cited wording is established in print; the selected source anchor is 1852 recognition.', 'Bind the source to the existing 1850 publication event and the target to the relevant printed formulation event, or explicitly leave the oral-presentation claim unverified. Retain the independent-proof qualification.'),
 'mech-blockmill-to-coaking': ('medium', 'modelling_choice', 'The direction from integrated system to its component is membership, not a development of that component caused by the completed mill.', 'Retain as part-of/contains with explicit nonchronological semantics; avoid inventing an influence sequence.'),
 'entry-electronics-edsac-informs-leo': ('medium', 'modelling_choice', 'Neither endpoint identifies the transfer event: the 1950 service anchor follows the documented 1947 exchange.', 'Keep the lineage but bind it to the 1947 agreement/development episode and the receiving development episode. The display anchor should remain a separate question.'),
 'chem-ph-scale-to-oxford-penicillin': ('high', 'modelling_choice', 'The cited production/extraction work establishes use of pH in the Oxford programme, not its documented role in the specifically anchored 12 February clinical treatment.', 'Redirect to a properly scoped penicillin-production/research configuration or a matching programme event, if later approved. Until then describe this as contextual programme association, not verified trial-specific combination.'),
 'mat-bessemer-to-gerlafingen-converter': ('medium', 'modelling_choice', 'Reuse of a Bessemer-type vessel with changed gas and blowing geometry is an adaptation; development alone obscures that change.', 'Prefer documented-adaptation with vessel reuse and changed oxygen-blowing geometry explicit; preserve the court-account limitation and do not infer the 1948 vessel identity.'),
}

UNVERIFIED = {
 'global-muldoons-channel-to-walls': 'The publisher abstract does not expose sections 3.9 and 4.1-4.3, which are needed to check the physical phase relationship. DOI access failed and no retained full text exists.',
 'bio-termination-to-fluorescent-primer': 'The retained source is an index/research note rather than the original Strategy passage. Reopening the USPTO exhibit returned HTTP 403. The Smith abstract verifies the readout but not the cited adaptation/reference passage.',
}

unverified_sources = {'global-mcniven-condah-2012', 'entry-molecular-smith-1986-exhibit'}
live_sources = {'bio-wyatt-1952','entry-elec-smg-blackwall','entry-regional-source-unesco-inca','entry-regional-source-smithsonian-chaski','entry-exp-calculation-chemla-2020','entry-mech-k2-rmg','entry-mech-coaking-smg','entry-materials-gap08-court-1949'}
checked_sources = {e['source_id'] for r in relationships for e in r['evidence']} - unverified_sources
checked_sources.update('bio-smith-1986 entry-molecular-hart-2015 entry-molecular-kung-1980 entry-calculation-reception-bell elec-volta-abstract global-dholavira-icomos global-jikji-bnf src-google-ee2-2019 mat-gerzeh-2013 mat-bebber-2022 mat-merv-1997 mat-wagner-cofusion entry-exp-calculation-b6063 entry-exp-calculation-ybc7289 entry-exp-calculation-zero entry-regional-source-keawanui entry-materials-exp-bronze entry-materials-exp-muza entry-materials-exp-maya entry-materials-exp-xing entry-materials-exp-gongxian entry-mech-double-expansive'.split())
checked_sources.update('elec-chm-kilby-solid-circuit global-diamond-sutra-idp global-roteiro-malindi-1498 mat-belovode-2014 entry-materials-bishop-1959 mat-ld-anniversary mat-bronze-2013 nonmarket-ra-museum src-zeiss-1885 entry-exp-calculation-rhind-museum entry-regional-source-unesco-subak entry-materials-exp-sinica-shang-jar entry-mech-ritti-2007 entry-mech-aljazari-met entry-mech-elsecar-ledger entry-mech-maudslay-lathe entry-elec-morse-service entry-elec-india-1855 entry-elec-cable-letter-1866 entry-elec-japan-1870 entry-elec-new-haven entry-elec-pearl-street entry-elec-lauffen entry-elec-colossus entry-elec-fortran entry-elec-web-primary-1991 entry-molecular-forbes-1824 entry-molecular-marshall-1870 entry-molecular-liston-1930 entry-molecular-oxford-timeline entry-molecular-maxam-1977 entry-molecular-galibert-1979'.split())
live_sources.update({'global-diamond-sutra-idp','entry-regional-source-unesco-subak','entry-materials-exp-sinica-shang-jar'})

# Specific later identity checks. The findings record the inspected passage, not
# an automatic conclusion from having extracted text from a shared source.
ENTRY_FINDINGS = {
 'elec-kilby-germanium-oscillator-1958':'CHM explicitly identifies the 12 September germanium oscillator and flying-wire connections, distinguishing the following amplifier and later commercial devices.',
 'global-diamond-sutra-paper-print-868':'Reopened the IDP page live: it identifies the dated 868 scroll, seven woodblock-printed paper sheets and an earlier printing tradition. The source supports the witness, not the invention of printing.',
 'global-malindi-assisted-passage-1498':'Reopened Roteiro pp.45–48: the king supplied the pilot, the fleet left on 24 April, and the pilot interpreted the coastal mountains. The narrative also reports a local identification error; guidance is not infallibility.',
 'mat-belovode-copper-smelting':'The archaeological paper describes slagged ceramics and small slag pieces in the excavation context as evidence of copper extraction. The identity is the evidenced process, not a universal first-smelter claim.',
 'mat-bessemer-air-conversion':'Bishop describes Göransson’s trials and commercial Bessemer ingots in the 1858–59 account; this supports the scoped air-conversion practice without resolving universal priority.',
 'mat-linz-ld-production':'The voestalpine anniversary account explicitly identifies operation of the Linz LD works on 27 November 1952. It is a corporate retrospective, not an independent operating-log audit.',
 'mat-plocnik-tainted-ore-bronze':'The 2013 paper identifies the Pločnik tin-bronze foil and interprets mixed copper/tin ore smelting. The inferred production route and contextual dating retain the paper’s qualifications.',
 'math-brahmagupta-zero-rules-628':'Another source, the inspected MacTutor zero-history passage, sets out Brahmagupta’s signed-number/zero rules and his problematic division statements. The node’s excluded division claim must remain excluded; the cited original Sanskrit witness was not reopened.',
 'nonmarket-ra-i-1969':'The museum account identifies the 1969 papyrus Ra built at Giza, the Safi departure and abandoned Atlantic attempt; it distinguishes this vessel from Ra II.',
 'zeiss-homogeneous-1-18':'Visually inspected the original 1885 catalogue excerpt: printed pp.31,35,37 (source PDF pp.36,40,42; excerpt pp.7–9) identify no.46, 1/18, 1.25 mm, prices and fixed/correction mounting. The catalogue also discloses a later working-distance improvement.',
 'math-rhind-worked-mathematics':'The museum object page identifies the Rhind papyrus’s worked arithmetic, fractions and geometry problems. Its museum dating is a witness date, not an invention date for all the procedures.',
 'entry-regional-bali-subak':'Reopened UNESCO’s description and synthesis live: cooperative water management, canals/weirs, rice cultivation, temples and collective institutions support the sociotechnical referent. Broad dating claims do not prove unchanged continuity of every component.',
 'mat-shang-anyang-burial-jar':'Reopened Academia Sinica’s Chinese object record live: lidded white pottery jar R000167 from Xiaotun tomb331, fragmented before burial, with described form and marks. This verifies the specimen, not a general pottery breakthrough.',
 'mech-hierapolis-geared-stone-saw':'The retained rendered article transcript describes the sarcophagus relief and proposed rotary-to-reciprocating reconstruction. Textual interpretation was read; the original figure was not independently inspected in this audit.',
 'mech-gerasa-water-stone-saw':'The retained Ritti article transcript describes the Gerasa saw-mill remains and qualified late-antique dating. A reconstructed drive is not a surviving complete working machine.',
 'mech-ephesos-water-stone-saw':'The retained Ritti article transcript identifies the Ephesos remains and discusses the saw-mill reconstruction. Textual support is bounded; the original figures and excavation record were not independently re-examined.',
 'mech-aljazari-donkey-water-lift-1315':'The retained Met object description identifies a 1315 manuscript folio and donkey-driven water-lifting design. This authenticates the represented configuration, not a demonstrated installation in 1315.',
 'mech-elsecar-newcomen-pump':'The museum’s ledger account identifies the Elsecar Newcomen pump and distinguishes its 1795 installation from later accounts. This is custodian documentary support, not a new audit of the original ledger.',
 'mech-maudslay-geared-screw-lathe':'The retained Science Museum description identifies the circa1800 geared screw-cutting lathe, screw feed and change-wheel function, while noting missing change wheels. It supports the object identity without a universal priority claim.',
 'entry-electronics-morse-public-telegraph-1845':'The USPS historical account explicitly places paid public service on the Washington–Baltimore line on 1 April1845. This does not validate every broad telegraph-priority assertion on that page.',
 'entry-electronics-india-public-telegraph-1855':'The scholarly book abstract identifies public opening on 1 February1855 and later press uptake. Scope is the stated service, not all electrical communication in India.',
 'entry-electronics-atlantic-cable-1866':'The contemporary Bigelow-to-Seward letter of 3 August1866 reports Field’s successful laying message and newspaper dispatches. This verifies the service episode alongside the existing continuation account, not every duration or tariff claim.',
 'entry-electronics-japan-tokyo-yokohama-1870':'NTT’s timeline identifies Tokyo–Yokohama service in1870. This supports the local installation/service referent, not an unqualified global priority.',
 'entry-electronics-new-haven-exchange-1878':'The object/history account identifies Coy’s New Haven exchange, 28 January1878 and21 subscribers. The scoped local episode is supported; expansive first-ever wording is not independently settled here.',
 'entry-electronics-pearl-street-1882':'The Census history identifies Pearl Street’s September1882 service and its initial local customers. This is support for the named station, not for the invention of electric supply.',
 'entry-electronics-lauffen-frankfurt-1891':'Kapp’s contemporary Western Electrician account describes the August demonstration, three-phase equipment, lamps and motor-driven waterfall. It supports the specified system and demonstration.',
 'entry-electronics-colossus-bletchley-1944':'The CHM account identifies Colossus’s1944 Bletchley Lorenz work and punched-tape processing. General performance claims are not independently benchmarked here.',
 'entry-electronics-ibm-fortran-1957':'IBM’s historical account identifies the1957 release and IBM704 compiler. This verifies the scoped compiler/service identity rather than the invention of every higher-level programming concept.',
 'entry-electronics-web-public-ftp-1991':'The original6 August1991 Usenet message identifies HTTP/WWW, anonymous FTP distribution and the available browser/editor/server implementations. This is public availability evidence, not mass adoption.',
 'med-forbes-stethoscope-chichester-1822':'Reopened Forbes CaseI: May24 is the initial case date; May28 explicitly records stethoscope examination, with later fuller examinations. The configured1822 clinical use is supported; do not silently date the instrument examination to May24.',
 'med-lister-antisepsis-preston-1869':'Visually read Marshall’s original BMJ p.457 scan: the August1869 injured-joint case explicitly credits Lister’s germ theory and ordinary-wound treatment and reports antiseptic treatment. The author’s favourable outcome is not independent modern efficacy proof.',
 'bio-penicillin-selective-culture-1929':'Liston’s1930 discussion explicitly credits Fleming’s1929 work and describes selective isolation use. This verifies the microbiological application; it does not establish clinical antibiotic treatment at that time.',
 'med-oxford-penicillin-1941':'Oxford’s historical timeline identifies the12 February1941 Albert Alexander treatment and subsequent shortage. This verifies the named clinical episode without using unrelated mechanism claims on the page.',
 'bio-maxam-gilbert-sequencing-1979':'The original method abstract identifies chemical cleavage sequencing, and the Galibert1979 abstract explicitly reports use of Maxam and Gilbert’s method on the adenovirus fragment. This separates method publication from later research uptake.',
}
ALTERNATE_NODE_SOURCES = {'math-brahmagupta-zero-rules-628':['entry-exp-calculation-zero']}

def source_basis(sid, locator=None):
    s = sources[sid]
    return {'source_id':sid, 'locator':locator, 'url':s.get('url'),
            'retained_path':s.get('local_copy',{}).get('path'),
            'retained_sha256':s.get('local_copy',{}).get('sha256'),
            'representation':s.get('local_copy',{}).get('representation', 'as retained; may be a rendered transcript or excerpt; inspect the path and source metadata'),
            'check':'cannot_verify' if sid in unverified_sources else 'bounded cited passage inspected',
            'route':'live cited source' if sid in live_sources else 'retained cited source reopened',
            'limit':'Passage-level check; not a full-document audit or independent replication of the source.'}

def event_basis(ep):
    explicit = ep.get('event_id')
    node = next(n for n in nodes if n['id']==ep['node_id'])
    e = events[explicit or node['graph_anchor']['event_id']]
    return {'node_id':ep['node_id'],'event_id':explicit,
            'fallback_anchor_for_comparison':None if explicit else e['id'],
            'date':e['date'], 'interpretation':'Event order must come from the source; a display anchor is not a causal date.'}

connection_rows = []
for r, note in zip(relationships, NOTES):
    rid=r['id']; change=CHANGES.get(rid)
    verdict='cannot_verify' if rid in UNVERIFIED else 'change' if change else 'agree'
    connection_rows.append({'id':rid,'verdict':verdict,
        'severity': 'medium' if rid in UNVERIFIED else change[0] if change else 'none',
        'issue':UNVERIFIED.get(rid) or (change[2] if change else 'Agree with the bounded historical statement, direction and current relation interpretation; no additional defect established.'),
        'proposed_change': 'No rejection warranted. Obtain and inspect the cited original passage before acceptance.' if rid in UNVERIFIED else change[3] if change else None,
        'basis':{'method':'reopened the cited source',
            'scope':'All connection records read individually; statements, directions, event bounds, types, confidence, necessity and alternatives considered. Reopened retained originals/excerpts or live cited source; prior reviews were not treated as evidence.',
            'finding':note,'historical_status':'cannot_verify' if rid in UNVERIFIED else 'supported_with_stated_limits',
            'issue_category':'evidence_limit' if rid in UNVERIFIED else change[1] if change else 'agreement',
            'sources':[source_basis(e['source_id'],e['locator']) for e in r['evidence']],
            'endpoint_check':{'from':event_basis(r['from']),'to':event_basis(r['to'])},
            'confidence_assessment':'Unresolved for the uninspected passage.' if rid in UNVERIFIED else 'Reasonable for the narrowly stated claim; not a probability of necessity or a guarantee of every embedded date.',
            'necessity_alternatives_assessment':'Read the record\'s explicit scope, alternatives and uncertainty. No additional universal or exclusive requirement accepted.'}})

# Tier changes are this reviewer's consequentiality judgement, not historical facts.
TIERS = {
 'bio-fluorescent-terminator-sequencing-1987':(1,'The widespread dye-terminator route is ranked below primer labelling without a consistent impact criterion.'),
 'bio-phix174-sequence-report-1977':(1,'An early complete genome sequence and overlapping coding regions merit the same broad-result tier as other consequential molecular results.'),
 'elec-ampere-parallel-currents-1820':(1,'The current-current force result is foundational across electrodynamics; calling it fine apparatus detail undervalues the scientific result.'),
 'global-barbegal-aqueduct-mills':(1,'A major industrial site is an exemplar of hydraulic production, rather than the general watermill breakthrough.'),
 'global-dholavira-reservoirs-stage3':(1,'A major regional hydraulic configuration is not by itself the general development of water management.'),
 'global-diamond-sutra-paper-print-868':(2,'The dated surviving printed scroll is a witness to already developed paper and woodblock practices; documentary survival is not the onset or total importance of printing.'),
 'global-hokulea-built-1975':(2,'This experimental reconstruction vessel should not carry the worldwide consequence of oceanic voyaging as a whole.'),
 'global-jikji-metal-type-1377':(1,'A major surviving Korean printing witness deserves prominence without equating its survival with the full movable-metal-type breakthrough.'),
 'global-mau-hokulea-passage-1976':(1,'A consequential cultural-revival voyage remains a particular use of much older navigation knowledge.'),
 'global-muldoons-channel-infill':(1,'A remarkable engineered witness should not be ranked as the single general invention of aquaculture; phase evidence remains unverified here.'),
 'mat-maya-blue-pigment':(1,'A consequential regional material deserves an intermediate tier; the current top-tier reasoning does not establish impact comparable with broadly enabling materials processes.'),
 'mat-alcoa-aluminum-supply':(1,'The supply business is a commercialization configuration, not the underlying broadly enabling electrolytic reduction process.'),
 'mat-nylon-filament-bristles':(2,'The scoped object is toothbrush-bristle filament, not nylon synthesis or the whole synthetic-polymer industry.'),
 'mat-egypt-glass-heart-amulet':(2,'The museum object witnesses a technique and funerary use; it is not evidence that this specific amulet transformed glassmaking.'),
 'mat-shang-anyang-burial-jar':(2,'A single burial object needs a demonstrated historical consequence to rank alongside major mathematical and physical methods.'),
 'mat-aluminum-teakettle-1895':(2,'A commercial application has no supplied impact argument sufficient for the same rank as enabling metalworking methods.'),
 'mat-dr-west-nylon-toothbrush':(2,'The named consumer product is an application and should not duplicate the importance assigned to its material platform.'),
 'math-brahmagupta-zero-rules-628':(0,'Explicit arithmetic on zero and signed quantities has broad mathematical consequence, independently of how late a reception witness is chosen.'),
 'math-nine-chapters-text':(1,'The structured mathematical canon has a broader role than the generic tier-2 documentary-witness rationale recognizes.'),
 'math-nine-chapters-fangcheng':(1,'Systematic elimination with signed quantities is a substantial computational method; its importance is not determined by the surviving commentary date.'),
 'math-euclid-greatest-common-measure':(1,'The general common-measure algorithm is more consequential than its particular later witness; explicit subtraction and later restricted examples remain distinguishable.'),
 'mech-bloomfield-pump-1776':(1,'A named commercial installation should not stand in for the total consequence of steam power or the separate condenser.'),
 'mech-condenser-model-1765':(0,'This node is scoped as the separate-condensation arrangement with a model witness; that general technical contribution is more consequential than one later installation.'),
 'mech-harrison-h4-watch':(1,'The practical marine timekeeper is more consequential for longitude than a generic specialist-object rationale suggests.'),
 'entry-regional-bali-subak':(1,'The durable cooperative irrigation system is a major sociotechnical configuration, not equivalent in scope to a single inlet or repair.'),
 'entry-regional-inca-qhapaq-nan':(1,'A state-scale transport and communications network should rank above an individual regional artifact or component.'),
 'entry-regional-inca-storehouse-quipu':(1,'Knotted-cord accounting is a substantial information technology; this rank is conditional on the node representing the practice rather than only one 1533 observation.'),
 'bio-crispr-cas9-fitness-screen-2015':(2,'The configuration is Hart\'s particular 2015 screen, explicitly not the general CRISPR-Cas9 editing breakthrough. Its top tier borrows importance from a broader missing identity.'),
}
KIND_CHANGES = {
 'math-khwarizmi-indian-arithmetic-825', 'math-latin-dixit-algorizmi-1100s',
 'math-latin-liber-alchorismi-1100s','math-liber-abaci-revision-1228','math-hawari-worked-arithmetic-1305'
}
IDENTITY_CHANGES = {
 'elec-hoerni-planar-transistor-1959':'The broad retained-oxide configuration explicitly encompasses the separately represented 2N1613. These are class and product scopes, not identical objects; make that containment explicit before counting breakthroughs.',
 'bio-recombinant-plasmid-cloning-1979':'A general cloning method is anchored by the specific insulin-expression use that supplies its only provenance source. Preserve the general-method versus particular-application distinction in the identity and add earlier evidence only after review.',
 'global-hokulea-built-1975':'An individual vessel, reconstruction programme and broader voyaging tradition must remain separate scopes; do not let its tier or outgoing uses turn this object into the origin of the tradition.',
 'mat-nylon-filament-bristles':'The specific bristle material and the complete Dr West toothbrush are distinct component/product identities, but neither should silently stand for all nylon. Clarify the scope at which breakthroughs are counted.',
}
IDENTITY_ACCESS_LIMITS = {
 'global-muldoons-channel-infill':'The publisher abstract was reopened, but not the cited excavation and construction-phase sections; the particular F10 excavated phase remains unverified.',
 'global-muldoons-walled-channel':'The publisher abstract was reopened, but not the cited wall and phasing sections; the particular multi-tiered F10 addition remains unverified.',
 'entry-regional-inca-storehouse-quipu':'The cited NGA exhibition page timed out and has no retained source copy. General knowledge of khipu does not verify this specific storehouse/retied-knot observation.',
 'mat-bakelite-ekco-ad36':'The original magazine PDF returned HTTP403. Short retained OCR notes were inspected but not independently authenticated against the original pages; the particular AD36 configuration remains unverified.',
}

entry_rows=[]
for n in nodes:
    checked=[sid for sid in n['provenance']['source_ids'] if sid in checked_sources]
    alternate=ALTERNATE_NODE_SOURCES.get(n['id'],[])
    checked+=alternate
    identity='change' if n['id'] in IDENTITY_CHANGES else 'agree' if checked else 'cannot_verify'
    kind='change' if n['id'] in KIND_CHANGES else 'agree'
    tier='change' if n['id'] in TIERS else 'agree'
    issues=[]
    if kind=='change': issues.append('Modelling choice: this computational exposition is technology while closely comparable mathematical texts and algorithms are science. Under a knowledge-versus-artifact convention, use science plus a mathematical/procedural subkind. This is not a historical error.')
    if n['id'] in IDENTITY_CHANGES: issues.append('Modelling choice: '+IDENTITY_CHANGES[n['id']])
    elif not checked: issues.append('Evidence limit: '+IDENTITY_ACCESS_LIMITS[n['id']]+' Kind and tier were assessed from the supplied configuration and general knowledge. No duplicate or false claim is inferred from that gap.')
    if tier=='change': issues.append('Opinion under a consistent consequentiality criterion: '+TIERS[n['id']][1])
    entry_rows.append({'id':n['id'],'kind_verdict':kind,'identity_verdict':identity,'tier_verdict':tier,
        'proposed_kind':'science' if kind=='change' else n['kind'],
        'proposed_tier':TIERS[n['id']][0] if tier=='change' else n['tier'],
        'issue':' '.join(issues) if issues else 'Agree with the stated kind, bounded identity and display tier; no additional defect established.',
        'basis':{'method':'used another source' if alternate else 'reopened the cited source' if checked else 'from knowledge only',
            'finding':ENTRY_FINDINGS.get(n['id'],'The inspected bounded source passages identify the supplied referent; identity agreement is restricted to that scope.' if checked else IDENTITY_ACCESS_LIMITS[n['id']]),
            'sources':[source_basis(sid) for sid in checked],
            'unchecked_provenance_source_ids':[sid for sid in n['provenance']['source_ids'] if sid not in checked],
            'source_extent':'Bounded passages about the referent, including related connection passages; not a verification of every lifecycle event, date or provenance source.',
            'kind_check':{'supplied_kind':n['kind'],'referent':n['configuration'],'criterion':'Knowledge claim/model/mathematical content versus operational process, instrument, material, infrastructure or practice; the binary requires explicit subkinds.'},
            'identity_check':'Compared all 221 configurations for object, process, text, class, component and application overlap. Different witnesses and components are not automatically duplicates.',
            'tier_check':{'supplied_tier':n['tier'],'supplied_reason':n.get('tier_reason'),'criterion':'Breadth and durable consequence of the scoped referent, enabling reach and distinctness; source survival and neat dating are not impact measures. Proposed tier is reviewer judgement, not a source-derived fact.'}}})

label_changes={
 'chem-beckman-acidimeter-1935':(['chemistry','measurement','instruments'],'The glass electrode is electrochemical, not optical; glass in the name does not establish a materials-innovation topic.'),
 'bio-penicillin-selective-culture-1929':(['medicine','microbiology'],'The prefix bio- supplies genetics although this record is antibacterial selective culture; microbiology is currently absent from the label vocabulary.'),
 'bio-hybridoma-monoclonal-antibodies-1980':(['immunology','medicine'],'Hybridoma antibodies and T-cell classification need immunology; a genetics-only label loses the actual topic.'),
 'mat-egypt-glass-heart-amulet':(['glassmaking','materials'],'Mold-cast funerary glass is a glassmaking/material use, not an optics investigation.'),
 'mat-ennion-mold-blown-glass':(['glassmaking','materials'],'A mold-blown vessel is a glassmaking technology; the combined Optics & glass label conflates crafts with ray optics.'),
 'mat-byzantine-pilgrim-glass':(['glassmaking','materials'],'Religious souvenir vessels are glassmaking and material culture, not optical instruments.'),
 'google-glass-enterprise-2':(['computing','electronics','optics'],'The negative lookbehind excludes google- but the title contains Google Glass with a space; Materials is not justified by the brand name. Optics remains relevant to its display.'),
 'mat-wright-aluminum-engine-castings':(['metallurgy','materials','energy','transport'],'The rules catch engine but miss the aluminum material and aircraft application.'),
 'mech-shadwell-expansive-pump':(['steam','energy','water'],'Its nonmatching ID loses Steam power; this is a pumping application of expansive steam working.'),
 'mech-elsecar-newcomen-pump':(['steam','energy'],'Newcomen pumping is steam power despite not matching the ID whitelist.'),
 'mech-rotative-specification-1781':(['steam','energy','machining'],'Rotary power conversion is missing Energy and its manufacturing context.'),
 'mech-thomson-dynamical-heat-1851':(['heat','energy'],'The general heat-engine formulation lacks Energy merely because the name misses the energy regex.'),
 'global-marshall-waverider-survey':(['wayfinding','measurement','instruments'],'The buoy instrument is not caught by the instrument-word list.'),
 'global-planetarium-latitude-method-1980':(['wayfinding','astronomy','measurement'],'Planetarium and star-latitude work falls outside the astronomy word list.'),
 'global-hokulea-built-1975':(['wayfinding','transport'],'The voyaging craft deserves a transport label; that vocabulary currently covers roads better than vessels.'),
 'global-mau-hokulea-passage-1976':(['wayfinding','transport'],'The named passage is transport as well as navigation.'),
 'global-korent-wavefinding-2005':(['wayfinding','transport'],'The yacht passage is navigation and maritime transport, not an isolated modern measurement technique.'),
 'nonmarket-ra-i-1969':(['transport','wayfinding'],'The experimental vessel belongs in transport; ordering should not imply documented navigational instruction absent from its record.'),
 'global-muldoons-channel-infill':(['water','food-agriculture'],'The engineered fishing feature needs an aquaculture/food-production topic as well as water works.'),
 'global-muldoons-walled-channel':(['water','food-agriculture'],'The fishing-channel modification is not adequately described by water infrastructure alone.'),
 'entry-regional-molokai-keawanui-pond':(['water','food-agriculture'],'A managed fishpond is aquaculture, not just a reservoir-like water work.'),
 'entry-regional-bali-subak':(['water','food-agriculture'],'Cooperative irrigation is also food production and an institutional practice.'),
 'bio-nanopore-ebola-guinea-2015':(['genetics','medicine','microbiology','instruments'],'The outbreak-surveillance use and portable sequencer are lost behind the generic bio- rule.'),
 'bio-fluorescent-primer-readout-1985':(['genetics','measurement','instruments'],'The configured automated readout is an instrument and measurement system.'),
 'bio-fluorescent-terminator-sequencing-1987':(['genetics','measurement','instruments'],'The configured chemistry/detector readout is a measurement method, not only genetics.'),
 'mat-faraday-magneto-optic-rotation-1845':(['electromagnetism','optics','measurement'],'Magneto-optic rotation loses Optics because the chosen spelling and title miss the optical regex.'),
 'mat-powell-lealand-apochromat-1886':(['optics','instruments'],'The objective-eyepiece instrument is missing Instruments despite its explicit configuration.'),
 'mat-bakelite-ekco-ad36':(['polymers','materials','radio'],'The explicit replacement override preserves material labels but removes the radio-receiver application.'),
 'entry-electronics-pearl-street-1882':(['electric-power','energy','electromagnetism'],'The override suppresses the physical field topic; this is a vocabulary consistency choice, not new historical evidence.'),
 'entry-electronics-lauffen-frankfurt-1891':(['electric-power','energy','electromagnetism'],'A polyphase transmission demonstration belongs to electromagnetism under the current physical-topic convention.'),
 'entry-electronics-niagara-buffalo-1896':(['electric-power','energy','electromagnetism'],'A hydroelectric AC supply is omitted from Electromagnetism by its replacement override.'),
}
for n in nodes:
    if n['id'].startswith('math-') and not any(w in n['id'] for w in ['spyglass','telescope','jupiter','lunar','refraction','reflector']):
        # Add Mathematics without forcing every numerical subject into Arithmetic.
        label_changes.setdefault(n['id'],(None,'Mathematics is assigned to newer entries through overrides but omitted from comparable older arithmetic, logarithm and calculating-method entries.'))

raw=json.loads(pinned_text('web/public/data/timeline.json'))
actual={x['id']:x['labels'] for x in raw['nodes']}
overrides=json.loads(pinned_text('web/data/label-overrides.json'))
rules=[]
for line in pinned_text('web/scripts/import-research.ts').splitlines():
    m=re.search(r"\{ id: '([^']+)'.*test: /(.+)/ \},",line)
    if m: rules.append((m[1],re.compile(m[2])))
label_rows=[]
for n in nodes:
    haystack=f"{n['id']} {n['label']} icon:{n.get('icon','')}".lower()
    matches=[key for key,regex in rules if regex.search(haystack)]
    generated=overrides.get(n['id'],n.get('labels',matches))
    assert generated==actual[n['id']],n['id']
    change=label_changes.get(n['id'])
    proposed=change[0] if change and change[0] is not None else list(dict.fromkeys(actual[n['id']]+['mathematics'])) if change else actual[n['id']]
    # Do not issue a correction if the required general topic is already present.
    if change and proposed==actual[n['id']]: change=None
    label_rows.append({'id':n['id'],'verdict':'change' if change else 'agree','current':actual[n['id']],
        'regex_matches_before_replacement':matches,'assignment_route':'override replaces all regex labels' if n['id'] in overrides else 'node labels' if 'labels' in n else 'regex',
        'proposed':proposed,'issue':change[1] if change else 'No additional wrong or missing label established for this scoped entry.',
        'basis':{'method':'from knowledge only','technical_check':'Read the current LABEL_RULES and replacement precedence; recomputed all 221 assignments and compared with the saved web dataset. Topic judgement uses the node configuration, not a source claim of influence.'}})

for filename, rows in [('connection-verdicts.jsonl',connection_rows),('entry-verdicts.jsonl',entry_rows),('label-verdicts.jsonl',label_rows)]:
    (OUT/filename).write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in rows))

summary={'connections':dict(collections.Counter(x['verdict'] for x in connection_rows)),
         'entries':{k:dict(collections.Counter(x[k] for x in entry_rows)) for k in ['kind_verdict','identity_verdict','tier_verdict']},
         'labels':dict(collections.Counter(x['verdict'] for x in label_rows)),
         'relationship_types':dict(collections.Counter(x['relation'] for x in relationships)),
         'confidence':dict(collections.Counter(x['confidence'] for x in relationships)),
         'tiers':dict(collections.Counter(x['tier'] for x in nodes)),
         'relationship_source_ids':len({e['source_id'] for r in relationships for e in r['evidence']}),
         'relationship_source_ids_with_unverified_original_passages':sorted(unverified_sources)}
(OUT/'counts.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2))
