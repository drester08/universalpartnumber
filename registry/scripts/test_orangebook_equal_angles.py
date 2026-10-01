"""Fail closed on source layout, missing measurements and identity shortcuts."""
import unittest
from decimal import Decimal
import check_orangebook_equal_angles as checker


class EqualAngleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = checker.ARTIFACT.read_text(encoding='utf-8')
        cls.report = checker.build_report()

    def test_coverage_and_no_approval(self):
        r = self.report
        self.assertEqual(r['source_fact_count'], 192)
        self.assertEqual(r['outcome_counts'], {'no_geometry_candidate': 25, 'nominal_geometry_candidate': 111})
        self.assertEqual(r['earlier_gap_outcome_counts'], {'no_geometry_candidate': 3, 'nominal_geometry_candidate': 7})
        self.assertEqual(len({x['seller_sku'] for x in r['records']}), 136)
        for record in r['records']:
            for field in ('seller_article_manufacturer_verified', 'exact_grade_verified',
                          'delivery_condition_verified', 'exact_article_verified',
                          'identity_approved', 'earlier_context_gap_closed'):
                self.assertIs(record[field], False)

    def test_blank_size_inherits_only_designation(self):
        first, second = self.report['source_facts'][:2]
        self.assertEqual(second['raw_size_cell'], '')
        self.assertEqual(second['designation_data_row'], first['html_data_row'])
        self.assertEqual(second['leg_a_mm'], '300')
        self.assertEqual(second['thickness_mm'], '34.0')
        self.assertEqual(second['mass_kg_per_m'], '150')
        self.assertEqual(second['source_grade_context'], 'S355')

    def test_orphan_blank_size_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Blank size'):
            checker.parse(self.html.replace('<b>300x300</b>', '<b></b>', 1))

    def test_measurement_never_inherits_or_becomes_zero(self):
        with self.assertRaisesRegex(ValueError, 'Missing or invalid'):
            checker.parse(self.html.replace('<td>150</td>', '<td></td>', 1))

    def test_unit_drift_rejected(self):
        with self.assertRaisesRegex(ValueError, 'headers/units'):
            checker.parse(self.html.replace('<th>kg/m</th>', '<th>kg</th>', 1))

    def test_body_span_rejected(self):
        with self.assertRaisesRegex(ValueError, 'cell span'):
            checker.parse(self.html.replace('<td><b>300x300</b>', '<td rowspan="2"><b>300x300</b>', 1))

    def test_grade_context_drift_rejected(self):
        with self.assertRaisesRegex(ValueError, 'grade context'):
            checker.parse(self.html.replace('Equal leg angles - L - S355 - 1. Section properties',
                                           'Equal leg angles - L - S235 - 1. Section properties'))

    def test_duplicate_geometry_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Duplicate nominal'):
            checker.parse(self.html.replace('<b>34.0</b>', '<b>35.0</b>', 1))

    def test_smaller_gaps_preserved(self):
        candidates = [r for r in self.report['earlier_gap_records'] if r['outcome'] == 'nominal_geometry_candidate']
        r = next(r for r in candidates if r['seller_sku'] == 'AE_S355RA_0023')
        f = r['manufacturer_catalogue_candidates'][0]
        self.assertEqual((f['leg_a_mm'], f['thickness_mm'], f['mass_kg_per_m']), ('45', '3.0', '2.09'))
        absent = {tuple(Decimal(v) for v in r['nominal_geometry_mm']) for r in self.report['earlier_gap_records']
                  if r['outcome'] == 'no_geometry_candidate'}
        self.assertEqual(absent, {(Decimal(40), Decimal(40), Decimal(3)),
                                 (Decimal(50), Decimal(50), Decimal(3))})


if __name__ == '__main__':
    unittest.main()
