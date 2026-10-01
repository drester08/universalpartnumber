import sqlite3
import unittest
from pathlib import Path
import build_numeric_evidence_gaps as gaps

ROOT = Path(__file__).resolve().parents[1]


class NumericEvidenceGapTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        self.db.row_factory = sqlite3.Row
        with sqlite3.connect(ROOT/'build/registry.sqlite') as original:
            original.backup(self.db)
        self.addCleanup(self.db.close)

    def test_real_three_counts_preserve_scopes_and_custody_gaps(self):
        report = gaps.build_report(self.db)
        self.assertEqual((report['active_normalized_numeric_records'],report['usable_explicit_conversion_records'],report['issue_count']), (301,298,3))
        self.assertTrue(all(row['property_id']=='PROP-REQUIRED-SPLICE-COUNT' for row in report['issues']))
        self.assertTrue(all(row['normalized_number']=='4' and row['unit_id'] is None for row in report['issues']))
        self.assertEqual([row['registered_source_artifact_states'] for row in report['issues']], [['blocked'],['remote_only'],['remote_only']])
        self.assertTrue(all(row['observation_declares_source_hash'] is False for row in report['issues']))
        self.assertTrue(any('SWK sets' in row['raw_value'] for row in report['issues']))
        self.assertTrue(all('inclusion' in row['qualifier'] or 'included hardware' in row['qualifier'] for row in report['issues']))

    def test_no_mutation_or_approval(self):
        before = self.db.total_changes
        report = gaps.build_report(self.db)
        self.assertEqual(self.db.total_changes, before)
        for key in ('database_mutated','source_truth_verified','identity_approved','application_suitability_approved','production_upn_allowed'):
            self.assertIs(report[key], False)

    def test_rejected_and_superseded_observations_excluded(self):
        for state in ('rejected','superseded'):
            self.db.execute('UPDATE observations SET review_state=? WHERE source_id=?', (state,'SRC-LEGRAND-US-WIRE-MESH-INSTALL'))
            report = gaps.build_report(self.db)
            self.assertEqual(report['issue_count'], 1)
            self.assertTrue(all(row['source_id']!='SRC-LEGRAND-US-WIRE-MESH-INSTALL' for row in report['issues']))

    def test_invalid_nonmissing_metadata_is_distinguished(self):
        self.db.execute("UPDATE units SET conversion_factor='NaN' WHERE unit_id='UNIT-MM'")
        report = gaps.build_report(self.db)
        self.assertGreater(report['issue_count'], 3)
        invalid = [row for row in report['issues'] if row['unit_id']=='UNIT-MM']
        self.assertTrue(invalid)
        self.assertTrue(all(row['issue_type']=='invalid_conversion_metadata' and row['missing_metadata']==[] for row in invalid))

    def test_single_source_can_have_multiple_distinct_counting_methods(self):
        report = gaps.build_report(self.db)
        legrand = [row for row in report['issues'] if row['source_id']=='SRC-LEGRAND-US-WIRE-MESH-INSTALL']
        self.assertEqual(len(legrand), 2)
        self.assertEqual(len({row['issue_id'] for row in report['issues']}), 3)
        self.assertNotEqual(legrand[0]['raw_value'], legrand[1]['raw_value'])


if __name__ == '__main__':
    unittest.main()
