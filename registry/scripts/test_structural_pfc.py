import unittest
from check_structural_pfc import compare, screen

class PFCTests(unittest.TestCase):
    def test_full_partition(self):
        r=compare()
        self.assertEqual(r['outcomes'],{'no_serial_candidate':2,'nominal_field_conflict':2,'nominal_values_agree':2})
        self.assertEqual(sorted(r['outside_family_scope_csv_lines']+[x['csv_line'] for x in r['records']]),list(range(2,807)))
        self.assertTrue(all(not x['exact_article_verified'] for x in r['records']))
    def test_200x75_retains_all_differences(self):
        x=next(x for x in compare()['records'] if x['serial_size_candidate']==['200','75'])
        self.assertEqual(x['nominal_differences'],['web_mm','flange_mm','mass_kg_per_m'])
        self.assertEqual(x['source_candidates'][0]['mass_kg_per_m'],'23.4')
        self.assertEqual(x['actual']['mass_kg_per_m'],'24.3')
    def test_mass_difference_not_rounded(self):
        x=compare()['records'][-1]
        self.assertEqual(x['nominal_differences'],['mass_kg_per_m'])
        self.assertEqual(x['actual']['mass_kg_per_m'],'45.4')
        self.assertEqual(x['source_candidates'][0]['mass_kg_per_m'],'45.5')
    def test_units_separate(self):
        o=compare()['records'][-1]['source_candidates'][0]
        self.assertEqual((o['centroid_distance_cm'],o['root_radius_mm'],o['depth_between_fillets_mm']),('3.05','15','237'))
    def test_ambiguity_not_first_match(self):
        o=compare()['records'][-1]['source_candidates'][0]
        row={'Height (mm)':'300','Width (mm)':'100','Web Thickness (mm)':'9',
             'Flange Thickness (mm)':'16.5','Mass per meter (kg)':'45.4'}
        x=screen(row,[o,o.copy()])
        self.assertEqual(x['outcome'],'ambiguous_serial_candidate')
        self.assertEqual(x['nominal_differences'],[])

if __name__=='__main__':
    unittest.main()
