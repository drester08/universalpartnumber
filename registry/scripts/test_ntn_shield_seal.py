"""Catalogue corroboration and uninterpreted-code screening regressions."""
import sqlite3
import unittest
from unittest.mock import patch
import check_ntn_shield_seal as checker
import screen_candidates


class NTNCatalogueTests(unittest.TestCase):
    def test_catalogue_custody_and_scope(self):
        report = checker.build_report()
        self.assertEqual(report['pdf_page_count'], 12)
        self.assertEqual(report['closure_proposal']['state'], 'proposed')
        self.assertFalse(report['identity_approved'])
        self.assertFalse(report['publisher_correction_obtained'])

    def test_mounting_columns_remain_distinct(self):
        report = checker.build_report()
        self.assertEqual(report['catalogue_6205_context']['da_max_mm'], '32')
        self.assertEqual(report['catalogue_6205_context']['Da_max_mm'], '47')
        self.assertEqual(report['catalogue_6205_context']['static_load_rating_kn'], '7.85')

    def test_changed_pdf_hash_fails_closed(self):
        with patch.object(checker, 'SHA', '0' * 64):
            with self.assertRaises(ValueError):
                checker.extract()

    def test_unmapped_code_wording_is_not_a_hard_conflict(self):
        connection = sqlite3.connect(checker.ROOT / 'registry/build/registry.sqlite')
        connection.row_factory = sqlite3.Row
        try:
            parts = screen_candidates.load_parts(connection)
            ntn = parts['MP-NTN-6205ZZ']['values']
            self.assertFalse(ntn.get('PROP-BEARING-TOLERANCE-CLASS'))
            self.assertFalse(ntn.get('PROP-BEARING-MATERIAL'))
            self.assertEqual(ntn['PROP-BEARING-CLOSURE'], {'double_non_contact_metal_shield'})
            pairs = screen_candidates.screen(connection, '2026-09-30')
        finally:
            connection.close()
        ntn_pairs = [r for r in pairs if 'MP-NTN-6205ZZ' in (r['left_part_id'], r['right_part_id'])]
        self.assertEqual(len(ntn_pairs), 2)
        self.assertTrue(all(r['result'] == 'insufficient_evidence' for r in ntn_pairs))
        self.assertTrue(all('PROP-BEARING-TOLERANCE-CLASS' in r['missing_properties'] for r in ntn_pairs))


if __name__ == '__main__':
    unittest.main()
