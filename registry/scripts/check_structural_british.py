"""Independent nominal screening, not source correction or article approval."""
import argparse
import csv
import hashlib
import json
import re
from collections import Counter
from decimal import Decimal
from pathlib import Path
from pypdf import PdfReader
from check_structural_heavy import candidate_key, FIELDS, DATASET_SHA, compare as previous_compare

ROOT=Path(__file__).resolve().parents[1]
SOURCES={
    'UB':('SRC-BS-UB-2024','ub-190724.pdf','3bd480c5ba81da6948f37237b6a9763b3dacee5dd8f00f0018280ba00d2068ad',[(1,42,4),(3,45,0)]),
    'UC':('SRC-BS-UC-2023','uc-100723.pdf','d380b9c067bfd3a675576522e20f148cc3daf0fa80a92f415815811f734beecb',[(1,42,0)])}


def extract(path, family, source_id, pages):
    reader=PdfReader(path)
    observations=[]
    keys=set()
    for page,count,incomplete in pages:
        lines=[line for line in reader.pages[page-1].extract_text().splitlines()
               if re.match(r'^\d+ x \d+ x \d+ ',line)]
        if len(lines)!=count:
            raise ValueError('Unexpected British Steel source table row count')
        rejected=0
        for line in lines:
            tokens=line.split()
            if len(tokens)==17 and page==1 and family=='UB' and tokens[:3]==['410','x','260']:
                # Four unselected rows omit their mass cell; do not shift columns.
                rejected+=1
                continue
            if len(tokens)!=18 or tokens[1]!='x' or tokens[3]!='x':
                raise ValueError('Malformed British Steel source row')
            if any(Decimal(v)<=0 for v in tokens[5:]):
                raise ValueError('Invalid source numeric values')
            height,width,label_mass=tokens[0],tokens[2],tokens[4]
            mass,depth,b,web,flange,radius,clear=tokens[5:12]
            key=candidate_key(family,height,width,mass)
            if key in keys:
                raise ValueError('Duplicate British Steel candidate key')
            keys.add(key)
            observations.append({'family':family,'designation_height':height,'designation_width':width,
                'designation_mass_label':label_mass,'mass_kg_per_m':mass,'depth_mm':depth,'width_mm':b,
                'web_mm':web,'flange_mm':flange,'root_radius_mm':radius,'depth_between_fillets_mm':clear,
                'source_id':source_id,'pdf_page':page,'designation':f'{height} x {width} x {label_mass}'})
        if rejected!=incomplete:
            raise ValueError('Unexpected incomplete mass-column count')
    return observations


def compare():
    dataset=ROOT/'artifacts/user-reference-csvs/Structural Steel - Rev01 - 02 July 2026.csv'
    if hashlib.sha256(dataset.read_bytes()).hexdigest()!=DATASET_SHA:
        raise ValueError('Supplied dataset revision mismatch')
    observations=[]
    for family,(source_id,name,sha,pages) in SOURCES.items():
        path=ROOT/'artifacts/british-steel'/name
        if hashlib.sha256(path.read_bytes()).hexdigest()!=sha:
            raise ValueError('British Steel PDF revision mismatch')
        observations.extend(extract(path,family,source_id,pages))
    previous_bytes=(ROOT/'reports/structural-heavy-comparison.json').read_bytes()
    previous=json.loads(previous_bytes)
    if previous!=previous_compare():
        raise ValueError('Earlier source comparison is stale or modified')
    if previous['dataset_sha256']!=DATASET_SHA:
        raise ValueError('Earlier source comparison dataset revision mismatch')
    previous_index={r['csv_line']:r for r in previous['records']}
    with dataset.open(encoding='utf-8-sig',newline='') as handle:
        rows=list(csv.DictReader(handle))
    if len(rows)!=805:
        raise ValueError('Unexpected dataset count')
    records=[]
    outside=[]
    for line,row in enumerate(rows,2):
        family=row['Type/Section/Channels/Angle/Bars/UC/I-Beams']
        if family not in SOURCES:
            outside.append(line)
            continue
        key=candidate_key(family,row['Height (mm)'],row['Width (mm)'],row['Mass per meter (kg)'])
        candidates=[o for o in observations if candidate_key(o['family'],o['designation_height'],o['designation_width'],o['mass_kg_per_m'])==key]
        actual={f:row[c] for f,c in FIELDS.items()}
        differences=[]
        intersource=[]
        prior=previous_index[line]
        if len(candidates)==1:
            differences=[f for f in FIELDS if Decimal(actual[f])!=Decimal(candidates[0][f])]
            if len(prior['source_candidates'])==1:
                intersource=[f for f in FIELDS if Decimal(prior['source_candidates'][0][f])!=Decimal(candidates[0][f])]
            outcome='nominal_field_conflict' if differences else 'nominal_values_agree'
        else:
            outcome='no_exact_candidate_key' if not candidates else 'ambiguous_candidate_key'
        # Separate explicit printed designation observation; not a mass-key match.
        label_observations=[]
        if not candidates:
            label_observations=[o for o in observations if (o['family'],o['designation_height'],o['designation_width'],o['designation_mass_label'])==(family,row['Height (mm)'],row['Width (mm)'],row['Mass per meter (kg)'])]
        records.append({'csv_line':line,'designation_mass_candidate':[family,row['Height (mm)'],row['Width (mm)'],row['Mass per meter (kg)']],
            'actual':actual,'source_candidates':candidates,'nominal_differences':differences,'outcome':outcome,
            'designation_label_observations_not_mass_matches':label_observations,
            'previous_source_candidates':prior['source_candidates'],'previous_source_outcome':prior['outcome'],
            'cross_source_nominal_differences':intersource,'exact_article_verified':False})
    if Counter(r['designation_mass_candidate'][0] for r in records)!={'UB':31,'UC':18}:
        raise ValueError('Unexpected supplied selected-family count')
    return {'dataset_sha256':DATASET_SHA,'source_pdf_sha256':{s[0]:s[2] for s in SOURCES.values()},
        'earlier_report_sha256':hashlib.sha256(previous_bytes).hexdigest(),
        'dataset_rows':805,'selected_rows':49,'outside_family_scope_csv_lines':outside,
        'outcomes':dict(Counter(r['outcome'] for r in records)),
        'cross_source_compared_rows':sum(len(r['source_candidates'])==len(r['previous_source_candidates'])==1 for r in records),
        'cross_source_conflict_rows':sum(bool(r['cross_source_nominal_differences']) for r in records),
        'records':records,
        'limitations':['UB PDF pages1/3 and UC page1 fully rendered/reviewed; other pages not visually reviewed.',
            'Automatic text extraction remains unreviewed; tests prove consistency, not full fidelity.',
            'Four unselected UB410x260 entries omit mass cells; skipped explicitly, not column-shifted.',
            'Height/Width used as designation candidates, not certified physical dimensions.',
            'Printed designation mass label is distinct from actual mass; no rounded mass-key matching.',
            'New nominal candidates do not close older source-specific coverage findings.',
            'Same nominal dimensions do not establish material, certificates, tolerances, identity or suitability.',
            'Root radius and clear depth retained as source facts, not approved defining attributes.',
            'Source-specific findings retain unresolved differences; no raw correction or approved equivalence.']}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--write-snapshot',action='store_true')
    args=p.parse_args()
    result=compare()
    content=json.dumps(result,indent=2)+'\n'
    path=ROOT/'reports/structural-british-comparison.json'
    if args.write_snapshot:
        path.write_text(content,encoding='utf-8',newline='')
    elif path.read_text(encoding='utf-8')!=content:
        raise ValueError('Stale British Steel comparison')
    print(f"British Steel: {result['outcomes']}; cross-source compared {result['cross_source_compared_rows']}, conflicts {result['cross_source_conflict_rows']}. No identity approval.")
