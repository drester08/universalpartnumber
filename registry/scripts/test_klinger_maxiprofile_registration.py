"""Manufacturer family custody is not exact gasket identity."""
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import check_klinger_maxiprofile_registration as c
import build_registry
import build_review_queue


class KlingerRegistrationTests(unittest.TestCase):
    def setUp(self):
        self.db=sqlite3.connect(':memory:')
        with sqlite3.connect(c.ROOT/'build/registry.sqlite') as original:
            original.backup(self.db)
        self.addCleanup(self.db.close)

    def test_context_registered_without_article_or_reuse(self):
        report=c.verify(self.db)
        self.assertTrue(report['registered_source'])
        self.assertFalse(report['identity_approved'])
        self.assertFalse(report['reuse_permission'])
        self.assertFalse(report['historical_findings_resolved'])
        self.assertEqual(report['article_observations_added'],0)
        self.assertEqual(report['component_material_rows'],19)

    def test_three_new_tasks_bound_to_research(self):
        self.db.row_factory=sqlite3.Row
        items=build_review_queue.build_items(self.db)
        new=[r for r in items if r['source_id']==c.SOURCE]
        self.assertEqual(len(new),3)
        self.assertEqual(len(items),472)
        scoped=[r for r in new if r['work_item_id'].startswith('RW-KLINGER-MAXIPROFILE-')]
        self.assertEqual(len(scoped),2)
        self.assertTrue(all(c.RESEARCH_SHA in r['next_action'] for r in scoped))

    def test_invented_date_rejected(self):
        self.db.execute("UPDATE sources SET publication_date='2024-08-01' WHERE source_id=?",(c.SOURCE,))
        with self.assertRaisesRegex(ValueError,'source metadata'):
            c.verify(self.db)

    def test_reuse_gate_change_rejected(self):
        self.db.execute("UPDATE sources SET ingestion_status='reference_only' WHERE source_id=?",(c.SOURCE,))
        with self.assertRaisesRegex(ValueError,'reuse gate'):
            c.verify(self.db)

    def test_artifact_tampering_rejected(self):
        self.db.execute('UPDATE source_artifacts SET sha256=? WHERE artifact_id=?',('0'*64,c.ARTIFACT))
        with self.assertRaisesRegex(ValueError,'custody'):
            c.verify(self.db)

    def test_generic_article_promotion_rejected(self):
        self.db.execute('UPDATE observations SET source_id=? WHERE observation_id=(SELECT observation_id FROM observations LIMIT 1)',(c.SOURCE,))
        with self.assertRaisesRegex(ValueError,'promoted to article'):
            c.verify(self.db)

    def test_historical_revision_rejected_and_preserved(self):
        path=c.ROOT/'reports/klinger-maxiprofile-context.json'
        before=path.read_bytes()
        with patch.object(c,'RESEARCH_SHA','0'*64):
            with self.assertRaisesRegex(ValueError,'revision changed'):
                c.verify(self.db)
        self.assertEqual(path.read_bytes(),before)

    def test_failed_build_preserves_previous_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)/'registry.sqlite'
            target.write_bytes(b'previous output')
            with patch.object(c,'verify',side_effect=ValueError('KLINGER guard rejected')):
                with self.assertRaisesRegex(ValueError,'guard rejected'):
                    build_registry.build(target)
            self.assertEqual(target.read_bytes(),b'previous output')
            self.assertFalse(target.with_suffix('.tmp').exists())


if __name__=='__main__':
    unittest.main()
