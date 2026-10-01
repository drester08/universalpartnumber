"""Verify manufacturer-family custody without inventing exact gasket articles."""
import argparse
import hashlib
import json
import sqlite3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SOURCE='SRC-KLINGER-MAXIPROFILE-SA'
ARTIFACT='ART-KLINGER-MAXIPROFILE-SA'
URL='https://www.klinger.co.za/wp-content/uploads/2024/08/KLINGER-Maxiprofile-1.pdf'
PDF_PATH='registry/artifacts/klinger/Maxiprofile-South-Africa-20261001.pdf'
PDF_SHA='0C632A50EFF0BA9BD3FBA663340B4BA0C52E1B1032BA1592078E025D452597D8'
RESEARCH_SHA='B6FD9F86173A4131B1C8FDF64B5A9EE2002DDA6C74D1B1D19CD03F479876F27D'
HISTORY_SHA='8B6CAA9D3B69FC81C544815D810B3828D0971E046361C4C6A352AF9B18688C9C'


def bytes_at(path, expected):
    data=path.read_bytes()
    if hashlib.sha256(data).hexdigest().upper()!=expected:
        raise ValueError('KLINGER immutable input revision changed: '+path.name)
    return data


def verify(db):
    research=json.loads(bytes_at(ROOT/'reports/klinger-maxiprofile-context.json',RESEARCH_SHA))
    bytes_at(ROOT/'reports/klinger-maxiprofile-comparison.json',HISTORY_SHA)
    bytes_at(ROOT.parent/PDF_PATH,PDF_SHA)
    if research['source_sha256']!=PDF_SHA or research['source_registered'] or research['identity_approved'] or research['historical_findings_resolved']:
        raise ValueError('KLINGER historical family scope changed')
    source=db.execute('SELECT publisher_name,title,source_url,source_type,authority_tier,access_state,license_state,license_url,version_label,publication_date,retrieved_at,ingestion_status FROM sources WHERE source_id=?',(SOURCE,)).fetchone()
    expected=('KLINGER South Africa','Maxiprofile construction context South Africa',URL,'catalog',1,'public','review_required',None,'Captured revision 2026-10-01',None,'2026-10-01','license_review')
    if source is None or tuple(source)!=expected:
        raise ValueError('KLINGER family source metadata or reuse gate changed')
    artifacts=db.execute('SELECT artifact_id,artifact_url,media_type,local_path,sha256,retrieved_at,retrieval_state FROM source_artifacts WHERE source_id=?',(SOURCE,)).fetchall()
    expected_artifact=(ARTIFACT,URL,'application/pdf',PDF_PATH,PDF_SHA,'2026-10-01','retrieved')
    if len(artifacts)!=1 or tuple(artifacts[0])!=expected_artifact:
        raise ValueError('KLINGER original artifact custody changed')
    if db.execute('SELECT count(*) FROM observations WHERE source_id=?',(SOURCE,)).fetchone()[0]:
        raise ValueError('Generic KLINGER context promoted to article observations')
    return dict(policy_version='klinger-maxiprofile-registration-0.1',registered_source=True,
                source_id=SOURCE,artifact_id=ARTIFACT,source_sha256=PDF_SHA,
                historical_research_sha256=RESEARCH_SHA,historical_comparison_sha256=HISTORY_SHA,
                source_role='manufacturer product-family context, not exact supplied article',
                publication_date=None,previously_reviewed_physical_pages=[1,2,3,4,5,6],
                component_material_rows=19,style_contexts=4,article_observations_added=0,
                identity_approved=False,historical_findings_resolved=False,reuse_permission=False,
                independent_review='outstanding',source_reuse_review='outstanding',
                maintenance_clarification='outstanding',
                required_article_evidence=research['required_article_evidence'])


def review_tasks(db):
    verify(db)
    common=dict(priority='P2',readiness='ready',subject_type='source_artifact',subject_id=ARTIFACT,
                source_id=SOURCE,policy_version='klinger-maxiprofile-registration-0.1')
    evidence=' Evidence: registry/reports/klinger-maxiprofile-registration.json; immutable research SHA-256 '+RESEARCH_SHA+'.'
    return [dict(common,work_item_id='RW-KLINGER-MAXIPROFILE-CONTEXT',queue_type='manufacturer_family_context_review',
                 summary='Independently review Maxiprofile component, style and application scope',
                 next_action='Review complete pages 1-6 and separate core/facing options, profile, ring, partitions and ratings scope. Seek exact article drawings; no supplied tuple roles, grade defaults or universal joint rating.'+evidence),
            dict(common,work_item_id='RW-KLINGER-MAXIPROFILE-MAINTENANCE',queue_type='manufacturer_family_publication_question',
                 summary='Clarify core refurbishment versus gasket non-reuse scope',
                 next_action='Obtain revision-bound publisher clarification for page 1 core refurbishment and pages 5-6 non-reuse instructions. Preserve both statements; no supplied gasket reuse permission.'+evidence)]


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write-snapshot',action='store_true')
    args=parser.parse_args()
    with sqlite3.connect(ROOT/'build/registry.sqlite') as db:
        report=verify(db)
    target=ROOT/'reports/klinger-maxiprofile-registration.json'
    if args.write_snapshot:
        target.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    elif json.loads(target.read_text(encoding='utf-8'))!=report:
        raise ValueError('KLINGER registration snapshot stale')
    print('KLINGER family capture registered; reuse, independent context review and maintenance clarification outstanding.')
