"""Regression tests for pipe precision and ambiguous source-key handling."""

import csv
import tempfile
import unittest
from pathlib import Path

from check_piping_tenaris import compare, number, precision_compatible

ROOT = Path(__file__).resolve().parents[2]
CATALOGUE = ROOT / 'registry/artifacts/tenaris/civil-industrial-pipes-2026.pdf'
DATASET = ROOT / 'registry/artifacts/user-reference-csvs/Piping - Rev01 - 02 July 2026.csv'


class PipeTests(unittest.TestCase):
    def test_exact_original_outcomes(self):
        result = compare(CATALOGUE, DATASET)
        self.assertEqual(result['outcomes'], {'outside_source_key_scope': 12, 'printed_precision_compatible': 34, 'ambiguous_source_key': 4})
        self.assertEqual(result['construction_conflicts'], 50)
        self.assertEqual(len(result['records']), 50)
        ambiguous = [r for r in result['records'] if r['outcome'] == 'ambiguous_source_key']
        self.assertTrue(all(len(r['source_candidates']) == 2 for r in ambiguous))

    def test_strict_locale_and_precision(self):
        self.assertEqual(number('2,769'), number('2.769'))
        self.assertTrue(precision_compatible('21,3', '21,34'))
        self.assertFalse(precision_compatible('21,30', '21,34'))
        for raw in ('1,234.5', '', 'NaN'):
            with self.assertRaises(ValueError):
                number(raw)

    def mutated(self, action):
        with DATASET.open(encoding='utf-8-sig', newline='') as handle:
            reader = csv.DictReader(handle)
            fields, rows = reader.fieldnames, list(reader)
        action(rows)
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / 'fixture.csv'
            with p.open('w', encoding='utf-8', newline='') as handle:
                writer = csv.DictWriter(handle, fieldnames=fields)
                writer.writeheader()
                writer.writerows(rows)
            return compare(CATALOGUE, p)

    def test_truncation_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Expected 50'):
            self.mutated(lambda rows: rows.pop())

    def test_duplicate_rejected(self):
        def change(rows):
            rows[1] = rows[0].copy()
        with self.assertRaisesRegex(ValueError, 'Duplicate supplied key'):
            self.mutated(change)

    def test_changed_supported_dimension_is_conflict(self):
        def change(rows):
            rows[6]['Wall Thickness (mm)'] = '9.000'
        self.assertEqual(self.mutated(change)['outcomes']['dimension_conflict'], 1)


if __name__ == '__main__':
    unittest.main()
