"""Supplier context registration must not become article approval."""
import sqlite3
import unittest
from unittest.mock import patch
import check_mps_pipe_registration as c
import build_review_queue
import build_registry
import tempfile
from pathlib import Path


class MPSRegistrationTests(unittest.TestCase):
    def setUp(self):
        self.db=sqlite3.connect(':memory:')
        with sqlite3.connect(c.ROOT/'build/registry.sqlite') as original:
            original.backup(self.db)
        self.addCleanup(self.db.close)

    def test_registered_context_not_article(self):
        report=c.verify(self.db)
        self.assertTrue(report['registered_source'])
        self.assertFalse(report['identity_approved'])
        self.assertFalse(report['source_correction_obtained'])
        self.assertEqual(report['article_observations_added'],0)
        self.assertEqual(len(report['questions']),4)
        self.db.execute('UPDATE observations SET source_id=? WHERE observation_id=(SELECT observation_id FROM observations LIMIT 1)',(c.SOURCE,))
        with self.assertRaisesRegex(ValueError,'promoted to article'):
            c.verify(self.db)

    def test_six_new_tasks_with_bound_evidence(self):
        self.db.row_factory=sqlite3.Row
        items=build_review_queue.build_items(self.db)
        new=[r for r in items if r['source_id']==c.SOURCE]
        self.assertEqual(len(new),6)
        self.assertEqual(len(items),466)
        self.assertEqual(sum(r['readiness']=='blocked' for r in items),11)
        scoped=[r for r in new if r['work_item_id'].startswith('RW-MPS-')]
        self.assertEqual(len(scoped),5)
        self.assertTrue(all(c.MPS_SHA in r['next_action'] for r in scoped))

    def test_mill_authority_promotion_rejected(self):
        self.db.execute('UPDATE sources SET authority_tier=1 WHERE source_id=?',(c.SOURCE,))
        with self.assertRaisesRegex(ValueError,'supplier authority'):
            c.verify(self.db)

    def test_invented_publication_date_rejected(self):
        self.db.execute("UPDATE sources SET publication_date='2020-01-01' WHERE source_id=?",(c.SOURCE,))
        with self.assertRaisesRegex(ValueError,'unknown date'):
            c.verify(self.db)

    def test_reuse_gate_change_rejected(self):
        self.db.execute("UPDATE sources SET ingestion_status='reference_only' WHERE source_id=?",(c.SOURCE,))
        with self.assertRaisesRegex(ValueError,'reuse gate'):
            c.verify(self.db)

    def test_custody_tampering_rejected(self):
        self.db.execute('UPDATE source_artifacts SET sha256=? WHERE artifact_id=?',('0'*64,c.ARTIFACT))
        with self.assertRaisesRegex(ValueError,'custody'):
            c.verify(self.db)

    def test_historical_revision_rejected_without_mutation(self):
        before=c.MPS.read_bytes()
        with patch.object(c,'MPS_SHA','0'*64):
            with self.assertRaisesRegex(ValueError,'revision changed'):
                c.verify(self.db)
        self.assertEqual(c.MPS.read_bytes(),before)

    def test_failed_build_preserves_previous_database(self):
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)/'registry.sqlite'
            target.write_bytes(b'previous database placeholder')
            with patch.object(c,'verify',side_effect=ValueError('MPS guard rejected')):
                with self.assertRaisesRegex(ValueError,'guard rejected'):
                    build_registry.build(target)
            self.assertEqual(target.read_bytes(),b'previous database placeholder')
            self.assertFalse(target.with_suffix('.tmp').exists())


if __name__=='__main__':
    unittest.main()
