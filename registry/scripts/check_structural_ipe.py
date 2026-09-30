"""Compare supplied IPE/IPE-AA rows with unreviewed manufacturer transcriptions.

Designation labels are lookup candidates, not measured depth or identity approvals.
"""
import argparse
import csv
import hashlib
import json
from collections import Counter
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATASET_SHA = '65b5f1c34fe0ab178281e7682a2a70c01b6dcdcd5fd0f83b6d7b94c19bfe9e90'
CATALOGUE_SHA = '7590ab9108d6ac89d44d37399d0a3b859364b38cf0b5a566f831e1a82fbf0d4f'
FIELDS = {'depth_mm':'Height (mm)', 'width_mm':'Width (mm)', 'web_mm':'Web Thickness (mm)',
          'flange_mm':'Flange Thickness (mm)', 'mass_kg_per_m':'Mass per meter (kg)'}


def compare_row(row, source):
    differences = [field for field, column in FIELDS.items() if Decimal(row[column]) != Decimal(source[field])]
    return {'actual': {field:row[column] for field,column in FIELDS.items()},
            'nominal_differences': differences,
            'outcome':'nominal_field_conflict' if differences else 'nominal_values_agree',
            'exact_article_verified':False}


def compare():
    dataset = ROOT / 'artifacts/user-reference-csvs/Structural Steel - Rev01 - 02 July 2026.csv'
    catalogue = ROOT / 'artifacts/arcelormittal/e1-2-parallel-sections.pdf'
    source_path = ROOT / 'reports/arcelormittal-ipe-observations.json'
    for path, expected in ((dataset,DATASET_SHA),(catalogue,CATALOGUE_SHA)):
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError('Input revision mismatch')
    payload = source_path.read_bytes()
    document = json.loads(payload)
    if document['catalogue_sha256'] != CATALOGUE_SHA or len(document['observations']) != 12:
        raise ValueError('Unexpected source transcription revision/count')
    index = {}
    for values in document['observations']:
        if len(values) != len(document['fields']):
            raise ValueError('Malformed source transcription row')
        observation = dict(zip(document['fields'],values))
        key = tuple(observation[f] for f in ('family','designation_height','designation_width'))
        if key in index:
            raise ValueError('Duplicate source key')
        index[key] = observation
    with dataset.open(encoding='utf-8-sig',newline='') as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != 805:
        raise ValueError('Expected805 supplied records')
    records, seen = [], set()
    for line,row in enumerate(rows,2):
        family = row['Type/Section/Channels/Angle/Bars/UC/I-Beams']
        if family not in ('IPE','IPE AA'):
            continue
        key = (family,row['Height (mm)'],row['Width (mm)'])
        if key in seen or key not in index:
            raise ValueError('Duplicate or absent designation candidate')
        seen.add(key)
        observation = index[key]
        records.append({'csv_line':line, 'designation_candidate':list(key),
                        'source':observation, **compare_row(row,observation)})
    if seen != set(index):
        raise ValueError('Incomplete IPE designation coverage')
    return {'dataset_sha256':DATASET_SHA, 'catalogue_sha256':CATALOGUE_SHA,
            'transcription_sha256':hashlib.sha256(payload).hexdigest(),
            'dataset_rows':805,'compared_rows':len(records),'not_compared_rows':805-len(records),
            'outcomes':dict(Counter(r['outcome'] for r in records)), 'records':records,
            'limitations':['Manual source transcription unreviewed; consistency tests do not prove transcription fidelity.',
                'Lookup infers designation candidate from CSV Height/Width; ambiguity of Height meaning remains unresolved.',
                'Nominal equality only, not a manufacturing tolerance or identity/interchangeability decision.',
                'Grade/certificate, length/end/coating, root radius and current availability not verified.',
                'Other793 structural records are outside this comparison, not invalid.']}


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write-snapshot',action='store_true')
    args=parser.parse_args()
    result=compare()
    content=json.dumps(result,indent=2)+'\n'
    path=ROOT/'reports/structural-ipe-comparison.json'
    if args.write_snapshot:
        path.write_text(content,encoding='utf-8',newline='')
    elif path.read_text(encoding='utf-8') != content:
        raise ValueError('Stale structural IPE comparison')
    print(f"IPE nominal comparison: {result['compared_rows']} checked; {result['outcomes']}; {result['not_compared_rows']} not compared. No article approval.")
