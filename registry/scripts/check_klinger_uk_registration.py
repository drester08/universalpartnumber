"""Register UK family custody without promoting claims to exact articles."""
import argparse
import hashlib
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = 'SRC-KLINGER-MAXIPROFILE-UK'
ARTIFACT = 'ART-KLINGER-MAXIPROFILE-UK'
URL = 'https://www.klinger.co.uk/wp-content/uploads/2025/01/maxiprofile.pdf'
PDF_PATH = 'registry/artifacts/klinger/Maxiprofile-UK-issue01-20190828-captured20261001.pdf'
PDF_SHA = 'D769825A67D89D12E3F3C929D506D31E15F51C175F38B440FA6B1F546A6418E5'
RESEARCH_SHA = '14E813FEDC62FF06611C2A2C206CCF929BF43669CA1797FDD9E5A40947E4F860'


def verify(db):
    import check_klinger_uk_maxiprofile as research_module
    data = (ROOT/'reports/klinger-uk-maxiprofile.json').read_bytes()
    if hashlib.sha256(data).hexdigest().upper() != RESEARCH_SHA:
        raise ValueError('UK immutable research revision changed')
    research = json.loads(data)
    if research_module.build_report() != research:
        raise ValueError('UK research reproduction changed')
    if any(research[k] for k in ('source_registered', 'identity_approved',
                                'application_suitability_approved', 'production_upn_allowed',
                                'dimensional_tuple_roles_resolved')):
        raise ValueError('UK historical research scope changed')
    source = db.execute('SELECT publisher_name,title,source_url,source_type,authority_tier,access_state,license_state,license_url,version_label,publication_date,retrieved_at,ingestion_status FROM sources WHERE source_id=?', (SOURCE,)).fetchone()
    expected = ('KLINGER United Kingdom', 'Maxiprofile UK issue 01 family specification', URL,
                'datasheet', 1, 'public', 'review_required', None, 'Issue 01',
                '2019-08-28', '2026-10-01', 'license_review')
    if source is None or tuple(source) != expected:
        raise ValueError('UK family source metadata or reuse gate changed')
    artifacts = db.execute('SELECT artifact_id,artifact_url,media_type,local_path,sha256,retrieved_at,retrieval_state FROM source_artifacts WHERE source_id=?', (SOURCE,)).fetchall()
    expected_artifact = (ARTIFACT, URL, 'application/pdf', PDF_PATH, PDF_SHA, '2026-10-01', 'retrieved')
    if len(artifacts) != 1 or tuple(artifacts[0]) != expected_artifact:
        raise ValueError('UK original artifact custody changed')
    if db.execute('SELECT count(*) FROM observations WHERE source_id=?', (SOURCE,)).fetchone()[0]:
        raise ValueError('Generic UK context promoted to article observations')
    return dict(policy_version='klinger-uk-registration-0.1', source_id=SOURCE,
                artifact_id=ARTIFACT, registered_source=True, source_sha256=PDF_SHA,
                historical_research_sha256=RESEARCH_SHA, printed_issue='01', publication_date='2019-08-28',
                source_role='manufacturer family context, not exact article or certificate',
                previously_reviewed_physical_pages=[1, 2, 3], component_material_rows=25,
                research_label_comparisons=14, temperature_disagreements=7,
                article_observations_added=0, independent_review='outstanding',
                temperature_clarification='outstanding', source_reuse_review='outstanding',
                identity_approved=False, application_suitability_approved=False,
                reuse_permission=False, production_upn_allowed=False,
                dimensional_tuple_roles_resolved=False)


def review_tasks(db):
    verify(db)
    common = dict(priority='P2', readiness='ready', subject_type='source_artifact',
                  subject_id=ARTIFACT, source_id=SOURCE, policy_version='klinger-uk-registration-0.1')
    evidence = ' Immutable evidence: registry/reports/klinger-uk-maxiprofile.json SHA-256 ' + RESEARCH_SHA + '.'
    return [dict(common, work_item_id='RW-KLINGER-UK-CONTEXT', queue_type='manufacturer_family_context_review',
                 summary='Independently review UK component and style scope',
                 next_action='Review complete pages 1-3, all 25 component rows, printed issue date and LA3 floating-ring text. Do not infer supplied style, fixed LA1 attachment, tuple roles, certificate truth or universal ratings.' + evidence),
            dict(common, work_item_id='RW-KLINGER-UK-TEMPERATURE', queue_type='manufacturer_family_publication_question',
                 summary='Clarify seven UK versus South Africa temperature-context differences',
                 next_action='Obtain revision-bound publisher clarification for 316L, 347, 321, Monel 400, Nickel 200, Inconel 600 and Inconel 625. Preserve both documents and raw values; label correspondences are not approved material mappings or article suitability.' + evidence)]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write-snapshot', action='store_true')
    args = parser.parse_args()
    with sqlite3.connect(ROOT/'build/registry.sqlite') as db:
        report = verify(db)
    target = ROOT/'reports/klinger-uk-registration.json'
    if args.write_snapshot:
        target.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    elif json.loads(target.read_text(encoding='utf-8')) != report:
        raise ValueError('UK registration snapshot stale')
    print('UK family custody registered; independent interpretation, temperature clarification and reuse review outstanding.')
