#!/usr/bin/env python3
"""Derive source-dataset review findings from checksummed comparison reports.

Does not correct source rows, decide identity or issue UPNs.
"""

import argparse
import csv
import hashlib
import io
import json
from collections import Counter, defaultdict
from pathlib import Path
from decimal import Decimal
from check_structural_heavy import candidate_key, screen, FIELDS as HEAVY_FIELDS
from check_structural_pfc import screen as screen_pfc
from check_structural_pfc_corroboration import validate_report as validate_pfc_corroboration, SOURCES as PFC_SOURCES

ROOT = Path(__file__).resolve().parents[1]
DATASET = 'DATASET-USER-KLINGER-GASKETS-20260713'
ARTIFACT = 'ART-KLINGER-CATALOGUE-2014'
PIPE_DATASET = 'DATASET-USER-PIPING-20260702'
PIPE_ARTIFACT = 'ART-TENARIS-CIVIL-2026'
PLATE_DATASET = 'DATASET-USER-STEEL-PLATE-20260702'
PLATE_ARTIFACT = 'ART-MACSTEEL-VRN-2021'
STRUCTURAL_DATASET = 'DATASET-USER-STRUCTURAL-STEEL-20260702'
STRUCTURAL_ARTIFACT = 'ART-AMSA-E12-PARALLEL'
HEAVY_ARTIFACT = 'ART-AMSA-H11-HEAVY'
BRITISH_ARTIFACTS = {'UB':'ART-BS-UB-2024','UC':'ART-BS-UC-2023'}
PFC_ARTIFACT='ART-BS-PFC-2023'
PFC_CORROBORATION_ARTIFACTS = {'macsteel': 'ART-MACSTEEL-PFC', 'orangebook': 'ART-AM-ORANGEBOOK-PFC'}
FINDING_FIELDS = ('finding_id', 'dataset_id', 'dataset_sha256', 'artifact_id',
                  'issue_type', 'priority', 'subject_key', 'summary', 'next_action',
                  'evidence_path', 'evidence_sha256', 'evidence_locators', 'policy_version')
ROW_FIELDS = ('finding_id', 'csv_line')
ACTION = {
    'dimension_conflict': 'Verify the exact drawing and source edition, retain the raw value and record a separately reviewed correction; do not silently replace dimensions.',
    'unsupported_key': 'Confirm flange standard, class and size against exact source evidence; do not relabel by matching diameters or assume absence from this catalogue proves invalidity.',
    'duplicate_key': 'Determine the intended article and missing class/size assignment; retain both raw records until the duplicate is independently resolved.',
    'coverage_gap': 'Confirm source coverage and scope using independent evidence; an absent key does not prove an invalid part, and missing articles must not be synthesized.',
    'construction_conflict': 'Obtain exact grade, manufacturing-route and certificate evidence; preserve the raw specification/type conflict and do not approve identity from dimensional compatibility.',
    'source_ambiguity': 'Corroborate the printed nominal-size anomaly with independent primary evidence; do not choose a convenient source candidate or silently correct its nominal diameter.',
    'material_interpretation': 'Verify exact specification, grade, delivery condition and product-name meaning against article/certificate evidence; proposed interpretations are not approved aliases or corrections.',
    'mass_discrepancy': 'Verify dimensions, density, mass basis and original source entry; assumed-density arithmetic is a screening check, not an authorized correction or article identity.',
    'article_evidence_gap': 'Obtain source-defined article keys, exact dimensions/tolerances, grade and delivery-condition evidence with certificates and independent review before identity ingestion; family wording alone is insufficient.'}


def csv_text(fields, records):
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator='\n')
    writer.writeheader()
    writer.writerows(records)
    return stream.getvalue()


def derive(root=ROOT):
    with (root / 'data/source-datasets.csv').open(encoding='utf-8-sig', newline='') as handle:
        datasets = {r['dataset_id']: r for r in csv.DictReader(handle)}
    with (root / 'data/source-artifacts.csv').open(encoding='utf-8-sig', newline='') as handle:
        artifacts = {r['artifact_id']: r for r in csv.DictReader(handle)}
    findings, row_refs = [], []
    reports = [(n, f, DATASET, ARTIFACT) for n, f in (
        ('klinger-maxiflex-comparison.json', 'Klinger Maxiflex Gasket'),
        ('klinger-maxiprofile-comparison.json', 'Klinger MaxiProfile Gasket'),
        ('klinger-softcut-comparison.json', 'softcut'))]
    reports.append(('piping-tenaris-comparison.json', 'pipe', PIPE_DATASET, PIPE_ARTIFACT))
    reports.append(('plate-macsteel-screening.json', 'plate', PLATE_DATASET, PLATE_ARTIFACT))
    reports.append(('structural-ipe-comparison.json', 'structural', STRUCTURAL_DATASET, STRUCTURAL_ARTIFACT))
    reports.append(('structural-heavy-comparison.json', 'heavy', STRUCTURAL_DATASET, HEAVY_ARTIFACT))
    reports.extend(('structural-british-comparison.json','british_'+f,STRUCTURAL_DATASET,a)
                   for f,a in BRITISH_ARTIFACTS.items())
    reports.append(('structural-pfc-comparison.json','pfc',STRUCTURAL_DATASET,PFC_ARTIFACT))
    reports.append(('structural-pfc-corroboration.json', 'pfc_corroboration', STRUCTURAL_DATASET,
                    PFC_CORROBORATION_ARTIFACTS['orangebook']))
    for name, family, dataset_id, artifact_id in reports:
        dataset, artifact = datasets[dataset_id], artifacts[artifact_id]
        path = root / 'reports' / name
        payload = path.read_bytes()
        report = json.loads(payload)
        if report['dataset_sha256'].lower() != dataset['sha256'].lower():
            raise ValueError(f'{name}: dataset checksum mismatch')
        source_sha = (report['source_sha256'].get('orangebook', '') if family == 'pfc_corroboration'
                      else report['source_pdf_sha256'].get(artifact['source_id'],'') if family.startswith('british_')
                      else report['catalogue_sha256'])
        if source_sha.lower() != artifact['sha256'].lower():
            raise ValueError(f'{name}: catalogue checksum mismatch')
        groups = defaultdict(lambda: {'locators': [], 'lines': set(), 'count': 0})

        def add(kind, subject, locator, lines=(), count=1):
            entry = groups[(kind, tuple(subject))]
            if any(type(line) is not int or not 2 <= line <= int(dataset['row_count']) + 1 for line in lines):
                raise ValueError('Finding row locator outside registered dataset scope')
            entry['locators'].append(locator)
            entry['lines'].update(lines)
            entry['count'] += count

        if family == 'pfc_corroboration':
            if set(report['source_sha256']) != set(PFC_CORROBORATION_ARTIFACTS) or any(
                    artifacts[a]['source_id'] != PFC_SOURCES[s][0]
                    or report['source_sha256'][s].lower() != artifacts[a]['sha256'].lower()
                    for s, a in PFC_CORROBORATION_ARTIFACTS.items()):
                raise ValueError('PFC corroboration catalogue checksum mismatch')
            prior_bytes = (root / 'reports/structural-pfc-comparison.json').read_bytes()
            if report['earlier_report_sha256'] != hashlib.sha256(prior_bytes).hexdigest():
                raise ValueError('PFC corroboration earlier report checksum mismatch')
            validate_pfc_corroboration(report, json.loads(prior_bytes))
            for i, case in enumerate(report['records']):
                result = case['source_screens']['orangebook']['outcome']
                if result == 'nominal_field_conflict':
                    add('dimension_conflict', ('Structural Steel', 'PFC', 'Orange Book nominal fields'),
                        f'/records/{i}', [case['csv_line']])
                elif result == 'no_serial_candidate':
                    add('coverage_gap', ('Structural Steel', 'PFC', 'Orange Book serial key absent'),
                        f'/records/{i}', [case['csv_line']])
            source_only = report['source_only_observations']['orangebook']
            if source_only:
                add('coverage_gap', ('Structural Steel', 'PFC', 'Orange Book source-only serial keys'),
                    '/source_only_observations/orangebook', count=len(source_only))
        elif family=='pfc':
            records,outside=report['records'],report['outside_family_scope_csv_lines']
            all_lines=outside+[r['csv_line'] for r in records]
            if (report['dataset_rows']!=int(dataset['row_count']) or report['selected_rows']!=len(records)
                    or len(records)!=6 or any(type(line) is not int for line in all_lines)
                    or sorted(all_lines)!=list(range(2,int(dataset['row_count'])+2))):
                raise ValueError('PFC report has missing, duplicate or overlapping row locators')
            observations=report['source_observations']
            if report['source_table_rows']!=12 or len(observations)!=12 or report['source_id']!=artifact['source_id']:
                raise ValueError('PFC source table scope mismatch')
            keys=set()
            for o in observations:
                key=(Decimal(o['designation_height']),Decimal(o['designation_width']))
                if (key in keys or o['source_id']!=artifact['source_id'] or type(o['pdf_page']) is not int
                        or o['pdf_page']!=1 or o['designation']!=f"{o['designation_height']} x {o['designation_width']} x {o['designation_mass_label']}"
                        or any(Decimal(o[v])<=0 for v in (*HEAVY_FIELDS,'centroid_distance_cm','root_radius_mm','depth_between_fillets_mm'))):
                    raise ValueError('PFC source key/locator/value invalid')
                keys.add(key)
            if dict(Counter(r['outcome'] for r in records))!=report['outcomes']:
                raise ValueError('PFC outcome counts mismatch')
            supplied_keys=set()
            for i,case in enumerate(records):
                if case['exact_article_verified'] is not False:
                    raise ValueError('PFC comparison cannot assert reviewed article identity')
                row={c:case['actual'][f] for f,c in HEAVY_FIELDS.items()}
                key=(Decimal(row['Height (mm)']),Decimal(row['Width (mm)']))
                if key in supplied_keys:
                    raise ValueError('Duplicate PFC supplied key')
                supplied_keys.add(key)
                expected=screen_pfc(row,observations)
                if any(case[k]!=v for k,v in expected.items()):
                    raise ValueError('PFC candidates/differences differ from source observations')
                locator=f'/records/{i}'
                if case['outcome']=='nominal_field_conflict':
                    add('dimension_conflict',('Structural Steel','PFC','British Steel nominal fields'),locator,[case['csv_line']])
                elif case['outcome']=='no_serial_candidate':
                    add('coverage_gap',('Structural Steel','PFC','British Steel serial key absent'),locator,[case['csv_line']])
        elif family.startswith('british_'):
            source_ids={artifacts[a]['source_id'] for a in BRITISH_ARTIFACTS.values()}
            if set(report['source_pdf_sha256']) != source_ids or any(
                    report['source_pdf_sha256'][artifacts[a]['source_id']].lower()!=artifacts[a]['sha256'].lower()
                    for a in BRITISH_ARTIFACTS.values()):
                raise ValueError('British source PDF checksum mismatch')
            prior_bytes=(root/'reports/structural-heavy-comparison.json').read_bytes()
            if hashlib.sha256(prior_bytes).hexdigest()!=report['earlier_report_sha256']:
                raise ValueError('British earlier report checksum mismatch')
            prior={r['csv_line']:r for r in json.loads(prior_bytes)['records']}
            records,outside=report['records'],report['outside_family_scope_csv_lines']
            lines=outside+[r['csv_line'] for r in records]
            if (report['dataset_rows']!=int(dataset['row_count']) or report['selected_rows']!=len(records)
                    or any(type(line) is not int for line in lines)
                    or sorted(lines)!=list(range(2,int(dataset['row_count'])+2))):
                raise ValueError('British report has missing, duplicate or overlapping row locators')
            if (Counter(r['designation_mass_candidate'][0] for r in records)!={'UB':31,'UC':18}
                    or dict(Counter(r['outcome'] for r in records))!=report['outcomes']):
                raise ValueError('British family/outcome counts mismatch')
            cross_count=conflict_count=0
            seen=set()
            for i,case in enumerate(records):
                if case['exact_article_verified'] is not False:
                    raise ValueError('British comparison cannot assert reviewed article identity')
                f,h,w,m=case['designation_mass_candidate']
                actual=case['actual']
                if (h,w,m)!=(actual['depth_mm'],actual['width_mm'],actual['mass_kg_per_m']):
                    raise ValueError('British raw candidate key mismatch')
                key=candidate_key(f,h,w,m)
                if key in seen:
                    raise ValueError('Duplicate British supplied key')
                seen.add(key)
                old=prior[case['csv_line']]
                if case['previous_source_candidates']!=old['source_candidates'] or case['previous_source_outcome']!=old['outcome'] or actual!=old['actual']:
                    raise ValueError('British prior evidence differs from bound report')
                candidates=case['source_candidates']
                label_only=case['designation_label_observations_not_mass_matches']
                if len(candidates)>1 or len(label_only)>1 or (candidates and label_only):
                    raise ValueError('British candidate selection is ambiguous')
                for o in candidates+label_only:
                    if (o['family']!=f or o['source_id']!=artifacts[BRITISH_ARTIFACTS[f]]['source_id']
                            or type(o['pdf_page']) is not int or o['pdf_page'] not in ({1,3} if f=='UB' else {1})
                            or o['designation']!=f"{o['designation_height']} x {o['designation_width']} x {o['designation_mass_label']}"
                            or any(Decimal(o[v])<=0 for v in (*HEAVY_FIELDS,'root_radius_mm','depth_between_fillets_mm'))):
                        raise ValueError('British source candidate values/locator invalid')
                    if candidate_key(f,o['designation_height'],o['designation_width'],o['mass_kg_per_m'])[:3]!=key[:3]:
                        raise ValueError('British source serial key mismatch')
                differences=[]
                cross=[]
                if candidates:
                    o=candidates[0]
                    if candidate_key(f,o['designation_height'],o['designation_width'],o['mass_kg_per_m'])!=key:
                        raise ValueError('British exact mass key mismatch')
                    differences=[v for v in HEAVY_FIELDS if Decimal(actual[v])!=Decimal(o[v])]
                    outcome='nominal_field_conflict' if differences else 'nominal_values_agree'
                    if len(old['source_candidates'])==1:
                        cross_count+=1
                        cross=[v for v in HEAVY_FIELDS if Decimal(old['source_candidates'][0][v])!=Decimal(o[v])]
                        conflict_count+=bool(cross)
                else:
                    outcome='no_exact_candidate_key'
                    if label_only and (label_only[0]['designation_mass_label']!=m or Decimal(label_only[0]['mass_kg_per_m'])==Decimal(m)):
                        raise ValueError('British label-only observation cannot be a mass match')
                if case['outcome']!=outcome or case['nominal_differences']!=differences or case['cross_source_nominal_differences']!=cross:
                    raise ValueError('British nominal differences/outcome mismatch')
                if f!=family.removeprefix('british_'):
                    continue
                locator=f'/records/{i}'
                if differences:
                    add('dimension_conflict',('Structural Steel',f,'British Steel nominal fields'),locator,[case['csv_line']])
                elif not candidates:
                    add('coverage_gap',('Structural Steel',f,'British Steel exact mass key absent'),locator,[case['csv_line']])
                if cross:
                    add('dimension_conflict',('Structural Steel',f,'British Steel versus DS.0001 source fields'),locator,[case['csv_line']])
            if report['cross_source_compared_rows']!=cross_count or report['cross_source_conflict_rows']!=conflict_count:
                raise ValueError('British cross-source totals mismatch')
        elif family == 'heavy':
            transcription_bytes = (root / 'reports/arcelormittal-heavy-observations.json').read_bytes()
            transcription = json.loads(transcription_bytes)
            if hashlib.sha256(transcription_bytes).hexdigest() != report['transcription_sha256']:
                raise ValueError('Heavy source transcription checksum mismatch')
            if (transcription['catalogue_sha256'].lower() != artifact['sha256'].lower()
                    or transcription['status'] != 'manual_transcription_unreviewed'
                    or transcription['source_id'] != artifact['source_id']
                    or report['source_id'] != artifact['source_id']):
                raise ValueError('Heavy source revision/status mismatch')
            observations=[]
            source_keys=set()
            for values in transcription['observations']:
                if len(values) != len(transcription['fields']):
                    raise ValueError('Malformed heavy source transcription')
                o=dict(zip(transcription['fields'],values))
                key=candidate_key(o['family'],o['designation_height'],o['designation_width'],o['mass_kg_per_m'])
                if key in source_keys or o['family'] not in ('UB','UC') or o['pdf_page'] != {'UB':1,'UC':2}[o['family']] or type(o['enquiry_only']) is not bool:
                    raise ValueError('Invalid heavy source key/locator')
                source_keys.add(key)
                observations.append(o)
            if Counter(o['family'] for o in observations) != {'UB':30,'UC':19}:
                raise ValueError('Heavy source family counts mismatch')
            records, outside = report['records'], report['outside_family_scope_csv_lines']
            all_lines=outside+[r['csv_line'] for r in records]
            if (report['dataset_rows'] != int(dataset['row_count']) or report['selected_rows'] != len(records)
                    or any(type(line) is not int for line in all_lines)
                    or sorted(all_lines) != list(range(2,int(dataset['row_count'])+2))):
                raise ValueError('Heavy report has missing, duplicate or overlapping row locators')
            if (Counter(r['designation_mass_candidate'][0] for r in records) != {'UB':31,'UC':18}
                    or dict(Counter(r['outcome'] for r in records)) != report['outcomes']
                    or report['uniquely_compared_rows'] != sum(len(r['source_candidates'])==1 for r in records)):
                raise ValueError('Heavy report coverage/outcome counts mismatch')
            used=set()
            supplied_keys=set()
            for i, case in enumerate(records):
                if case['exact_article_verified'] is not False:
                    raise ValueError('Heavy comparison cannot assert reviewed article identity')
                family_name,height,width,mass=case['designation_mass_candidate']
                row={column:case['actual'][field] for field,column in HEAVY_FIELDS.items()}
                row['Type/Section/Channels/Angle/Bars/UC/I-Beams']=family_name
                if (height,width,mass) != (row['Height (mm)'],row['Width (mm)'],row['Mass per meter (kg)']):
                    raise ValueError('Heavy candidate key differs from reported raw values')
                key=candidate_key(family_name,height,width,mass)
                if key in supplied_keys:
                    raise ValueError('Duplicate heavy supplied candidate key')
                supplied_keys.add(key)
                expected=screen(row,observations)
                if any(case[k] != v for k,v in expected.items()):
                    raise ValueError('Heavy candidate/differences differ from source transcription')
                used.update(candidate_key(o['family'],o['designation_height'],o['designation_width'],o['mass_kg_per_m']) for o in case['source_candidates'])
                locator=f'/records/{i}'
                if case['outcome']=='nominal_field_conflict':
                    add('dimension_conflict', ('Structural Steel',family_name,'DS.0001 nominal fields'),locator,[case['csv_line']])
                elif case['outcome']=='no_exact_candidate_key':
                    add('coverage_gap', ('Structural Steel',family_name,'DS.0001 exact designation/mass key absent'),locator,[case['csv_line']])
                elif case['outcome']=='ambiguous_candidate_key':
                    add('source_ambiguity', ('Structural Steel',family_name,'DS.0001 candidate key'),locator,[case['csv_line']])
            source_only=[o for o in observations if candidate_key(o['family'],o['designation_height'],o['designation_width'],o['mass_kg_per_m']) not in used]
            if source_only != report['source_rows_without_supplied_key']:
                raise ValueError('Heavy source-only coverage mismatch')
            if source_only:
                add('coverage_gap', ('Structural Steel','DS.0001 source entries without supplied key'), '/source_rows_without_supplied_key',count=len(source_only))
        elif family == 'structural':
            transcription_bytes = (root / 'reports/arcelormittal-ipe-observations.json').read_bytes()
            transcription = json.loads(transcription_bytes)
            if hashlib.sha256(transcription_bytes).hexdigest() != report['transcription_sha256']:
                raise ValueError('Structural source transcription checksum mismatch')
            if transcription['catalogue_sha256'].lower() != artifact['sha256'].lower():
                raise ValueError('Structural transcription catalogue checksum mismatch')
            records, outside = report['records'], report['not_compared_csv_lines']
            if (report['dataset_rows'] != int(dataset['row_count']) or report['compared_rows'] != len(records)
                    or report['not_compared_rows'] != len(outside)):
                raise ValueError('Structural coverage count differs from registered dataset')
            all_lines = outside + [r['csv_line'] for r in records]
            if any(type(line) is not int for line in all_lines) or sorted(all_lines) != list(range(2, int(dataset['row_count']) + 2)):
                raise ValueError('Structural report has missing, duplicate or overlapping row locators')
            if dict(Counter(r['outcome'] for r in records)) != report['outcomes']:
                raise ValueError('Structural outcome counts do not reconcile')
            for i, case in enumerate(records):
                if case['exact_article_verified'] is not False:
                    raise ValueError('Structural comparison cannot assert reviewed article identity')
                locator, lines = f'/records/{i}', [case['csv_line']]
                add('article_evidence_gap', ('Structural Steel', 'exact article/certified specification'), locator, lines)
                if case['outcome'] == 'nominal_field_conflict':
                    if not case['nominal_differences']:
                        raise ValueError('Structural conflict lacks differing fields')
                    add('dimension_conflict', ('Structural Steel', case['designation_candidate'][0], 'Height/designation versus depth'), locator, lines)
                elif case['outcome'] != 'nominal_values_agree' or case['nominal_differences']:
                    raise ValueError('Unsupported or inconsistent structural outcome')
            for i, line in enumerate(outside):
                locator = f'/not_compared_csv_lines/{i}'
                add('article_evidence_gap', ('Structural Steel', 'exact article/certified specification'), locator, [line])
                add('coverage_gap', ('Structural Steel', 'outside selected IPE families'), locator, [line])
        elif family == 'plate':
            records = report['records']
            if report['dataset_rows'] != int(dataset['row_count']) or len(records) != int(dataset['row_count']):
                raise ValueError('Plate report coverage count differs from registered dataset')
            if any(type(r['csv_line']) is not int for r in records) or sorted(r['csv_line'] for r in records) != list(range(2, int(dataset['row_count']) + 2)):
                raise ValueError('Plate report has missing or duplicate row locators')
            if dict(Counter(r['family_outcome'] for r in records)) != report['family_outcomes']:
                raise ValueError('Plate report outcome counts do not reconcile')
            if any(type(r['mass_discrepancy']) is not bool for r in records) or sum(r['mass_discrepancy'] for r in records) != report['mass_discrepancies']:
                raise ValueError('Plate report mass discrepancy count does not reconcile')
            for i, case in enumerate(records):
                if case['interpretation_status'] != 'unreviewed' or case['exact_article_verified'] is not False:
                    raise ValueError('Plate screening cannot assert reviewed article identity')
                locator, lines = f'/records/{i}', [case['csv_line']]
                add('article_evidence_gap', ('Plate', 'exact article/dimensions/tolerances/certificate'), locator, lines)
                if case['mass_discrepancy']:
                    dimensions = case['dimensions_raw']
                    add('mass_discrepancy', ('Plate', *(dimensions[k] for k in ('length_mm', 'width_mm', 'thickness_mm'))), locator, lines)
                outcome = case['family_outcome']
                if outcome in ('grade_character_review', 'specification_scope_review', 'unverified_product_name'):
                    add('material_interpretation', ('Plate', case['moc_raw']), locator, lines)
                elif outcome == 'outside_selected_family_scope':
                    add('coverage_gap', ('Plate', case['moc_raw']), locator, lines)
                elif outcome != 'family_designation_supported':
                    raise ValueError('Unsupported plate screening outcome')
        elif family == 'pipe':
            records = report['records']
            if report['dataset_rows'] != int(dataset['row_count']) or len(records) != int(dataset['row_count']):
                raise ValueError('Pipe report coverage count differs from registered dataset')
            if any(type(r['csv_line']) is not int for r in records) or sorted(r['csv_line'] for r in records) != list(range(2, int(dataset['row_count']) + 2)):
                raise ValueError('Pipe report has missing or duplicate row locators')
            if dict(Counter(r['outcome'] for r in records)) != report['outcomes']:
                raise ValueError('Pipe report outcome counts do not reconcile')
            if any(type(r['construction_conflict']) is not bool for r in records) or sum(r['construction_conflict'] for r in records) != report['construction_conflicts']:
                raise ValueError('Pipe construction conflict count does not reconcile')
            for i, case in enumerate(records):
                if case['construction_conflict']:
                    add('construction_conflict', ('Pipe', 'specification/manufacturing route'), f'/records/{i}', [case['csv_line']])
                outcome = case['outcome']
                if outcome == 'ambiguous_source_key':
                    add('source_ambiguity', ('Pipe', 'DN' + case['key'][0]), f'/records/{i}', [case['csv_line']])
                elif outcome == 'outside_source_key_scope':
                    add('coverage_gap', ('Pipe', 'DN' + case['key'][0]), f'/records/{i}', [case['csv_line']])
                elif outcome == 'dimension_conflict':
                    add('dimension_conflict', ('Pipe', *case['key']), f'/records/{i}', [case['csv_line']])
                elif outcome != 'printed_precision_compatible':
                    raise ValueError('Unsupported pipe comparison outcome')
        elif family != 'softcut':
            for key, kind in (('conflicts', 'dimension_conflict'), ('unsupported_keys', 'unsupported_key')):
                for i, case in enumerate(report[key]):
                    add(kind, (family, *case['key'][:2]), f'/{key}/{i}', [case['csv_line']])
            if report['catalogue_only_keys']:
                add('coverage_gap', (family,), '/catalogue_only_keys', count=len(report['catalogue_only_keys']))
        else:
            for i, case in enumerate(report['cases']):
                if case['outcome'] not in ('dimension_conflict', 'unsupported_key'):
                    continue
                by_family = defaultdict(list)
                for ref in case['csv_references']:
                    by_family[ref['family']].append(ref['csv_line'])
                for f, lines in by_family.items():
                    add(case['outcome'], (f, *case['key'][:2]), f'/cases/{i}', lines, len(lines))
            for i, duplicate in enumerate(report['duplicates']):
                add('duplicate_key', (duplicate['family'], *duplicate['key']), f'/duplicates/{i}', duplicate['csv_lines'])
            for i, missing in enumerate(report['catalogue_only_keys_by_family']):
                if missing['keys']:
                    add('coverage_gap', (missing['family'],), f'/catalogue_only_keys_by_family/{i}', count=len(missing['keys']))
        for (kind, subject), entry in sorted(groups.items()):
            subject_key = json.dumps(subject, ensure_ascii=True, separators=(',', ':'))
            identifier = 'DF-' + hashlib.sha256((dataset_id + ':' + kind + ':' + subject_key).encode()).hexdigest()[:24].upper()
            findings.append(dict(zip(FINDING_FIELDS, (
                identifier, dataset_id, dataset['sha256'].lower(), artifact_id, kind,
                'P2' if kind == 'coverage_gap' else 'P0', subject_key,
                f"{subject[0]}: {kind.replace('_', ' ')}; {entry['count']} source case(s), {len(entry['lines'])} affected supplied row(s).",
                ACTION[kind], 'registry/reports/' + name, hashlib.sha256(payload).hexdigest(),
                json.dumps(sorted(set(entry['locators'])), separators=(',', ':')), '0.1'))))
            row_refs.extend({'finding_id': identifier, 'csv_line': line} for line in sorted(entry['lines']))
    findings.sort(key=lambda r: r['finding_id'])
    row_refs.sort(key=lambda r: (r['finding_id'], r['csv_line']))
    if len({r['finding_id'] for r in findings}) != len(findings):
        raise ValueError('Duplicate derived finding IDs')
    return findings, row_refs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--write-snapshot', action='store_true')
    mode.add_argument('--check', action='store_true')
    args = parser.parse_args()
    findings, refs = derive()
    outputs = ((ROOT / 'data/dataset-findings.csv', csv_text(FINDING_FIELDS, findings)),
               (ROOT / 'data/dataset-finding-rows.csv', csv_text(ROW_FIELDS, refs)))
    for path, content in outputs:
        if args.check:
            if not path.exists() or path.read_text(encoding='utf-8') != content:
                raise ValueError(f'Stale findings snapshot: {path}')
        else:
            path.write_text(content, encoding='utf-8', newline='')
    print(f'Dataset findings: {len(findings)} groups, {len(refs)} row references; no source corrections or review decisions.')


if __name__ == '__main__':
    main()
