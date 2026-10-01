"""Bind the proposed 6204ZZ closure interpretation to immutable evidence."""
import argparse
import hashlib
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT_NAME = 'ntn-6204zz-catalogue-context.json'
REPORT_SHA = 'CCBC3E1C24DD59F4820D51130787222CE1E7B6A031D6E5A32A99439219931CD0'
ARTICLE_SHA = '3F2253DB6EEA5B032A410C39E2C939FBB786C7014CD0E4F8FE96E83A24F25003'
CATALOGUE_SHA = '7F1357233C6089610F0E5246EB427553487A14101EB38E15E0D32BB59B405924'
RATIONALE = 'NTN 3015-5/E physical pages 3 and 6; Table 1 ZZ metal non-contact construction plus exact 6204 ZZ row and double-shield footnotes. Evidence registry/reports/ntn-6204zz-catalogue-context.json SHA256 CCBC3E1C24DD59F4820D51130787222CE1E7B6A031D6E5A32A99439219931CD0. Independent review outstanding; not publisher correction.'
EXPECTED = dict(mapping_id='MAP-NTN-6204ZZ-CLOSURE', specification_id='SPEC-NTN-6204ZZ-CLOSURE',
    property_id='PROP-BEARING-CLOSURE', controlled_value_id='CV-BEARING-CLOSURE-DOUBLE-NONCONTACT-METAL',
    mapping_basis='manufacturer_definition',mapping_state='proposed',rationale=RATIONALE,
    proposed_by='registry-research',proposed_at='2026-10-01',reviewer='',reviewed_at='',policy_version='0.1')


def verify_mapping_row(row):
    if {key: '' if value is None else value for key,value in dict(row).items()} != EXPECTED:
        raise ValueError('6204 closure proposal scope/state/evidence binding changed')


def verify(connection):
    raw = (ROOT/'reports'/REPORT_NAME).read_bytes()
    if hashlib.sha256(raw).hexdigest().upper() != REPORT_SHA:
        raise ValueError('6204 closure evidence report revision changed')
    evidence = json.loads(raw)
    if (evidence['manufacturer_part_id'],evidence['article_source_id'],evidence['article_sha256'],
        evidence['source_id'],evidence['source_sha256'],evidence['definition_pdf_page'],evidence['dimension_pdf_page']) != (
        'MP-NTN-6204ZZ','SRC-NTN-6204ZZ',ARTICLE_SHA,'SRC-NTN-SHIELD-SEAL-3015',CATALOGUE_SHA,3,6):
        raise ValueError('6204 closure report namespace changed')
    connection.row_factory = sqlite3.Row
    mappings = connection.execute('SELECT * FROM specification_value_mappings WHERE mapping_id=?', (EXPECTED['mapping_id'],)).fetchall()
    if len(mappings) != 1:
        raise ValueError('6204 closure proposal missing or duplicated')
    verify_mapping_row(mappings[0])
    controlled=connection.execute('SELECT property_id,canonical_code FROM controlled_values WHERE controlled_value_id=?',(EXPECTED['controlled_value_id'],)).fetchone()
    if controlled is None or tuple(controlled)!=('PROP-BEARING-CLOSURE','double_non_contact_metal_shield'):
        raise ValueError('6204 closure controlled-value meaning changed')
    spec = connection.execute('SELECT s.raw_value,s.normalized_text,s.normalized_number,s.qualifier,o.manufacturer_part_id,o.source_id,o.raw_payload_sha256,o.review_state,p.manufacturer_id,p.manufacturer_part_number FROM specification_values s JOIN observations o USING(observation_id) JOIN manufacturer_parts p USING(manufacturer_part_id) WHERE s.specification_id=?', (EXPECTED['specification_id'],)).fetchone()
    if spec is None or tuple('' if value is None else value for value in spec) != ('Double Shielded','','','No full contact/material definition assigned','MP-NTN-6204ZZ','SRC-NTN-6204ZZ',ARTICLE_SHA,'unreviewed','ORG-NTN-AMERICAS','6204ZZ'):
        raise ValueError('6204 closure raw observation or namespace changed')
    for source_id, sha, artifact_id in [('SRC-NTN-6204ZZ',ARTICLE_SHA,'ART-NTN-6204ZZ'),('SRC-NTN-SHIELD-SEAL-3015',CATALOGUE_SHA,'ART-NTN-SHIELD-SEAL-3015')]:
        artifacts = connection.execute('SELECT artifact_id,sha256,retrieval_state FROM source_artifacts WHERE source_id=?',(source_id,)).fetchall()
        if len(artifacts)!=1 or tuple(artifacts[0])!=(artifact_id,sha,'retrieved'):
            raise ValueError('6204 closure source custody changed')
    for source_id,publisher,url in [('SRC-NTN-6204ZZ','NTN Bearing Corporation of America','https://bearingfinder.ntnamericas.com/item/deep-groove-ball-bearings/single-row-radial-ball-bearings/6204zz'),('SRC-NTN-SHIELD-SEAL-3015','NTN Corporation','https://www.ntnglobal.com/en/products/catalog/pdf/3015E.pdf')]:
        source=connection.execute('SELECT publisher_name,source_url FROM sources WHERE source_id=?',(source_id,)).fetchone()
        if source is None or tuple(source)!=(publisher,url):
            raise ValueError('6204 closure source publisher changed')
    return {'policy_version':'ntn-6204zz-closure-proposal-0.1','mapping':EXPECTED,
        'evidence_report_path':'registry/reports/'+REPORT_NAME,'evidence_report_sha256':REPORT_SHA,
        'article_sha256':ARTICLE_SHA,'catalogue_sha256':CATALOGUE_SHA,
        'canonical_code':'double_non_contact_metal_shield','identity_approved':False,
        'publisher_correction_obtained':False,'independent_review':'outstanding',
        'limitations':['Exact specification mapping only; not manufacturer-wide or suffix-wide defaults.',
            'Raw article wording and immutable intake/catalogue snapshots remain unchanged.',
            'Proposed terminology can support research screening, not identity issuance.',
            'Approval or observation revisions require deliberate evidence and policy reconciliation.']}


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write-snapshot',action='store_true')
    args=parser.parse_args()
    with sqlite3.connect(ROOT/'build/registry.sqlite') as db:
        report=verify(db)
    target=ROOT/'reports/ntn-6204zz-closure-proposal.json'
    if args.write_snapshot:
        target.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    elif json.loads(target.read_text(encoding='utf-8')) != report:
        raise ValueError('6204 closure proposal snapshot stale')
    print('NTN 6204ZZ closure proposal reproduced; independent review and identity approval outstanding.')
