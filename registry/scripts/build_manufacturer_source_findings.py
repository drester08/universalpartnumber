"""Expose retained manufacturer publication issues as persistent research work."""
import argparse
import hashlib
import json
import sqlite3
from pathlib import Path
import manufacturer_source_resolutions

ROOT = Path(__file__).resolve().parents[1]
INPUTS = {
    'ntn-6204zz-source.json': 'AA2461CE23CAF12EE57C63A7860664241C167E0F145DB2AAC8AC1CE72A62EC67',
    'ntn-6205zz-source.json': 'F3988876EBD7F33E071AEC3FE8A4665242A21F035C1DF8D57BA7D2C645AE8F6D',
    'ntn-shield-seal-corroboration.json': '1A50EE384B5B12F3D1098DD0390F2F0953C8D9F932AAF6F06BDF3E78904CA948',
}


def load_report(name):
    raw = (ROOT / 'reports' / name).read_bytes()
    if hashlib.sha256(raw).hexdigest().upper() != INPUTS[name]:
        raise ValueError('Manufacturer finding input revision changed: ' + name)
    return json.loads(raw)


def finding_id(subject):
    raw = json.dumps(subject, sort_keys=True, separators=(',', ':'))
    return 'MRF-' + hashlib.sha256(raw.encode()).hexdigest()[:24].upper()


def derive(connection, article, corroboration, part_number='6205ZZ'):
    if part_number not in ('6204ZZ', '6205ZZ'):
        raise ValueError('Unsupported manufacturer article scope')
    connection.row_factory = sqlite3.Row
    part_id = 'MP-NTN-' + part_number
    part = connection.execute('SELECT * FROM manufacturer_parts WHERE manufacturer_part_id=?', (part_id,)).fetchone()
    if part is None or part['manufacturer_id'] != 'ORG-NTN-AMERICAS' or part['manufacturer_part_number'] != part_number:
        raise ValueError('Manufacturer finding namespace missing or changed')
    if article['source_id'] != 'SRC-NTN-' + part_number or article['manufacturer_article'] != part_number or article['manufacturer_namespace'] != 'NTN' or article['identity_approved'] is not False:
        raise ValueError('Manufacturer article report scope changed')
    if part_number == '6205ZZ' and (corroboration['source_id'] != 'SRC-NTN-SHIELD-SEAL-3015' or corroboration['article_source_id'] != article['source_id'] or corroboration['article_sha256'] != article['source_sha256'] or corroboration['publisher_correction_obtained'] is not False or corroboration['identity_approved'] is not False):
        raise ValueError('Corroboration was detached or promoted to publisher correction')
    if part_number == '6204ZZ' and corroboration is not None:
        raise ValueError('6205ZZ corroboration cannot be inherited by 6204ZZ')
    evidence = []
    inputs = [('ntn-' + part_number.lower() + '-source.json', article)]
    if corroboration is not None:
        inputs.append(('ntn-shield-seal-corroboration.json', corroboration))
    for name, report in inputs:
        source = connection.execute('SELECT source_url FROM sources WHERE source_id=?', (report['source_id'],)).fetchone()
        artifacts = connection.execute('SELECT artifact_id, local_path, sha256 FROM source_artifacts WHERE source_id=? AND sha256=? AND retrieval_state=?', (report['source_id'], report['source_sha256'], 'retrieved')).fetchall()
        if source is None or len(artifacts) != 1:
            raise ValueError('Manufacturer finding source/artifact custody changed')
        evidence.append({'source_id': report['source_id'], 'source_url': source[0],
            'artifact_id': artifacts[0]['artifact_id'], 'artifact_sha256': artifacts[0]['sha256'],
            'report_path': 'registry/reports/' + name, 'report_sha256': INPUTS[name]})
    observation = connection.execute('SELECT * FROM observations WHERE observation_id=?', ('OBS-NTN-' + part_number + '-20261001',)).fetchone()
    if observation is None or observation['manufacturer_part_id'] != part_id or observation['source_id'] != article['source_id'] or observation['raw_payload_sha256'] != article['source_sha256'] or observation['review_state'] in ('rejected', 'superseded'):
        raise ValueError('Manufacturer finding observation custody changed; reconcile explicitly')
    issues = {
        'inconsistent_static_load_metric_units': ('Static Load Rating', 'PROP-BASIC-STATIC-LOAD-RATING',
            'The exact NTN article publishes contradictory metric static-load cells; catalogue corroboration is not a publisher correction.',
            'Obtain a corrected exact-article publication or explicit manufacturer clarification. Preserve 7850 N and 11.60 kN, rating basis and source revisions. Do not choose a rating or approve physical identity from corroboration alone.'),
        'ambiguous_da_max_values': ('da max', '',
            'The exact NTN article places multiple values under da max; the catalogue distinguishes lowercase da from uppercase Da.',
            'Obtain a corrected exact-article drawing/table or explicit manufacturer clarification of both case-sensitive symbols and dimensions. Preserve all four article cells and the separate catalogue columns. Do not silently repair the article or infer variant identity.'),
    }
    if part_number == '6204ZZ':
        issues['inconsistent_static_load_metric_units'] = ('Static Load Rating', 'PROP-BASIC-STATIC-LOAD-RATING',
            'The exact NTN 6204ZZ article publishes contradictory metric static-load cells.',
            'Obtain a corrected exact-article publication or explicit manufacturer clarification. Preserve 6650 N and 9.75 kN and source revisions. Do not select a rating or inherit another article rating.')
        issues['ambiguous_da_max_values'] = ('da max', '',
            'The exact NTN 6204ZZ article places multiple values under da max.',
            'Obtain a corrected exact-article drawing/table or explicit manufacturer clarification. Preserve all four da max cells and the separate case-sensitive Da max row. Do not inherit 6205ZZ catalogue clarification.')
    if len(article['quality_findings']) != 2 or {q['issue_type'] for q in article['quality_findings']} != set(issues):
        raise ValueError('Manufacturer finding issue scope changed')
    findings = []
    for index, issue in enumerate(article['quality_findings']):
        field, property_id, summary, action = issues[issue['issue_type']]
        if issue['corrected_value'] is not None or not issue['retained_displays'] or not isinstance(issue['source_html_line'], int) or issue['source_html_line'] <= 0:
            raise ValueError('Manufacturer issue was corrected or detached from source locators')
        if issue.get('rating_trusted', False):
            raise ValueError('Contradictory rating promoted to trusted')
        subject = {'manufacturer_id': part['manufacturer_id'], 'manufacturer_part_id': part_id,
                   'source_id': article['source_id'], 'source_field': field, 'issue_type': issue['issue_type']}
        findings.append({'finding_id': finding_id(subject), 'subject_key': subject,
            'priority': 'P2', 'review_state': 'open_research', 'property_id': property_id,
            'profile_id': part['profile_id'], 'observation_id': observation['observation_id'],
            'source_html_line': issue['source_html_line'], 'retained_displays': issue['retained_displays'],
            'evidence_pointer': '/quality_findings/' + str(index), 'evidence': evidence,
            'summary': summary, 'next_action': action, 'policy_version': 'manufacturer-source-research-0.1',
            'publisher_correction_obtained': False, 'physical_conflict_verified': False, 'identity_approved': False})
    ids = [f['finding_id'] for f in findings]
    if len(ids) != len(set(ids)):
        raise ValueError('Duplicate manufacturer source finding')
    return sorted(findings, key=lambda f: f['finding_id'])


def build_report(connection):
    findings = derive(connection, load_report('ntn-6205zz-source.json'), load_report('ntn-shield-seal-corroboration.json'))
    findings += derive(connection, load_report('ntn-6204zz-source.json'), None, '6204ZZ')
    findings.sort(key=lambda finding: finding['finding_id'])
    resolutions = manufacturer_source_resolutions.replay(connection, findings)
    for finding in findings:
        finding['resolution'] = resolutions[finding['finding_id']]
    return {'policy_version': 'manufacturer-source-research-0.1', 'input_report_hashes': INPUTS,
        'finding_count': len(findings), 'findings': findings, 'identity_approved': False,
        'resolution_policy_version': manufacturer_source_resolutions.POLICY,
        'resolution_event_count': sum(len(state['history']) for state in resolutions.values()),
        'limitations': ['Research-ready tasks, not identity-ready evidence or physical incompatibility decisions.',
            'Manufacturer links, observation acceptance and terminology mappings do not correct source publications.',
            'Report or observation revision requires deliberate reconciliation; issues are never silently dropped.',
            'This adapter binds retained reports and registry custody, not independent extraction approval.',
            'Resolution history is research governance only; no source cell, specification, identity review or UPN is changed.',
            'Reviewer identities and scope attestations require external independent review; event hashes are not signatures.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write-snapshot', action='store_true')
    args = parser.parse_args()
    with sqlite3.connect(ROOT / 'build/registry.sqlite') as connection:
        report = build_report(connection)
    target = ROOT / 'reports/manufacturer-source-findings.json'
    if args.write_snapshot:
        target.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    elif json.loads(target.read_text(encoding='utf-8')) != report:
        raise ValueError('Manufacturer finding snapshot stale or altered')
    print('Manufacturer publication findings and resolution history reproduced; no automatic correction or identity approval.')
