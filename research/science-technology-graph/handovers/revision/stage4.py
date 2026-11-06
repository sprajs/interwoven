"""One whole-graph pass for kinds, relation boundaries, influence and tiers."""
from common import *
sys.path.insert(0,str(ROOT/'handovers/self-audit'))
from comparison_judgements import ENTRY_OPINIONS

records=load();before=deepcopy(records);decisions={}
manifest=json.loads((ROOT/'handovers/self-audit/comparison-inputs.json').read_text())
opinions={nid:line.split('|') for nid,line in zip(manifest['entry_comparison_ids'],ENTRY_OPINIONS)}
foundations={
 'bio-dna-double-helix-model-1953':'Complementary molecular structure supplied a reusable explanatory framework for replication, genetics and later molecular methods across generations.',
 'bio-human-genome-draft-2000':'The genome reference resource supports subsequent genetic mapping, comparative biology and medical interpretation; rank concerns the shared dataset, not completeness of the first draft.',
 'bio-chain-termination-sequencing-1977':'The reusable sequencing method underlies later automated sequencing and genome production across molecular research and medicine.',
 'bio-dna-polymerase-preparation-1957':'A reusable DNA-synthesis reagent capability supports sequencing and later synthesis/amplification methods, not just the original physical preparation.',
 'bio-taq-pcr-immunology-1989':'The general Taq-based amplification method supports research, diagnosis and later sequencing workflows; the 1989 application is a witness, not its invention.',
 'elec-atalla-kahng-mos-1959':'The insulated-gate transistor architecture underlies subsequent MOS integration and computing across device generations.',
 'elec-faraday-ring-induction-1831':'Induction is a reusable physical principle behind transformers and electrical engineering across generations; the experiment is its bounded witness.',
 'elec-hoerni-planar-transistor-1959':'Retained-oxide planar processing supports later integrated-device fabrication across semiconductor generations, independently of one transistor product.',
 'elec-maxwell-field-theory-1864':'A unified electromagnetic framework supplies later wave experiments, radio and electrical/optical theory across generations.',
 'elec-volta-batteries-1800':'Sustained electrical supply supports electrochemistry and the experimental electromagnetism chain across several generations.',
 'mat-bessemer-air-conversion':'Bulk air-conversion steelmaking enabled successive infrastructure, transport and manufacturing applications; the ranked referent is the production process.',
 'math-napier-logarithms-1614':'Logarithmic calculation supplied reusable numerical methods for astronomy, navigation and engineering over generations.',
 'mech-carnot-heat-engine-analysis-1824':'Reversible-cycle reasoning is explicitly developed through Clapeyron, Thomson and Clausius and supports later thermodynamic disciplines.',
 'mech-clausius-heat-work-1850':'Reconciliation of heat/work and reversible engines supplies a reusable foundation for thermodynamics and later physical theory.',
 'mech-joule-friction-equivalent-1849':'Quantitative equivalence of heat and work supplied thermodynamic reasoning and energy accounting across physics and engineering.',
 'cont-c-industrial-ammonia-synthesis':'Large-scale fixed-nitrogen production supports successive agricultural and chemical-production systems, not merely one factory.',
 'cont-c-continuous-wire-papermaking':'Continuous sheet production supports subsequent printing, packaging and administrative infrastructure over generations.',
 'cont-a-handformed-fibre-sheet':'Paper as a reproducible writing/printing substrate supports administration, mathematical transmission and printing across regions and generations.',
 'cont-a-kepler-mars-elliptical-orbit':'The elliptical-orbit result supplied later celestial-mechanics reasoning and generations of orbital prediction; rank concerns the result rather than a surviving copy.',
 'cont-a-newton-universal-gravitation':'Mutual gravitation connects celestial and terrestrial mechanics and underlies later astronomy and engineering calculations across generations.',
 'cont-a-mendeleev-predictive-periodic-system':'Predictive elemental classification supplied later chemical discovery, teaching and material reasoning across generations.',
 'cont-a-dalton-chemical-atomic-framework':'Relative atomic weights and simple combining ratios supplied later chemical formulae and quantitative chemistry across generations.',
}
practice={'math-bugia-numeral-instruction-before1202','global-korent-wavefinding-2005','global-mau-thompson-teaching-1979',
          'global-mau-hokulea-passage-1976','entry-regional-bali-subak','entry-regional-bali-tirta-empul-irrigation',
          'entry-regional-inca-chaski-relay','entry-regional-inca-storehouse-quipu','cont-b-end-reversing-outrigger-sailing'}
math_tech={'math-allen-circles-proportion-1635','math-dutch-spyglass-1608','math-galileo-improved-telescope-1609',
           'math-gunter-logarithmic-scale-1620','math-newton-reflector-1668','math-oughtred-sliding-scales-1620s'}
math_science={'math-galileo-jupiter-satellites-1610','math-galileo-lunar-relief-1609','math-newton-differential-refraction-1666'}
tier_rows=[]
for n in records['nodes']:
    nid=n['id'];old=n['tier'];old_kind=n['kind'];tier=old
    if nid in opinions and opinions[nid][0].isdigit():tier=int(opinions[nid][0])
    if nid in foundations:
        tier=0;reason=foundations[nid]
    elif tier==0 or old==0:
        tier=1 if not nid.startswith(('global-','mat-alcoa','mat-nylon','bio-crispr')) else 2
        reason='The scoped record is a particular configuration, local witness, trial or material application. Dependence across fields or generations on THIS referent is not established; do not inherit the importance of its broader missing family.'
    elif nid in opinions:
        reason=opinions[nid][1]+' This is a scoped consequence judgement, not a reward for documentation or representation.'
    else:
        reason={1:'A major reusable result, process or system within its field; broader multi-field or multi-generation dependence on this exact referent is not established.',2:'A bounded technical contribution, transmission episode or documented configuration useful within a specific history; no broad dependence claim is established.',3:'Fine historical detail or an evidentiary witness; retention supports explanation without claiming broad later dependence.'}[tier]
    if nid in practice:n['kind']='practice'
    elif nid.startswith('math-') and nid not in math_tech|math_science:n['kind']='mathematics'
    n['tier']=tier;n['tier_reason']=reason
    decisions[nid]='Whole-graph editorial tier/kind review against the owner’s written test. '+reason+' Kind refers to the scoped content, not material substrate or geographical setting. Historical dates and sources are unchanged.'
    tier_rows.append({'id':nid,'old_kind':old_kind,'kind':n['kind'],'old_tier':old,'tier':tier,'moved':old!=tier,'reason':reason,'basis':'reviewer judgement against scoped source-backed record; no claim of a new historical fact'})

companion={'global-types-to-form','mat-objectives-with-compensating-eyepieces','mat-shaft-combined-with-bronze-head',
           'entry-regional-link-hafir-inlet-to-basin','entry-regional-link-hafir-to-enclosure',
           'entry-regional-link-relay-post-to-chaski','entry-regional-link-koh-ker-outlets-weir',
           'mech-blockmill-to-coaking','cont-d-aloha-arpanet-interconnection'}
production={'mat-furnace-to-heavy-glass'}
requirements={'entry-regional-link-road-to-chaski','bio-taq-pcr-to-ebola-nanopore'}
for r in records['relationships']:
    old=r['relation']
    if old=='observed-combination':
        r['relation']='companion-of' if r['id'] in companion else 'process-enables-production' if r['id'] in production else 'bounded-technical-requirement' if r['id'] in requirements else 'documented-development'
    if r['id']=='mech-shadwell-to-expansion-spec':r['relation']='same-principle'
    r['influence']='contributing' if r['id'] in {'bio-base-ratios-to-double-helix','revision-regnault-to-clausius'} else 'not_assessed'
    del r['necessity']
    decisions[r['id']]='Fresh relation/strength review of the exact scoped statement and Stage 1/2 passage checks. '+('Noncausal relation: co-function or shared principle is supported, causal ancestry is not asserted. ' if r['relation'] in {'companion-of','same-principle','same-family'} else 'Documented contribution or bounded use retained; no new personal-transmission claim. ')+('Influence not assessed; confidence measures support for the statement only.' if r['influence']=='not_assessed' else 'Explicitly one input among several; contributing influence does not assert necessity.')+' Original necessity text is preserved in this ledger, not silently treated as a strength assessment.'
finish('stage4',before,records,decisions,'Owner-directed four-kind and relation vocabulary; no observed-combination, one separate influence field, and one whole-graph tier pass. Tier reasons are editorial consequence judgements, not historical source authentication.')
write_json(Path(__file__).parent/'stage4-tiers.json',tier_rows)
