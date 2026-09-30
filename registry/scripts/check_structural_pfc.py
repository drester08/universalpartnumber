"""Screen supplied PFC nominal fields without approving part identity."""
import argparse
import csv
import hashlib
import json
import re
from collections import Counter
from decimal import Decimal
from pathlib import Path
from pypdf import PdfReader
from check_structural_heavy import DATASET_SHA, FIELDS

ROOT=Path(__file__).resolve().parents[1]
SHA='7254c5037cfe6913240dae1c38f43142e8066c7f53e6d418e7edc6bceb724f7a'


def extract(path):
    reader=PdfReader(path)
    if len(reader.pages)!=2:
        raise ValueError('Unexpected PFC page count')
    lines=[l for l in reader.pages[0].extract_text().splitlines() if re.match(r'^\d+ x \d+ x \d+ ',l)]
    if len(lines)!=12:
        raise ValueError('Unexpected PFC source row count')
    result=[]
    seen=set()
    for line in lines:
        t=line.split()
        if len(t)!=18 or t[1]!='x' or t[3]!='x' or any(Decimal(v)<=0 for v in t[5:]):
            raise ValueError('Malformed PFC source row')
        key=(Decimal(t[0]),Decimal(t[2]))
        if key in seen:
            raise ValueError('Ambiguous PFC serial size')
        seen.add(key)
        mass,depth,width,web,flange,cy,radius,clear=t[5:13]
        result.append({'designation':f'{t[0]} x {t[2]} x {t[4]}',
            'designation_height':t[0],'designation_width':t[2],'designation_mass_label':t[4],
            'mass_kg_per_m':mass,'depth_mm':depth,'width_mm':width,'web_mm':web,'flange_mm':flange,
            'centroid_distance_cm':cy,'root_radius_mm':radius,'depth_between_fillets_mm':clear,
            'source_id':'SRC-BS-PFC-2023','pdf_page':1})
    return result


def screen(row, observations):
    key=(Decimal(row['Height (mm)']),Decimal(row['Width (mm)']))
    candidates=[o for o in observations if (Decimal(o['designation_height']),Decimal(o['designation_width']))==key]
    actual={f:row[c] for f,c in FIELDS.items()}
    differences=[]
    if len(candidates)==1:
        differences=[f for f in FIELDS if Decimal(actual[f])!=Decimal(candidates[0][f])]
        outcome='nominal_field_conflict' if differences else 'nominal_values_agree'
    else:
        outcome='no_serial_candidate' if not candidates else 'ambiguous_serial_candidate'
    return {'serial_size_candidate':[row['Height (mm)'],row['Width (mm)']],
        'actual':actual,'source_candidates':candidates,'nominal_differences':differences,
        'outcome':outcome,'exact_article_verified':False}


def compare():
    dataset=ROOT/'artifacts/user-reference-csvs/Structural Steel - Rev01 - 02 July 2026.csv'
    source=ROOT/'artifacts/british-steel/pfc-datasheet.pdf'
    for path,sha in [(dataset,DATASET_SHA),(source,SHA)]:
        if hashlib.sha256(path.read_bytes()).hexdigest()!=sha:
            raise ValueError('PFC input revision mismatch')
    observations=extract(source)
    with dataset.open(encoding='utf-8-sig',newline='') as handle:
        rows=list(csv.DictReader(handle))
    if len(rows)!=805:
        raise ValueError('Unexpected supplied row count')
    records=[]
    outside=[]
    for line,row in enumerate(rows,2):
        if row['Type/Section/Channels/Angle/Bars/UC/I-Beams']=='Parallel Flange':
            records.append({'csv_line':line,**screen(row,observations)})
        else:
            outside.append(line)
    if len(records)!=6 or len({tuple(r['serial_size_candidate']) for r in records})!=6:
        raise ValueError('Unexpected supplied PFC family scope')
    return {'dataset_sha256':DATASET_SHA,'catalogue_sha256':SHA,'source_id':'SRC-BS-PFC-2023',
        'dataset_rows':805,'selected_rows':6,'source_table_rows':12,'source_observations':observations,
        'outside_family_scope_csv_lines':outside,'outcomes':dict(Counter(r['outcome'] for r in records)),
        'records':records,'limitations':['Both PDF pages rendered/reviewed; numeric extraction from page1, fidelity unreviewed.',
            'Serial Height/Width candidate binding only; mass is independently compared, not rounded to a designation.',
            'Absent keys limit this table, not proof that supplied parts are invalid.',
            'Centroid distance is cm, radius and clear depth mm; these are not interchanged.',
            'Nominal equality is not a manufacturing tolerance, material certificate or identity approval.',
            'Grade, product article, finish/ends/length/tolerances and current availability not verified.',
            'Older source-specific findings remain open; PFC findings expose issues without approving corrections.']}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--write-snapshot',action='store_true')
    args=p.parse_args()
    result=compare()
    content=json.dumps(result,indent=2)+'\n'
    path=ROOT/'reports/structural-pfc-comparison.json'
    if args.write_snapshot:
        path.write_text(content,encoding='utf-8',newline='')
    elif path.read_text(encoding='utf-8')!=content:
        raise ValueError('Stale PFC comparison')
    print(f"PFC: {result['outcomes']}. No article approval.")
