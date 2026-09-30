import unittest
from check_structural_british import compare, extract, ROOT, SOURCES

class BritishTests(unittest.TestCase):
    def test_partition(self):
        r=compare()
        self.assertEqual(r['outcomes'],{'nominal_field_conflict':48,'no_exact_candidate_key':1})
        self.assertEqual(sorted(r['outside_family_scope_csv_lines']+[x['csv_line'] for x in r['records']]),list(range(2,807)))
        self.assertTrue(all(not x['exact_article_verified'] for x in r['records']))
    def test_missing_beams_found_without_rounding(self):
        records=compare()['records']
        for line,designation in [(702,'406 x 140 x 46'),(703,'406 x 178 x 54')]:
            r=next(x for x in records if x['csv_line']==line)
            self.assertEqual(r['previous_source_outcome'],'no_exact_candidate_key')
            self.assertEqual(len(r['source_candidates']),1)
            self.assertEqual(r['source_candidates'][0]['designation'],designation)
    def test_label_not_mass(self):
        r=next(x for x in compare()['records'] if x['csv_line']==748)
        self.assertEqual(r['source_candidates'],[])
        o=r['designation_label_observations_not_mass_matches'][0]
        self.assertEqual(o['designation_mass_label'],'167')
        self.assertEqual(o['mass_kg_per_m'],'167.1')
        self.assertEqual(o['root_radius_mm'],'20.0')
    def test_source_conflict(self):
        report=compare()
        self.assertEqual(report['cross_source_compared_rows'],46)
        self.assertEqual(report['cross_source_conflict_rows'],1)
        r=next(x for x in report['records'] if x['cross_source_nominal_differences'])
        self.assertEqual(r['cross_source_nominal_differences'],['width_mm'])
        self.assertEqual(r['source_candidates'][0]['designation'],'305 x 102 x 33')
        self.assertEqual(r['source_candidates'][0]['width_mm'],'102.4')
        self.assertEqual(r['previous_source_candidates'][0]['width_mm'],'102.0')
    def test_bad_source_row_count(self):
        with self.assertRaisesRegex(ValueError,'row count'):
            extract(ROOT/'artifacts/british-steel/ub-190724.pdf','UB',SOURCES['UB'][0],[(1,43,4)])
    def test_incomplete_cells_are_not_shifted(self):
        s=SOURCES['UB']
        rows=extract(ROOT/'artifacts/british-steel'/s[1],'UB',s[0],s[3])
        self.assertFalse(any(o['designation'].startswith('410 x 260') for o in rows))
        self.assertEqual(len(rows),83)

if __name__=='__main__':
    unittest.main()
