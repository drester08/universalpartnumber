"""Synthetic decision fixtures; no real research issue is approved by tests."""
import copy
import hashlib
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import build_registry
import build_review_queue
import build_manufacturer_source_findings as findings_module
import manufacturer_source_resolutions as resolutions


class ResolutionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='upn-resolution-')
        self.path = Path(self.temp.name) / 'registry.sqlite'
        build_registry.build(self.path)
        self.db = sqlite3.connect(self.path)
        self.db.row_factory = sqlite3.Row
        self.findings = findings_module.derive(self.db,
            findings_module.load_report('ntn-6205zz-source.json'),
            findings_module.load_report('ntn-shield-seal-corroboration.json'))
        self.finding = self.findings[0]
        self.ledger = {'policy_version': resolutions.POLICY, 'events': []}

    def tearDown(self):
        self.db.close()
        self.temp.cleanup()

    def append(self, action, payload, actor='fixture-proposer'):
        previous = self.ledger['events'][-1] if self.ledger['events'] else None
        event = {'event_id': 'MRE-' + format(len(self.ledger['events']) + 1, '024X'),
            'previous_event_id': previous['event_id'] if previous else '',
            'previous_event_sha256': resolutions.digest(previous) if previous else '',
            'finding_id': self.finding['finding_id'],
            'finding_evidence_sha256': resolutions.evidence_binding(self.finding),
            'action': action, 'actor': actor, 'occurred_at': '2026-10-01T12:00:00Z',
            'rationale': 'Synthetic test rationale; not a real approval.',
            'policy_version': resolutions.POLICY, 'payload': payload}
        self.ledger['events'].append(event)
        return event

    def proposal(self, disposition='local_interpretation'):
        evidence = self.finding['evidence'][1]
        entry = {'source_id': evidence['source_id'], 'artifact_id': evidence['artifact_id'],
            'artifact_sha256': evidence['artifact_sha256'], 'source_locator': 'Synthetic fixture locator',
            'manufacturer_part_id': self.finding['subject_key']['manufacturer_part_id'],
            'source_field': self.finding['subject_key']['source_field'], 'observation_id': ''}
        return self.append('propose', {'disposition': disposition, 'evidence': [entry],
            'interpretation': 'Synthetic local reading; retain original displays.',
            'residual_risk': 'Original source remains unresolved; no identity approval.'})

    def review(self, action='approve', actor='fixture-independent-reviewer'):
        return self.append(action, {'proposal_event_id': self.ledger['events'][0]['event_id'],
            'independence_attested': True, 'scope_attested': True}, actor)

    def replay(self, root=None):
        return resolutions.replay(self.db, self.findings, self.ledger, root)[self.finding['finding_id']]

    def queue(self):
        with patch.object(resolutions, 'load_ledger', return_value=self.ledger):
            return build_review_queue.build_items(self.db)

    def test_empty_ledger_has_two_open_findings_and_no_writes(self):
        before = self.db.total_changes
        states = resolutions.replay(self.db, self.findings, self.ledger)
        self.assertEqual(len(states), 2)
        self.assertTrue(all(s['resolution_state'] == 'open' and not s['history'] for s in states.values()))
        self.assertEqual(self.db.total_changes, before)

    def test_proposal_adds_review_without_dropping_research(self):
        self.proposal()
        state = self.replay()
        self.assertEqual(state['resolution_state'], 'open')
        queue = self.queue()
        self.assertEqual(len(queue), 467)
        self.assertEqual(sum(i['queue_type'] == 'manufacturer_source_resolution_review' for i in queue), 1)
        self.assertIn('RW-' + self.finding['finding_id'], {i['work_item_id'] for i in queue})

    def test_local_interpretation_does_not_resolve_publication(self):
        self.proposal(); self.review()
        state = self.replay()
        self.assertEqual(state['resolution_state'], 'interpreted')
        self.assertEqual(state['publication_status'], 'unresolved')
        self.assertFalse(state['identity_approved'])
        self.assertFalse(state['physical_conflict_verified'])
        self.assertEqual(len(self.queue()), 466)
        self.assertIn('RW-' + self.finding['finding_id'], {i['work_item_id'] for i in self.queue()})

    def test_waiver_remains_unresolved_and_reopen_restores_stable_task(self):
        self.proposal('waived'); approval = self.review()
        self.assertEqual(self.replay()['publication_status'], 'unresolved')
        self.assertEqual(len(self.queue()), 465)
        self.append('reopen', {'decision_event_id': approval['event_id']}, 'fixture-reviewer')
        self.assertEqual(self.replay()['resolution_state'], 'open')
        self.assertEqual(len(self.replay()['history']), 3)
        self.assertIn('RW-' + self.finding['finding_id'], {i['work_item_id'] for i in self.queue()})

    def test_rejection_retains_open_task_and_history(self):
        self.proposal(); self.review('reject')
        self.assertEqual(self.replay()['resolution_state'], 'open')
        self.assertEqual(len(self.replay()['history']), 2)
        self.assertEqual(len(self.queue()), 466)

    def test_corroboration_cannot_be_publisher_correction_or_clarification(self):
        for disposition in ('publisher_corrected', 'manufacturer_clarified'):
            self.ledger['events'] = []
            self.proposal(disposition)
            with self.assertRaisesRegex(ValueError, 'new exact-article primary'):
                self.replay()

    def test_same_actor_case_insensitive_rejected(self):
        self.proposal(); self.review(actor='FIXTURE-PROPOSER')
        with self.assertRaisesRegex(ValueError, 'independent reviewer'):
            self.replay()

    def test_false_or_missing_attestations_rejected(self):
        self.proposal(); event = self.review()
        for key in ('independence_attested', 'scope_attested'):
            payload = copy.deepcopy(event['payload'])
            event['payload'][key] = False
            with self.assertRaisesRegex(ValueError, 'attestations'):
                self.replay()
            event['payload'] = payload

    def test_modified_history_rejected(self):
        proposal = self.proposal(); self.review()
        proposal['rationale'] = 'Changed after review'
        with self.assertRaisesRegex(ValueError, 'history chain'):
            self.replay()

    def test_duplicate_event_and_broken_chain_rejected(self):
        proposal = self.proposal(); approval = self.review()
        approval['event_id'] = proposal['event_id']
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            self.replay()
        approval['event_id'] = 'MRE-' + 'F'*24
        approval['previous_event_sha256'] = '0'*64
        with self.assertRaisesRegex(ValueError, 'history chain'):
            self.replay()

    def test_finding_revision_or_unknown_finding_rejected(self):
        proposal = self.proposal()
        proposal['finding_evidence_sha256'] = '0'*64
        with self.assertRaisesRegex(ValueError, 'unreconciled'):
            self.replay()
        proposal['finding_id'] = 'MRF-UNKNOWN'
        with self.assertRaisesRegex(ValueError, 'finding missing'):
            self.replay()

    def test_unsupported_action_fields_and_policy_rejected(self):
        proposal = self.proposal()
        for key, value in [('action', 'delete'), ('policy_version', 'unknown')]:
            old = proposal[key]; proposal[key] = value
            with self.assertRaises(ValueError): self.replay()
            proposal[key] = old
        proposal['identity_approved'] = True
        with self.assertRaisesRegex(ValueError, 'event fields'):
            self.replay()

    def test_exact_field_is_case_sensitive(self):
        proposal = self.proposal()
        proposal['payload']['evidence'][0]['source_field'] = 'Wrong field'
        with self.assertRaisesRegex(ValueError, 'exact article/field'):
            self.replay()

    def test_artifact_detachment_and_missing_bytes_rejected(self):
        proposal = self.proposal()
        proposal['payload']['evidence'][0]['artifact_sha256'] = '0'*64
        with self.assertRaisesRegex(ValueError, 'custody invalid'):
            self.replay()
        proposal['payload']['evidence'][0]['artifact_sha256'] = self.finding['evidence'][1]['artifact_sha256']
        with self.assertRaisesRegex(ValueError, 'bytes missing'):
            self.replay(Path(self.temp.name) / 'registry')

    def test_double_proposal_review_without_proposal_and_reopen_without_decision(self):
        for action, payload in [('approve', {'proposal_event_id': 'absent', 'independence_attested': True, 'scope_attested': True}),
                                ('reopen', {'decision_event_id': 'absent'})]:
            self.ledger['events'] = []; self.append(action, payload, 'fixture-reviewer')
            with self.assertRaises(ValueError): self.replay()
        self.ledger['events'] = []; self.proposal(); self.proposal()
        with self.assertRaisesRegex(ValueError, 'reopen'):
            self.replay()

    def test_waiver_requires_evidence_and_risk(self):
        proposal = self.proposal('waived')
        proposal['payload']['evidence'] = []
        with self.assertRaisesRegex(ValueError, 'waiver basis'):
            self.replay()
        proposal['payload']['residual_risk'] = ''
        with self.assertRaisesRegex(ValueError, 'residual risk'):
            self.replay()

    def test_timestamp_zone_and_order(self):
        proposal = self.proposal(); approval = self.review()
        proposal['occurred_at'] = '2026-10-01T12:00:00'
        with self.assertRaisesRegex(ValueError, 'UTC timezone'):
            self.replay()
        proposal['occurred_at'] = '2026-10-01T12:00:00Z'
        approval['previous_event_sha256'] = resolutions.digest(proposal)
        approval['occurred_at'] = '2026-09-30T12:00:00Z'
        with self.assertRaisesRegex(ValueError, 'out of order'):
            self.replay()

    def test_duplicate_json_keys_rejected(self):
        path = Path(self.temp.name) / 'duplicate.json'
        path.write_text('{"policy_version":"x","policy_version":"x","events":[]}', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'Duplicate resolution JSON key'):
            resolutions.load_ledger(path)

    def test_new_primary_correction_is_research_only_and_preserves_finding(self):
        root = Path(self.temp.name) / 'registry'
        (root / 'artifacts').mkdir(parents=True)
        raw = b'Synthetic manufacturer correction fixture, not real evidence.'
        (root / 'artifacts/fixture.html').write_bytes(raw)
        sha = hashlib.sha256(raw).hexdigest().upper()
        self.db.execute('''INSERT INTO sources SELECT 'SRC-FIXTURE', publisher_name,
            'Synthetic correction', 'https://bearingfinder.ntnamericas.com/synthetic-fixture', 'datasheet', 1,
            access_state, license_state, license_url, ingestion_status, version_label,
            publication_date, retrieved_at, notes FROM sources WHERE source_id='SRC-NTN-6205ZZ' ''')
        self.db.execute('''INSERT INTO source_artifacts VALUES ('ART-FIXTURE', 'SRC-FIXTURE',
            'https://bearingfinder.ntnamericas.com/synthetic-fixture', 'text/html', 'registry/artifacts/fixture.html',
            ?, '2026-10-01', 'retrieved', 'Synthetic fixture')''', (sha,))
        self.db.execute('''INSERT INTO observations SELECT 'OBS-FIXTURE', manufacturer_part_id,
            item_id, 'SRC-FIXTURE', source_locator, observed_name, observed_part_number,
            observed_at, ?, 'accepted' FROM observations WHERE observation_id='OBS-NTN-6205ZZ-20261001' ''', (sha,))
        proposal = self.proposal('publisher_corrected')
        evidence = proposal['payload']['evidence'][0]
        evidence.update(source_id='SRC-FIXTURE', artifact_id='ART-FIXTURE', artifact_sha256=sha, observation_id='OBS-FIXTURE')
        self.review()
        before = self.db.total_changes
        state = self.replay(root)
        self.assertEqual(state['resolution_state'], 'resolved')
        self.assertEqual(state['publication_status'], 'corrected')
        self.assertFalse(state['identity_approved'])
        self.assertEqual(self.db.total_changes, before)
        self.assertEqual(len(self.findings), 2)
        self.assertTrue(self.finding['retained_displays'])
        self.db.execute("UPDATE sources SET source_url='https://ntnamericas.com.example.invalid/fixture' WHERE source_id='SRC-FIXTURE'")
        with self.assertRaisesRegex(ValueError, 'new exact-article primary'):
            self.replay(root)
        self.db.execute("UPDATE sources SET source_url='https://bearingfinder.ntnamericas.com/synthetic-fixture' WHERE source_id='SRC-FIXTURE'")
        (root / 'artifacts/fixture.html').write_bytes(b'Changed synthetic bytes')
        with self.assertRaisesRegex(ValueError, 'hash changed'):
            self.replay(root)
        (root / 'artifacts/fixture.html').write_bytes(raw)
        self.db.execute("UPDATE observations SET review_state='unreviewed' WHERE observation_id='OBS-FIXTURE'")
        with self.assertRaisesRegex(ValueError, 'must be accepted'):
            self.replay(root)

    def test_registry_build_preserves_previous_database_on_invalid_resolution(self):
        before = self.path.read_bytes()
        self.proposal(); self.review(actor='fixture-proposer')
        with patch.object(resolutions, 'load_ledger', return_value=self.ledger):
            with self.assertRaisesRegex(ValueError, 'independent reviewer'):
                build_registry.build(self.path)
        self.assertEqual(self.path.read_bytes(), before)


if __name__ == '__main__':
    unittest.main()
