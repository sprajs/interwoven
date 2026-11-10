"""Pilot-to-sweep invariants independent of private evidence and model calls."""
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/cards'))
import quality_sweep as q

class QualitySweepTest(unittest.TestCase):
    def test_blind_groups_cover_six_unique_variants_and_two_reviewers(self):
        groups=q.blind_groups('candidate-test')
        self.assertEqual([len(g) for g in groups],[3,3])
        self.assertEqual(set().union(*(set(g.values()) for g in groups)),set(q.SETTINGS))
        self.assertEqual(groups,q.blind_groups('candidate-test'))
        self.assertEqual(set(q.JUDGES),{'astra_medium','sol_high'})
        self.assertIn('terra_high',q.SETTINGS)
        self.assertIn('sol_medium',q.SETTINGS)

    def test_reference_and_claim_coverage_is_strict(self):
        case={'id':'candidate-test'}
        labeled=q.blind_groups(case['id'])[0]
        def final(_,name,repeat=False):
            return {'decision':'admit_minimal','claims':[{'statement':'example'}]}
        def response(variants):
            return {'parsed':{'case_id':case['id'],'reference_decision':'admit_minimal','reference_note':'source',
                    'variants':variants}}
        base=[{'label':label,'false_reject':False,'source_flagged_admission':False,
               'claims':[{'index':0,'verdict':'supported','reason':'source'}]} for label in labeled]
        with patch.object(q,'answer',side_effect=final),patch.object(q,'stored',return_value=response(base)),patch.object(q.compare,'mechanical',return_value={'pass':True}):
            assessed=q.checked_judgment(case,'astra_medium',0)
            self.assertEqual(set(assessed),set(labeled.values()))
        duplicate=[dict(x) for x in base];duplicate[1]['label']=duplicate[0]['label']
        with patch.object(q,'stored',return_value=response(duplicate)):
            with self.assertRaisesRegex(ValueError,'Duplicate or missing label'):
                q.checked_judgment(case,'astra_medium',0)
        boolean=[dict(x) for x in base];boolean[0]['claims']=[{'index':True,'verdict':'supported','reason':'source'}]
        with patch.object(q,'answer',side_effect=final),patch.object(q,'stored',return_value=response(boolean)):
            with self.assertRaisesRegex(ValueError,'Incomplete/bad claim'):
                q.checked_judgment(case,'astra_medium',0)

    def test_case_group_survives_blind_group_iteration(self):
        case={'id':'candidate-test','candidate':{'name':'Example'}}
        judgment={'reference_decision':'admit_minimal','source_flagged_admission':False,
                  'false_reject':False,'useful_record':True,'claim_verdicts':[],
                  'unresolved_admitted_claims':0}
        assessed={name:judgment for name in q.SETTINGS}
        call={'parsed':{'decision':'admit_minimal','claims':[]},'usage_records':{},'elapsed_seconds':1}
        with patch.object(q,'read',return_value={'fresh_ids':[case['id']]}), \
             patch.object(q,'checked_judgment',return_value=assessed), \
             patch.object(q,'stored',return_value=call), \
             patch.object(q.compare,'mechanical',return_value={'pass':True,'errors':[]}):
            rows=q.review_rows([case])
        self.assertEqual(len(rows),len(q.SETTINGS))
        self.assertEqual({row['group'] for row in rows},{'fresh'})

    def test_repeat_plan_rejects_changed_pair_and_call_fingerprint(self):
        case={'id':'candidate-test'}
        registration={'fresh_ids':[case['id']],'regression_ids':[]}
        plan={'case_ids':[case['id']],'review_settings':['astra_medium','astra_low'],
              'completed_review_fingerprints':[{'case_id':case['id'],'variant':'astra_medium','fingerprint':'original'}]}
        with tempfile.TemporaryDirectory() as directory, \
             patch.object(q,'STATE',Path(directory)), \
             patch.object(q,'registration',return_value=registration), \
             patch.object(q,'case_contexts',return_value=[case]), \
             patch.object(q,'review_rows') as review_rows, \
             patch.object(q,'publish') as publish:
            with patch.object(q,'read',return_value={**plan,'review_settings':['terra_medium','astra_low']}):
                with self.assertRaisesRegex(ValueError,'Frozen repeat plan mismatch'):
                    q.run_repeat()
            with patch.object(q,'read',return_value=plan), \
                 patch.object(q,'stored',return_value={'fingerprint':'changed'}):
                with self.assertRaisesRegex(ValueError,'Immutable repeat review changed'):
                    q.run_repeat()
            review_rows.assert_not_called()
            publish.assert_not_called()

if __name__=='__main__':unittest.main()
