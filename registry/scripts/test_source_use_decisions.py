"""Entirely synthetic permission fixtures; no real authorization decisions."""
import copy
import hashlib
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import source_use_decisions as d
import source_use_gates as g
import build_registry


class SourceDecisionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        folder = self.root/'registry/artifacts/TEST'
        folder.mkdir(parents=True)
        self.source_path = folder/'source.txt'
        self.permission_path = folder/'permission.txt'
        self.source_path.write_bytes(b'SYNTHETIC SOURCE - NOT A REAL ARTICLE')
        self.permission_path.write_bytes(b'SYNTHETIC PERMISSION - NOT A REAL GRANT')
        self.sha = hashlib.sha256(self.source_path.read_bytes()).hexdigest().upper()
        self.permission_sha = hashlib.sha256(self.permission_path.read_bytes()).hexdigest().upper()
        self.root_patch = patch.object(d, 'ROOT', self.root)
        self.root_patch.start()
        self.addCleanup(self.root_patch.stop)
        self.db = sqlite3.connect(':memory:')
        self.addCleanup(self.db.close)
        self.db.executescript('CREATE TABLE sources(source_id,license_state,ingestion_status,source_url); '
                              'CREATE TABLE observations(manufacturer_part_id,source_id,review_state,raw_payload_sha256); '
                              'CREATE TABLE source_artifacts(source_id,local_path,sha256,retrieval_state);')
        self.db.execute("INSERT INTO sources VALUES ('TEST-SOURCE','open','license_verified','https://example.test/article')")
        self.db.execute("INSERT INTO observations VALUES ('TEST-PART','TEST-SOURCE','accepted',?)", (self.sha,))
        self.db.execute("INSERT INTO source_artifacts VALUES ('TEST-SOURCE','registry/artifacts/TEST/source.txt',?,'retrieved')", (self.sha,))
        self.ledger = dict(policy_version=d.VERSION, revocations=[], decisions=[dict(
            decision_id='TEST-DECISION', source_id='TEST-SOURCE', source_url='https://example.test/article',
            artifact_sha256=self.sha, permitted_use=d.USE, permission_path='registry/artifacts/TEST/permission.txt',
            permission_sha256=self.permission_sha, permission_locator='SYNTHETIC TEST CLAUSE',
            attribution_requirements=[], proposed_by='TEST-PROPOSER', proposed_at='2026-09-29',
            reviewer='TEST-REVIEWER', reviewed_at='2026-09-30', independence_attested=True,
            valid_from='2026-10-01', valid_until='2026-10-31', decision='approved')])

    def holds(self, as_of='2026-10-01'):
        return g.part_holds(self.db, self.ledger, as_of)

    def test_complete_synthetic_chain_clears_only_fixture_hold(self):
        self.assertEqual(self.holds(), {})
        self.assertEqual(self.holds('2026-10-31'), {})

    def test_empty_real_ledger_does_not_grant_permission(self):
        self.assertIn('TEST-PART', g.part_holds(self.db, dict(policy_version=d.VERSION, decisions=[], revocations=[]), '2026-10-01'))

    def test_future_and_expired_permission_held(self):
        self.assertIn('TEST-PART', self.holds('2026-09-30'))
        self.assertIn('TEST-PART', self.holds('2026-11-01'))

    def test_future_review_cannot_authorize_present_use(self):
        self.ledger['decisions'][0]['reviewed_at'] = '2026-10-02'
        self.assertIn('TEST-PART', self.holds())

    def test_revocation_effective_date(self):
        self.ledger['revocations'] = [dict(decision_id='TEST-DECISION', revoked_at='2026-10-02', revoked_by='TEST', reason='SYNTHETIC')]
        self.assertEqual(self.holds(), {})
        self.assertIn('TEST-PART', self.holds('2026-10-02'))

    def test_url_source_revision_and_purpose_not_inherited(self):
        for key, value in [('source_id', 'TEST-OTHER'), ('source_url', 'https://example.test/other'), ('artifact_sha256', 'A'*64)]:
            ledger = copy.deepcopy(self.ledger)
            ledger['decisions'][0][key] = value
            self.assertIn('TEST-PART', g.part_holds(self.db, ledger, '2026-10-01'))
        self.ledger['decisions'][0]['permitted_use'] = 'raw_html_publication'
        with self.assertRaises(ValueError):
            self.holds()

    def test_self_review_and_unattested_review_rejected(self):
        for key, value in [('reviewer', ' test-proposer '), ('independence_attested', False), ('independence_attested', 1)]:
            ledger = copy.deepcopy(self.ledger)
            ledger['decisions'][0][key] = value
            with self.assertRaises(ValueError):
                g.part_holds(self.db, ledger, '2026-10-01')

    def test_permission_evidence_tamper_rejected(self):
        self.permission_path.write_bytes(b'CHANGED SYNTHETIC LETTER')
        with self.assertRaisesRegex(ValueError, 'checksum changed'):
            self.holds()

    def test_source_artifact_tamper_missing_or_remote_held(self):
        self.source_path.write_bytes(b'CHANGED SOURCE')
        self.assertIn('TEST-PART', self.holds())
        self.source_path.unlink()
        self.assertIn('TEST-PART', self.holds())
        self.db.execute("UPDATE source_artifacts SET retrieval_state='remote_only'")
        self.assertIn('TEST-PART', self.holds())

    def test_path_escape_and_absolute_path_rejected(self):
        for path in ('registry/artifacts/../../outside.txt', str(self.permission_path), 'registry/artifacts/../data/permission.json'):
            ledger = copy.deepcopy(self.ledger)
            ledger['decisions'][0]['permission_path'] = path
            with self.assertRaises(ValueError):
                g.part_holds(self.db, ledger, '2026-10-01')

    def test_duplicate_or_overlapping_current_grants_held(self):
        other = copy.deepcopy(self.ledger['decisions'][0])
        self.ledger['decisions'].append(other)
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            self.holds()
        other['decision_id'] = 'TEST-SECOND'
        self.assertIn('TEST-PART', self.holds())

    def test_unfulfilled_attribution_is_not_permission(self):
        self.ledger['decisions'][0]['attribution_requirements'] = ['SYNTHETIC CREDIT']
        self.assertIn('not yet implemented', self.holds()['TEST-PART'][0]['reason'])

    def test_bad_dates_unknown_fields_and_rejected_decisions(self):
        for key, value in [('valid_until', '2026-09-30'), ('proposed_at', '2026-10-02'), ('reviewed_at', '2026-02-30')]:
            ledger = copy.deepcopy(self.ledger)
            ledger['decisions'][0][key] = value
            with self.assertRaises(ValueError):
                g.part_holds(self.db, ledger, '2026-10-01')
        self.ledger['decisions'][0]['decision'] = 'rejected'
        self.assertIn('TEST-PART', self.holds())
        self.ledger['decisions'][0]['unexpected'] = True
        with self.assertRaises(ValueError):
            self.holds()

    def test_gate_does_not_mutate_ledger(self):
        before = copy.deepcopy(self.ledger)
        self.holds()
        self.assertEqual(before, self.ledger)

    def test_attribution_state_cannot_omit_obligations(self):
        self.db.execute("UPDATE sources SET license_state='attribution'")
        self.assertIn('attribution license fulfillment', self.holds()['TEST-PART'][0]['reason'])

    def test_bad_ledger_preserves_previous_built_database(self):
        target = self.root/'previous.sqlite'
        target.write_bytes(b'PREVIOUS SYNTHETIC OUTPUT')
        with patch.object(d, 'load', side_effect=ValueError('authorization ledger rejected')):
            with self.assertRaisesRegex(ValueError, 'authorization ledger rejected'):
                build_registry.build(target)
        self.assertEqual(target.read_bytes(), b'PREVIOUS SYNTHETIC OUTPUT')
        self.assertFalse(target.with_suffix('.tmp').exists())


if __name__ == '__main__':
    unittest.main()
