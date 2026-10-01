"""Manufacturer construction evidence must not become special-design defaults."""
import sqlite3
import unittest
from unittest.mock import patch
import check_nsk_6204zz_metal_research as c


class NSKMetalResearchTests(unittest.TestCase):
    def test_complete_closure_hypothesis_not_identity(self):
        report = c.build_report()
        self.assertEqual(report['closure_hypothesis']['canonical_code'], 'double_non_contact_metal_shield')
        self.assertIsNone(report['closure_hypothesis']['metal_grade'])
        self.assertTrue(report['ready_for_scoped_mapping_proposal'])
        self.assertFalse(report['identity_approved'])
        self.assertFalse(report['canonical_mapping_added'])

    def test_shield_is_not_adjacent_seal(self):
        evidence = c.extract()
        self.assertEqual(evidence['zz_figure_label'], 'ZZ Non-contact shield')
        self.assertIn('ZZ Double metal shields', evidence['closure_rows'])
        self.assertIn('VV Double non-contact seals', evidence['closure_rows'])

    def test_changed_original_rejected(self):
        with patch.object(c, 'SHA', '0'*64):
            with self.assertRaisesRegex(ValueError, 'original PDF revision'):
                c.extract()

    def test_changed_table_meaning_rejected(self):
        with patch.object(c, 'CLOSURE_ROWS', c.CLOSURE_ROWS[:3]+['ZZ Double rubber seals']+c.CLOSURE_ROWS[4:]):
            with self.assertRaisesRegex(ValueError, 'table boundary'):
                c.extract()

    def test_historical_reference_and_no_special_defaults(self):
        report = c.build_report()
        self.assertEqual(report['extracted_evidence']['publication_reference'], 'DGB/H/E/01.15')
        self.assertEqual(report['extracted_evidence']['copyright_year'], 2009)
        self.assertNotIn('supplied_grease', report)
        self.assertTrue(any('special designs' in text for text in report['limitations']))

    def test_prior_snapshot_and_registry_unchanged(self):
        path = c.ROOT/'reports/nsk-6204zz-code-registration.json'
        before = path.read_bytes()
        c.build_report()
        self.assertEqual(before, path.read_bytes())
        with sqlite3.connect(c.ROOT/'build/registry.sqlite') as db:
            self.assertEqual(db.execute("SELECT mapping_state FROM specification_value_mappings WHERE specification_id='SPEC-NSK-6204ZZ-CLOSURE'").fetchone()[0], 'proposed')
            self.assertEqual(db.execute('SELECT count(*) FROM upn_allocations').fetchone()[0], 0)


if __name__ == '__main__':
    unittest.main()
