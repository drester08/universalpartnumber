"""Check plate screening preserves unresolved material distinctions."""
import unittest
from check_plate_macsteel import classify, compare


class PlateTests(unittest.TestCase):
    def row(self, moc):
        return {'MOC': moc, 'Length (mm)': '2000', 'Width (mm)': '1000',
                'Thickness (mm)': '5', 'Mass per sheet (kg)': '78.5'}

    def test_full_coverage(self):
        result = compare()
        self.assertEqual(len(result['records']), 395)
        self.assertEqual(result['mass_discrepancies'], 3)
        self.assertEqual(result['family_outcomes'], {'outside_selected_family_scope':76,
            'family_designation_supported':268, 'grade_character_review':13,
            'specification_scope_review':14, 'unverified_product_name':24})
        self.assertEqual([r['csv_line'] for r in result['records']], list(range(2,397)))
        self.assertTrue(all(not r['exact_article_verified'] for r in result['records']))

    def test_jo_not_silently_corrected(self):
        result = classify(self.row('SANS 50025 / EN 10025 S355 JO+AR'), 2)
        self.assertIn('JO', result['moc_raw'])
        self.assertEqual(result['family_outcome'], 'grade_character_review')
        self.assertEqual(result['interpretation_status'], 'unreviewed')

    def test_pressure_specification_stays_unresolved(self):
        self.assertEqual(classify(self.row('B.S 1501/151 GRADE 430A'),2)['family_outcome'], 'specification_scope_review')

    def test_w200_not_approved_alias(self):
        self.assertEqual(classify(self.row('W200'),2)['family_outcome'], 'unverified_product_name')

    def test_unknown_grade_rejected(self):
        with self.assertRaises(KeyError):
            classify(self.row('unknown grade'),2)


if __name__ == '__main__':
    unittest.main()
