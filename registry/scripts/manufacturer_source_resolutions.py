"""Replay evidence-bound publication decisions without changing source facts.

The event chain detects accidental edits against later events; it is not a
signature, reviewer authentication, or proof against rewriting the whole file.
Git history and independent review remain required governance controls.
"""
import hashlib
import json
import re
import sqlite3
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
POLICY = 'manufacturer-source-resolution-0.1'
LEDGER = ROOT / 'data/manufacturer-source-resolution-events.json'
DISPOSITIONS = {'publisher_corrected', 'manufacturer_clarified', 'local_interpretation', 'waived'}
EVENT_FIELDS = {'event_id', 'previous_event_id', 'previous_event_sha256', 'finding_id',
                'finding_evidence_sha256', 'action', 'actor', 'occurred_at', 'rationale',
                'policy_version', 'payload'}
EVIDENCE_FIELDS = {'source_id', 'artifact_id', 'artifact_sha256', 'source_locator',
                   'manufacturer_part_id', 'source_field', 'observation_id'}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                    ensure_ascii=False).encode('utf-8')).hexdigest().upper()


def evidence_binding(finding):
    """Bind the original issue, displays, pointers and registered custody."""
    return digest({key: finding[key] for key in ('finding_id', 'subject_key',
        'observation_id', 'source_html_line', 'retained_displays', 'evidence_pointer', 'evidence')})


def load_ledger(path=None):
    def unique_pairs(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('Duplicate resolution JSON key: ' + key)
            result[key] = value
        return result
    ledger = json.loads((path or LEDGER).read_text(encoding='utf-8'), object_pairs_hook=unique_pairs)
    if not isinstance(ledger, dict) or set(ledger) != {'policy_version', 'events'} or ledger['policy_version'] != POLICY or not isinstance(ledger['events'], list):
        raise ValueError('Unsupported manufacturer resolution ledger shape or policy')
    return ledger


def text(value, label):
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ValueError('Missing or noncanonical resolution ' + label)
    return value


def timestamp(value):
    text(value, 'timestamp')
    try:
        parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError as exc:
        raise ValueError('Invalid resolution timestamp') from exc
    if parsed.tzinfo is None or parsed.utcoffset().total_seconds() != 0:
        raise ValueError('Resolution timestamps must include UTC timezone')
    return parsed


def verify_evidence(connection, finding, proposal, root):
    evidence = proposal['evidence']
    if not isinstance(evidence, list) or not evidence:
        raise ValueError('Resolution requires retained evidence, including a waiver basis')
    seen = set()
    primary_exact = False
    subject = finding['subject_key']
    old_hashes = {e['artifact_sha256'].upper() for e in finding['evidence']}
    for entry in evidence:
        if not isinstance(entry, dict) or set(entry) != EVIDENCE_FIELDS:
            raise ValueError('Unsupported resolution evidence fields')
        for key in EVIDENCE_FIELDS - {'observation_id'}:
            text(entry[key], 'evidence ' + key)
        if not isinstance(entry['observation_id'], str):
            raise ValueError('Invalid resolution observation reference')
        if entry['manufacturer_part_id'] != subject['manufacturer_part_id'] or entry['source_field'] != subject['source_field']:
            raise ValueError('Resolution evidence detached from exact article/field')
        locator_key = (entry['artifact_id'], entry['source_locator'])
        if locator_key in seen:
            raise ValueError('Duplicate resolution evidence locator')
        seen.add(locator_key)
        row = connection.execute('''SELECT a.*, s.publisher_name, s.source_url, s.authority_tier,
            s.ingestion_status FROM source_artifacts a JOIN sources s USING(source_id)
            WHERE a.artifact_id=?''', (entry['artifact_id'],)).fetchone()
        if row is None or row['source_id'] != entry['source_id'] or row['retrieval_state'] != 'retrieved' or row['ingestion_status'] == 'blocked' or row['sha256'].upper() != entry['artifact_sha256'].upper():
            raise ValueError('Resolution evidence source/artifact custody invalid')
        local = (root.parent / row['local_path']).resolve()
        artifact_root = (root / 'artifacts').resolve()
        if not local.is_relative_to(artifact_root) or not local.is_file() or hashlib.sha256(local.read_bytes()).hexdigest().upper() != entry['artifact_sha256'].upper():
            raise ValueError('Resolution evidence bytes missing, outside cache or hash changed')
        observation_id = entry['observation_id']
        if observation_id:
            observation = connection.execute('SELECT * FROM observations WHERE observation_id=?', (observation_id,)).fetchone()
            if observation is None or observation['manufacturer_part_id'] != subject['manufacturer_part_id'] or observation['source_id'] != entry['source_id'] or (observation['raw_payload_sha256'] or '').upper() != entry['artifact_sha256'].upper() or observation['review_state'] != 'accepted':
                raise ValueError('Resolution exact-article observation must be accepted and checksum-bound')
            maker = connection.execute('SELECT legal_name, website_url FROM organizations WHERE organization_id=?', (subject['manufacturer_id'],)).fetchone()
            maker_host = urlparse(maker['website_url'] or '').hostname
            urls = [urlparse(row['source_url']), urlparse(row['artifact_url'])]
            first_party = bool(maker_host) and all(url.scheme == 'https' and url.hostname and
                (url.hostname == maker_host or url.hostname.endswith('.' + maker_host)) for url in urls)
            primary_exact |= first_party and row['authority_tier'] == 1 and row['publisher_name'] == maker['legal_name'] and entry['artifact_sha256'].upper() not in old_hashes
    if proposal['disposition'] in {'publisher_corrected', 'manufacturer_clarified'} and not primary_exact:
        raise ValueError('Publisher correction/clarification requires new exact-article primary evidence')


def replay(connection, findings, ledger=None, root=None):
    """Fail closed on invalid history; return research state without DB writes."""
    connection.row_factory = sqlite3.Row
    root = root or ROOT
    ledger = load_ledger() if ledger is None else ledger
    if not isinstance(ledger, dict) or set(ledger) != {'policy_version', 'events'} or ledger['policy_version'] != POLICY or not isinstance(ledger['events'], list):
        raise ValueError('Unsupported manufacturer resolution ledger shape or policy')
    by_id = {f['finding_id']: f for f in findings}
    states = {key: {'resolution_state': 'open', 'publication_status': 'unresolved',
                    'active_proposal': None, 'history': [], 'identity_approved': False,
                    'physical_conflict_verified': False} for key in by_id}
    seen = set()
    previous = None
    previous_time = None
    proposals = {}
    for event in ledger['events']:
        if not isinstance(event, dict) or set(event) != EVENT_FIELDS or event['policy_version'] != POLICY:
            raise ValueError('Unsupported resolution event fields or policy')
        identifier = text(event['event_id'], 'event ID')
        if not re.fullmatch(r'MRE-[0-9A-F]{24}', identifier) or identifier in seen:
            raise ValueError('Duplicate or invalid resolution event ID')
        seen.add(identifier)
        if event['previous_event_id'] != (previous['event_id'] if previous else '') or event['previous_event_sha256'] != (digest(previous) if previous else ''):
            raise ValueError('Resolution event history chain changed')
        occurred = timestamp(event['occurred_at'])
        if previous_time and occurred < previous_time:
            raise ValueError('Resolution history timestamps out of order')
        text(event['actor'], 'actor')
        text(event['rationale'], 'rationale')
        key = event['finding_id']
        if key not in by_id or event['finding_evidence_sha256'] != evidence_binding(by_id[key]):
            raise ValueError('Resolution finding missing or evidence revision unreconciled')
        state = states[key]
        payload = event['payload']
        if not isinstance(payload, dict):
            raise ValueError('Invalid resolution event payload')
        action = event['action']
        if action == 'propose':
            if set(payload) != {'disposition', 'evidence', 'interpretation', 'residual_risk'} or payload['disposition'] not in DISPOSITIONS:
                raise ValueError('Invalid resolution proposal disposition or fields')
            if state['active_proposal'] or state['resolution_state'] not in {'open', 'interpreted'}:
                raise ValueError('Resolution requires reopen before a new proposal')
            text(payload['interpretation'], 'interpretation')
            text(payload['residual_risk'], 'residual risk')
            verify_evidence(connection, by_id[key], payload, root)
            proposals[identifier] = event
            state['active_proposal'] = identifier
        elif action in {'approve', 'reject'}:
            if set(payload) != {'proposal_event_id', 'independence_attested', 'scope_attested'} or payload['independence_attested'] is not True or payload['scope_attested'] is not True:
                raise ValueError('Resolution review requires independence and exact-scope attestations')
            proposal = proposals.get(payload['proposal_event_id'])
            if proposal is None or proposal['finding_id'] != key or state['active_proposal'] != proposal['event_id']:
                raise ValueError('Resolution review is not bound to the active proposal')
            if event['actor'].casefold() == proposal['actor'].casefold():
                raise ValueError('Resolution review requires an independent reviewer')
            # Recheck original evidence at review, not just at proposal creation.
            verify_evidence(connection, by_id[key], proposal['payload'], root)
            state['active_proposal'] = None
            if action == 'approve':
                disposition = proposal['payload']['disposition']
                state['resolution_state'] = {'publisher_corrected': 'resolved',
                    'manufacturer_clarified': 'resolved', 'local_interpretation': 'interpreted',
                    'waived': 'waived'}[disposition]
                state['publication_status'] = {'publisher_corrected': 'corrected',
                    'manufacturer_clarified': 'clarified', 'local_interpretation': 'unresolved',
                    'waived': 'unresolved'}[disposition]
        elif action == 'reopen':
            if set(payload) != {'decision_event_id'} or state['active_proposal'] or state['resolution_state'] not in {'resolved', 'interpreted', 'waived'}:
                raise ValueError('Resolution reopen requires a closed reviewed decision')
            decisions = [e for e in state['history'] if e['action'] == 'approve']
            if not decisions or payload['decision_event_id'] != decisions[-1]['event_id']:
                raise ValueError('Resolution reopen must reference the latest approval')
            state['resolution_state'] = 'open'
            state['publication_status'] = 'unresolved'
        else:
            raise ValueError('Unsupported resolution action')
        state['history'].append(event)
        previous, previous_time = event, occurred
    return states
