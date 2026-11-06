"""Commit explicit topic assignments after reviewing the complete candidate list."""
from common import *

records=load();before=deepcopy(records);decisions={}
web=ROOT.parents[1]/'web'
display=json.loads((web/'public/data/timeline.json').read_text())
candidate={n['id']:n['labels'] for n in display['nodes']+display['unplaced']}
renames={'genetics':'molecular-biology','wayfinding':'navigation','knowledge':'knowledge-transmission'}
fixes={
 'google-glass-enterprise-2':['computing','electronics'],
 'bio-dna-polymerase-preparation-1957':['molecular-biology'],
 'bio-taq-pcr-immunology-1989':['molecular-biology','medicine'],
 'bio-penicillin-selective-culture-1929':['medicine'],
 'bio-hybridoma-monoclonal-antibodies-1980':['molecular-biology','medicine'],
 'bio-nanopore-ebola-guinea-2015':['molecular-biology','medicine'],
 'chem-beckman-acidimeter-1935':['chemistry','measurement','instruments'],
 'elec-helmholtz-dielectric-test-1879':['electromagnetism'],
 'elec-fairchild-silicon-gate-3708-1968':['integrated-circuits','semiconductors','electronics'],
 'elec-kilby-germanium-oscillator-1958':['integrated-circuits','semiconductors','electronics'],
 'elec-noyce-planar-interconnection-1959':['integrated-circuits','semiconductors','electronics'],
 'elec-fairchild-physical-isolation-1960':['integrated-circuits','semiconductors','electronics'],
 'elec-fairchild-junction-isolation-1960':['integrated-circuits','semiconductors','electronics'],
 'fairchild-micrologic-type-f':['integrated-circuits','semiconductors','electronics','computing'],
 'elec-intel-4004-cpu-1971':['computing','integrated-circuits','semiconductors','electronics'],
 'mat-egypt-glass-heart-amulet':['glass','materials'],
 'mat-ennion-mold-blown-glass':['glass','materials'],
 'mat-byzantine-pilgrim-glass':['glass','materials'],
 'mat-faraday-heavy-optical-glass-1829':['optics','glass','materials'],
 'mat-jena-new-optical-glasses-1886':['optics','glass','materials'],
 'mat-jena-spectrometric-glass-research-1881':['optics','glass','materials','measurement'],
 'mat-ri-glass-furnace-1827':['glass','heat','materials'],
 'mat-faraday-magneto-optic-rotation-1845':['electromagnetism','optics'],
 'mat-powell-lealand-apochromat-1886':['optics','instruments'],
 'mat-gerlafingen-oxygen-trials':['metallurgy','materials'],
 'mat-linz-soft-blowing-trials':['metallurgy','materials'],
 'math-dutch-spyglass-1608':['optics','instruments'],
 'math-gwalior-place-value-inscription':['mathematics','arithmetic'],
 'mech-shadwell-expansive-pump':['steam','energy'],
 'mech-elsecar-newcomen-pump':['steam','energy'],
 'mech-thomson-dynamical-heat-1851':['heat','energy'],
 'mech-aljazari-donkey-water-lift-1315':['water','mechanisms'],
 'mech-portsmouth-block-mills':['machining','mechanisms'],
 'mech-portsmouth-coaking-machine':['machining','mechanisms'],
 'mech-maudslay-geared-screw-lathe':['machining','mechanisms'],
 'mat-wright-aluminum-engine-castings':['metallurgy','materials','transport'],
 'mech-kendall-k1-voyage':['timekeeping','navigation','measurement'],
 'entry-regional-bali-subak':['water','agriculture'],
 'entry-regional-bali-tirta-empul-irrigation':['water','agriculture'],
 'entry-regional-molokai-keawanui-pond':['water','aquaculture'],
 'cont-b-alkali-maize-preparation':['agriculture','chemistry'],
 'cont-b-frost-assisted-potato-preservation':['agriculture','heat'],
 'cont-b-woven-constricting-cassava-press':['agriculture','mechanisms'],
 'cont-b-toggling-harpoon':['mechanisms','navigation'],
 'cont-b-lever-spear-thrower':['mechanisms'],
 'cont-b-barbed-bone-points':['materials','mechanisms'],
 'cont-a-pressure-retouch-stone-edges':['materials'],
 'cont-c-next-continuous-float-glass':['glass','materials'],
 'cont-c-next5-differential-roller-drafting':['mechanisms','machining'],
 'cont-d-w4-uv-erasable-floating-gate-memory':['semiconductors','integrated-circuits','computing'],
 'cont-d-w4-ccd-image-sensor':['electronics','integrated-circuits','optics','instruments'],
}
for n in records['nodes']:
    labels=fixes.get(n['id'],[renames.get(x,x) for x in candidate[n['id']]])
    if n['kind']=='mathematics' and 'mathematics' not in labels:labels=['mathematics']+labels
    assert labels,n['id']
    n['labels']=list(dict.fromkeys(labels))
    decisions[n['id']]='Explicit topic review of this scoped configuration against the Stage 5 definitions. Reviewed the complete candidate list, correcting lexical false positives and omissions. Labels are editorial topics, not causal, priority or tier claims; source-backed history unchanged.'
finish('stage5',before,records,decisions,'Replace inferred regex labels with explicit reviewed topic assignments on every canonical entry. No automatic assignment for new entries.')
