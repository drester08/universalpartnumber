import sqlite3
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch
import specification_presence as presence
import screen_candidates as screen
import audit_completeness as audit

ROOT = Path(__file__).resolve().parents[1]


class SpecificationPresenceTests(unittest.TestCase):
    def test_blank_raw_values_are_missing(self):
        for value in (None, '', ' ', '\t\r\n', '\u00a0', 0, False):
            with self.subTest(value=value):
                self.assertFalse(presence.has_value(value, 'filled', '1'))

    def test_explicit_blank_normalization_does_not_fall_back(self):
        for value in ('', ' ', '\t', '\u00a0'):
            self.assertFalse(presence.has_value('source', value))
            self.assertFalse(presence.has_value('source', None, value))

    def test_nonfinite_or_malformed_numbers_are_missing(self):
        for value in ('NaN', 'sNaN', 'Infinity', '-Infinity', 'bad', '1,000', False, 0):
            with self.subTest(value=value):
                self.assertFalse(presence.has_value('source', None, value))

    def test_zero_negative_and_false_text_are_real_values(self):
        self.assertTrue(presence.has_value('0', None, '0'))
        self.assertTrue(presence.has_value('-1', None, '-1'))
        self.assertTrue(presence.has_value('false', 'false'))
        self.assertTrue(presence.has_value('source'))
        # Presence does not prove ranges, units, truth or semantic approval.

    def database(self):
        db = sqlite3.connect(':memory:')
        db.row_factory = sqlite3.Row
        with sqlite3.connect(ROOT/'build/registry.sqlite') as original:
            original.backup(db)
        self.addCleanup(db.close)
        return db

    def test_screen_does_not_load_empty_or_invalid_values(self):
        db = self.database()
        row = db.execute("SELECT o.manufacturer_part_id,sv.property_id FROM observations o JOIN specification_values sv ON sv.observation_id=o.observation_id JOIN properties p ON p.property_id=sv.property_id WHERE p.value_kind='number' LIMIT 1").fetchone()
        self.assertIn(row[1], screen.load_parts(db)[row[0]]['values'])
        ids = [r[0] for r in db.execute('SELECT observation_id FROM observations WHERE manufacturer_part_id=?', (row[0],))]
        for value in ('', '\t', 'NaN', 'invalid'):
            for obs in ids:
                db.execute('UPDATE specification_values SET normalized_number=? WHERE observation_id=? AND property_id=?', (value, obs, row[1]))
            self.assertNotIn(row[1], screen.load_parts(db)[row[0]]['values'])

    def test_coverage_reports_blank_required_property_missing(self):
        db = self.database()
        part, prop, label = db.execute("SELECT mp.manufacturer_part_id,ipp.property_id,p.preferred_label FROM manufacturer_parts mp JOIN identity_profile_properties ipp ON ipp.profile_id=mp.profile_id JOIN properties p ON p.property_id=ipp.property_id WHERE ipp.requirement='required' AND p.value_kind='number' LIMIT 1").fetchone()
        observations = [r[0] for r in db.execute('SELECT observation_id FROM observations WHERE manufacturer_part_id=?', (part,))]
        self.assertTrue(observations)
        for obs in observations:
            db.execute('DELETE FROM specification_values WHERE observation_id=? AND property_id=?', (obs, prop))
        db.execute('INSERT INTO specification_values(specification_id,observation_id,property_id,raw_value) VALUES(?,?,?,?)', ('TEST-BLANK', observations[0], prop, '\t\u00a0'))
        db.commit()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'test.sqlite'
            target = sqlite3.connect(path)
            db.backup(target)
            target.close()
            result = subprocess.run([sys.executable, str(ROOT/'scripts/audit_completeness.py'), '--database', str(path)], text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
        line = next(line for line in result.stdout.splitlines() if 'required properties;' in line and f'manufacturer_part_id={part}' in line)
        self.assertIn(label, line.split('missing=')[1].split('; source_conflicts=')[0])

    def test_real_screen_unchanged_and_read_only(self):
        db = self.database()
        before = db.total_changes
        expected = screen.screen(db, '2026-10-01')
        with patch.object(presence, 'has_value', return_value=True):
            self.assertEqual(expected, screen.screen(db, '2026-10-01'))
        self.assertEqual(len(expected), 25)
        self.assertTrue(all(row['result'] in ('hard_conflict','insufficient_evidence') for row in expected))
        self.assertEqual(db.total_changes, before)

    def test_accepted_part_with_blank_value_fails_publication(self):
        db = self.database()
        part, profile, prop = db.execute("SELECT mp.manufacturer_part_id,mp.profile_id,ipp.property_id FROM manufacturer_parts mp JOIN identity_profile_properties ipp ON ipp.profile_id=mp.profile_id JOIN properties p ON p.property_id=ipp.property_id WHERE ipp.requirement='required' AND p.value_kind='number' LIMIT 1").fetchone()
        # Isolate the value-presence gate; all synthetic policy/review changes
        # stay in memory. No real permission or independent review is claimed.
        db.execute('DELETE FROM identity_profile_properties WHERE profile_id=? AND property_id!=?', (profile, prop))
        db.execute("UPDATE observations SET review_state='accepted' WHERE manufacturer_part_id=?", (part,))
        db.execute("UPDATE specification_values SET raw_value=' ',normalized_number=NULL,normalized_text=NULL WHERE property_id=? AND observation_id IN(SELECT observation_id FROM observations WHERE manufacturer_part_id=?)", (prop, part))
        db.execute("INSERT INTO manufacturer_part_reviews VALUES ('TEST-BLANK-REVIEW',?,'accepted','SYNTHETIC TEST ONLY','TEST','2026-10-01','TEST')", (part,))
        output = StringIO()
        with patch.object(audit.sqlite3, 'connect', return_value=db), patch.object(audit.source_use_gates, 'part_holds', return_value={}), patch.object(sys, 'argv', ['audit_completeness.py']), redirect_stdout(output):
            self.assertEqual(audit.main(), 1)
        line = next(line for line in output.getvalue().splitlines() if 'required properties;' in line and f'manufacturer_part_id={part}' in line)
        self.assertIn('0/1 required properties', line)
        self.assertIn('Publication gate failed:', output.getvalue())


if __name__ == '__main__':
    unittest.main()
