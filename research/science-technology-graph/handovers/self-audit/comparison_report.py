"""Assemble Stage1 comparison tables from pinned inputs and explicit judgements.

Run after comparison_support.py inventory. Never edits canonical graph files.
"""
import collections
import hashlib
import json
import re
from pathlib import Path

from comparison_support import BASE, MAIN, OUT, INDEPENDENT, CACHE, records, rows
from comparison_judgements import CONNECTIONS, ENTRY_OPINIONS

manifest=json.loads((OUT/'comparison-inputs.json').read_text())
old=records('nodes'); now=records('nodes',MAIN)
old_events=records('events'); now_events=records('events',MAIN)
old_links=records('relationships'); now_links=records('relationships',MAIN)
source_catalog=records('sources',MAIN)
self_links={x['id']:x for x in rows(OUT/'connection-verdicts.jsonl')}
other_links={x['id']:x for x in rows(INDEPENDENT/'connection-verdicts.jsonl')}
self_entries={x['id']:x for x in rows(OUT/'entry-verdicts.jsonl')}
other_entries={x['id']:x for x in rows(INDEPENDENT/'entry-verdicts.jsonl')}

def cell(value):
    return str(value).replace('|','/').replace('\n',' ')

def table(headers, data):
    return '\n'.join(['| '+' | '.join(headers)+' |','| '+' | '.join(['---']*len(headers))+' |']+['| '+' | '.join(map(cell,row))+' |' for row in data])+'\n'

def code(value):return '`'+value+'`'

LIVE={'global-diamond-sutra-idp','entry-regional-source-unesco-subak','entry-materials-exp-sinica-shang-jar','entry-elec-smg-blackwall','mech-smg-condenser'}
VISUAL={'bio-franklin-gosling-1953','entry-molecular-marshall-1870','src-zeiss-1885','mat-zeiss-catalogue-1889'}
ABSTRACT={'bio-prober-1987','entry-molecular-maxam-1977','entry-molecular-kung-1980','entry-molecular-bell-1989','entry-molecular-hart-2015'}
OVERRIDE={
 'math-brahmagupta-zero-rules-628':['entry-exp-calculation-zero'],
 'entry-electronics-blackwall-railway-telegraph-1840':['entry-elec-smg-blackwall','entry-elec-hamel-1859'],
 'bio-humidity-varied-dna-diffraction-1952':['bio-franklin-gosling-1953'],
 'mat-powell-lealand-apochromat-1886':['mat-abbe-new-glass-1887'],
}
UNVERIFIED={'global-muldoons-channel-infill','global-muldoons-walled-channel','entry-regional-inca-storehouse-quipu','mat-bakelite-ekco-ad36'}

def entry_basis(nid):
    if nid in UNVERIFIED:
        return {'method':'from knowledge only','source_ids':[], 'limit':'Original referent still cannot_verify; access attempts/retained note limits described above. No historical authentication inferred.'}
    sids=OVERRIDE.get(nid,[sid for sid in old[nid]['provenance']['source_ids'] if sid in LIVE|VISUAL|ABSTRACT or (CACHE/(sid+'.txt')).exists()])
    assert sids,('No reopened source basis',nid)
    method='used another source' if nid in OVERRIDE and not set(sids)<=set(old[nid]['provenance']['source_ids']) else 'reopened the cited source'
    return {'method':method,'source_ids':sids,'limit':'Bounded referent/content check; tier preference is explicit opinion, not source-certified impact or a full lifecycle audit.'}

def identity_resolution(nid):
    a=self_entries[nid];b=other_entries[nid];v=b['identity_verdict']
    if nid in UNVERIFIED:return 'cannot_verify remains; neither a duplicate nor a false claim is established.'
    if nid=='elec-fairchild-junction-isolation-1960':return 'Clarify p–n junction isolation against the distinct physical-isolation node; do not broaden electrical separation into both.'
    if nid=='bio-recombinant-plasmid-cloning-1979':return 'Both found broad method versus insulin-expression use. Source1979 is specific; separate/scope the witness and source the earlier method.'
    if nid=='elec-hoerni-planar-transistor-1959':return 'Both found class/product overlap; preserve distinct conception/prototype/product roles rather than treating them as one die.'
    if nid=='mech-rumford-friction-apparatus-1798':return 'Apparatus remains technology; represent the scientific result/event separately before changing a link endpoint.'
    if v=='duplicate':return 'Reject automatic duplicate merge: the reopened description distinguishes method/component/system roles used in the chain. Decision5 preserves that split.'
    if v in {'wrong_witness','witness_for_broader','too_narrow'}:return 'The bounded referent is supported. Separate its witness/use from a broader advance; missing broad coverage does not make this identity false.'
    if nid=='global-mau-thompson-teaching-1979':return 'Retain the teaching/transmission episode as practice, distinct from vessel and voyage.'
    if nid=='bio-penicillin-selective-culture-1929':return 'Retain the precise microbiological application; clinical-discovery expectations do not make the source referent unclear.'
    if nid=='mech-condenser-model-1765':return 'Separate-condenser arrangement and early specimen are distinguishable; retain independent deployment events/roles.'
    if a['identity_verdict']=='change':return 'Scope/importance warning remains; it is not a newly disproved historical object.'
    return 'No historical identity disagreement established after reopening; tier/kind or anchor policy is the actual issue.'

details=[]
connection_table=[]
assert len(CONNECTIONS)==40
for line in CONNECTIONS:
    nid,finding,basis=line.split('|')
    a=self_links[nid]['verdict'];b=other_links[nid]['verdict']
    current='removed' if nid not in now_links else 'modified' if old_links[nid]!=now_links[nid] else 'unchanged'
    row={'section':'connection','id':nid,'self':a,'independent':b,'current_status':current,'finding':finding,'source_check':basis}
    details.append(row);connection_table.append([code(nid),a+' / '+b,current,finding,basis])
assert {x['id'] for x in details}==set(manifest['comparison_connection_ids'])

entry_table=[]
ids=manifest['entry_comparison_ids'];assert len(ids)==len(ENTRY_OPINIONS)==120
for nid,line in zip(ids,ENTRY_OPINIONS):
    preference,note=line.split('|');a=self_entries[nid];b=other_entries[nid]
    other_tier=b['tier'] if b['proposed_tier'] is None else b['proposed_tier']
    kind=b.get('proposed_kind') or old[nid]['kind']
    if nid=='mech-rumford-friction-apparatus-1798':kind=old[nid]['kind']
    if nid in ['entry-regional-bali-tirta-empul-irrigation','entry-regional-inca-storehouse-quipu']:
        kind='practice (content/operation); distinguish documentary witness'
    basis=entry_basis(nid)
    identity=identity_resolution(nid)
    row={'section':'entry','id':nid,'self_tier':a['proposed_tier'],'independent_tier':other_tier,'stage1_preferred_tier':preference,'stage1_preferred_kind':kind,'self_identity':a['identity_verdict'],'independent_identity':b['identity_verdict'],'identity_resolution':identity,'finding':note,'basis':basis,'current_status':'removed' if nid not in now else 'modified' if now[nid]!=old[nid] else 'unchanged'}
    details.append(row)
    entry_table.append([code(nid),f"{a['proposed_tier']} / {other_tier} → {preference}",kind,identity+' '+note,basis['method']+': '+', '.join(map(code,basis['source_ids'])) if basis['source_ids'] else basis['method']+'; cannot_verify'])

REMOVALS={
 'elec-hoerni-planar-conception-1957':('consolidation into planar-transistor','Same retained-oxide architecture was treated as lifecycle stages of one broad configuration. Both event IDs were rehomed; conception-to-Noyce was retargeted.','Not sound under decision5 as written:1957 conception has an independent date and the role feeding Noyce before a working device. Keep a deliberate conceptual/working split or an equally explicit event-level chain, without pretending the dates are duplicates.','CHM/Moore planar account and patent scope; conception date and receiving patent/project dates; original source passages reopened.'),
 'mech-kendall-k1-voyage':('consolidation into H4','K1 was judged a copy without a newly established performance/architecture advance; completion/voyage events were rehomed and K2 link retargeted.','Not sound: K1 is a separate commissioned physical watch, completed1769 and used1772–1775, with a role in the K2 account. Same design is not same thing; lack of proven performance advance is not decision5.','Board of Longitude K1 resource and RMG K2 description reopened; the latter says simplified H4/K1.'),
 'mech-bloomfield-pump-1776':('consolidation into condenser arrangement','The broad arrangement already used Bloomfield as a practical-use witness. The1776 event was rehomed and both incoming links retargeted.','Not sound under the independent-date/chain-role rule:1765 model and1776 full-sized installation are different things, and boring/trial-to-installation links relied on that distinction. Keeping event IDs is useful but does not prove duplicate nodes.','Andrew2009 p.15 and notes12–14; Gazette reprint1776 passage; condenser custodian page reopened.'),
 'entry-electronics-india-public-telegraph-1855':('frontier eligibility exclusion','Public message service existed elsewhere earlier; the record supplied no separately proved new global service mechanism. Its sole event was deleted from active data.','Not a merge: a different1855 regional service and adoption community are not the1845 Washington–Baltimore service. A selective coverage decision may omit it, but decision5 does not authorize calling it duplicate.','Manchester scholarly abstract and USPS public-service account reopened; they describe different episodes.'),
 'entry-electronics-japan-tokyo-yokohama-1870':('frontier eligibility exclusion','Earlier Breguet pointer service and local script adaptation were treated as insufficient new global capability; its event was removed.','Not a merge: the local apparatus/service and community have an independent date. Preserve Japanese adaptation context; the1869/1870 calendar issue remains flagged rather than silently settled.','NTT1870 service history reopened. Later ledger records the calendar/model qualifications; those are not new source adjudications here.'),
 'global-hokulea-built-1975':('reconstruction eligibility exclusion','The cold-molded plywood/fibreglass vessel was judged a reconstruction rather than a new global technical frontier. Four active events and its connected links were removed; full records survive in the ledger.','Not a merge, and not sound as duplicate removal: a1975 vessel is a separate experimental platform with roles in design-to-build,1976 passage and1980 trial. Its tier can fall without deleting the chain.','Low design/construction account, PVS launch information and Kyselka1980 experimental-voyage report reopened.'),
 'global-mau-hokulea-passage-1976':('reconstruction/use eligibility exclusion','A voyage employing an existing navigational practice was not accepted as a new global mechanism; two active events and its vessel-use link were removed.','Not a merge: a separately dated navigation episode is not the vessel, its design hypothesis or the later1980 test. Decision5 preserves the roles needed by those histories.','Kyselka p.25908 and PVS account reopened: Mau’s1976 use is distinguished from Thompson’s later training/testing.'),
 'nonmarket-ra-i-1969':('reconstruction eligibility exclusion','The experimental reed boat was excluded as a reconstruction rather than a new global capability; its three production/use/abandonment events left active data.','Not a merge: this1969 object and failed attempt have independent dates and a failure role. It can be fine detail; there is no second active record of the same physical boat proving duplication.','Kon-Tiki museum Ra/RaII account reopened; construction, voyage and abandonment distinguished.'),
 'math-latin-dixit-algorizmi-1100s':('frontier eligibility exclusion','A derived Latin translation/redaction was not shown to introduce a later global-frontier mathematical capability; its two active events and transmission link were removed.','Not sound as a merge: a Latin text/translation has an independent linguistic/transmission role and composition/copy history, distinct from the lost Arabic arithmetic. New theorem novelty is not decision5.','Folkerts preface/chapter2/chapter4 excerpt reopened; Arabic work, DA and later Latin reworkings are distinguished.'),
 'math-latin-liber-alchorismi-1100s':('frontier eligibility exclusion','A Latin reworking was excluded absent a proved further global-frontier result; two events and its incoming link were removed, context added to the Arabic node.','Not sound as a merge: LA is an expanded Latin redaction with a separate chain role. Its reordering comparison needs correction, but that does not make the work identical to the Arabic source.','Folkerts chapter2 source PDF pp.18–19 reopened; LA/LP versus LY comparator is explicit.'),
 'mat-bakelite-ekco-ad36':('frontier eligibility exclusion','The circular molded cabinet was already familiar from the earlier AD65; no distinct cabinet advance was established. Both AD36 events were removed; source records retained.','Not a merge: AD36 and AD65 are different product objects and dates. This may be a defensible curation exclusion, but cannot satisfy same-thing duplication. Original AD36 magazine authentication remains incomplete.','Original magazine retrieval remains403; retained OCR note says familiar cabinet. The later ledger cites Cooper Hewitt AD65 comparison; it is an exclusion rationale, not fresh acceptance here.'),
}
assert set(REMOVALS)==set(manifest['changes_since_audited_snapshot']['nodes']['removed'])
removal_table=[]
for nid,(kind,why,judgement,basis) in REMOVALS.items():
    details.append({'section':'removal','id':nid,'operation':kind,'reason_recorded':why,'finding':judgement,'source_check':basis})
    removal_table.append([code(nid),kind+'; '+why,judgement,basis])

LINK_REMOVALS={
 'elec-planar-concept-to-device':'Removed during Hoerni consolidation; source and target became the same broad node. The original1957→1959 conception/realisation sequence is not a false claim; preserve that distinct dated role under decision5.',
 'mech-h4-to-k1-copy':'Removed when K1 was consolidated into H4. The reopened Board resource explicitly calls K1 a commissioned copy; different physical watches/dates mean the adaptation history should remain represented.',
 'global-hokulea-build-to-mau-voyage':'Removed with both vessel and voyage exclusions. Reopened sources support platform use, so retype rather than discard it as false.',
 'global-hokulea-study-to-build':'Removed with the vessel. Low supports design work selecting the experimental craft; excluding the boat does not refute this contribution.',
 'global-hokulea-to-field-trial':'Removed with the vessel. Kyselka explicitly reports testing at sea; platform and observation roles are deliberately different.',
 'math-edge02-khwarizmi-to-dixit':'Removed with the Latin text. Folkerts supports a translation/redaction route, with uncertainty about the lost Arabic original and translator; not a duplicate-language identity.',
 'math-edge02-khwarizmi-to-alchorismi':'Removed with LA. Expanded exposition is supported; its reordered-operations comparator needs qualification. Correcting that overstatement does not justify erasing the textual transmission role.',
}
assert set(LINK_REMOVALS)==set(manifest['changes_since_audited_snapshot']['relationships']['removed'])

DATE_IMPACTS={
 'cont-a-dalton-chemical-atomic-framework':'The by-about1804 recognition anchor relies on Thomson’s1831 retrospective account; the1807 Thomson and1808 Dalton publications are different records. Check the earliest defensible same-framework record, preserving the retrospective qualification and later community events. Do not turn recollection into an exact contemporary publication date.',
 'cont-a-mendeleev-predictive-periodic-system':'Existing1869 publication precedes1870 recognition. Verify the earlier arrangement without backdating detailed1871–1872 predictions or the1876 gallium test. Original journal issues remain uninspected in this later batch.',
 'cont-b-decked-skin-frame-kayak':'The1577 account does not explicitly identify deck/cockpit; those features are inferred through a later account. Check whether the earliest record establishes the full scoped configuration before choosing its anchor.',
 'cont-b-framed-openwork-snowshoe':'The approximate wood age and inferred ancient use are not a directly witnessed manufacturing/travel date. Keep the dating/source-access limitations visible under decision1.',
 'cont-b-slit-snow-goggles':'Keep the100BCE–800CE object interval as an interval, not an invented first-use year. The1820s purchases/observations remain separate use and sale witnesses.',
 'cont-b-snow-block-dome':'The1822 record describes a dome but not a spiral; retain the later1888 spiral account separately rather than backdating that feature.',
 'cont-c-next7-ammonia-soda-production':'The record names an earlier proposed reaction and conflicting early manufacturing accounts. Verify a full-process record before choosing it over the by1837 use bound; do not settle first sale or output by fiat.',
 'cont-a-current-powered-water-lifting-wheel':'Earlier Lucretius simile event exists; verify it identifies the same current-driven lifting mechanism before preferring it to the clearer Vitruvius record. No automatic min-date selection.',
 'cont-a-kepler-mars-elliptical-orbit':'Existing1609 publication precedes1611 reception. Decision1 changes the chart anchor to the supported earlier record; reception remains separate.',
 'cont-a-newton-universal-gravitation':'Existing1687 publication precedes1688 review. Decision1 changes the chart position; review and later recognitions remain events.',
 'cont-c-birkeland-eyde-disc-arc':'Existing summer1905 prototype precedes autumn1907 deployment. Check prototype configuration, then use its earliest defensible record rather than later uptake.',
 'cont-c-next-continuous-float-glass':'The record itself cites a comparable1902 design and a failed1920s trial. Earliest-record policy requires checking that design, not automatically retaining1959 first product.',
 'cont-c-next-multistage-steam-turbogenerator':'The record distinguishes earlier reaction prototypes from1887 public operation. Check which earlier record includes the turbine-generator configuration; do not substitute a turbine-only predecessor blindly.',
 'cont-c-next4-planographic-lithography':'The retained1799 contract precedes1800 entry. Check its exact described method and preserve contract/publication/use as different events.',
 'cont-c-next4-reversing-regenerative-furnace':'The chart already uses the1857 evidence before1861 community entry. Preserve both; no need to move it later.',
 'cont-c-next5-electronic-numerical-contour-milling':'Existing September1952 demonstration precedes by1958 field use. Match the exact servo/interpolation configuration and re-anchor if supported.',
 'cont-c-next6-ammonia-vapor-compression':'Existing18 December1868 society-journal event precedes the by1874 deployment. Reopen its actual ammonia-compression description before preferring it.',
 'cont-d-dec-pdp11-20-1970':'Already anchored to the January1970 offer before April entry. Preserve that separation; earlier concept evidence still needs the normal scope check.',
 'cont-d-ibm-305-350-1956':'June1956 prototype/customer-use event precedes September entry. Check the same305/350 configuration, then retain earliest and community milestones separately.',
 'cont-d-ibm-726-1953':'Already anchored by1952 offer before1953 entry. Preserve separate records and keep bounds explicit.',
 'cont-d-w3-carbon-cobalt-lithium-ion':'Existing1986 prototype precedes1991 commercialization. Check the carbon/LiCoO2 architecture and use the earlier supported record, not a generic earlier lithium cell.',
 'cont-d-w3-optical-fiber-communications':'Existing1974 Fujitsu/NTT record precedes1975 selected use. Verify endpoint/configuration and separate demonstration from deployment.',
 'cont-d-xerox-parc-ethernet-1976':'Already placed by1974 PARC use before1976 paper. Preserve both and check any earlier bounded architecture record without inventing one.',
}
PRACTICE_CANDIDATES={
 'cont-b-end-reversing-outrigger-sailing':'Practice is a strong candidate for the manoeuvring skill; distinguish it from the canoe architecture.',
 'cont-b-alkali-maize-preparation':'Decide operational food-processing technology versus learned practice by the scoped referent; cultural setting alone is insufficient.',
 'cont-b-frost-assisted-potato-preservation':'Decide preservation process versus learned regional practice explicitly; do not file it by era or region.',
}
SCOPE_FLAGS={
 'cont-d-ibm-305-350-1956':'System/product witness versus general random-access disk architecture needs Stage3 separation before0 is justified.',
 'cont-d-w2-contact-compound-ultrasound':'The specific compound-contact architecture is narrower than all diagnostic ultrasound; do not borrow that whole field for0.',
 'cont-d-w2-spin-warp-mri':'Spin-warp is a particular imaging architecture, not all MRI; require its own cross-generation dependence case.',
 'cont-d-w4-ctss-file-batch':'The1963 files/batch configuration is narrower than all time-sharing or stored-program computing; its0 needs scope-specific support.',
 'cont-d-sony-mz1-minidisc-1992':'Separate MZ-1 product witness from the MiniDisc format identity before judging consequences.',
 'cont-d-w4-digital-compact-cassette':'A particular format and withdrawal history is valid fine detail; evidence of a failed market is not a reason to delete it.',
 'cont-c-inverform-twin-wire':'Keep the distinct upper/lower-wire development role; membership in papermaking is not sameness of mechanism.',
 'cont-c-next6-ammonia-vapor-compression':'Keep distinct from general compression refrigeration: the refrigerant/component adaptation supplies a separate chain role.',
}
added_table=[]
for nid in manifest['changes_since_audited_snapshot']['nodes']['added']:
    n=now[nid];anchor=now_events[n['graph_anchor']['event_id']]['date']['label']
    specific=DATE_IMPACTS.get(nid,'No earlier qualifying record established by this comparison; current recorded anchor is not thereby certified earliest.')
    if nid in PRACTICE_CANDIDATES:specific+=' '+PRACTICE_CANDIDATES[nid]
    if nid in SCOPE_FLAGS:specific+=' '+SCOPE_FLAGS[nid]
    flags=['D1 two date questions','D3 full tier pass','D5 identity screen','D2 selective-coverage context']
    if nid in PRACTICE_CANDIDATES:flags.append('D4 kind candidate')
    details.append({'section':'added_entry','id':nid,'label':n['label'],'kind':n['kind'],'tier':n['tier'],'current_anchor':anchor,'decision_impacts':flags,'finding':specific,'basis':'Current pinned record/events and cited-source leads; this is a policy-impact screen, not a fresh historical acceptance of the66 additions.'})
    added_table.append([code(nid),n['label'],f"{n['kind']}; tier{n['tier']}; {anchor}",specific])

NEW_LINK_NOTES={
 'cont-a-handformed-to-continuous-paper':'D4: retain actual mechanisation/adaptation if the passage supports it; assess influence independently. D1: bind process-class events, not ancient specimen→Frogmore ancestry.',
 'cont-c-link-arc-ammonia-notodden':'D4: local supersession is neither technical descent nor universal necessity. Keep overlapping1928–1934 operation; influence may remain not_assessed.',
 'cont-c-link-fourdrinier-inverform':'D4: keep documented-development; later contribution labels can record the added top-wire/drainage role. D1: preserve distinct development and commercial-use dates.',
 'cont-c-next6-compression-to-linde-ammonia':'D4: keep the documented Linde development while separating generic cycle, ether history and ammonia adaptation; do not imply a particular1857 machine caused it.',
 'cont-d-aloha-arpanet-interconnection':'D4 definitely changes observed-combination. A physical network interconnection is a real configuration/use, not ancestry. Preserve the1972/1973 satellite-date qualifications and bind a matching interconnection event.',
 'cont-d-aloha-to-ethernet':'D4: keep documented-development and the explicitly credited collision/retransmission ideas; use future contribution labels rather than another predicate scheme.',
 'cont-d-w2-xray-to-ct':'D4: retain method-level adaptation if confirmed, not descent from a particular1896 patient apparatus. D1/D3: separate imaging architecture from early clinical witnesses.',
 'cont-d-w4-eprom-4004-tester':'D4 definitely changes observed-combination. It describes EPROM program storage in a particular4004 tester; use a bounded use/configuration relation and matching event, without universal EPROM necessity.',
}
assert set(NEW_LINK_NOTES)==set(manifest['changes_since_audited_snapshot']['relationships']['added'])
new_link_table=[]
for nid,note in NEW_LINK_NOTES.items():
    r=now_links[nid];evidence='; '.join(e['source_id']+' @ '+e['locator'] for e in r['evidence'])
    details.append({'section':'added_connection','id':nid,'relation':r['relation'],'finding':note,'basis':'Current record and its locators; not fresh source acceptance of a later batch.'})
    new_link_table.append([code(nid),code(r['from']['node_id'])+' → '+code(r['to']['node_id']),r['relation'],note,evidence])

GAP_FINDINGS={
 1:'Historian hold on the exact pre-model transmission route. Watson–Crick acknowledge unpublished King’s results, but that alone does not identify this particular diffraction event as their accessed input.',
 2:'Historian hold: the April same-issue constraints paper is not automatically the earlier MRC-report input. Do not approve a precisely timed edge from a later publication just because the acknowledgement is genuine.',
 3:'Passage confirmed: Abraham p.178 footnote2 says strains came from Fleming. Ready to draft a strain-supply/programme link after matching the receiving event; it is not proof that selective-culture technique itself caused the specific clinical trial.',
 8:'Cooke explicitly credits Ampere’s signalling idea. The current Ampere endpoint is a parallel-current experiment; scope or add the actual proposal event before adding a transmission edge.',
 13:'Field confirms Morse’s advice/involvement, not influence of the1845 paid-service configuration on the1858 cable. Rebind to the supported contribution; do not link by actor identity alone.',
 14:'Marconi names a Morse key in his early apparatus. That supports component/design-family use, not ancestry from the Washington–Baltimore paid service, nor automatically every later aerial configuration.',
 18:'A bounded induction-function link is plausible and distinguishable from a copied-instrument claim. Joule confirms magneto-electric operation; formulate the required phenomenon without making this particular Faraday apparatus uniquely necessary.',
 19:'Source confirms an altered inducing arrangement and reused rotating apparatus; a bounded adaptation link is a strong candidate. This contradicts automatically merging the two configurations as duplicates.',
 20:'Clausius explicitly names and uses Regnault. Ready to draft with the particular numerical input/event identified, retaining the mediated-access and source-edition qualifications.',
 24:'Not established as proposed. Maudslay built both kinds of machine, but the coaking object page does not say this particular screw-cutting lathe enabled the block mills. Shared maker is not an edge.',
 25:'Sanger–Coulson explicitly uses DNA polymerase I. Ready to draft a bounded enzyme-class use relation; do not identify the1970s preparation with Kornberg’s original physical batch.',
 27:'Not established as proposed. The genome paper lists sequencing polymerases and cycle sequencing; these are not automatically the1989 PCR review or its application. Confirm the exact production operation and references before adding.',
 28:'Same company/page and adjacent dates do not prove a development relationship from the1891 supply episode to this1895 kettle. A class/material-use relation may be supportable, but the proposed lineage needs a narrower claim.',
 29:'Chapter membership is confirmed. Use noncausal semantics for handbook/procedure containment or companion roles under the approved scheme; preserve the deliberate distinction rather than merging.',
}

parts=[]
parts.append('## Every connection comparison case\n\nSelf / independent are the original verdicts. Current status is relative to the two pinned snapshots. Each finding is a Stage1 adjudication, not an applied correction.\n\n'+table(['ID','Self / independent','Current','Adjudication','Source reopened / limit'],connection_table))
parts.append('## Entry disagreements and differences in scope\n\nThis table covers all120 entries whose normalized proposed kind, tier or identity verdict differs, including cases where different verdict words actually express the same concern. It is a superset of substantive disagreements, not120 demonstrated errors. The remaining101 entries have no disagreement in those dimensions. Each row states the reopened source route or cannot_verify limit. Numbers mean self / independent → Stage1 preference for the old referent. Kind preferences implement the owner’s convention only as a report recommendation; no record has been changed. The source authenticates content, not the tier opinion.\n\n'+table(['Entry ID','Tier comparison','Kind recommendation','Identity and tier adjudication','Check method / sources'],entry_table))
anchor_flags=[]
anchor_exceptions={
 'global-mau-hokulea-passage-1976':'The1976 witness date itself is appropriate for that passage. The missing ancient tradition is a coverage/scope problem, not evidence that this voyage should be moved into antiquity.',
 'global-barbegal-aqueduct-mills':'Accept construction-versus-late-bound concern; reject the claim that by300 alone proves post-abandonment use or that the2024 paper introduced the hardtack argument.',
 'mat-shang-piece-mold-bronze':'Represent the source interval/bound; do not call by900 a known900 inception or invent1300 as exact first use.',
 'mech-expansion-specification-1782':'The patent/specification cannot be backdated to Shadwell merely because the earlier engine shared an expansion principle. Match the1782 document to its own dated record.',
 'global-rome-aqueduct-mills-537':'The existing by537 use bound does not assert invention in537. An earlier independently evidenced use may improve placement; do not invent its date.',
 'mat-great-lakes-native-copper-tools':'Do not select the earliest end of a modelled archaeological interval as a known onset. Keep uncertainty and the dated material/use interpretation explicit.',
 'med-humulin-recombinant-insulin-1982':'Regulatory approval and commercial sale remain distinct; the already flagged1982/1983 disagreement is not resolved here.',
}
for nid,r in other_entries.items():
    if r['anchor_verdict']=='agree':continue
    old_label=old_events[old[nid]['graph_anchor']['event_id']]['date']['label']
    current_label=now_events[now[nid]['graph_anchor']['event_id']]['date']['label'] if nid in now else 'entry removed'
    finding=anchor_exceptions.get(nid,'Accept the precedence/scope warning where an earlier record establishes the SAME referent. Confirm the exact source/date and retain the later community event in Stage3; do not choose an arbitrary earliest bound.')
    anchor_flags.append([code(nid),r['anchor_verdict'],old_label,current_label,finding])
assert len(anchor_flags)==67
parts.append('## All67 independent anchor flags\n\nMy original entry schema had no anchor-verdict dimension: absence of a flag there was not an independently verified agreement with the display date. This table makes all67 additional leads explicit, including33 entries outside the120 comparison cases. The old and current labels below were checked against the pinned EVENT RECORDS; that mechanical check is not fresh source authentication of every earliest-date lead. The source-confirmed corrections and disputed interpretations are distinguished in the Facts and connection tables above. No Stage3 date is applied here.\n\n'+table(['Entry','Independent flag','Old anchor label','Current anchor label','Comparison / scope qualification'],anchor_flags))
parts.append('## Later removals: all11 entries\n\nThree operations consolidated records and retained their events; eight were frontier-eligibility exclusions and deleted active events. Original records are retained in the frontier ledger, so the exclusions were not wholesale destruction of historical evidence. They nevertheless change what can be traversed in the graph. Under the current decision5, none of these is approved here as a same-thing duplicate merge.\n\n'+table(['Removed ID','Recorded reason and operation','Decision5 judgement','Reopened basis / limit'],removal_table))
parts.append('### All7 removed links\n\n'+table(['Removed link','Reason and judgement'],[(code(k),v) for k,v in LINK_REMOVALS.items()]))
parts.append('## Later additions: all66 entries\n\nAll66 fall under the new date representation, all-entry tier pass and strict identity rule. Seven arrived after f12527a: Mendeleev, kayak, snowshoe, snow goggles, snow-block shelter, ammonia-soda and Dalton’s chemical atomic framework. The table gives specific consequences in addition to those universal requirements. A blank earlier-history investigation is not agreement that the selected date is the first record. This is a policy-impact screen of committed records, not a substitute independent audit of their335 new sources. No new historical date has been invented or applied.\n\n'+table(['Added ID','Entry','Current kind / tier / anchor','Specific impact of decisions1–5'],added_table))
parts.append('### All8 added links\n\nAll8 need the influence field/review binding under decision4, without replacing evidence confidence. Two use the retired observed-combination type. The paper/printing, ammonia, X-ray and network branches now exist, but the old audits did not review these records.\n\n'+table(['Added ID','Endpoints','Current type','Decision impact','Current evidence locators, not fresh acceptance'],new_link_table))
parts.append('## Retained records modified since the audits\n\n'+table(['Entry','What changed / consequence'],[
 [code('elec-fairchild-physical-isolation-1960'),'Later batch added an end-1960 Phase Two phase-out decision and refined the Life publication evidence. This new decision/event is not historical acceptance by either old audit; publication and physical-implementation dates remain separate.'],
 [code('elec-hoerni-planar-transistor-1959'),'Conception events and class scope absorbed; concept-to-Noyce retargeted. Revisit separate conception/device roles under decision5 and use earliest-record rather than late sale for the chart.'],
 [code('mech-harrison-h4-watch'),'K1 completion/voyage events absorbed and K2 source retargeted. Separate watches/dates/roles remain real; same-family or adaptation is different from identity.'],
 [code('mech-condenser-model-1765'),'Bloomfield installation/event and two incoming links absorbed. Early arrangement/model and later full-scale deployment must remain distinguishable.'],
 [code('math-khwarizmi-indian-arithmetic-825'),'Latin branches moved into provenance prose; their active events/links removed. Prose preservation does not replace a traversable transmission chain; reordering comparator still needs qualification.'],
 [code('math-gwalior-place-value-inscription'),'Widened to circular-zero decimal notation, added Talang Tuwo684 event and sources, changed anchor. This is a materially new proposition; do not apply the old Gwalior-witness verdict as approval.'],
 [code('med-forbes-stethoscope-chichester-1822'),'Widened to Laennec instrument/method, added1819 publication, retained Forbes use and added Paris. Old local-witness criticisms are partly addressed; earliest conception/use still needs the Stage3 check.'],
 [code('med-lister-antisepsis-preston-1869'),'Widened to Lister method, added byApril1867 use evidence and Glasgow while retaining Preston. Old region error is not a rule to delete Glasgow from this broader scope.'],
 [code('global-hokulea-design-study-1973'),'Removed vessel/build relation preserved as provenance context rather than a traversable edge; no new proof that design and vessel are duplicates.'],
 [code('global-hokulea-wayfinding-trial-1980'),'Removed platform-use history preserved in provenance and vessel sources retained. The1980 experiment still depends on an experimental platform role.'],
 [code('mat-bessemer-air-conversion'),'Later batch added scoped U.S. establishment counts, U.S. output decline and Workington end-of-use evidence. This is new lifecycle content, not a new invention or a date replacing earlier air-conversion evidence.'],
 ]))
parts.append('After f12527a the already-added ARPANET, IBM726, RAMAC, Birkeland–Eyde, continuous-wire papermaking and Linotype nodes also acquired lifecycle/context evidence. The Notodden1934 end event was qualified. The one changed old source, entry-src-micrologic-life, gained inspected-passage metadata; its retained file hash is unchanged. These changes need their own evidence/review assessment; neither old audit certified them.\n')
parts.append('The four surviving links changed are '+', '.join(code(x) for x in manifest['changes_since_audited_snapshot']['relationships']['changed'])+'. They were retargeted during the three consolidations. Event IDs mostly survived, which preserves useful evidence, but a new node endpoint is a new proposition and requires its own review; it is not covered by either old audit.\n')

gaps=rows(INDEPENDENT/'gaps.jsonl');read_gaps=[g for g in gaps if g['type']=='missing_connection' and g['check_method']=='read_source_locally']
assert {g['rank'] for g in read_gaps}==set(GAP_FINDINGS)
parts.append('## The review’s Read gap proposals\n\nFourteen connection proposals are marked Read. That means a passage was located; it does not automatically prove the proposed endpoints or relation. The following table reopens/adjudicates every one. Knowledge-only and record-only proposals remain leads; none enters data in Stage1.\n\n'+table(['Rank / endpoints','Comparison after reopening'],[[str(g['rank'])+' '+code(g['from'])+' → '+code(g['to']),GAP_FINDINGS[g['rank']]] for g in read_gaps]))
parts.append('Additional gap disagreements: Elsecar1795 cannot be an ancestor of Watt1765 merely because both are Newcomen-type; the review itself admits it needs a different general source identity. A Faraday disc is not automatically a physical ancestor of a later dynamo. Similarity/family, bounded function and actual transmission are different propositions. The surviving speculative refusals remain refused: no Oughtred→Soho, Newton→Abbe or4004→genome leap is approved. Briggs→Gunter and Abu Kamil→Leonardo are worthwhile sourced leads, not accepted because both names are familiar.\n')

self_labels={x['id']:x for x in rows(OUT/'label-verdicts.jsonl')}
A={k for k,v in self_labels.items() if v['verdict']=='change'};B={k for k,v in other_entries.items() if v.get('label_issue')}
parts.append('## Label comparison\n\nThere are29 shared flags,19 self-only and14 independent-only flags:62 IDs in the union. Silence in one audit is not opposition to the other suggestion. The old importer produced its intended outputs; the disputes are semantics and vocabulary. Current main’s later overrides are a different input and have not been certified by either old label audit. Stage5 should replace the regex derivation with explicit reviewed labels.\n')
label_other={
 'bio-dna-polymerase-preparation-1957':'Accept: enzyme/reagent is not hardware merely because polymerase matched. Use molecular biology and a reviewed reagent/method topic.',
 'bio-taq-pcr-immunology-1989':'Accept: PCR is a method; Instruments should describe actual hardware or a clearly defined tool-inclusive category.',
 'elec-fairchild-silicon-gate-3708-1968':'Accept the analog-multiplexer distinction; Integrated circuits is more accurate than Computing inferred from the word multiplexer.',
 'elec-helmholtz-dielectric-test-1879':'Prefer Electromagnetism for the scoped prize/investigation, not Radio merely because it precedes radio history.',
 'elec-kilby-germanium-oscillator-1958':'Accept Integrated circuits/electronics; a surname does not make an oscillator Computing.',
 'elec-noyce-planar-interconnection-1959':'Accept Integrated circuits; Computing cannot be inferred from Noyce’s name alone.',
 'elec-point-contact-amplifier-1947':'Not a plain factual bug: germanium is the active material. Decide whether Materials covers semiconductor material use; label it explicitly rather than by substring.',
 'entry-regional-inca-storehouse-quipu':'Information/accounting is appropriate to the stated scope; Communication needs the referent/evidence, and the specific observation remains unverified.',
 'global-bi-sheng-fired-types':'Not automatically a false Materials hit: fired clay units are a material/process contribution. A defined Printing label is essential; keep/remove Materials by an explicit inclusion rule.',
 'mat-gerlafingen-oxygen-trials':'Accept consistent Materials/metallurgy coverage if the label means production-process topics.',
 'mat-linz-soft-blowing-trials':'Accept the same metallurgy/materials convention as comparable steel processes.',
 'math-dutch-spyglass-1608':'Prefer Optics and Instruments; glass in a device name alone does not establish a material advance.',
 'mech-aljazari-donkey-water-lift-1315':'Accept Mechanisms alongside water; do not equate every mechanism with precision machining.',
 'mech-portsmouth-block-mills':'Accept manufacturing/precision-making rather than assuming a grain mill from mills. Keep the integrated-system role.',
}
assert set(label_other)==B-A
parts.append(table(['Independent-only flag','Adjudication'],[(code(k),v) for k,v in label_other.items()]))
parts.append('\n'+table(['Self-only flag','Reason to retain or define'],[(code(k),self_labels[k]['issue']) for k in sorted(A-B)]))
parts.append('\nThe29 shared labels concern the acidimeter, Google Glass, glass-vessel/optics conflation, molecular/medical topics, mathematical coverage, steam omissions and related spelling failures; IDs: '+', '.join(map(code,sorted(A&B)))+'. Both accept their correction; precise final assignment follows explicit label definitions.\n')
parts.append('The review’s vocabulary direction is sound: separate Optics from Glass; widen Genetics to Molecular biology; use Navigation and seafaring; add Integrated circuits, Agriculture, Mechanisms and Medicine/microbiology. My earlier aquaculture, immunology and broader maritime/transport suggestions can be represented as reviewed subtopics or additional labels where useful. Energy and Spread of knowledge need inclusion definitions rather than automatic merging of unlike topics. These are modelling choices; no new label set has been written.\n')

gap_status={2:'Now represented by cont-a-handformed-fibre-sheet; earliest-record and scope review still needed.',7:'Partly: universal gravitation added, but calculus is not thereby represented.',8:'Partly: Kepler’s Mars ellipse added; Copernicus and broader heliocentric system are not covered by that one model.',11:'Now represented by industrial ammonia synthesis; arc-fixation alternative and local replacement are also present.',18:'Partly: circular-zero notation widened, but this is not the whole decimal place-value arithmetic system.',20:'Partly: predictive periodic system and Dalton’s scoped chemical atomic framework added after f12527a. Lavoisier’s chemical revolution remains a distinct gap; the new Dalton record is not certified by the old audits.',24:'Partly: ARPANET, ALOHAnet and Ethernet added; TCP/IP is still a separate gap.',29:'Partly: optical-fiber links added; this does not supply the laser or Kao’s particular theoretical/material contribution.',30:'Still missing, and the c.1000–1300CE scope must be corrected: distinguish earlier Remote Oceania settlement from later East Polynesian expansion.'}
parts.append('## Missing breakthroughs: compare the30 review leads with main\n\nThese are coverage statuses, not source approvals. The original likely-source leads remain in the independent gaps file. No new entry is authorized merely by appearing in this table.\n\n'+table(['Priority / proposed breakthrough','Current status'],[[str(g['rank'])+' '+g['name'],gap_status.get(g['rank'],'Not supplied by a matching current entry. Related instruments, products or applications do not fill the general gap.')] for g in gaps if g['type']=='missing_breakthrough']))
parts.append('Our self-audit also proposed general scientific and engineering capabilities rather than automatically linking all witnesses: its polymerase-to-sequencing functional use, sequence-chemistry-to-genome-production, oxide/patterning-to-planar, Joule apparatus adaptation and Briggs/Gunter leads overlap the review’s repair programme. Its material/procurement and Tirta/subak proposals were explicitly bounded/unverified; the review’s desire for connectedness does not remove those limits. The important new review priority I accept is restoring the DNA-structure and Fleming/Oxford context, while retaining the exact-event and historian qualifications above.\n')
parts.append('The30-breakthrough lists are capped prioritisation proposals, so an item omitted from one is not a disagreement about whether it happened. Distinct self-audit emphases absent from the independent30 include controlled fire, early pottery, wheel-and-axle transport, variolation, ether anaesthesia, urban water filtration, Shannon communication theory, programmable Cas9 and antibiotic-production scale-up. Distinct independent emphases absent from my30 include Gutenberg, Newcomen, railways, compass, gunpowder, Ibn al-Haytham, fission/reactors, early stored-program origins, ARPANET/TCP-IP, powered flight, telephone, dynamo/lamp, laser/fibre and Oceanian settlement. Both include food production, writing, paper, iron, Euclid, algebra, heliocentrism, Newton/calculus, vaccination/germ theory, evolution, periodic classification, ammonia synthesis, modern physics, electronic amplification and the junction transistor, at different granularities. Use the review list as the owner-directed starting queue, source every knowledge-only lead, and split bundled claims before admission. No new research batch has been launched to fill these lists.\n')
parts.append('## Historian flags retained, and the stop\n\nNo Stage1 adjudication settles: (1) Muldoons construction/use/phasing; (2) the precise timing and wording of Franklin’s pre-model contribution routes; (3) the specific Volta-to-trough transmission; (4) Hoerni/Fairchild access to Atalla/Bell oxide work; (5) actual Shadwell expansive operation; (6) Barbegal function and precise chronology; (7) independent Wright-engine aluminum procurement; (8) Jikji woodblock descent from the metal edition. The additional early junction-isolation chronology and Humulin first-sale tensions remain explicit too.\n\nThe next authorized action after the owner replies is Stage2, committed separately: remove the two presently unsupported drawn associations if this comparison is accepted, draft only the Read proposals that survive passage AND endpoint checks, and correct verified facts. It must not include knowledge-only leads, automatic duplicate merges, a second relation-label scheme or premature analysis labels. Stage3 then shows about10 actual re-anchorings before scaling. **This task stops after committing and reporting Stage1.**\n')

path=OUT/'COMPARISON.md';text=path.read_text().split('<!-- GENERATED CASE TABLES BELOW: comparison_report.py -->')[0]
assembled=text+'<!-- GENERATED CASE TABLES BELOW: comparison_report.py -->\n\n'+'\n'.join(parts)
# Improve prose spacing without changing identifiers, inline code or link URLs.
segments=re.split(r'(`[^`]*`|\]\([^)]*\))',assembled)
for i,segment in enumerate(segments):
    if segment.startswith('`') or segment.startswith(']('):continue
    segment=re.sub(r'(?<=[A-Za-z])(?=(?:1\d{3}|20\d{2})\b)',' ',segment)
    segment=re.sub(r'\b(Stage|stage|tier|decision)([0-9])\b',r'\1 \2',segment)
    segment=re.sub(r'\bc\.(?=\d)','c. ',segment)
    segment=re.sub(r'\b(all|All|their|the|There are|my|our|another|and)(?=\d)',r'\1 ',segment)
    segment=re.sub(r'(?<=\d)(?=(?:entries|entry|events|connections|sources|IDs|cases|labels|nodes|tests|files|new|removed|retained|added|shared|self-only|independent-only)\b)',' ',segment)
    segments[i]=segment
path.write_text(''.join(segments))
(OUT/'comparison-findings.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in details))
checks={'base_commit':BASE,'main_compared':MAIN,'connections_accounted_for':{'shared_agree':91,'comparison_cases':len(connection_table),'total':131},'entry_comparison_cases':len(entry_table),'independent_anchor_flags':len(anchor_flags),'removed_entries':len(REMOVALS),'removed_links':len(LINK_REMOVALS),'added_entries':len(added_table),'added_links':len(new_link_table),'read_gap_proposals':len(read_gaps),'label_union':len(A|B),'no_canonical_data_mutation_by_this_audit':True,'preservation':{'initial_evidence_files':156,'present_with_original_hash':156,'initial_generated_build_cache':'absent at closeout; not deleted by this audit'},'validation':{'graph_validator':'valid:true; zero errors and zero concerns on 276 nodes, 535 events, 132 links, 645 sources','web_tests':'11 files,133 tests passed from an isolated archive of committed c388b6d; unrelated working-tree UI drafts were not moved or stashed'},'limitations':'No claim of full new-batch historical review, complete lifecycle validation or objective resolution of tier opinions.'}
(OUT/'comparison-checks.json').write_text(json.dumps(checks,indent=2)+'\n')
print(json.dumps(checks,indent=2))
