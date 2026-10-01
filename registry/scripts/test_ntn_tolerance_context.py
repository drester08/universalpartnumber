"""Regression tests for manufacturer-specific P0 interpretation and scope limits."""
import sqlite3
import unittest
from unittest.mock import patch
import check_ntn_tolerance_context as checker
import screen_candidates


class NTNToleranceTests(unittest.TestCase):
    def test_source_scope(self):
        report = checker.build_report()
        self.assertEqual([s['page_count'] for s in report['sources']], [4, 11, 14])
        self.assertEqual(report['proposal']['raw_value_retained'], 'ISO Class 0')
        self.assertEqual(report['proposal']['state'], 'proposed')
        self.assertFalse(report['identity_approved'])

    def test_crosswalk_mixed_cells_not_flattened(self):
        cells = checker.extract()['comparison_normal_column_cells']
        self.assertEqual(cells['ISO 492']['normal_column'], 'Normal class Class 6X')
        self.assertEqual(cells['JIS B 1514-1']['normal_column'], 'Class 0, 6')
        self.assertEqual(cells['DIN 620']['normal_column'], 'P0')

    def test_changed_code_pdf_rejected(self):
        inputs = dict(checker.INPUTS)
        v = inputs['codes']
        inputs['codes'] = (v[0], v[1], '0' * 64, v[3])
        with patch.object(checker, 'INPUTS', inputs):
            with self.assertRaises(ValueError):
                checker.read_pdf('codes')

    def test_lubricant_context_does_not_fill_article_gap(self):
        connection = sqlite3.connect(checker.ROOT / 'registry/build/registry.sqlite')
        try:
            count = connection.execute("SELECT count(*) FROM specification_values sv JOIN observations o USING(observation_id) WHERE o.manufacturer_part_id='MP-NTN-6205ZZ' AND sv.property_id='PROP-SUPPLIED-LUBRICANT'").fetchone()[0]
        finally:
            connection.close()
        self.assertEqual(count, 0)
        self.assertEqual(checker.build_report()['new_specification_rows'], 0)

    def test_screen_matches_proposed_p0_but_not_identity(self):
        connection = sqlite3.connect(checker.ROOT / 'registry/build/registry.sqlite')
        connection.row_factory = sqlite3.Row
        try:
            pairs = screen_candidates.screen(connection, '2026-10-01')
        finally:
            connection.close()
        pair = next(p for p in pairs if (p['left_part_id'], p['right_part_id']) == ('MP-NSK-6205ZZ', 'MP-NTN-6205ZZ'))
        self.assertEqual(pair['result'], 'insufficient_evidence')
        self.assertIn('PROP-BEARING-TOLERANCE-CLASS', pair['matched_properties'])
        self.assertIn('PROP-SUPPLIED-LUBRICANT', pair['missing_properties'])

    def test_class_six_remains_distinct(self):
        connection = sqlite3.connect(checker.ROOT / 'registry/build/registry.sqlite')
        connection.row_factory = sqlite3.Row
        try:
            pairs = screen_candidates.screen(connection, '2026-10-01')
        finally:
            connection.close()
        pair = next(p for p in pairs if (p['left_part_id'], p['right_part_id']) == ('MP-NTN-6205ZZ', 'MP-SKF-6205-2Z'))
        self.assertEqual(pair['result'], 'hard_conflict')
        self.assertEqual(pair['conflicting_properties'], 'PROP-BEARING-TOLERANCE-CLASS')


if __name__ == '__main__':
    unittest.main()
