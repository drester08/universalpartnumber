"""Exact evidence proposal isolation; synthetic mutations are never approvals."""
import copy
import hashlib
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import check_ntn_6204zz_closure_mapping as c
import screen_candidates
import build_review_queue
import build_registry


class ClosureTests(unittest.TestCase):
    def setUp(self):
        self.db=sqlite3.connect(':memory:')
        source=sqlite3.connect(c.ROOT/'build/registry.sqlite')
        source.backup(self.db)
        source.close()
        self.db.row_factory=sqlite3.Row

    def tearDown(self):
        self.db.close()

    def test_evidence_proposal_and_review_task(self):
        report=c.verify(self.db)
        self.assertFalse(report['identity_approved'])
        self.assertEqual(report['mapping']['mapping_state'],'proposed')
        queue=build_review_queue.build_items(self.db)
        tasks=[r for r in queue if r['subject_id']==c.EXPECTED['mapping_id']]
        self.assertEqual(len(tasks),1)
        self.assertEqual(tasks[0]['queue_type'],'terminology_mapping_review')
        self.assertIn(c.REPORT_SHA,tasks[0]['next_action'])

    def test_exact_normalization_no_cross_brand_inheritance(self):
        parts=screen_candidates.load_parts(self.db)
        self.assertEqual(parts['MP-NTN-6204ZZ']['values']['PROP-BEARING-CLOSURE'],{'double_non_contact_metal_shield'})
        self.assertFalse(parts['MP-NSK-6204ZZ']['values'].get('PROP-BEARING-CLOSURE'))
        self.assertFalse(any('MP-NTN-6204ZZ' in (r['left_part_id'],r['right_part_id']) for r in screen_candidates.screen(self.db,'2026-10-01')))
        self.assertEqual(self.db.execute('SELECT count(*) FROM upn_allocations').fetchone()[0],0)

    def test_rejected_mapping_not_used_in_screen(self):
        self.db.execute("UPDATE specification_value_mappings SET mapping_state='rejected' WHERE mapping_id=?",(c.EXPECTED['mapping_id'],))
        self.assertFalse(screen_candidates.load_parts(self.db)['MP-NTN-6204ZZ']['values'].get('PROP-BEARING-CLOSURE'))

    def test_approval_or_moved_scope_rejected(self):
        for key,value in [('mapping_state','approved'),('specification_id','SPEC-NTN-6205ZZ-CLOSURE'),('rationale','Other article evidence')]:
            row=copy.deepcopy(c.EXPECTED)
            row[key]=value
            with self.assertRaisesRegex(ValueError,'scope/state/evidence'):
                c.verify_mapping_row(row)

    def test_source_custody_change_rejected(self):
        self.db.execute("UPDATE source_artifacts SET sha256=? WHERE artifact_id='ART-NTN-SHIELD-SEAL-3015'",('0'*64,))
        with self.assertRaisesRegex(ValueError,'source custody'):
            c.verify(self.db)

    def test_report_revision_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            (root/'reports').mkdir()
            (root/'reports'/c.REPORT_NAME).write_text('{}',encoding='utf-8')
            with patch.object(c,'ROOT',root):
                with self.assertRaisesRegex(ValueError,'report revision'):
                    c.verify(self.db)

    def test_controlled_value_meaning_change_rejected(self):
        self.db.execute("UPDATE controlled_values SET canonical_code='different_closure' WHERE controlled_value_id=?",(c.EXPECTED['controlled_value_id'],))
        with self.assertRaisesRegex(ValueError,'controlled-value meaning'):
            c.verify(self.db)

    def test_raw_fact_and_historical_report_unchanged(self):
        before=self.db.total_changes
        c.verify(self.db)
        self.assertEqual(self.db.total_changes,before)
        self.assertEqual(self.db.execute("SELECT raw_value FROM specification_values WHERE specification_id='SPEC-NTN-6204ZZ-CLOSURE'").fetchone()[0],'Double Shielded')
        self.assertEqual(hashlib.sha256((c.ROOT/'reports'/c.REPORT_NAME).read_bytes()).hexdigest().upper(),c.REPORT_SHA)

    def test_failed_binding_preserves_existing_database(self):
        with tempfile.TemporaryDirectory() as folder:
            output=Path(folder)/'registry.sqlite'
            output.write_bytes(b'previous verified database fixture')
            with patch.object(c,'verify',side_effect=ValueError('changed evidence fixture')):
                with self.assertRaisesRegex(ValueError,'changed evidence'):
                    build_registry.build(output)
            self.assertEqual(output.read_bytes(),b'previous verified database fixture')
            self.assertFalse(output.with_suffix('.tmp').exists())


if __name__=='__main__':
    unittest.main()
