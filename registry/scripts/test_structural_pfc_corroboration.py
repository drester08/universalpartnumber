"""Check source separation and reject unsafe PFC extraction assumptions."""
import copy
import unittest
from pathlib import Path
from unittest.mock import patch
import check_structural_pfc_corroboration as checker
from check_structural_pfc import screen
import validate_registry


class CorroborationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = checker.compare()
        cls.html = (checker.ROOT / 'artifacts' / checker.SOURCES['orangebook'][1]).read_text(encoding='utf-8')

    def test_scope_and_no_identity_approval(self):
        r = self.result
        self.assertEqual(r['outcomes']['macsteel'], {'nominal_values_agree': 6})
        self.assertEqual(r['outcomes']['orangebook'], {'nominal_field_conflict': 3, 'no_serial_candidate': 1,
                                                     'nominal_values_agree': 2})
        self.assertEqual(len(r['source_observations']['macsteel']), 6)
        self.assertEqual(len(r['source_observations']['orangebook']), 16)
        self.assertEqual(sorted(r['outside_family_scope_csv_lines'] + [x['csv_line'] for x in r['records']]), list(range(2, 807)))
        self.assertTrue(all(x['exact_article_verified'] is False for x in r['records']))
        self.assertTrue(all(s['exact_article_verified'] is False for x in r['records'] for s in x['source_screens'].values()))

    def by_size(self, h, b):
        return next(x for x in self.result['records'] if x['british_screen']['serial_size_candidate'] == [h, b])

    def test_absent_british_sizes_corroborated_not_closed(self):
        for size in [('100', '50'), ('180', '70')]:
            r = self.by_size(*size)
            self.assertEqual(r['british_screen']['outcome'], 'no_serial_candidate')
            self.assertEqual(r['source_screens']['macsteel']['outcome'], 'nominal_values_agree')
        r = self.by_size('100', '50')['source_screens']['orangebook']
        self.assertEqual(set(r['nominal_differences']), {'mass_kg_per_m', 'flange_mm'})
        self.assertEqual(r['source_candidates'][0]['mass_kg_per_m'], '10.2')
        self.assertEqual(r['source_candidates'][0]['flange_mm'], '8.5')

    def test_three_sources_preserve_conflicts(self):
        for size, diffs in [(('200', '75'), {'web_mm', 'flange_mm', 'mass_kg_per_m'}),
                            (('300', '100'), {'mass_kg_per_m'})]:
            r = self.by_size(*size)
            self.assertEqual(set(r['source_screens']['orangebook']['nominal_differences']), diffs)
            self.assertEqual(set(r['british_screen']['nominal_differences']), diffs)
            self.assertEqual(r['source_screens']['macsteel']['outcome'], 'nominal_values_agree')

    def test_non_equivalent_distance_and_grade_context(self):
        r = self.by_size('300', '100')
        am = r['source_screens']['orangebook']['source_candidates'][0]
        bs = r['british_screen']['source_candidates'][0]
        mac = r['source_screens']['macsteel']['source_candidates'][0]
        self.assertEqual(am['shear_centre_distance_cm'], '3.67')
        self.assertNotIn('centroid_distance_cm', am)
        self.assertEqual(bs['centroid_distance_cm'], '3.05')
        self.assertNotIn('shear_centre_distance_cm', bs)
        self.assertEqual(am['source_grade_context'], 'S355')
        self.assertEqual(mac['source_grade_context'], 'SANS 50025 / EN 10025 S355JR')
        self.assertNotIn('root_radius_mm', mac)
        self.assertEqual(am['root_radius_mm'], '15')
        self.assertEqual(am['depth_between_fillets_mm'], '237')

    def test_duplicate_keys_not_first_matched(self):
        rows = copy.deepcopy(self.result['source_observations']['macsteel'])
        rows[1] = copy.deepcopy(rows[0])
        with self.assertRaisesRegex(ValueError, 'duplicate source'):
            checker.validate_observations(rows, 6)
        actual = self.by_size('100', '50')['british_screen']['actual']
        row = {col: actual[field] for field, col in checker.FIELDS.items()}
        self.assertEqual(screen(row, rows)['outcome'], 'ambiguous_serial_candidate')

    def test_html_scope_units_and_numeric_guards(self):
        cases = [self.html.replace('kg/m', 'kg/mm'), self.html.replace('shear centre', 'centroid'),
                 self.html.replace('<td>10.2</td>', '<td>NaN</td>'),
                 self.html.replace('100x50x10', '125x65x15'),
                 self.html.replace('class="display table-data"', 'class="other"')]
        for text in cases:
            with self.subTest():
                self.assertNotEqual(text, self.html)
                with self.assertRaises(ValueError):
                    checker.parse_orangebook(text)

    def test_revision_mismatch_rejected(self):
        changed = copy.deepcopy(checker.SOURCES)
        sid, path, _ = changed['macsteel']
        changed['macsteel'] = (sid, path, '0'*64)
        with patch.object(checker, 'SOURCES', changed):
            with self.assertRaisesRegex(ValueError, 'source revision mismatch'):
                checker.compare()

    def test_source_type_rejected_before_database_build(self):
        rows = copy.deepcopy(validate_registry.read_csv('source-register.csv'))
        rows[0]['source_type'] = 'catalogue'
        errors = []
        with patch.object(validate_registry, 'read_csv', return_value=rows):
            validate_registry.validate_sources(errors)
        self.assertTrue(any('invalid source_type' in e for e in errors))


if __name__ == '__main__':
    unittest.main()
