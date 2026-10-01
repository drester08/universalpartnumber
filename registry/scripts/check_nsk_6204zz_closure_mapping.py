"""Current scoped NSK closure proposal, not cross-brand equivalence approval."""
import argparse
import hashlib
import json
import sqlite3
from pathlib import Path
import check_nsk_6204zz_metal_research as research
import check_nsk_6204zz_code_registration as prior

ROOT = Path(__file__).resolve().parents[1]
REPORT_SHA = '4152E16FFEA4A47C6F24DF608D1C8764026BDBD14C3641E0FD8285C07854A058'
SOURCE = 'SRC-NSK-DGBB-EU-0115'
OBS = 'OBS-NSK-6204ZZ-EU-20261001'
RATIONALE = 'NSK DGB/H/E/01.15 physical pages 7 and 9 define ZZ non-contact shielding and double metal shields in 62-series scope. Exact article and catalogue bound through registry/reports/nsk-6204zz-metal-research.json SHA256 4152E16FFEA4A47C6F24DF608D1C8764026BDBD14C3641E0FD8285C07854A058. Historical applicability and independent review outstanding; no special design defaults.'
EXPECTED = dict(mapping_id='MAP-NSK-6204ZZ-CLOSURE', specification_id='SPEC-NSK-6204ZZ-CLOSURE',
                property_id='PROP-BEARING-CLOSURE', controlled_value_id='CV-BEARING-CLOSURE-DOUBLE-NONCONTACT-METAL',
                mapping_basis='manufacturer_definition', mapping_state='proposed', rationale=RATIONALE,
                proposed_by='registry-research', proposed_at='2026-10-01', reviewer='', reviewed_at='', policy_version='0.1')


def verify_mapping_row(row):
    if {k: '' if v is None else v for k,v in dict(row).items()} != EXPECTED:
        raise ValueError('NSK closure proposal scope/state/evidence changed')


def verify(db):
    raw = (ROOT/'reports/nsk-6204zz-metal-research.json').read_bytes()
    if hashlib.sha256(raw).hexdigest().upper() != REPORT_SHA:
        raise ValueError('NSK metal evidence report revision changed')
    evidence = json.loads(raw)
    if evidence['manufacturer_part_id'] != 'MP-NSK-6204ZZ' or evidence['source_sha256'] != research.SHA or evidence['closure_hypothesis']['canonical_code'] != 'double_non_contact_metal_shield':
        raise ValueError('NSK closure evidence namespace changed')
    prior.verify(db)
    db.row_factory = sqlite3.Row
    mapping = db.execute('SELECT * FROM specification_value_mappings WHERE mapping_id=?', (EXPECTED['mapping_id'],)).fetchone()
    if mapping is None:
        raise ValueError('NSK closure proposal absent')
    verify_mapping_row(mapping)
    controlled = db.execute('SELECT property_id,canonical_code FROM controlled_values WHERE controlled_value_id=?', (EXPECTED['controlled_value_id'],)).fetchone()
    if controlled is None or tuple(controlled) != ('PROP-BEARING-CLOSURE','double_non_contact_metal_shield'):
        raise ValueError('NSK closure controlled meaning changed')
    source = db.execute('SELECT publisher_name,source_url,authority_tier,license_state,ingestion_status,version_label FROM sources WHERE source_id=?', (SOURCE,)).fetchone()
    if source is None or tuple(source) != ('NSK Europe', research.URL, 1, 'review_required', 'license_review', 'DGB/H/E/01.15 copyright 2009'):
        raise ValueError('NSK historical source scope/reuse changed')
    artifacts = db.execute('SELECT artifact_id,artifact_url,local_path,sha256,media_type,retrieval_state FROM source_artifacts WHERE source_id=?', (SOURCE,)).fetchall()
    if len(artifacts) != 1 or tuple(artifacts[0]) != ('ART-NSK-DGBB-EU-0115',research.URL,'registry/artifacts/nsk/EN-DGBB-Europe-20261001.pdf',research.SHA,'application/pdf','retrieved'):
        raise ValueError('NSK metal source custody changed')
    if hashlib.sha256(research.PATH.read_bytes()).hexdigest().upper() != research.SHA:
        raise ValueError('NSK metal original bytes changed')
    obs = db.execute('SELECT manufacturer_part_id,source_id,raw_payload_sha256,review_state,observed_part_number FROM observations WHERE observation_id=?', (OBS,)).fetchone()
    if obs is None or tuple(obs) != ('MP-NSK-6204ZZ',SOURCE,research.SHA,'unreviewed','6204ZZ'):
        raise ValueError('NSK metal observation scope/review changed')
    spec = db.execute('SELECT s.property_id,s.raw_value,s.normalized_text,s.normalized_number,o.manufacturer_part_id,o.source_id,o.raw_payload_sha256,o.review_state FROM specification_values s JOIN observations o USING(observation_id) WHERE s.specification_id=?', (EXPECTED['specification_id'],)).fetchone()
    if spec is None or tuple(spec) != ('PROP-BEARING-CLOSURE','ZZ: Shield on both sides',None,None,'MP-NSK-6204ZZ','SRC-NSK-6204ZZ','6AA72C0BD671B2E0A21269F5F303D5CCB48DF0D6662419D678E57D70CAD04EA9','unreviewed'):
        raise ValueError('NSK raw article closure or scope changed')
    import check_nsk_6204zz as article
    article_artifacts = db.execute('SELECT artifact_url,sha256,retrieval_state FROM source_artifacts WHERE source_id=?', ('SRC-NSK-6204ZZ',)).fetchall()
    if len(article_artifacts) != 1 or tuple(article_artifacts[0]) != (article.URL,article.SHA,'retrieved') or hashlib.sha256(article.PATH.read_bytes()).hexdigest().upper() != article.SHA:
        raise ValueError('NSK exact article custody changed')
    if db.execute('SELECT count(*) FROM specification_values WHERE observation_id=?',(OBS,)).fetchone()[0]:
        raise ValueError('NSK general construction promoted into article defaults')
    return dict(policy_version='nsk-6204zz-closure-proposal-0.1', mapping=EXPECTED,
                source_id=SOURCE, observation_id=OBS, source_sha256=research.SHA,
                evidence_report_path='registry/reports/nsk-6204zz-metal-research.json',
                evidence_report_sha256=REPORT_SHA, registered_new_source=True,
                canonical_code='double_non_contact_metal_shield', identity_approved=False,
                independent_review='outstanding', historical_applicability_review='outstanding',
                limitations=['Exact specification only; no maker-wide or suffix-wide inheritance.',
                             'Proposed terminology supports research screening, not equivalence or UPN issuance.',
                             'Historical source reuse and current applicability remain under review.',
                             'No exact metal grade, bearing material, lubricant or locating default assigned.',
                             'Raw article facts and historical evidence reports remain unchanged.'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write-snapshot', action='store_true')
    args = parser.parse_args()
    with sqlite3.connect(ROOT/'build/registry.sqlite') as db:
        report = verify(db)
    target = ROOT/'reports/nsk-6204zz-closure-proposal.json'
    if args.write_snapshot:
        target.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    elif json.loads(target.read_text(encoding='utf-8')) != report:
        raise ValueError('NSK closure proposal snapshot stale')
    print('Exact NSK closure proposal reproduced; current applicability and independent review outstanding.')
