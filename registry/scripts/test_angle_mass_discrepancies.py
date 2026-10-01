"""Verify mass-audit grain and diagnostic boundaries without physical approval."""
import copy
import json
import unittest
from collections import Counter
import check_angle_mass_discrepancies as checker


class MassAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parent = json.loads(checker.PARENT.read_text(encoding='utf-8'))
        cls.report = checker.build_report()

    def test_population_and_distinct_grain(self):
        r = self.report
        self.assertEqual((r['supplier_offer_count'], r['distinct_section_context_comparisons'],
                          r['compared_offer_count'], r['uncompared_offer_count']), (136, 40, 104, 32))
        self.assertEqual(r['offer_outcomes'], {'nearest_rounding_hypothesis_not_excluded': 76,
            'exact_displayed_agreement': 19, 'not_explained_by_displayed_nearest_rounding': 9})
        self.assertEqual(Counter(x['reason'] for x in r['uncompared_offers']),
                         {'no_manufacturer_geometry_candidate': 25, 'no_same_context_seller_pdf_mass': 7})
        skus = [s for x in r['records'] for s in x['affected_seller_skus']]
        skus += [x['seller_sku'] for x in r['uncompared_offers']]
        self.assertEqual(len(set(skus)), 136)

    def test_four_discrepancies_not_physical_conflicts(self):
        rows = [r for r in self.report['records'] if r['comparison']['outcome'] == 'not_explained_by_displayed_nearest_rounding']
        self.assertEqual(len(rows), 4)
        self.assertEqual({tuple(r['nominal_geometry_mm']) for r in rows},
                         {('25', '25', '3'), ('45', '45', '3'), ('70', '70', '8'), ('200', '200', '18')})
        for r in self.report['records']:
            self.assertFalse(r['material_context_equivalence_verified'])
            self.assertFalse(r['comparison']['physical_conflict_verified'])
            self.assertFalse(r['comparison']['rounding_convention_source_verified'])
            self.assertFalse(r['comparison']['identity_approved'])

    def test_rounding_hypothesis_and_exact_values(self):
        r = checker.rounding_audit('15.036', '15.0')
        self.assertEqual(r['outcome'], 'nearest_rounding_hypothesis_not_excluded')
        self.assertEqual(r['signed_manufacturer_minus_seller_kg_per_m'], '-0.036')
        self.assertEqual(checker.rounding_audit('9.630', '9.63')['outcome'], 'exact_displayed_agreement')

    def test_intervals_independently_recomputed(self):
        # 2.131 ± 0.0005 is wholly above 2.09 ± 0.005.
        r = checker.rounding_audit('2.131', '2.09')
        self.assertEqual(r['seller_nearest_rounding_interval_kg_per_m'], ['2.1305', '2.1315'])
        self.assertEqual(r['manufacturer_nearest_rounding_interval_kg_per_m'], ['2.085', '2.095'])
        self.assertFalse(r['intervals_overlap'])

    def test_boundary_ties_conservatively_retained(self):
        self.assertTrue(checker.rounding_audit('1.115', '1.11')['intervals_overlap'])
        self.assertTrue(checker.rounding_audit('1.1145', '1.115')['intervals_overlap'])

    def test_invalid_and_missing_values_rejected(self):
        for value in ('', '0', '-1', 'NaN', '1e2', '2.131*'):
            with self.assertRaises(ValueError):
                checker.rounding_audit(value, '2.09')

    def test_duplicate_offer_rejected(self):
        p = copy.deepcopy(self.parent)
        p['records'].append(copy.deepcopy(p['records'][0]))
        with self.assertRaisesRegex(ValueError, 'Duplicate seller'):
            checker.audit(p)

    def test_detached_comparison_rejected(self):
        p = copy.deepcopy(self.parent)
        record = next(r for r in p['records'] if r['seller_table_mass_comparisons'])
        record['seller_table_mass_comparisons'][0]['manufacturer_mass_kg_per_m'] = '999'
        with self.assertRaisesRegex(ValueError, 'detached'):
            checker.audit(p)


if __name__ == '__main__':
    unittest.main()
