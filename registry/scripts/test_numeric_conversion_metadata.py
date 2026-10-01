import sqlite3
import unittest
import sys
from contextlib import redirect_stdout
from io import StringIO
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch
import numeric_rules as numeric
import screen_candidates as screen
import audit_completeness as audit

ROOT = Path(__file__).resolve().parents[1]


class NumericConversionMetadataTests(unittest.TestCase):
    def row(self, **changes):
        value = dict(normalized_number='25.4', quantity_kind='length',
                     conversion_factor='0.001', conversion_offset='0')
        value.update(changes)
        return value

    def test_no_default_factor_or_offset(self):
        for key in ('normalized_number', 'conversion_factor', 'conversion_offset'):
            for value in (None, '', ' ', '\t', '\u00a0'):
                with self.subTest(key=key, value=value):
                    self.assertIsNone(numeric.to_base_value(self.row(**{key:value})))

    def test_invalid_numbers_rejected_without_exception(self):
        for key in ('normalized_number', 'conversion_factor', 'conversion_offset'):
            for value in ('bad', 'NaN', 'sNaN', 'Infinity', '-Infinity'):
                self.assertIsNone(numeric.to_base_value(self.row(**{key:value})))

    def test_factor_must_be_positive(self):
        for value in ('0', '-1', '-0.001'):
            self.assertIsNone(numeric.to_base_value(self.row(conversion_factor=value)))

    def test_quantity_kind_required(self):
        for value in (None, '', ' ', False):
            self.assertIsNone(numeric.to_base_value(self.row(quantity_kind=value)))

    def test_metric_and_inch_conversion(self):
        metric = numeric.to_base_value(self.row())
        inch = numeric.to_base_value(self.row(normalized_number='1', conversion_factor='0.0254'))
        self.assertEqual(metric, inch)
        self.assertEqual(metric.base_value, Decimal('0.0254'))

    def test_explicit_affine_offset_and_zero(self):
        result = numeric.to_base_value(self.row(normalized_number='0', quantity_kind='temperature', conversion_factor='1', conversion_offset='273.15'))
        self.assertEqual(result.base_value, Decimal('273.15'))
        self.assertEqual(numeric.to_base_value(self.row(normalized_number='-1')).base_value, Decimal('-0.001'))

    def test_invalid_values_or_tolerances_cannot_match(self):
        valid = numeric.NumericValue('length', Decimal('1'))
        rule = numeric.NumericRule('length', Decimal('0'), Decimal('0'))
        for value in ('NaN', 'sNaN', 'Infinity'):
            self.assertFalse(numeric.compatible(valid, numeric.NumericValue('length', Decimal(value)), rule))
            self.assertFalse(numeric.compatible(valid, valid, numeric.NumericRule('length', Decimal(value), Decimal('0'))))
        for value in ('-1', '0.03', 'Infinity'):
            self.assertFalse(numeric.compatible(valid, valid, numeric.NumericRule('length', Decimal('0'), Decimal(value))))

    def test_sql_coverage_function_requires_registered_metadata(self):
        db = sqlite3.connect(':memory:')
        self.addCleanup(db.close)
        db.create_function('numeric_ready', 4, numeric.conversion_ready)
        self.assertEqual(db.execute('SELECT numeric_ready(?,?,?,?)', ('1','length',None,'0')).fetchone()[0], 0)
        self.assertEqual(db.execute('SELECT numeric_ready(?,?,?,?)', ('0','length','1','0')).fetchone()[0], 1)

    def test_screen_excludes_missing_metadata_not_raw_fallback(self):
        db = sqlite3.connect(':memory:')
        db.row_factory = sqlite3.Row
        self.addCleanup(db.close)
        with sqlite3.connect(ROOT/'build/registry.sqlite') as original:
            original.backup(db)
        baseline = screen.screen(db, '2026-10-01')
        self.assertEqual(len(baseline), 25)
        db.execute("UPDATE units SET conversion_factor=NULL WHERE quantity_kind='length'")
        values = screen.load_parts(db)
        for part in values.values():
            for key in ('PROP-LENGTH','PROP-BORE-DIAMETER','PROP-OUTSIDE-DIAMETER'):
                self.assertNotIn(key, part['values'])
        remaining = screen.screen(db, '2026-10-01')
        self.assertTrue(all(row['result'] != 'candidate' for row in remaining))
        self.assertTrue(all('PROP-LENGTH' in row['missing_properties'] for row in remaining))

    def test_equal_singleton_sets_still_validate_kind_and_rule(self):
        valid = numeric.NumericValue('length', Decimal('1'))
        for rule in (numeric.NumericRule('mass', Decimal('0'), Decimal('0')),
                     numeric.NumericRule('length', Decimal('Infinity'), Decimal('0'))):
            self.assertFalse(numeric.sets_compatible({valid}, {valid}, rule))
        invalid = numeric.NumericValue('length', Decimal('Infinity'))
        self.assertFalse(numeric.sets_compatible({invalid}, {invalid}, numeric.NumericRule('length', Decimal('0'), Decimal('0'))))

    def test_accepted_coverage_rejects_missing_factor_and_wrong_kind(self):
        for corruption in ('factor', 'kind'):
            with self.subTest(corruption=corruption):
                db = sqlite3.connect(':memory:')
                db.row_factory = sqlite3.Row
                with sqlite3.connect(ROOT/'build/registry.sqlite') as original:
                    original.backup(db)
                part, profile, prop = db.execute("SELECT mp.manufacturer_part_id,mp.profile_id,ipp.property_id FROM manufacturer_parts mp JOIN identity_profile_properties ipp ON ipp.profile_id=mp.profile_id WHERE ipp.requirement='required' AND ipp.comparison_rule='numeric_exact' LIMIT 1").fetchone()
                db.execute('DELETE FROM identity_profile_properties WHERE profile_id=? AND property_id!=?', (profile,prop))
                units = [r[0] for r in db.execute('SELECT DISTINCT sv.unit_id FROM specification_values sv JOIN observations o ON o.observation_id=sv.observation_id WHERE o.manufacturer_part_id=? AND sv.property_id=?', (part,prop))]
                self.assertTrue(units)
                for unit in units:
                    if corruption == 'factor':
                        db.execute('UPDATE units SET conversion_factor=NULL WHERE unit_id=?', (unit,))
                    else:
                        db.execute("UPDATE units SET quantity_kind='TEST-WRONG-KIND' WHERE unit_id=?", (unit,))
                db.execute("UPDATE observations SET review_state='accepted' WHERE manufacturer_part_id=?", (part,))
                db.execute("INSERT INTO manufacturer_part_reviews VALUES ('TEST-CONVERSION-REVIEW',?,'accepted','SYNTHETIC TEST ONLY','TEST','2026-10-01','TEST')", (part,))
                output = StringIO()
                with patch.object(audit.sqlite3, 'connect', return_value=db), patch.object(audit.source_use_gates, 'part_holds', return_value={}), patch.object(sys, 'argv', ['audit_completeness.py']), redirect_stdout(output):
                    self.assertEqual(audit.main(), 1)
                line = next(line for line in output.getvalue().splitlines() if 'required properties;' in line and f'manufacturer_part_id={part}' in line)
                self.assertIn('0/1 required properties', line)


if __name__ == '__main__':
    unittest.main()
