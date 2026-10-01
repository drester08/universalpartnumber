"""Validate source-bound research relationships, never infer part identity."""
import argparse
import hashlib
import json
import re
from pathlib import Path, PurePosixPath
from urllib.parse import urlsplit

VERSION = 'standard-relationship-research-0.1'
KINDS = {'standard_reference', 'manufacturer_part', 'product_family'}
RELATIONS = {'declared_conformance', 'supplier_cross_reference',
             'successor_standard', 'application_interchangeability'}
ROOT = Path(__file__).resolve().parents[2]


def text(value, field):
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ValueError(field + ' requires explicit nonblank text')


def fields(value, expected, name):
    if not isinstance(value, dict) or set(value) != set(expected):
        raise ValueError('Invalid ' + name + ' fields')


def entity(value):
    fields(value, ('kind', 'namespace', 'identifier', 'edition'), 'entity')
    text(value['kind'], 'kind')
    if value['kind'] not in KINDS:
        raise ValueError('Unknown entity kind')
    for key in ('namespace', 'identifier'):
        text(value[key], key)
    if value['edition'] is not None:
        text(value['edition'], 'edition')
    if value['kind'] != 'standard_reference' and value['edition'] is not None:
        raise ValueError('Standard edition cannot describe a part or family')


def evidence(value, root):
    fields(value, ('source_url', 'artifact_path', 'sha256', 'locator'), 'evidence')
    for key in value:
        text(value[key], key)
    url = urlsplit(value['source_url'])
    if url.scheme not in ('https', 'http') or not url.hostname or url.username or url.password:
        raise ValueError('Evidence requires a public HTTP source URL without credentials')
    if not re.fullmatch(r'[0-9a-fA-F]{64}', value['sha256']):
        raise ValueError('Evidence requires an exact SHA-256')
    raw = value['artifact_path']
    path = PurePosixPath(raw)
    if ('\\' in raw or ':' in raw or path.is_absolute() or '..' in path.parts or
        path.parts[:2] != ('registry', 'artifacts') or len(path.parts) < 3):
        raise ValueError('Evidence must use a relative registry/artifacts path')
    base = (root / 'registry' / 'artifacts').resolve()
    artifact = (root / path).resolve()
    if not artifact.is_relative_to(base) or not artifact.is_file():
        raise ValueError('Evidence artifact missing or escapes custody directory')
    if hashlib.sha256(artifact.read_bytes()).hexdigest() != value['sha256'].lower():
        raise ValueError('Evidence source bytes changed')


def validate(capture, root=ROOT):
    fields(capture, ('policy_version', 'scope', 'assertions'), 'capture')
    if capture['policy_version'] != VERSION or capture['scope'] != 'research_only':
        raise ValueError('Unsupported relationship policy or scope')
    assertions = capture['assertions']
    if not isinstance(assertions, list) or not assertions:
        raise ValueError('Nonempty assertion list required')
    identifiers, results = set(), []
    for assertion in assertions:
        fields(assertion, ('assertion_id', 'subject', 'target', 'relation', 'context',
                           'qualifiers', 'evidence', 'review_state'), 'assertion')
        text(assertion['assertion_id'], 'assertion_id')
        if assertion['assertion_id'] in identifiers:
            raise ValueError('Duplicate assertion ID')
        identifiers.add(assertion['assertion_id'])
        entity(assertion['subject'])
        entity(assertion['target'])
        subject, target = assertion['subject'], assertion['target']
        relation = assertion['relation']
        text(relation, 'relation')
        if relation not in RELATIONS or assertion['review_state'] != 'unreviewed':
            raise ValueError('No identity relation or review approval is supported')
        if subject == target:
            raise ValueError('Self relationships do not establish a research crosswalk')
        if relation == 'declared_conformance':
            if subject['kind'] not in {'manufacturer_part', 'product_family'} or target['kind'] != 'standard_reference':
                raise ValueError('Conformance needs a part/family subject and a standard target')
        elif relation == 'successor_standard':
            if subject['kind'] != 'standard_reference' or target['kind'] != 'standard_reference':
                raise ValueError('Successor relation requires two standard references')
        elif subject['kind'] != target['kind']:
            raise ValueError('Cross-reference/interchangeability endpoints must have the same kind')
        text(assertion['context'], 'context')
        qualifiers = assertion['qualifiers']
        if not isinstance(qualifiers, list):
            raise ValueError('Qualifiers must be an explicit list')
        for qualifier in qualifiers:
            text(qualifier, 'qualifier')
        if len(qualifiers) != len(set(qualifiers)):
            raise ValueError('Duplicate qualifiers')
        evidence(assertion['evidence'], Path(root))
        results.append(dict(assertion_id=assertion['assertion_id'], relation=relation,
                            subject=dict(subject), target=dict(target),
                            context=assertion['context'], qualifiers=list(qualifiers),
                            unknown_standard_editions=[name for name, node in
                                (('subject', subject), ('target', target))
                                if node['kind'] == 'standard_reference' and node['edition'] is None],
                            source_bytes_match=True, review_state='unreviewed'))
    return dict(policy_version=VERSION, scope='research_only', assertions=results,
                semantic_claims_verified=False, source_truth_verified=False,
                reuse_permission=False, identity_approved=False,
                application_suitability_approved=False, production_upn_allowed=False,
                database_mutated=False, symmetric_or_transitive_links_inferred=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('capture', type=Path)
    args = parser.parse_args()
    print(json.dumps(validate(json.loads(args.capture.read_text(encoding='utf-8'))), indent=2))
