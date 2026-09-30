"""Screen all supplied UB/UC rows against unreviewed manufacturer nominal data.

Exact designation-size/mass keys bind candidates only. No nearest-key matching,
manufacturing tolerances, source corrections or identity approvals are implied.
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
CATALOGUE_SHA = '7395f9d038095e2b65d0bebce89019a3e0d29203c85691a337a740337c4464ae'
FIELDS = {'depth_mm':'Height (mm)', 'width_mm':'Width (mm)',
          'web_mm':'Web Thickness (mm)', 'flange_mm':'Flange Thickness (mm)',
          'mass_kg_per_m':'Mass per meter (kg)'}


def candidate_key(family, height, width, mass):
    return (family, Decimal(height), Decimal(width), Decimal(mass))


def screen(row, observations):
    family = row['Type/Section/Channels/Angle/Bars/UC/I-Beams']
    key = candidate_key(family, row['Height (mm)'], row['Width (mm)'], row['Mass per meter (kg)'])
    candidates = [o for o in observations if candidate_key(o['family'], o['designation_height'],
                  o['designation_width'], o['mass_kg_per_m']) == key]
    serial = [o for o in observations if candidate_key(o['family'], o['designation_height'],
              o['designation_width'], o['mass_kg_per_m'])[:3] == key[:3]]
    actual = {field:row[column] for field,column in FIELDS.items()}
    differences = []
    if len(candidates) == 1:
        differences = [f for f in FIELDS if Decimal(actual[f]) != Decimal(candidates[0][f])]
        outcome = 'nominal_field_conflict' if differences else 'nominal_values_agree'
    else:
        outcome = 'ambiguous_candidate_key' if candidates else 'no_exact_candidate_key'
    return {'designation_mass_candidate':[family, row['Height (mm)'],row['Width (mm)'],
             row['Mass per meter (kg)']], 'actual':actual, 'outcome':outcome,
            'nominal_differences':differences, 'source_candidates':candidates,
            'same_serial_source_candidates':serial if not candidates else [],
            'exact_article_verified':False}


def compare():
    dataset = ROOT/'artifacts/user-reference-csvs/Structural Steel - Rev01 - 02 July 2026.csv'
    catalogue = ROOT/'artifacts/arcelormittal/h1-1-heavy-structural.pdf'
    for path, expected in ((dataset,DATASET_SHA),(catalogue,CATALOGUE_SHA)):
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError('Input revision mismatch')
    payload = (ROOT/'reports/arcelormittal-heavy-observations.json').read_bytes()
    source = json.loads(payload)
    if source['catalogue_sha256'] != CATALOGUE_SHA or source['status'] != 'manual_transcription_unreviewed':
        raise ValueError('Unexpected source revision/status')
    observations=[]
    keys=set()
    for values in source['observations']:
        if len(values) != len(source['fields']):
            raise ValueError('Malformed transcription')
        o=dict(zip(source['fields'],values))
        key=candidate_key(o['family'],o['designation_height'],o['designation_width'],o['mass_kg_per_m'])
        if key in keys or o['family'] not in ('UB','UC') or o['pdf_page'] != {'UB':1,'UC':2}[o['family']]:
            raise ValueError('Duplicate or invalid source key/locator')
        if type(o['enquiry_only']) is not bool or any(Decimal(o[f]) <= 0 for f in FIELDS):
            raise ValueError('Invalid source values')
        keys.add(key)
        observations.append(o)
    if Counter(o['family'] for o in observations) != {'UB':30,'UC':19}:
        raise ValueError('Incomplete source table transcription')
    with dataset.open(encoding='utf-8-sig',newline='') as handle:
        rows=list(csv.DictReader(handle))
    if len(rows) != 805:
        raise ValueError('Unexpected dataset count')
    records=[]
    outside=[]
    for line,row in enumerate(rows,2):
        if row['Type/Section/Channels/Angle/Bars/UC/I-Beams'] not in ('UB','UC'):
            outside.append(line)
        else:
            records.append({'csv_line':line,**screen(row,observations)})
    if Counter(r['designation_mass_candidate'][0] for r in records) != {'UB':31,'UC':18}:
        raise ValueError('Unexpected supplied UB/UC coverage')
    used={candidate_key(o['family'],o['designation_height'],o['designation_width'],o['mass_kg_per_m'])
          for r in records for o in r['source_candidates']}
    return {'dataset_sha256':DATASET_SHA, 'catalogue_sha256':CATALOGUE_SHA,
            'transcription_sha256':hashlib.sha256(payload).hexdigest(),
            'source_id':source['source_id'], 'dataset_rows':805, 'selected_rows':len(records),
            'uniquely_compared_rows':sum(len(r['source_candidates'])==1 for r in records),
            'outside_family_scope_csv_lines':outside,
            'outcomes':dict(Counter(r['outcome'] for r in records)), 'records':records,
            'source_rows_without_supplied_key':[o for o in observations if candidate_key(o['family'],
                o['designation_height'],o['designation_width'],o['mass_kg_per_m']) not in used],
            'limitations':['Manual image-table transcription remains unreviewed; tests do not prove fidelity.',
                'Height/Width interpreted as designation candidates only, not approved physical dimensions.',
                'Exact mass key for candidate binding; no rounding, nearest-key selection or correction.',
                'Source URL calls this H1.1; document labels DS.0001 and has no verified publication date.',
                'Nominal equality is not manufacturing tolerance, article identity or interchangeability.',
                'Grade, certificates, radii, length/end/finish and current availability remain unverified.',
                'Enquiry-only footnotes retained; their absence does not prove current availability.',
                'Earlier IPE/source-specific findings remain open; this report is not yet in the review queue.']}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write-snapshot',action='store_true')
    args=parser.parse_args()
    result=compare()
    content=json.dumps(result,indent=2)+'\n'
    path=ROOT/'reports/structural-heavy-comparison.json'
    if args.write_snapshot:
        path.write_text(content,encoding='utf-8',newline='')
    elif path.read_text(encoding='utf-8') != content:
        raise ValueError('Stale heavy structural comparison')
    print(f"UB/UC screening: {result['selected_rows']} rows; {result['outcomes']}. No article approval.")
