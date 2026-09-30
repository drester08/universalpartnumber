"""Historical soft-cut comparison regression checks; disposable inputs only."""

import csv
import tempfile
import unittest
from pathlib import Path

from check_klinger_softcut_dimensions import compare, extract, FIELDS


ROOT = Path(__file__).resolve().parents[2]
CATALOGUE = ROOT / 'registry/artifacts/klinger/klinger-catalogue-2014.pdf'
DATASET = ROOT / 'registry/artifacts/user-reference-csvs/Klinger Gaskets - Rev02 - 13 July 2026.csv'


class ComparisonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = compare(CATALOGUE, DATASET)

    def mutate(self, action):
        with DATASET.open(encoding='utf-8-sig', newline='') as handle:
            reader = csv.DictReader(handle)
            fields, rows = reader.fieldnames, list(reader)
        action(rows)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'fixture.csv'
            with path.open('w', encoding='utf-8', newline='') as handle:
                writer = csv.DictWriter(handle, fieldnames=fields)
                writer.writeheader()
                writer.writerows(rows)
            return compare(CATALOGUE, path)

    def test_exact_original_totals(self):
        self.assertEqual(self.result['totals'], {'rows': 11280, 'full_face_od_id_agreement': 10360, 'unsupported_key': 920})
        self.assertEqual(self.result['catalogue_keys'], 470)
        self.assertEqual(len(self.result['duplicates']), 1)
        self.assertEqual(self.result['duplicates'][0]['csv_lines'], [11714, 11734])
        self.assertEqual(sum(len(c['csv_references']) for c in self.result['cases']), 11280)

    def test_drilling_and_footnote_survive(self):
        source, _ = extract(CATALOGUE)
        a, d, e = (source[('BS10 Flanges', 'Table ' + t, '6')] for t in ('A', 'D', 'E'))
        self.assertEqual(a['full_face'], d['full_face'])
        self.assertEqual(d['full_face'], e['full_face'])
        self.assertEqual((a['bolt_holes'], d['bolt_holes'], e['bolt_holes']), ('4', '8', '8'))
        self.assertEqual((a['hole_diameter_mm'], d['hole_diameter_mm'], e['hole_diameter_mm']), ('18', '18', '22'))
        self.assertIn('not unconditional', source[('DIN Standard Flanges', 'PN10', '65')]['footnote'])

    def test_missing_row_fails(self):
        def change(rows):
            rows.pop(next(i for i, r in enumerate(rows) if r['Description'] == 'Klinger Quantum Gasket'))
        with self.assertRaisesRegex(ValueError, 'Expected 24 families'):
            self.mutate(change)

    def test_missing_family_fails(self):
        def change(rows):
            rows[:] = [r for r in rows if r['Description'] != 'Klinger Quantum Gasket']
        with self.assertRaisesRegex(ValueError, 'Expected 24 families'):
            self.mutate(change)

    def test_dimension_mutation_is_conflict(self):
        def change(rows):
            next(r for r in rows if r['Description'] == 'Klinger Quantum Gasket')[FIELDS[0]] = '999'
        self.assertEqual(self.mutate(change)['totals']['dimension_conflict'], 1)

    def test_extra_dimension_not_ignored(self):
        def change(rows):
            next(r for r in rows if r['Description'] == 'Klinger Quantum Gasket')[FIELDS[2]] = '3'
        self.assertEqual(self.mutate(change)['totals']['dimension_conflict'], 1)

    def test_duplicate_is_reported_without_dropping_row(self):
        def change(rows):
            indices = [i for i, r in enumerate(rows) if r['Description'] == 'Klinger Quantum Gasket']
            rows[indices[1]] = rows[indices[0]].copy()
        result = self.mutate(change)
        self.assertEqual(len(result['duplicates']), 2)
        self.assertEqual(result['totals']['rows'], 11280)


if __name__ == '__main__':
    unittest.main()
