import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import check_klinger_uk_registration as c
import build_registry
import build_review_queue


class UKRegistrationTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        with sqlite3.connect(c.ROOT/'build/registry.sqlite') as original:
            original.backup(self.db)
        self.addCleanup(self.db.close)

    def test_scope_and_issue_date(self):
        r = c.verify(self.db)
        self.assertTrue(r['registered_source'])
        self.assertEqual(r['publication_date'], '2019-08-28')
        self.assertEqual(r['temperature_disagreements'], 7)
        for key in ('identity_approved', 'application_suitability_approved', 'reuse_permission',
                    'production_upn_allowed', 'dimensional_tuple_roles_resolved'):
            self.assertFalse(r[key])

    def test_three_tasks_and_revision_binding(self):
        self.db.row_factory = sqlite3.Row
        items = build_review_queue.build_items(self.db)
        new = [r for r in items if r['source_id'] == c.SOURCE]
        self.assertEqual(len(items), 472)
        self.assertEqual(len(new), 3)
        scoped = [r for r in new if r['work_item_id'].startswith('RW-KLINGER-UK-')]
        self.assertEqual(len(scoped), 2)
        self.assertTrue(all(c.RESEARCH_SHA in r['next_action'] for r in scoped))

    def test_upload_date_substitution_rejected(self):
        self.db.execute("UPDATE sources SET publication_date='2025-01-01' WHERE source_id=?", (c.SOURCE,))
        with self.assertRaisesRegex(ValueError, 'source metadata'):
            c.verify(self.db)

    def test_gate_relaxation_rejected(self):
        self.db.execute("UPDATE sources SET ingestion_status='reference_only' WHERE source_id=?", (c.SOURCE,))
        with self.assertRaisesRegex(ValueError, 'reuse gate'):
            c.verify(self.db)

    def test_custody_change_rejected(self):
        self.db.execute('UPDATE source_artifacts SET sha256=? WHERE artifact_id=?', ('0'*64, c.ARTIFACT))
        with self.assertRaisesRegex(ValueError, 'custody'):
            c.verify(self.db)

    def test_generic_article_promotion_rejected(self):
        self.db.execute('UPDATE observations SET source_id=? WHERE observation_id=(SELECT observation_id FROM observations LIMIT 1)', (c.SOURCE,))
        with self.assertRaisesRegex(ValueError, 'promoted to article'):
            c.verify(self.db)

    def test_immutable_report_preserved(self):
        path = c.ROOT/'reports/klinger-uk-maxiprofile.json'
        before = path.read_bytes()
        with patch.object(c, 'RESEARCH_SHA', '0'*64):
            with self.assertRaisesRegex(ValueError, 'revision changed'):
                c.verify(self.db)
        self.assertEqual(before, path.read_bytes())

    def test_failed_build_preserves_output(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)/'registry.sqlite'
            target.write_bytes(b'previous database')
            with patch.object(c, 'verify', side_effect=ValueError('UK custody rejected')):
                with self.assertRaisesRegex(ValueError, 'custody rejected'):
                    build_registry.build(target)
            self.assertEqual(target.read_bytes(), b'previous database')
            self.assertFalse(target.with_suffix('.tmp').exists())


if __name__ == '__main__':
    unittest.main()
