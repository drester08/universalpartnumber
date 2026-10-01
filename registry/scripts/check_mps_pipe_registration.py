"""Bind registered supplier custody and review tasks to immutable pipe research."""
import argparse
import json
import sqlite3
from check_piping_mps import ROOT, MPS, MPS_SHA, PDF_SHA, build_report, bound_bytes

SOURCE='SRC-MPS-TECHNICAL-MANUAL'
ARTIFACT='ART-MPS-TECHNICAL-MANUAL'
COMPARISON_SHA='30330BF06214E19A696982BC22E5D9E2F820490F7CE5114430C7E649BF489A79'
URL='https://www.miningpressure.co.za/uploads/1/2/4/2/124291661/mps_technical_manual_full.pdf'


def verify(db):
    historical=json.loads(bound_bytes(MPS,MPS_SHA))
    comparison=json.loads(bound_bytes(ROOT/'reports/piping-mps-comparison.json',COMPARISON_SHA))
    if build_report()!=comparison:
        raise ValueError('MPS nominal comparison no longer reproduces')
    row=db.execute('SELECT publisher_name,title,source_url,source_type,authority_tier,access_state,license_state,license_url,version_label,publication_date,retrieved_at,ingestion_status FROM sources WHERE source_id=?',(SOURCE,)).fetchone()
    expected=('Mining Pressure Systems','Technical manual supplier pipe context',URL,'catalog',2,'public','review_required',None,'Captured revision 2026-10-01',None,'2026-10-01','license_review')
    if row is None or tuple(row)!=expected:
        raise ValueError('MPS supplier authority, unknown date or reuse gate changed')
    artifacts=db.execute('SELECT artifact_id,artifact_url,media_type,local_path,sha256,retrieved_at,retrieval_state FROM source_artifacts WHERE source_id=?',(SOURCE,)).fetchall()
    expected_artifact=(ARTIFACT,URL,'application/pdf','registry/artifacts/mining-pressure-systems/technical-manual-20261001.pdf',PDF_SHA,'2026-10-01','retrieved')
    if len(artifacts)!=1 or tuple(artifacts[0])!=expected_artifact:
        raise ValueError('MPS original artifact custody changed')
    if db.execute('SELECT count(*) FROM observations WHERE source_id=?',(SOURCE,)).fetchone()[0]:
        raise ValueError('Generic MPS context promoted to article observation')
    questions=[]
    for question in historical['diagnostics']['internal_diameter_precision_conflicts']:
        questions.append(dict(question_id='ID-'+question['nominal_bore']+'-'+question['schedule_raw'],
                              kind='internal_diameter_publication_question',physical_page=question['physical_page'],
                              nominal_bore=question['nominal_bore'],schedule_raw=question['schedule_raw'],
                              summary='Clarify printed internal diameter for DN '+question['nominal_bore']+' schedule '+question['schedule_raw']))
    for question in historical['diagnostics']['repeated_mass_different_wall']:
        questions.append(dict(question_id='MASS-'+question['nominal_bore'],kind='approximate_mass_publication_question',
                              physical_page=12,nominal_bore=question['nominal_bore'],schedule_raw='40/80',
                              summary='Clarify repeated approximate mass for DN '+question['nominal_bore']+' schedules 40/80'))
    return dict(policy_version='mps-pipe-registration-0.1',source_id=SOURCE,artifact_id=ARTIFACT,
                registered_source=True,source_role='supplier/fabricator, not identified stock mill',
                source_sha256=PDF_SHA,historical_research_sha256=MPS_SHA,
                nominal_comparison_sha256=COMPARISON_SHA,reviewed_physical_pages=[12,13,14],
                research_rows=144,nominal_comparison_rows=50,questions=questions,
                article_observations_added=0,identity_approved=False,source_correction_obtained=False,
                historical_snapshots_unchanged=True,independent_review='outstanding',source_reuse_review='outstanding')


def review_tasks(db):
    report=verify(db)
    common=dict(priority='P2',readiness='ready',subject_type='source_artifact',subject_id=ARTIFACT,source_id=SOURCE,
                policy_version=report['policy_version'])
    evidence=' Evidence: registry/reports/mps-pipe-registration.json; immutable research SHA-256 '+MPS_SHA+'.'
    tasks=[dict(common,work_item_id='RW-MPS-EXTRACTION',queue_type='supplier_context_review',
                summary='Independently review 144 MPS pipe-table rows and the 50-row nominal comparison',
                next_action='Review complete pages 12-14, group inheritance, schedule/designation scope and all source questions. Do not approve supplied stock, ID, mass or A106 welded construction.'+evidence)]
    for question in report['questions']:
        tasks.append(dict(common,work_item_id='RW-MPS-'+question['question_id'],queue_type='supplier_publication_question',
                          summary=question['summary'],next_action='Obtain publisher clarification for page '+str(question['physical_page'])+'. Preserve original values and bind new evidence to this revision; local arithmetic is not a publisher correction.'+evidence))
    return tasks


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write-snapshot',action='store_true')
    args=parser.parse_args()
    with sqlite3.connect(ROOT/'build/registry.sqlite') as db:
        report=verify(db)
    target=ROOT/'reports/mps-pipe-registration.json'
    if args.write_snapshot:
        target.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    elif json.loads(target.read_text(encoding='utf-8'))!=report:
        raise ValueError('MPS registration snapshot stale')
    print('MPS supplier capture registered; four publication questions and independent/reuse reviews open.')
