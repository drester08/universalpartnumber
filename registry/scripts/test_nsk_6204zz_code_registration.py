"""Current source custody must not approve or normalize partial context."""
import sqlite3
import unittest
from unittest.mock import patch
import check_nsk_6204zz_code_registration as c
import build_review_queue


class RegistrationTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        with sqlite3.connect(c.ROOT/'build/registry.sqlite') as original:
            original.backup(self.db)
        self.addCleanup(self.db.close)

    def test_registered_but_unapproved(self):
        report = c.verify(self.db)
        self.assertTrue(report['registered_new_sources'])
        self.assertEqual(len(report['records']), 2)
        self.assertFalse(report['identity_approved'])
        self.assertFalse(report['canonical_mapping_added'])
        self.assertEqual(self.db.execute('SELECT count(*) FROM upn_allocations').fetchone()[0], 0)

    def test_reuse_and_observation_tasks_remain(self):
        self.db.row_factory = sqlite3.Row
        items = build_review_queue.build_items(self.db)
        text = str(items)
        for source, artifact, observation, publisher in c.BINDINGS:
            self.assertIn(source, text)
            self.assertIn(observation, text)
        self.assertEqual(len(items), 466)

    def test_other_article_rejected(self):
        self.db.execute("UPDATE observations SET manufacturer_part_id='MP-NSK-6205ZZ' WHERE observation_id=?", (c.BINDINGS[0][2],))
        with self.assertRaisesRegex(ValueError, 'observation scope'):
            c.verify(self.db)

    def test_automatic_approval_rejected(self):
        self.db.execute("UPDATE observations SET review_state='accepted' WHERE observation_id=?", (c.BINDINGS[0][2],))
        with self.assertRaisesRegex(ValueError, 'review state'):
            c.verify(self.db)

    def test_reuse_gate_change_rejected(self):
        self.db.execute("UPDATE sources SET ingestion_status='reference_only' WHERE source_id=?", (c.BINDINGS[0][0],))
        with self.assertRaisesRegex(ValueError, 'reuse gate'):
            c.verify(self.db)

    def test_custody_change_rejected(self):
        self.db.execute("UPDATE source_artifacts SET sha256=? WHERE artifact_id=?", ('0'*64, c.BINDINGS[1][1]))
        with self.assertRaisesRegex(ValueError, 'artifact custody'):
            c.verify(self.db)

    def test_historical_report_preserved(self):
        path = c.ROOT/'reports/nsk-6204zz-code-research.json'
        before = path.read_bytes()
        c.verify(self.db)
        self.assertEqual(before, path.read_bytes())
        with patch.object(c, 'RESEARCH_SHA', '0'*64):
            with self.assertRaisesRegex(ValueError, 'historical research revision'):
                c.verify(self.db)


if __name__ == '__main__':
    unittest.main()
