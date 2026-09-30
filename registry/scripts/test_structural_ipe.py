import unittest
from check_structural_ipe import compare, compare_row


class StructuralTests(unittest.TestCase):
    def test_full_selected_family_coverage(self):
        report=compare()
        self.assertEqual(report['compared_rows'],12)
        self.assertEqual(report['not_compared_rows'],793)
        self.assertEqual(report['outcomes'],{'nominal_values_agree':6,'nominal_field_conflict':6})
        self.assertEqual([r['csv_line'] for r in report['records']],list(range(754,766)))
        self.assertTrue(all(not r['exact_article_verified'] for r in report['records']))

    def test_aa_designation_not_depth(self):
        records=compare()['records'][6:]
        self.assertTrue(all(r['nominal_differences']==['depth_mm'] for r in records))
        self.assertEqual(records[0]['actual']['depth_mm'],'100')
        self.assertEqual(records[0]['source']['depth_mm'],'97.6')

    def test_numeric_text_representation(self):
        row={'Height (mm)':'100','Width (mm)':'55','Web Thickness (mm)':'4.1',
             'Flange Thickness (mm)':'5.7','Mass per meter (kg)':'8.104'}
        source={'depth_mm':'100.0','width_mm':'55','web_mm':'4.10','flange_mm':'5.70','mass_kg_per_m':'8.1040'}
        self.assertEqual(compare_row(row,source)['outcome'],'nominal_values_agree')


if __name__=='__main__':
    unittest.main()
