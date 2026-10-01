"""Regression tests for exact-article extraction and conservative NTN ingestion."""
import copy
import unittest
import subprocess
import sys
import check_ntn_6205zz as checker


class NTNSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = checker.PATH.read_text(encoding='utf-8-sig')
        cls.report = checker.build_report()

    def test_source_scope(self):
        self.assertEqual(len(checker.parse(self.raw)), 26)
        self.assertEqual(self.report['metric_boundary_dimensions_mm'], {'d': '25.000', 'D': '52.000', 'B': '15.000'})

    def test_static_conflict_is_not_corrected(self):
        issue = self.report['quality_findings'][0]
        self.assertEqual(issue['metric_values_converted_to_n'], ['7850', '11600.00'])
        self.assertEqual(issue['difference_n'], '3750.00')
        self.assertIsNone(issue['corrected_value'])
        self.assertFalse(issue['rating_trusted'])
        self.assertFalse(self.report['identity_approved'])

    def test_da_max_retains_four_cells(self):
        self.assertEqual(len(self.report['quality_findings'][1]['retained_displays']), 4)
        self.assertIsNone(self.report['quality_findings'][1]['corrected_value'])

    def test_wrong_article_rejected(self):
        with self.assertRaises(ValueError):
            checker.parse(self.raw.replace('<h1>Item # 6205ZZ</h1>', '<h1>Item # 6206ZZ</h1>'))

    def test_duplicate_property_rejected(self):
        with self.assertRaises(ValueError):
            checker.parse(self.raw.replace('Static Load Rating', 'Dynamic Load Rating'))

    def test_blank_unidentified_row_rejected(self):
        with self.assertRaises(ValueError):
            checker.parse(self.raw.replace('data-imageasset="6205ZZ"', 'data-imageasset="unknown"'))

    def test_ingestion_custody(self):
        self.assertEqual(checker.verify_seed_bindings(self.report), 11)

    def test_source_field_mutation_rejected(self):
        report = copy.deepcopy(self.report)
        next(r for r in report['native_properties'] if r['name'] == 'Enclosure')['values'][0]['text'] = 'Open'
        with self.assertRaises(ValueError):
            checker.verify_seed_bindings(report)

    def test_source_dimension_mutation_rejected(self):
        report = copy.deepcopy(self.report)
        report['metric_boundary_dimensions_mm']['d'] = '30.000'
        with self.assertRaises(ValueError):
            checker.verify_seed_bindings(report)

    def test_completeness_does_not_merge_manufacturer_namespaces(self):
        result = subprocess.run([sys.executable, str(checker.ROOT / 'registry/scripts/audit_completeness.py')], capture_output=True, text=True, check=True)
        lines = [line for line in result.stdout.splitlines() if line.startswith('6205ZZ:') and 'required properties' in line]
        self.assertEqual(len(lines), 2)
        self.assertTrue(all('9/12 required properties' in line for line in lines))
        self.assertEqual({line.split('manufacturer_part_id=')[1] for line in lines}, {'MP-NTN-6205ZZ', 'MP-NSK-6205ZZ'})
        conditions = [line for line in result.stdout.splitlines() if line.startswith('6205ZZ:') and 'unresolved_conditional_applicability=' in line]
        self.assertEqual(len(conditions), 2)
        self.assertEqual({line.split('manufacturer_part_id=')[1] for line in conditions}, {'MP-NTN-6205ZZ', 'MP-NSK-6205ZZ'})


if __name__ == '__main__':
    unittest.main()
