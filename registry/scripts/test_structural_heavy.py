import unittest
from check_structural_heavy import compare, screen

class HeavyStructuralTests(unittest.TestCase):
    def test_partition(self):
        r=compare()
        self.assertEqual(r['outcomes'],{'nominal_field_conflict':46,'no_exact_candidate_key':3})
        self.assertEqual(r['uniquely_compared_rows'],46)
        self.assertEqual(sorted(r['outside_family_scope_csv_lines']+[x['csv_line'] for x in r['records']]),list(range(2,807)))
        self.assertTrue(all(not x['exact_article_verified'] for x in r['records']))
        self.assertEqual(len(r['source_rows_without_supplied_key']),3)
    def test_designation_and_web(self):
        x=compare()['records'][0]
        self.assertEqual(x['actual']['depth_mm'],'203')
        self.assertEqual(x['source_candidates'][0]['depth_mm'],'203.2')
        self.assertEqual(x['source_candidates'][0]['web_mm'],'5.7')
        self.assertEqual(x['nominal_differences'],['depth_mm','width_mm','web_mm'])
    def test_no_mass_rounding(self):
        x=next(x for x in compare()['records'] if x['csv_line']==748)
        self.assertEqual(x['source_candidates'],[])
        self.assertEqual(x['outcome'],'no_exact_candidate_key')
        self.assertIn('167.1',[o['mass_kg_per_m'] for o in x['same_serial_source_candidates']])
    def test_enquiry_marks(self):
        self.assertEqual(sum(bool(x['source_candidates']) and x['source_candidates'][0]['enquiry_only'] for x in compare()['records']),13)
    def test_ambiguity(self):
        o=compare()['records'][0]['source_candidates'][0]
        row={'Type/Section/Channels/Angle/Bars/UC/I-Beams':'UB','Height (mm)':'203','Width (mm)':'133',
             'Mass per meter (kg)':'25.10','Web Thickness (mm)':'5.8','Flange Thickness (mm)':'7.8'}
        x=screen(row,[o,o.copy()])
        self.assertEqual(x['outcome'],'ambiguous_candidate_key')
        self.assertEqual(len(x['source_candidates']),2)
        self.assertEqual(x['nominal_differences'],[])
        self.assertFalse(x['exact_article_verified'])

if __name__=='__main__':
    unittest.main()
