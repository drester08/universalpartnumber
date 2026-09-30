"""Test deterministic findings and stale-evidence/unsafe-promotion rejection."""

import copy
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import build_dataset_findings as findings
import validate_registry


class FindingTests(unittest.TestCase):
    def test_deterministic_complete_row_accounting(self):
        first = findings.derive()
        self.assertEqual(first, findings.derive())
        self.assertEqual(len(first[0]), 81)
        self.assertEqual(len(first[1]), 1594)
        self.assertEqual(sum(f['priority'] == 'P0' for f in first[0]), 50)
        self.assertEqual(sum(f['priority'] == 'P2' for f in first[0]), 31)
        by_kind = {}
        index = {f['finding_id']: f for f in first[0]}
        self.assertEqual(len({(index[r['finding_id']]['dataset_id'], r['csv_line']) for r in first[1]}), 1448)
        for ref in first[1]:
            kind = index[ref['finding_id']]['issue_type']
            by_kind[kind] = by_kind.get(kind, 0) + 1
        self.assertEqual(by_kind, {'dimension_conflict': 52, 'unsupported_key': 949, 'duplicate_key': 2,
                                   'construction_conflict': 50, 'source_ambiguity': 4, 'coverage_gap': 88,
                                   'material_interpretation': 51, 'mass_discrepancy': 3, 'article_evidence_gap': 395})

    def test_snapshot_tampering_rejected(self):
        original = validate_registry.read_csv
        def altered(name):
            rows = copy.deepcopy(original(name))
            if name == 'dataset-finding-rows.csv':
                rows.pop()
            return rows
        errors = []
        with patch.object(validate_registry, 'read_csv', altered):
            validate_registry.validate_dataset_findings(errors)
        self.assertTrue(any('stale or modified' in e for e in errors))

    def check_unsafe_identity_promotion(self, dataset_id):
        original = validate_registry.read_csv
        def altered(name):
            rows = copy.deepcopy(original(name))
            if name == 'source-datasets.csv':
                for row in rows:
                    if row['dataset_id'] == dataset_id:
                        row.update(verification_state='validated', allowed_use='identity_evidence')
            return rows
        errors = []
        with patch.object(validate_registry, 'read_csv', altered):
            validate_registry.validate_dataset_findings(errors)
        self.assertTrue(any('prevent identity promotion' in e for e in errors))

    def test_unsafe_identity_promotion_rejected(self):
        for dataset_id in (findings.DATASET, findings.PIPE_DATASET, findings.PLATE_DATASET):
            with self.subTest(dataset_id=dataset_id):
                self.check_unsafe_identity_promotion(dataset_id)

    def changed_report(self, action, name='klinger-maxiflex-comparison.json'):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'data').mkdir()
            (root / 'reports').mkdir()
            for seed_name in ('source-datasets.csv', 'source-artifacts.csv'):
                shutil.copy2(findings.ROOT / 'data' / seed_name, root / 'data' / seed_name)
            for report in findings.ROOT.glob('reports/*-comparison.json'):
                shutil.copy2(report, root / 'reports' / report.name)
            shutil.copy2(findings.ROOT / 'reports/plate-macsteel-screening.json', root / 'reports/plate-macsteel-screening.json')
            payload = json.loads((findings.ROOT / 'reports' / name).read_text(encoding='utf-8'))
            action(payload)
            (root / 'reports' / name).write_text(json.dumps(payload), encoding='utf-8')
            return findings.derive(root)

    def test_wrong_dataset_revision_rejected(self):
        with self.assertRaisesRegex(ValueError, 'dataset checksum mismatch'):
            self.changed_report(lambda r: r.update(dataset_sha256='0' * 64))

    def test_wrong_catalogue_revision_rejected(self):
        with self.assertRaisesRegex(ValueError, 'catalogue checksum mismatch'):
            self.changed_report(lambda r: r.update(catalogue_sha256='0' * 64))

    def test_out_of_range_report_locator_rejected(self):
        def change(report):
            report['conflicts'][0]['csv_line'] = 12164
        with self.assertRaisesRegex(ValueError, 'outside registered'):
            self.changed_report(change)

    def test_pipe_duplicate_locator_rejected(self):
        def change(report):
            report['records'][1]['csv_line'] = report['records'][0]['csv_line']
        with self.assertRaisesRegex(ValueError, 'missing or duplicate'):
            self.changed_report(change, 'piping-tenaris-comparison.json')

    def test_pipe_outcome_totals_rejected(self):
        def change(report):
            report['outcomes']['printed_precision_compatible'] += 1
        with self.assertRaisesRegex(ValueError, 'outcome counts'):
            self.changed_report(change, 'piping-tenaris-comparison.json')

    def test_pipe_wrong_input_revision_rejected(self):
        with self.assertRaisesRegex(ValueError, 'dataset checksum mismatch'):
            self.changed_report(lambda r: r.update(dataset_sha256='0' * 64), 'piping-tenaris-comparison.json')

    def test_pipe_nonboolean_conflict_rejected(self):
        def change(report):
            report['records'][0]['construction_conflict'] = 1
        with self.assertRaisesRegex(ValueError, 'construction conflict count'):
            self.changed_report(change, 'piping-tenaris-comparison.json')

    def test_plate_missing_locator_rejected(self):
        def change(report):
            report['records'][1]['csv_line'] = report['records'][0]['csv_line']
        with self.assertRaisesRegex(ValueError, 'missing or duplicate'):
            self.changed_report(change, 'plate-macsteel-screening.json')

    def test_plate_false_article_approval_rejected(self):
        def change(report):
            report['records'][0]['exact_article_verified'] = True
        with self.assertRaisesRegex(ValueError, 'cannot assert reviewed'):
            self.changed_report(change, 'plate-macsteel-screening.json')

    def test_plate_wrong_mass_totals_rejected(self):
        with self.assertRaisesRegex(ValueError, 'mass discrepancy count'):
            self.changed_report(lambda r: r.update(mass_discrepancies=0), 'plate-macsteel-screening.json')

    def test_plate_wrong_outcome_totals_rejected(self):
        with self.assertRaisesRegex(ValueError, 'outcome counts'):
            self.changed_report(lambda r: r.update(family_outcomes={}), 'plate-macsteel-screening.json')

    def test_plate_wrong_input_revision_rejected(self):
        with self.assertRaisesRegex(ValueError, 'dataset checksum mismatch'):
            self.changed_report(lambda r: r.update(dataset_sha256='0'*64), 'plate-macsteel-screening.json')


if __name__ == '__main__':
    unittest.main()
