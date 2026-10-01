import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import conditional_requirements as c
import screen_candidates as s

ROOT = Path(__file__).resolve().parents[1]


class ConditionalRequirementTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        self.db.row_factory = sqlite3.Row
        with sqlite3.connect(ROOT/'build/registry.sqlite') as original:
            original.backup(self.db)
        self.addCleanup(self.db.close)

    def test_current_profiles_all_have_unresolved_conditions(self):
        profiles = c.unresolved_profiles(self.db)
        self.assertEqual(len(profiles), 5)
        self.assertIn(('PROP-CERTIFICATIONS', 'Certifications'), profiles['PROFILE-ANGLE-EQUAL-HOT-ROLLED-STEEL-0.1'])

    def test_populated_values_do_not_resolve_applicability(self):
        before = c.unresolved_parts(self.db)
        self.assertTrue(before)
        populated = self.db.execute("SELECT DISTINCT o.manufacturer_part_id FROM observations o JOIN specification_values sv ON sv.observation_id=o.observation_id JOIN manufacturer_parts mp ON mp.manufacturer_part_id=o.manufacturer_part_id JOIN identity_profile_properties ipp ON ipp.profile_id=mp.profile_id AND ipp.property_id=sv.property_id WHERE ipp.requirement='conditional'").fetchall()
        self.assertTrue(populated)
        self.assertTrue(all(row[0] in before for row in populated))
        self.db.execute("UPDATE identity_profile_properties SET requirement='required' WHERE requirement='conditional'")
        self.assertFalse(c.unresolved_parts(self.db))

    def test_otherwise_positive_screen_fails_closed(self):
        # Synthetic comparison policy in memory; never persisted or reviewed.
        def blocking_only(connection, profile_id):
            return [(pid, rule) for pid, rule in s.required_properties_original(connection, profile_id)
                    if pid in s.PROFILE_RULES[profile_id]['blocking_properties']]
        with patch.object(s, 'required_properties_original', s.required_properties, create=True):
            with patch.object(s, 'required_properties', blocking_only):
                rows = s.screen(self.db, '2026-10-01')
                with patch.object(c, 'unresolved_profiles', return_value={}):
                    unguarded = s.screen(self.db, '2026-10-01')
        self.assertTrue(rows)
        self.assertTrue(all(r['result'] == 'insufficient_evidence' for r in rows))
        self.assertTrue(all(r['missing_properties'] != 'none' for r in rows))
        positives = {r['screening_id'] for r in unguarded if r['result'] == 'candidate'}
        self.assertTrue(positives)
        self.assertTrue(all(r['algorithm_version'].endswith('-conditional-guard-0.1')
                            for r in rows if r['screening_id'] in positives))

    def test_negative_research_screens_unchanged(self):
        baseline = s.screen(self.db, '2026-10-01')
        with patch.object(c, 'unresolved_profiles', return_value={}):
            without_guard = s.screen(self.db, '2026-10-01')
        self.assertEqual(baseline, without_guard)

    def audit(self, script='audit_completeness.py'):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'test.sqlite'
            target = sqlite3.connect(path)
            try:
                self.db.backup(target)
            finally:
                target.close()
            return subprocess.run([sys.executable, str(ROOT/'scripts'/script),
                                   '--database', str(path)], text=True, capture_output=True)

    def test_conditional_only_accepted_part_is_not_skipped(self):
        part = self.db.execute('SELECT manufacturer_part_id, profile_id FROM manufacturer_parts LIMIT 1').fetchone()
        self.db.execute("UPDATE identity_profile_properties SET requirement='conditional' WHERE profile_id=?", (part[1],))
        self.db.execute("INSERT INTO manufacturer_part_reviews VALUES ('TEST-CONDITIONAL-REVIEW', ?, 'accepted', 'SYNTHETIC TEST ONLY', 'TEST', '2026-10-01', 'TEST')", (part[0],))
        self.db.commit()
        result = self.audit()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn('unresolved_conditional_applicability=', result.stdout)
        self.assertIn('Publication gate failed:', result.stdout)

    def test_unreviewed_research_remains_permitted(self):
        result = self.audit()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('unresolved_conditional_applicability=', result.stdout)

    def test_issuance_audit_inherits_publication_failure(self):
        part = self.db.execute('SELECT manufacturer_part_id, profile_id FROM manufacturer_parts LIMIT 1').fetchone()
        self.db.execute("UPDATE identity_profile_properties SET requirement='conditional' WHERE profile_id=?", (part[1],))
        self.db.execute("INSERT INTO manufacturer_part_reviews VALUES ('TEST-ISSUANCE-REVIEW', ?, 'accepted', 'SYNTHETIC TEST ONLY', 'TEST', '2026-10-01', 'TEST')", (part[0],))
        self.db.commit()
        result = self.audit('audit_issuance.py')
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn('manufacturer-part publication gate is not clean', result.stdout)


if __name__ == '__main__':
    unittest.main()
