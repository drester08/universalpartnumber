"""Source table audit preserves raw discrepancies and product-route boundaries."""
import copy
import unittest
from unittest.mock import patch
import check_mps_pipe_research as c


class MPSPipeResearchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = c.extract()

    def test_all_three_pages_and_group_boundaries(self):
        report = c.build_report()
        self.assertEqual(report['source_rows'],144)
        self.assertEqual(report['page_row_counts'],{'12':50,'13':46,'14':48})
        self.assertEqual([r['nominal_bore'] for r in self.records if r['text_line'] == self.records[0]['text_line']], ['6','150','400'])

    def test_small_size_scope_and_distinct_65_80(self):
        for dn,od in [('6','10,3'),('8','13,7'),('10','17,1'),('65','73,0'),('80','88,9'),('90','101,6')]:
            with self.subTest(dn=dn):
                rows = [r for r in self.records if r['nominal_bore']==dn]
                self.assertEqual({r['od_mm_raw'] for r in rows},{od})
                self.assertTrue({'40','80'} <= {r['schedule_raw'] for r in rows})

    def test_raw_id_error_not_corrected(self):
        row = next(r for r in self.records if r['nominal_bore']=='80' and r['schedule_raw']=='160')
        self.assertEqual(row['id_mm_raw'],'6,64')
        issue = c.audit([row])['internal_diameter_precision_conflicts'][0]
        self.assertEqual(issue['od_minus_two_wall_mm'],'66.64')
        self.assertEqual(issue['residual_mm'],'60.00')
        self.assertEqual(row['id_mm_raw'],'6,64')

    def test_three_diameter_questions_and_one_mass_question(self):
        report = c.build_report()
        issues = report['diagnostics']['internal_diameter_precision_conflicts']
        self.assertEqual({(r['nominal_bore'],r['schedule_raw']) for r in issues},{('80','160'),('400','10'),('600','160')})
        masses = report['diagnostics']['repeated_mass_different_wall']
        self.assertEqual(len(masses),1)
        self.assertEqual(masses[0]['nominal_bore'],'50')
        self.assertEqual(masses[0]['mass_approx_kg_m_raw'],'5,43')

    def test_xxs_not_invented_numeric_schedule(self):
        row = next(r for r in self.records if r['nominal_bore']=='80' and r['wall_designation_raw']=='(XXS)')
        self.assertEqual(row['schedule_raw'],'–')
        self.assertEqual(row['wall_mm_raw'],'15,24')

    def test_printed_precision_not_tolerance_or_identity(self):
        report = c.build_report()
        self.assertFalse(report['identity_approved'])
        self.assertFalse(report['registered_new_source'])
        self.assertFalse(report['source_correction_obtained'])
        self.assertIn('supplier/fabricator',report['source_role'])
        self.assertTrue(any('not a manufacturing tolerance' in x for x in report['limitations']))
        self.assertTrue(any('not A106 welded' in x for x in report['limitations']))

    def test_altered_bytes_rejected(self):
        with patch.object(c,'SHA','0'*64):
            with self.assertRaisesRegex(ValueError,'PDF revision'):
                c.extract()

    def test_audit_does_not_mutate_source_rows(self):
        before = copy.deepcopy(self.records)
        c.audit(self.records)
        self.assertEqual(before,self.records)


if __name__ == '__main__':
    unittest.main()
