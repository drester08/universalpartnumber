"""Compare private supplied piping dimensions with immutable staged MPS research.

No certificate, construction, mass, internal diameter or identity approval.
"""
import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from check_piping_tenaris import number, precision_compatible

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT/'artifacts/user-reference-csvs/Piping - Rev01 - 02 July 2026.csv'
DATASET_SHA = '674cb646412b8f1ef538f3c6cf4e473f1f832f0b9c65b0b45aebed04e4d7e875'
MPS = ROOT/'reports/mps-pipe-table-research.json'
MPS_SHA = '819584E30A42785723627C57635902C5369D45C717D114811F54219572AFC0FE'
OLD = ROOT/'reports/piping-tenaris-comparison.json'
OLD_SHA = '980ED9D4206EE77FD3997D55805381126B53A17897AE06A5B32C41737B568190'
PDF = ROOT/'artifacts/mining-pressure-systems/technical-manual-20261001.pdf'
PDF_SHA = 'FE5731D47330DAD79637F05CC44E969100B62651852E23F64DBAE147794DED4B'


def bound_bytes(path, expected):
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest().lower() != expected.lower():
        raise ValueError(f'Input revision changed: {path.name}')
    return data


def source_key(row):
    schedule = row['schedule_raw']
    if schedule in ('–','-'):
        if row['wall_designation_raw'] not in ('(XXS)','STD','XS'):
            raise ValueError('Unknown nonnumeric source schedule')
        schedule = row['wall_designation_raw'].strip('()')
    else:
        number(schedule)
    return row['nominal_bore'], schedule


def compare(source, supplied, prior):
    index = defaultdict(list)
    for row in source['records']:
        index[source_key(row)].append(row)
    previous = {r['csv_line']:r for r in prior['records']}
    if len(previous) != 50:
        raise ValueError('Prior comparison row coverage changed')
    id_questions = {(r['physical_page'],r['nominal_bore'],r['schedule_raw'])
                    for r in source['diagnostics']['internal_diameter_precision_conflicts']}
    mass_questions = {(group['nominal_bore'],r['schedule_raw'],r['wall_mm_raw'])
                      for group in source['diagnostics']['repeated_mass_different_wall'] for r in group['rows']}
    results, seen = [], set()
    for logical_row,row in enumerate(supplied,2):
        raw_schedule = row['Schedule Number'].strip()
        key = (row['Nominal Bore (mm)'].strip(), 'XXS' if raw_schedule == '(XXS)' else raw_schedule)
        if key in seen:
            raise ValueError('Duplicate supplied lookup key')
        seen.add(key)
        actual = {'od_mm':row['Outside Diameter (mm)'], 'wall_mm':row['Wall Thickness (mm)']}
        for value in actual.values():
            number(value)
        old = previous.get(logical_row)
        if old is None or list(key) != old['key'] or actual != old['actual']:
            raise ValueError('Prior comparison does not bind same supplied row')
        candidates = index.get(key,[])
        outcome = ('outside_source_key_scope' if not candidates else
                   'ambiguous_source_key' if len(candidates)>1 else
                   'printed_precision_compatible' if
                   precision_compatible(actual['od_mm'],candidates[0]['od_mm_raw']) and
                   precision_compatible(actual['wall_mm'],candidates[0]['wall_mm_raw']) else
                   'dimension_conflict')
        results.append(dict(csv_logical_row=logical_row,key=list(key),raw_schedule=raw_schedule,
                            actual=actual,outcome=outcome,
                            source_candidates=[{k:r[k] for k in ('physical_page','text_line','nominal_bore',
                                               'od_mm_raw','wall_mm_raw','wall_designation_raw','schedule_raw')} for r in candidates],
                            prior_tenaris_outcome=old['outcome'],
                            source_internal_diameter_question=any((r['physical_page'],r['nominal_bore'],r['schedule_raw']) in id_questions for r in candidates),
                            source_approximate_mass_question=any((r['nominal_bore'],r['schedule_raw'],r['wall_mm_raw']) in mass_questions for r in candidates),
                            construction_raw=row['Type'], specification_raw=row['MOC'],
                            construction_conflict=row['MOC']=='ASTM A106' and row['Type']=='Welded'))
    if len(results)!=50:
        raise ValueError('Expected exactly 50 supplied rows')
    return results


def build_report():
    source = json.loads(bound_bytes(MPS,MPS_SHA))
    prior = json.loads(bound_bytes(OLD,OLD_SHA))
    bound_bytes(PDF,PDF_SHA)
    raw = bound_bytes(DATASET,DATASET_SHA).decode('utf-8-sig')
    import io
    supplied = list(csv.DictReader(io.StringIO(raw,newline='')))
    if source['source_sha256']!=PDF_SHA or source['identity_approved'] or source['registered_new_source']:
        raise ValueError('Staged source scope changed')
    if prior['dataset_sha256']!=DATASET_SHA:
        raise ValueError('Prior dataset revision changed')
    records = compare(source,supplied,prior)
    return dict(policy_version='piping-mps-nominal-comparison-0.1',
                dataset_id='DATASET-USER-PIPING-20260702',dataset_sha256=DATASET_SHA,
                source_url=source['source_url'],source_pdf_sha256=PDF_SHA,
                source_research_sha256=MPS_SHA,prior_tenaris_report_sha256=OLD_SHA,
                dataset_rows=50,outcomes=dict(Counter(r['outcome'] for r in records)),
                prior_to_current_counts=dict(Counter(r['prior_tenaris_outcome']+' -> '+r['outcome'] for r in records)),
                construction_conflicts=sum(r['construction_conflict'] for r in records),
                rows_with_source_id_question=sum(r['source_internal_diameter_question'] for r in records),
                rows_with_source_mass_question=sum(r['source_approximate_mass_question'] for r in records),
                identity_approved=False,source_registered=False,dataset_corrected=False,
                prior_findings_resolved=False,records=records,
                interpretation='Nominal OD/wall printed-precision compatibility only. No manufacturing tolerance, actual-stock certificate, grade, construction, internal diameter, mass or interchangeability approval. Supplier/fabricator table does not identify the supplied mill. Earlier source-specific findings remain open. XXS is a wall designation, never inferred as schedule 160.',
                outstanding=['Independent extraction and source reuse review','Register scoped supplier evidence',
                             'Obtain actual-stock manufacturer/certificate and resolve A106 welded contradiction',
                             'Obtain publisher clarification for internal diameter and approximate mass questions'])


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write-snapshot',action='store_true')
    args=parser.parse_args()
    report=build_report()
    target=ROOT/'reports/piping-mps-comparison.json'
    if args.write_snapshot:
        target.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    elif json.loads(target.read_text(encoding='utf-8'))!=report:
        raise ValueError('MPS comparison snapshot stale')
    print(json.dumps({k:v for k,v in report.items() if k not in ('records','interpretation','outstanding')},indent=2))
