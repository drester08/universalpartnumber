"""Regression checks using retained source evidence and disposable CSV mutations."""

import csv
import tempfile
import unittest
from pathlib import Path

from check_klinger_maxiprofile_dimensions import compare


ROOT = Path(__file__).resolve().parents[2]
CATALOGUE = ROOT / 'registry/artifacts/klinger/klinger-catalogue-2014.pdf'
DATASET = ROOT / 'registry/artifacts/user-reference-csvs/Klinger Gaskets - Rev02 - 13 July 2026.csv'


class ComparisonTests(unittest.TestCase):
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

    def test_original_exact_findings(self):
        result = compare(CATALOGUE, DATASET)
        self.assertEqual(result['matched_rows'], 238)
        self.assertEqual(len(result['conflicts']), 1)
        self.assertEqual(result['conflicts'][0]['csv_line'], 789)
        self.assertEqual(result['conflicts'][0]['catalogue'], ('495', '450', '426', ''))
        self.assertEqual(result['unsupported_keys'], [])
        self.assertEqual(result['catalogue_only_keys'], [])

    def test_truncated_family_fails(self):
        def remove(rows):
            rows.pop(next(i for i, r in enumerate(rows) if r['Description'] == 'Klinger MaxiProfile Gasket'))
        with self.assertRaisesRegex(ValueError, 'Expected 239'):
            self.mutate(remove)

    def test_duplicate_fails(self):
        def duplicate(rows):
            rows.append(next(r for r in rows if r['Description'] == 'Klinger MaxiProfile Gasket').copy())
        with self.assertRaisesRegex(ValueError, 'Duplicate dataset key'):
            self.mutate(duplicate)

    def test_unsupported_key_is_visible(self):
        def change(rows):
            next(r for r in rows if r['Description'] == 'Klinger MaxiProfile Gasket')['Class / Table'] = 'Class 123'
        result = self.mutate(change)
        self.assertEqual(len(result['unsupported_keys']), 1)
        self.assertEqual(len(result['catalogue_only_keys']), 1)
        self.assertEqual(result['matched_rows'], 237)

    def test_fourth_value_is_not_ignored(self):
        def change(rows):
            next(r for r in rows if r['Description'] == 'Klinger MaxiProfile Gasket')['Dimensions Inner Ring Thk (mm)'] = '3'
        result = self.mutate(change)
        self.assertEqual(len(result['conflicts']), 2)


if __name__ == '__main__':
    unittest.main()
