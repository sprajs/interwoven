"""Accounting boundary tests; synthetic inputs never enter comparison artifacts."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[2]
SPEC=importlib.util.spec_from_file_location('analysis',ROOT/'tools/cards/analyze_comparison.py')
analysis=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(analysis)
VIEWER_SPEC=importlib.util.spec_from_file_location('comparison_viewer',ROOT/'tools/cards/comparison_viewer.py')
viewer=importlib.util.module_from_spec(VIEWER_SPEC);VIEWER_SPEC.loader.exec_module(viewer)
class AnalysisTest(unittest.TestCase):
    def test_public_claim_labels_survive_without_private_explanations(self):
        safe=analysis.public_judgment({'arm':'A','claim_judgments':[{
            'index':0,'verdict':'unsupported','error_types':['link','scope'],
            'rationale':'PRIVATE SOURCE CONTEXT','original_context':'PRIVATE PASSAGE'}]})
        self.assertEqual(safe['claim_judgments'],[{'index':0,'verdict':'unsupported','error_types':['link','scope']}])
        self.assertNotIn('PRIVATE',json.dumps(safe))

    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);(self.root/'calls').mkdir()
        self.cases=[{'id':f'test-{i}','split':'held_out' if i>=20 else 'calibration','stratum':'test','candidate':{'name':f'Test {i}'}} for i in range(100)]
        self.casepath=self.root/'cases.json';self.casepath.write_text(json.dumps({'cases':self.cases}))
    def tearDown(self):self.tmp.cleanup()
    def call(self,name,**kwargs):
        value={'case_id':'test-20','label':'A-extract','status':'success','started':100,'elapsed_seconds':10,'params':{'model':'gpt-6-luna','effort':'low'},'usage_records':{'response-1':{'input_tokens':100,'cached_input_tokens':20,'cache_write_input_tokens':10,'output_tokens':40,'reasoning_output_tokens':15}},'parsed':{'claims':[{'quote':'private quotation','statement':'A bounded claim'}]},'prompt':'private input','stderr':'private diagnostics'}
        value.update(kwargs);(self.root/'calls'/name).write_text(json.dumps(value));return value
    def test_global_dedup_and_subset_cost(self):
        self.call('first.json');self.call('repeat.json',started=105)
        result,rows,safe=analysis.analyze(self.root,self.casepath)
        totals=result['accounting']['totals']
        self.assertEqual(totals['unique_responses'],1);self.assertEqual(totals['duplicate_response_ids'],1)
        self.assertEqual(totals['input_tokens'],100);self.assertEqual(totals['uncached_input_tokens'],70)
        self.assertEqual(totals['output_tokens'],40);self.assertEqual(totals['reasoning_output_tokens'],15)
        self.assertAlmostEqual(totals['api_equivalent_usd'],(70*.1+20*.01+10*.125+40*.5)/1e6)
        self.assertEqual(totals['elapsed_sum_seconds'],20);self.assertEqual(totals['elapsed_wall_seconds'],15)
        public=json.dumps(safe)
        self.assertNotIn('private quotation',public);self.assertIn('quote_sha256',public)
        self.assertNotIn('private input',public);self.assertNotIn('private diagnostics',public)
        self.assertEqual(len(safe['cases']),100)
    def test_conflicting_response_id_rejected(self):
        self.call('first.json');self.call('second.json',usage_records={'response-1':{'input_tokens':101,'output_tokens':40}})
        with self.assertRaisesRegex(ValueError,'Conflicting'):analysis.analyze(self.root,self.casepath)
    def test_no_placeholder_and_invalid_token_scalars(self):
        with self.assertRaisesRegex(ValueError,'No actual'):analysis.analyze(self.root,self.casepath)
        with self.assertRaises(ValueError):analysis.checked_usage({'input_tokens':10,'cached_input_tokens':11})
        with self.assertRaises(ValueError):analysis.checked_usage({'output_tokens':10,'reasoning_output_tokens':11})
    def test_quality_denominators_and_no_confident_winner(self):
        groups={'A|held_out|review':{'api_equivalent_usd':2}}
        judgments={'reference_standard':'model_only','adequate_independent_reference':True,'judgments':[{'case_id':'test-20','arm':'A','resolved':True,'reference_admit':True,'false_reject':True,'false_admission':False,'unsupported_facets':0,'unsupported_links':0,'useful_reviewed_record':False,'supported_claims':2},{'case_id':'test-21','arm':'A','resolved':False,'reference_admit':True,'false_reject':True,'false_admission':False,'unsupported_facets':0,'unsupported_links':0,'useful_reviewed_record':False,'supported_claims':0}]}
        result=analysis.quality_metrics(self.cases,judgments,groups,self.passing_checks());a=result['arms']['A']
        self.assertEqual(a['resolved_reference_admissions'],1);self.assertEqual(a['false_reject_rate'],1)
        self.assertEqual(a['unresolved_cases'],1);self.assertFalse(a['provisional_quality_gate'])
        self.assertEqual(a['cost_per_supported_claim_usd'],1);self.assertIsNone(a['cost_per_useful_reviewed_record_usd'])
        self.assertFalse(result['adequate_independent_reference']);self.assertIsNone(result['winner'])
    def passing_checks(self):
        return {(c['id'],arm):{'pass':True,'admission_proposal':True,'failure_categories':[]} for c in self.cases for arm in ('A','B')}
    def judgment(self,index,**kwargs):
        row={'case_id':f'test-{index}','arm':'A','resolved':True,'reference_admit':True,'false_reject':False,'false_admission':False,'unsupported_facets':0,'unsupported_links':0,'unresolved_admitted_claims':0,'useful_reviewed_record':True,'supported_claims':1}
        row.update(kwargs);return row
    def test_unresolved_reference_does_not_hide_unsupported_admission(self):
        rows=[self.judgment(i) for i in range(20,100)]
        rows[0]=self.judgment(20,resolved=False,false_admission=True,unsupported_facets=1,unsupported_links=1,unresolved_admitted_claims=1)
        result=analysis.quality_metrics(self.cases,{'judgments':rows},{},self.passing_checks())['arms']['A']
        self.assertEqual(result['false_admissions'],1)
        self.assertEqual(result['unsupported_facets'],1)
        self.assertEqual(result['unsupported_links'],1)
        self.assertFalse(result['provisional_quality_gate'])
        self.assertEqual(result['supported_claims'],80)
    def test_correct_source_deferrals_allow_complete_provisional_gate(self):
        rows=[self.judgment(i) for i in range(20,100)]
        for i in range(10):rows[i]=self.judgment(20+i,resolved=False,reference_admit=False,useful_reviewed_record=False,supported_claims=0)
        result=analysis.quality_metrics(self.cases,{'judgments':rows},{},self.passing_checks())['arms']['A']
        self.assertTrue(result['judgment_coverage_complete'])
        self.assertEqual(result['unresolved_cases'],10)
        self.assertEqual(result['resolved_reference_admissions'],70)
        self.assertTrue(result['provisional_quality_gate'])
        self.assertEqual(result['useful_reviewed_records'],70)
    def test_missing_quality_stays_unknown(self):
        rows=[self.judgment(i) for i in range(20,100)]
        del rows[0]['unresolved_admitted_claims']
        result=analysis.quality_metrics(self.cases,{'judgments':rows},{},self.passing_checks())['arms']['A']
        self.assertIsNone(result['provisional_quality_gate'])
        self.assertIsNone(result['unresolved_admitted_claims'])
        self.assertEqual(result['unknown_quality_cases'],1)
    def test_svg_held_out_review_count_excludes_calibration(self):
        self.call('calibration.json',case_id='test-0',label='A-review')
        self.call('heldout.json',case_id='test-20',label='A-review',usage_records={})
        result,_,_=analysis.analyze(self.root,self.casepath)
        self.assertEqual(result['coverage']['completed_review_counts']['A'],2)
        self.assertEqual(result['coverage']['completed_held_out_review_counts']['A'],1)
        self.assertIn('Held-out reviewed: 1/80',analysis.svg(result))
    def test_overhead_separate_and_svg_valid(self):
        self.call('reference.json',label='reference');self.call('proposal.json',case_id='proposal-sol',label='job',usage_records={})
        result,rows,safe=analysis.analyze(self.root,self.casepath)
        self.assertIn('overhead|held_out|reference',result['accounting']['groups'])
        self.assertIn('overhead|overhead|proposal',result['accounting']['groups'])
        from xml.etree import ElementTree
        ElementTree.fromstring(analysis.svg(result))
    def test_native_viewer_strips_markdown_tables_and_keeps_prose(self):
        text='Before.\n\n| Arm | Cost |\n| --- | ---: |\n| A | 1 |\n\nAfter.'
        stripped=viewer.strip_markdown_tables(text)
        self.assertNotIn('|',stripped)
        self.assertIn('Before.',stripped);self.assertIn('After.',stripped)
        self.assertIn('quality-unit-cost',viewer.COMPONENT)
        self.assertIn('maximumFractionDigits:4',viewer.COMPONENT)
        self.assertIn('Accounting by arm, split and stage',viewer.COMPONENT)
    def test_markdown_group_keys_do_not_break_table_columns(self):
        self.call('call.json')
        result,_,_=analysis.analyze(self.root,self.casepath)
        markdown=analysis.report(result)
        row=next(line for line in markdown.splitlines() if line.startswith('| A / held_out / extract'))
        self.assertEqual(row.count('|'),9)
    def test_observed_zero_and_unknown_tool_calls_are_distinct(self):
        self.call('observed.json',observed_tool_calls=[])
        self.call('unknown.json',usage_records={})
        result,rows,safe=analysis.analyze(self.root,self.casepath)
        rows={r['call_file']:r for r in rows}
        self.assertEqual(rows['observed.json']['observed_tool_calls'],0)
        self.assertIsNone(rows['unknown.json']['observed_tool_calls'])
        self.assertEqual(result['accounting']['totals']['tool_observation_unknown_calls'],1)
        self.assertEqual(result['accounting']['totals']['observed_tool_calls'],0)
        self.assertIsNone(result['accounting']['provider_reported_tool_search_usage'])
        self.assertNotIn('private input',json.dumps(result))
        self.assertNotIn('private input',json.dumps(safe))
    def test_tool_audit_requires_exact_hash_and_fingerprint(self):
        self.call('old.json',fingerprint='exact-fingerprint')
        path=self.root/'calls/old.json'
        audit={'calls':[{'call':'old.json','call_sha256':analysis.sha(path.read_bytes()),'fingerprint':'exact-fingerprint','observed_tool_calls':[{'name':'web.search','count':2,'source':'rollout'}],'tool_free':False}]}
        auditpath=self.root/'tool-audit.json';auditpath.write_text(json.dumps(audit))
        result,rows,_=analysis.analyze(self.root,self.casepath)
        self.assertEqual(rows[0]['observed_tool_calls'],2)
        self.assertEqual(result['input_hashes']['tool_audit_sha256'],analysis.sha(auditpath.read_bytes()))
        for field in ('call_sha256','fingerprint'):
            original=audit['calls'][0][field];audit['calls'][0][field]='stale'
            auditpath.write_text(json.dumps(audit))
            result,rows,_=analysis.analyze(self.root,self.casepath)
            self.assertIsNone(rows[0]['observed_tool_calls'])
            self.assertEqual(result['accounting']['totals']['tool_observation_unknown_calls'],1)
            audit['calls'][0][field]=original
    def review_call(self,words=46,decision='admit_minimal'):
        quote=' '.join(f'word{i}' for i in range(words))
        case={'id':'test-20','evidence':[{'id':'source-1','original_context':'Private source context: '+quote}]}
        parsed={'id':'test-20','decision':decision,'claims':[{'facet':'achievement','statement':'Bounded test claim','source_id':'source-1','quote':quote,'earliest_year':None,'latest_year':None,'uncertainty':''}],'rationale':'Test rationale','unresolved':[],'corrections':[]}
        return self.call('review.json',label='A-review',prompt=json.dumps({'case':case}),parsed=parsed)
    def test_original_mechanical_length_vs_presence_and_privacy(self):
        call=self.review_call()
        checks=analysis.review_mechanical(call)
        self.assertFalse(checks['pass']);self.assertEqual(checks['failure_categories'],['quote_length'])
        result,_,safe=analysis.analyze(self.root,self.casepath)
        group=result['mechanical_validation']['groups']['A|held_out']
        self.assertEqual(group['failed_reviews'],1);self.assertEqual(group['failed_admission_proposals'],1)
        self.assertEqual(group['unknown_reviews'],79)
        self.assertNotIn('Private source context',json.dumps(result)+json.dumps(safe))
        call=self.review_call(words=10)
        call['parsed']['claims'][0]['quote']='entirely different source words have no support anywhere at all'
        checks=analysis.review_mechanical(call)
        self.assertEqual(checks['failure_categories'],['quote_presence'])
        self.assertIsNone(analysis.review_mechanical({'prompt':'missing'}))
    def test_mechanical_failure_blocks_usefulness_without_changing_truth(self):
        judgments={'judgments':[self.judgment(i) for i in range(20,100)]}
        checks=self.passing_checks();checks[('test-20','A')]=analysis.review_mechanical(self.review_call())
        result=analysis.quality_metrics(self.cases,judgments,{},checks)['arms']['A']
        self.assertEqual(result['raw_semantic_useful_records'],80)
        self.assertEqual(result['mechanical_blocked_useful_records'],1)
        self.assertEqual(result['useful_reviewed_records'],79)
        self.assertEqual(result['source_judged_supported_claims'],80)
        self.assertEqual(result['usable_supported_claims'],79)
        self.assertEqual(result['false_admissions'],0)
        self.assertFalse(result['provisional_quality_gate'])
    def test_mechanical_unknown_prevents_quality_pass_and_nonadmit_is_distinct(self):
        judgments={'judgments':[self.judgment(i) for i in range(20,100)]}
        checks=self.passing_checks();del checks[('test-20','A')]
        result=analysis.quality_metrics(self.cases,judgments,{},checks)['arms']['A']
        self.assertIsNone(result['provisional_quality_gate']);self.assertIsNone(result['useful_reviewed_records'])
        self.review_call(decision='reject_duplicate')
        result,_,_=analysis.analyze(self.root,self.casepath)
        group=result['mechanical_validation']['groups']['A|held_out']
        self.assertEqual(group['failed_reviews'],1);self.assertEqual(group['failed_admission_proposals'],0)
if __name__=='__main__':unittest.main()
