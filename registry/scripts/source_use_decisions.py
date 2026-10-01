"""Evidence-bound reuse decisions; structural checks do not authenticate grants."""
import hashlib
import json
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LEDGER = ROOT/'registry/data/source-use-decisions.json'
VERSION = 'source-use-decisions-0.1'
USE = 'upn_derived_fact_publication'


def text(value):
    return isinstance(value, str) and bool(value.strip())


def day(value):
    if not isinstance(value, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
        raise ValueError('Explicit ISO date required')
    return date.fromisoformat(value)


def digest(value):
    if not isinstance(value, str) or not re.fullmatch(r'[A-Fa-f0-9]{64}', value):
        raise ValueError('SHA-256 required')
    return value.upper()


def verify_bytes(path, expected):
    # Permissions and licensed artifact originals must be private local evidence.
    if not isinstance(path, str) or not path.startswith('registry/artifacts/') or '\\' in path:
        raise ValueError('Private registry artifact path required')
    resolved = (ROOT/path).resolve()
    base = (ROOT/'registry/artifacts').resolve()
    if not resolved.is_relative_to(base) or not resolved.is_file():
        raise ValueError('Evidence path outside private artifact root or missing')
    if hashlib.sha256(resolved.read_bytes()).hexdigest().upper() != digest(expected):
        raise ValueError('Permission or source evidence checksum changed')


def validate(ledger):
    if not isinstance(ledger, dict) or set(ledger) != {'policy_version', 'decisions', 'revocations'} or ledger['policy_version'] != VERSION:
        raise ValueError('Invalid source-use ledger contract')
    if not isinstance(ledger['decisions'], list) or not isinstance(ledger['revocations'], list):
        raise ValueError('Decision and revocation lists required')
    required = {'decision_id', 'source_id', 'source_url', 'artifact_sha256', 'permitted_use',
                'permission_path', 'permission_sha256', 'permission_locator', 'attribution_requirements',
                'proposed_by', 'proposed_at', 'reviewer', 'reviewed_at', 'independence_attested',
                'valid_from', 'valid_until', 'decision'}
    ids = set()
    for record in ledger['decisions']:
        if not isinstance(record, dict) or set(record) != required:
            raise ValueError('Invalid source-use decision fields')
        for key in ('decision_id', 'source_id', 'source_url', 'permission_path', 'permission_locator',
                    'proposed_by', 'reviewer'):
            if not text(record[key]):
                raise ValueError('Required decision text missing: ' + key)
        if record['decision_id'] in ids:
            raise ValueError('Duplicate source-use decision ID')
        ids.add(record['decision_id'])
        if record['permitted_use'] != USE or record['decision'] not in ('approved', 'rejected'):
            raise ValueError('Unsupported permission purpose or decision')
        if record['independence_attested'] is not True or record['reviewer'].strip().casefold() == record['proposed_by'].strip().casefold():
            raise ValueError('Independent authorization review required')
        if day(record['proposed_at']) > day(record['reviewed_at']):
            raise ValueError('Review predates proposal')
        if day(record['valid_from']) > day(record['valid_until']):
            raise ValueError('Invalid authorization validity interval')
        if not isinstance(record['attribution_requirements'], list) or any(not text(v) for v in record['attribution_requirements']):
            raise ValueError('Explicit attribution requirements list required')
        digest(record['artifact_sha256'])
        verify_bytes(record['permission_path'], record['permission_sha256'])
    revocations = set()
    for record in ledger['revocations']:
        if not isinstance(record, dict) or set(record) != {'decision_id', 'revoked_at', 'revoked_by', 'reason'}:
            raise ValueError('Invalid revocation fields')
        if record['decision_id'] not in ids or record['decision_id'] in revocations:
            raise ValueError('Unknown or duplicate revoked decision')
        revocations.add(record['decision_id'])
        day(record['revoked_at'])
        if not text(record['revoked_by']) or not text(record['reason']):
            raise ValueError('Revocation actor and reason required')


def load():
    ledger = json.loads(LEDGER.read_text(encoding='utf-8'))
    validate(ledger)
    return ledger


def hold_reason(connection, source_id, source_url, observed_sha, ledger, as_of):
    today = day(as_of)
    if not observed_sha:
        return 'observation has no captured source checksum'
    sha = digest(observed_sha)
    artifacts = connection.execute('SELECT local_path,sha256,retrieval_state FROM source_artifacts WHERE source_id=? AND upper(sha256)=?', (source_id, sha)).fetchall()
    if not artifacts:
        return 'observation source revision is not a registered captured artifact'
    try:
        for artifact in artifacts:
            if artifact[2] != 'retrieved':
                return 'licensed source artifact is not retrieved'
            verify_bytes(artifact[0], artifact[1])
    except (ValueError, OSError) as error:
        return 'source artifact custody failed: ' + str(error)
    revoked = {r['decision_id'] for r in ledger['revocations'] if day(r['revoked_at']) <= today}
    matches = [r for r in ledger['decisions'] if r['decision'] == 'approved' and r['source_id'] == source_id
               and r['source_url'] == source_url and digest(r['artifact_sha256']) == sha
               and r['permitted_use'] == USE and r['decision_id'] not in revoked
               and day(r['reviewed_at']) <= today and day(r['valid_from']) <= today <= day(r['valid_until'])]
    if len(matches) != 1:
        return 'no single current independently reviewed source-revision authorization'
    # Attribution obligations must be executable and enforced before publication.
    # This version does not claim that recording an obligation fulfills it.
    if matches[0]['attribution_requirements']:
        return 'authorization attribution obligations are not yet implemented'
    return None
