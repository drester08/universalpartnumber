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
        self.assertEqual(len(first[0]), 66)
        self.assertEqual(len(first[1]), 1003)
        self.assertEqual(len({r['csv_line'] for r in first[1]}), 1003)
        self.assertEqual(sum(f['priority'] == 'P0' for f in first[0]), 41)
        self.assertEqual(sum(f['priority'] == 'P2' for f in first[0]), 25)
        by_kind = {}
        index = {f['finding_id']: f for f in first[0]}
        for ref in first[1]:
            kind = index[ref['finding_id']]['issue_type']
            by_kind[kind] = by_kind.get(kind, 0) + 1
        self.assertEqual(by_kind, {'dimension_conflict': 52, 'unsupported_key': 949, 'duplicate_key': 2})

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

    def test_unsafe_identity_promotion_rejected(self):
        original = validate_registry.read_csv
        def altered(name):
            rows = copy.deepcopy(original(name))
            if name == 'source-datasets.csv':
                for row in rows:
                    if row['dataset_id'] == findings.DATASET:
                        row.update(verification_state='validated', allowed_use='identity_evidence')
            return rows
        errors = []
        with patch.object(validate_registry, 'read_csv', altered):
            validate_registry.validate_dataset_findings(errors)
        self.assertTrue(any('prevent identity promotion' in e for e in errors))

    def changed_report(self, action):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'data').mkdir()
            (root / 'reports').mkdir()
            for name in ('source-datasets.csv', 'source-artifacts.csv'):
                shutil.copy2(findings.ROOT / 'data' / name, root / 'data' / name)
            name = 'klinger-maxiflex-comparison.json'
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


if __name__ == '__main__':
    unittest.main()
