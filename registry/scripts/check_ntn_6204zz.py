"""Governed NTN 6204ZZ intake excludes contradictory fields from specifications."""
import argparse
import csv
import json
from pathlib import Path
import check_ntn_6204zz_research as source

ROOT = Path(__file__).resolve().parents[2]
PART, OBS = 'MP-NTN-6204ZZ', 'OBS-NTN-6204ZZ-20261001'


def build_report():
    staged = source.build_report()
    return {'source_id':'SRC-NTN-6204ZZ', 'artifact_id':'ART-NTN-6204ZZ',
        'source_sha256':source.SHA, 'manufacturer_article':'6204ZZ', 'manufacturer_namespace':'NTN',
        'manufacturer_part_id':PART, 'observation_id':OBS, 'identity_approved':False,
        'native_property_count':staged['native_property_count'], 'native_properties':staged['native_properties'],
        'quality_findings':staged['quality_findings'], 'policy_version':'ntn-6204zz-intake-0.1',
        'ingested_fact_count':12, 'excluded_fields':['Static Load Rating','da max'],
        'limitations':['Twelve unreviewed article facts; three proposed exact-source mappings.',
            'Conflicting static rating and ambiguous mounting cells retained in report only.',
            'Dynamic metric values 14200 N and 14.20 kN agree; calculation basis unstated.',
            'No full closure or tolerance mapping inherited from another NTN article.',
            'Round bore does not prove cylindrical bore; grease and locating remain absent.',
            'Raw High Carbon Chrome Steel remains unnormalized; no supplied grease inferred from speed.',
            'Independent extraction, interpretation and reuse review outstanding; no UPN or equivalence approval.']}


def verify_seed_bindings(report):
    if report != build_report():
        raise ValueError('NTN 6204 report altered or promoted')
    def read(name):
        with (ROOT/'registry/data'/name).open(encoding='utf-8-sig',newline='') as f:
            return list(csv.DictReader(f))
    def one(name,key,value):
        rows=[r for r in read(name) if r[key]==value]
        if len(rows)!=1:
            raise ValueError('NTN 6204 custody record missing or duplicated')
        return rows[0]
    s=one('source-register.csv','source_id',report['source_id'])
    a=one('source-artifacts.csv','artifact_id',report['artifact_id'])
    p=one('manufacturer-parts.csv','manufacturer_part_id',PART)
    o=one('observations.csv','observation_id',OBS)
    if (s['source_url'],s['publisher_name'],s['authority_tier'],s['ingestion_status'])!=(source.URL,'NTN Bearing Corporation of America','1','reference_only'):
        raise ValueError('NTN 6204 registered source changed')
    if (a['source_id'],a['artifact_url'],a['sha256'],a['local_path'],a['retrieval_state'])!=(report['source_id'],source.URL,source.SHA,'registry/artifacts/ntn/6204zz-20261001.html','retrieved'):
        raise ValueError('NTN 6204 artifact custody changed')
    if (p['manufacturer_id'],p['manufacturer_part_number'],p['profile_id'])!=('ORG-NTN-AMERICAS','6204ZZ','PROFILE-BEARING-DGBB-1R-DOUBLE-METAL-SHIELD-0.1'):
        raise ValueError('NTN 6204 article namespace changed')
    if (o['manufacturer_part_id'],o['source_id'],o['raw_payload_sha256'],o['review_state'])!=(PART,report['source_id'],source.SHA,'unreviewed'):
        raise ValueError('NTN 6204 observation custody changed')
    expected={
        'GEOMETRY':('PROP-BEARING-GEOMETRY','Deep Groove Ball Bearing; Single Row Radial Ball Bearing','single_row_deep_groove_ball','','','Exact article construction; mapping proposed'),
        'BORE':('PROP-BORE-DIAMETER','d 20.000 mm','','20.000','UNIT-MM','Exact metric boundary dimension; unreviewed'),
        'OD':('PROP-OUTSIDE-DIAMETER','D 47.000 mm','','47.000','UNIT-MM','Exact metric boundary dimension; unreviewed'),
        'WIDTH':('PROP-BEARING-WIDTH','B 14.000 mm','','14.000','UNIT-MM','Exact metric boundary dimension; unreviewed'),
        'CLOSURE':('PROP-BEARING-CLOSURE','Double Shielded','','','','No full contact/material definition assigned'),
        'CLEARANCE':('PROP-RADIAL-INTERNAL-CLEARANCE','CN','cn','','','Exact article clearance; mapping proposed'),
        'TOLERANCE':('PROP-BEARING-TOLERANCE-CLASS','ISO Class 0','','','','Manufacturer wording retained; no P0 crosswalk assigned'),
        'CAGE':('PROP-CAGE-CONSTRUCTION','Cage Type Pressed; Cage Material Steel','pressed_steel','','','Exact article cage fields combined; mapping proposed'),
        'MATERIAL':('PROP-BEARING-MATERIAL','High Carbon Chrome Steel','','','','Raw material family; standards and heat treatment unproven'),
        'DYNAMIC':('PROP-BASIC-DYNAMIC-LOAD-RATING','14200 N; 14.20 kN','','14200','UNIT-N','Both metric displays agree; manufacturer calculation basis unstated'),
        'SPEED':('PROP-LIMITING-SPEED-GREASE','16000 RPM','','16000','UNIT-RPM','Grease speed does not identify supplied lubricant'),
        'MASS':('PROP-MASS','0.103 kg','','0.103','UNIT-KG','Source weight; not independent measured article identity')}
    rows=[r for r in read('specification-values.csv') if r['observation_id']==OBS]
    actual={r['specification_id'].removeprefix('SPEC-NTN-6204ZZ-'):tuple(r[k] for k in ('property_id','raw_value','normalized_text','normalized_number','unit_id','qualifier')) for r in rows}
    if len(rows)!=12 or actual!=expected:
        raise ValueError('NTN 6204 ingestion changed or quarantined field promoted')
    mappings=[r for r in read('specification-value-mappings.csv') if r['specification_id'] in {r['specification_id'] for r in rows}]
    # The later proposal is governed separately; do not rewrite the historical
    # intake snapshot or its original three direct-source interpretations.
    import check_ntn_6204zz_closure_mapping as closure
    later=[r for r in mappings if r['mapping_id']=='MAP-NTN-6204ZZ-CLOSURE']
    if len(later)!=1:
        raise ValueError('NTN 6204 later closure proposal missing or duplicated')
    closure.verify_mapping_row(later[0])
    mappings=[r for r in mappings if r not in later]
    allowed={'GEOMETRY':'CV-BEARING-GEOMETRY-SR-DGBB','CLEARANCE':'CV-BEARING-CLEARANCE-CN','CAGE':'CV-BEARING-CAGE-PRESSED-STEEL'}
    if len(mappings)!=3 or {r['specification_id'].removeprefix('SPEC-NTN-6204ZZ-'):r['controlled_value_id'] for r in mappings}!=allowed or any(r['mapping_state']!='proposed' or r['mapping_basis']!='source_exact' for r in mappings):
        raise ValueError('NTN 6204 mapping scope/state changed')
    return 12


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write-snapshot',action='store_true')
    args=parser.parse_args()
    report=build_report()
    verify_seed_bindings(report)
    target=ROOT/'registry/reports/ntn-6204zz-source.json'
    if args.write_snapshot:
        target.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    elif json.loads(target.read_text(encoding='utf-8'))!=report:
        raise ValueError('NTN 6204 intake snapshot stale')
    print('NTN 6204ZZ: twelve unreviewed facts; contradictory static and mounting fields excluded.')
