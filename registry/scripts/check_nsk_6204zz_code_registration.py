"""Verify current NSK context custody without rewriting historical research."""
import argparse
import hashlib
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESEARCH_SHA = 'C5B91BA8DCE8A5553FC4465B76BD9C51D136DAD32145B94A47F522270B92F6C9'
BINDINGS = [
    ('SRC-NSK-APB-DGBB', 'ART-NSK-APB-DGBB', 'OBS-NSK-6204ZZ-APB-20261001', 'NSK Americas'),
    ('SRC-NSK-E1103C-PARTC', 'ART-NSK-E1103C-PARTC', 'OBS-NSK-6204ZZ-E1103C-20261001', 'NSK Ltd.'),
]


def verify(connection):
    raw = (ROOT/'reports/nsk-6204zz-code-research.json').read_bytes()
    if hashlib.sha256(raw).hexdigest().upper() != RESEARCH_SHA:
        raise ValueError('NSK historical research revision changed')
    evidence = json.loads(raw)
    if evidence['manufacturer_part_id'] != 'MP-NSK-6204ZZ' or evidence['registered_new_sources'] is not False:
        raise ValueError('NSK historical research scope changed')
    part = connection.execute('SELECT manufacturer_id,manufacturer_part_number FROM manufacturer_parts WHERE manufacturer_part_id=?', ('MP-NSK-6204ZZ',)).fetchone()
    if part is None or tuple(part) != ('ORG-NSK', '6204ZZ'):
        raise ValueError('NSK article namespace changed')
    records = []
    for (source_id, artifact_id, observation_id, publisher), source in zip(BINDINGS, evidence['sources'], strict=True):
        registered = connection.execute('SELECT publisher_name,source_url,authority_tier,access_state,license_state,ingestion_status FROM sources WHERE source_id=?', (source_id,)).fetchone()
        if registered is None or tuple(registered) != (publisher, source['url'], 1, 'public', 'review_required', 'license_review'):
            raise ValueError('NSK source scope or reuse gate changed')
        artifacts = connection.execute('SELECT artifact_id,artifact_url,media_type,local_path,sha256,retrieved_at,retrieval_state FROM source_artifacts WHERE source_id=?', (source_id,)).fetchall()
        expected = (artifact_id, source['url'], 'application/pdf', source['local_path'], source['sha256'], '2026-10-01', 'retrieved')
        if len(artifacts) != 1 or tuple(artifacts[0]) != expected:
            raise ValueError('NSK context artifact custody changed')
        path = ROOT.parent/source['local_path']
        if hashlib.sha256(path.read_bytes()).hexdigest().upper() != source['sha256']:
            raise ValueError('NSK context original bytes changed')
        observation = connection.execute('SELECT manufacturer_part_id,item_id,source_id,observed_part_number,observed_at,raw_payload_sha256,review_state,source_locator FROM observations WHERE observation_id=?', (observation_id,)).fetchone()
        if observation is None or tuple(observation)[:7] != ('MP-NSK-6204ZZ', None, source_id, '6204ZZ', '2026-10-01', source['sha256'], 'unreviewed'):
            raise ValueError('NSK context observation scope or review state changed')
        if 'registry/reports/nsk-6204zz-code-research.json' not in observation[7] or 'registry/reports/nsk-6204zz-code-registration.json' not in observation[7]:
            raise ValueError('NSK context evidence locator changed')
        if connection.execute('SELECT count(*) FROM specification_values WHERE observation_id=?', (observation_id,)).fetchone()[0]:
            raise ValueError('NSK context promoted into article specifications')
        records.append(dict(source_id=source_id, artifact_id=artifact_id, observation_id=observation_id,
                            sha256=source['sha256'], reviewed_physical_pages=source['reviewed_physical_pages']))
    return dict(policy_version='nsk-6204zz-code-registration-0.1', registered_new_sources=True,
                manufacturer_part_id='MP-NSK-6204ZZ', records=records,
                historical_research_path='registry/reports/nsk-6204zz-code-research.json',
                historical_research_sha256=RESEARCH_SHA, canonical_mapping_added=False,
                identity_approved=False, source_reuse_review='outstanding', independent_review='outstanding',
                limitations=['Custody binding is not independent extraction or applicability approval.',
                             'Historical staged report is preserved; this report describes current registration.',
                             'Shield material, supplied lubricant and exact locating construction remain unresolved.',
                             'No new article specifications, equivalence decisions or UPN allocations.'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write-snapshot', action='store_true')
    args = parser.parse_args()
    with sqlite3.connect(ROOT/'build/registry.sqlite') as db:
        report = verify(db)
    target = ROOT/'reports/nsk-6204zz-code-registration.json'
    if args.write_snapshot:
        target.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    elif json.loads(target.read_text(encoding='utf-8')) != report:
        raise ValueError('NSK code registration snapshot stale')
    print('Two NSK context captures registered; reuse and independent review outstanding.')
