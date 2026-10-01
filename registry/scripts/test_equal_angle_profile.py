"""Exercise the draft equal-angle identity profile through real screening rules."""
import copy
import sqlite3
import tempfile
import unittest
from collections import defaultdict
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch
import build_registry
import numeric_rules
import screen_candidates

PROFILE = 'PROFILE-ANGLE-EQUAL-HOT-ROLLED-STEEL-0.1'


class EqualAngleProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='upn-angle-profile-')
        cls.path = Path(cls.temp.name) / 'registry.sqlite'
        build_registry.build(cls.path)
        cls.db = sqlite3.connect(cls.path)
        cls.db.row_factory = sqlite3.Row
        cls.required = screen_candidates.required_properties(cls.db, PROFILE)
        cls.rules = numeric_rules.load_rules(cls.db)

    @classmethod
    def tearDownClass(cls):
        cls.db.close()
        cls.temp.cleanup()

    def setUp(self):
        values = defaultdict(set)
        for prop, rule in self.required:
            values[prop] = ({numeric_rules.NumericValue('length', Decimal('0.005'))}
                            if rule == 'numeric_exact' else {'specific_reviewable_value'})
        values['PROP-ANGLE-GEOMETRY'] = {'equal_leg_angle_90_degree'}
        values['PROP-SECTION-PRODUCTION-ROUTE'] = {'hot_rolled'}
        values['PROP-MATERIAL-GRADE'] = {'s355jr'}
        for p in ('PROP-ANGLE-LEG-A', 'PROP-ANGLE-LEG-B'):
            values[p] = {numeric_rules.NumericValue('length', Decimal('0.060'))}
        values['PROP-LENGTH'] = {numeric_rules.NumericValue('length', Decimal('6'))}
        self.parts = {name: {'manufacturer_id': name, 'profile_id': PROFILE,
                            'part_number': 'SYNTHETIC-' + name, 'values': copy.deepcopy(values)}
                      for name in ('A', 'B')}

    def screen(self):
        with patch.object(screen_candidates, 'load_parts', return_value=self.parts):
            return screen_candidates.screen(self.db, '2026-10-01')

    def test_scope_is_draft_and_no_real_angle_articles_ingested(self):
        self.assertEqual(self.db.execute('SELECT status FROM identity_profiles WHERE profile_id=?', (PROFILE,)).fetchone()[0], 'draft')
        self.assertEqual(self.db.execute('SELECT count(*) FROM manufacturer_parts WHERE profile_id=?', (PROFILE,)).fetchone()[0], 0)
        self.assertEqual(len(self.required), 17)
        self.assertEqual(self.screen()[0]['result'], 'candidate')
        added = self.db.execute("SELECT controlled_value_id FROM controlled_values WHERE controlled_value_id IN "
            "('CV-ANGLE-EQUAL-90','CV-SECTION-ROUTE-HOT-ROLLED','CV-STEEL-GRADE-S355JR','CV-STEEL-GRADE-S355J2')").fetchall()
        self.assertEqual(len(added), 4)
        self.assertEqual(self.db.execute("SELECT count(*) FROM specification_value_mappings WHERE controlled_value_id IN "
            "('CV-ANGLE-EQUAL-90','CV-SECTION-ROUTE-HOT-ROLLED','CV-STEEL-GRADE-S355JR','CV-STEEL-GRADE-S355J2')").fetchone()[0], 0)

    def test_each_required_field_missing_blocks_candidate(self):
        original = copy.deepcopy(self.parts)
        blocking = screen_candidates.PROFILE_RULES[PROFILE]['blocking_properties']
        for prop, _ in self.required:
            with self.subTest(property=prop):
                self.parts = copy.deepcopy(original)
                self.parts['B']['values'][prop] = set()
                rows = self.screen()
                if prop in blocking:
                    self.assertEqual(rows, [])
                else:
                    self.assertEqual(rows[0]['result'], 'insufficient_evidence')
                    self.assertIn(prop, rows[0]['missing_properties'])

    def test_geometry_only_never_candidate(self):
        keep = {'PROP-ANGLE-LEG-A', 'PROP-ANGLE-LEG-B', 'PROP-ANGLE-THICKNESS'}
        for p in self.parts.values():
            p['values'] = defaultdict(set, {k: v for k, v in p['values'].items() if k in keep})
        self.assertEqual(self.screen()[0]['result'], 'insufficient_evidence')

    def test_jr_and_j2_conflict(self):
        self.parts['B']['values']['PROP-MATERIAL-GRADE'] = {'s355j2'}
        self.assertEqual(self.screen()[0]['result'], 'hard_conflict')
        self.assertIn('PROP-MATERIAL-GRADE', self.screen()[0]['conflicting_properties'])

    def test_broad_grade_never_closes_full_grade(self):
        for value in ('s355', 'cq', 'commercial_quality', 'unknown', 's355jr+ar'):
            with self.subTest(value=value):
                self.parts['A']['values']['PROP-MATERIAL-GRADE'] = {value}
                self.parts['B']['values']['PROP-MATERIAL-GRADE'] = {value}
                self.assertEqual(self.screen()[0]['result'], 'insufficient_evidence')

    def test_out_of_scope_routes_and_shapes_are_not_candidates(self):
        for prop, value in [('PROP-SECTION-PRODUCTION-ROUTE', 'cold_formed'),
                            ('PROP-ANGLE-GEOMETRY', 'unequal_leg_angle')]:
            for p in self.parts.values():
                p['values'][prop] = {value}
            self.assertEqual(self.screen()[0]['result'], 'insufficient_evidence')

    def test_length_radii_condition_tolerance_conflicts(self):
        original = copy.deepcopy(self.parts)
        for prop, value in [('PROP-LENGTH', numeric_rules.NumericValue('length', Decimal('13'))),
                            ('PROP-ANGLE-ROOT-RADIUS', numeric_rules.NumericValue('length', Decimal('0.006'))),
                            ('PROP-ANGLE-TOE-RADIUS', numeric_rules.NumericValue('length', Decimal('0.0025'))),
                            ('PROP-SECTION-DELIVERY-CONDITION', 'normalised'),
                            ('PROP-SECTION-TOLERANCE-STANDARD', 'different_declared_tolerance')]:
            self.parts = copy.deepcopy(original)
            self.parts['B']['values'][prop] = {value}
            self.assertEqual(self.screen()[0]['result'], 'hard_conflict')

    def test_mass_cannot_rescue_missing_identity(self):
        for p in self.parts.values():
            p['values']['PROP-SECTION-MASS-PER-LENGTH'] = {numeric_rules.NumericValue('mass_per_length', Decimal('4.57'))}
            p['values']['PROP-SECTION-DELIVERY-CONDITION'] = set()
        self.assertEqual(self.screen()[0]['result'], 'insufficient_evidence')

    def test_exact_unit_conversion_and_no_tolerance_allowance(self):
        a = numeric_rules.NumericValue('length', Decimal('60') * Decimal('0.001'))
        b = numeric_rules.NumericValue('length', Decimal('0.06'))
        prop = 'PROP-ANGLE-LEG-A'
        self.assertEqual(screen_candidates.compare_property(PROFILE, prop, 'numeric_exact', {a}, {b}, self.rules), 'match')
        c = numeric_rules.NumericValue('length', Decimal('0.060001'))
        self.assertEqual(screen_candidates.compare_property(PROFILE, prop, 'numeric_exact', {a}, {c}, self.rules), 'conflict')
        wrong_kind = numeric_rules.NumericValue('mass', Decimal('0.06'))
        self.assertEqual(screen_candidates.compare_property(PROFILE, prop, 'numeric_exact', {a}, {wrong_kind}, self.rules), 'conflict')

    def test_numeric_policy_has_six_zero_tolerance_rules(self):
        rules = [r for (profile, _), r in self.rules.items() if profile == PROFILE]
        self.assertEqual(len(rules), 6)
        self.assertTrue(all(r.absolute_tolerance == 0 and r.relative_tolerance == 0 for r in rules))


if __name__ == '__main__':
    unittest.main()
