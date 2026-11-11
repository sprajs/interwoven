from pathlib import Path
import json,hashlib
from collections import Counter
r=Path(__file__).resolve().parent
materials=json.loads((r/'r1-materials/claim_audit.json').read_text())['rows']
industrial=json.loads((r/'r1-industrial/claim-audit.json').read_text())['rows']
parent=json.loads((r/'r1-parent/claim_audit.json').read_text())
graph=json.loads((r/'r1-graph/edge_audit.json').read_text())
claims={}
for reviewer,rows,path in [('materials',materials,'r1-materials/claim_audit.json'),('industrial',industrial,'r1-industrial/claim-audit.json'),('parent',parent,'r1-parent/claim_audit.json')]:
 for x in rows:
  ident=x.get('claim_id',x.get('id'));claims.setdefault(ident,[]).append({'reviewer':reviewer,'audit_file':path,'disposition':x['disposition']})
ma=json.loads((r/'r1-materials/edge_audit.json').read_text())['edge_ids']
ib=[x['id'] for x in json.loads((r/'r1-industrial/edge-audit.json').read_text())]
gc=graph['sample_edge_ids'];edges=sorted(set(ma+ib+gc))
sources=set(s['source_id'] for x in materials for s in x['sources_passages_inspected_access'])
sources.update(s['source_id'] for x in industrial for s in x['sources_locators_actually_inspected'])
sources.update(s for x in parent for s in x['source_ids'])
sources.update(s['source_id'] for s in graph['source_passage_checks'])
counts={};corecases=set()
for pref in ['MAT','ANC','IND','LBR']:
 p=r/'r1-snapshot/contributions'/pref
 rows=json.loads((p/'claims.json').read_text())
 counts[pref]={'cases':len(json.loads((p/'cases.json').read_text())),'claims':len(rows),'sources':len(json.loads((p/'sources.json').read_text())),'edges':len(json.loads((p/'graph.json').read_text())['edges']),'source_audited_claims':len([x for x in claims if x.startswith(pref+'-')])}
 for x in rows:
  if x['id'] in claims:corecases.update(x['case_ids'])
ordinary=['MAT-K01','MAT-K22','ANC-K08','ANC-K14','IND-K23','LBR-K03']
passage_edges=sorted((set(ma+ib)-{'IND-E14'}) | {e for s in graph['source_passage_checks'] for e in s['supports_edge_ids']})
scope={'snapshot_manifest':'r1-snapshot/MANIFEST.json','snapshot_manifest_sha256':hashlib.sha256((r/'r1-snapshot/MANIFEST.json').read_bytes()).hexdigest(),'selection':'Risk-based source samples saved before checking; graph sample adaptive risk selection; one disclosed parent follow-up IND-K11 to adjudicate IND-E14. No statistical error-rate inference.','snapshot_counts':{'cases':23,'claims':78,'source_records':49,'nodes':93,'edges':72,'comparisons':13},'per_dossier':counts,'source_audited_unique_claim_count':len(claims),'source_audited_claim_ids':sorted(claims),'core_claim_cases':sorted(corecases),'ordinary_descriptive_control_ids':ordinary,'detailed_edge_count':len(edges),'detailed_edge_ids':edges,'edge_source_passage_checks_before_parent_followup':passage_edges,'adaptive_edge_followup':'IND-E14: relevant co-support IND-K11 inspected by parent; remains unresolved scope/provenance, not counted as upheld','record_only_detailed_edges':sorted(set(edges)-set(passage_edges)-{'IND-E14'}),'unique_frozen_source_records_passage_checked':sorted(sources),'source_record_count':len(sources),'claim_review_index':claims,'extra_graph_claim_scope':'ANC-K09 and ANC-K11 were checked for edge-level subpropositions, not counted as full standalone claim audits. Other graph-linked claims are record checks only unless listed in source_audited_claim_ids.','completion_limit':'IND is included as delivered substantive records but provisional: frozen validation lists it complete while questions.md is absent. Rebuild gate excludes it until real handoff complete.'}
(r/'AUDIT_SCOPE_R1.json').write_text(json.dumps(scope,indent=2,ensure_ascii=False)+'\n')
print(json.dumps({k:v for k,v in scope.items() if k in ['per_dossier','source_audited_unique_claim_count','detailed_edge_count','source_record_count','record_only_detailed_edges','unique_frozen_source_records_passage_checked','edge_source_passage_checks_before_parent_followup']},indent=2))
