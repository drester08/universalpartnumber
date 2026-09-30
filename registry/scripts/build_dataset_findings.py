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

ROOT = Path(__file__).resolve().parents[1]
DATASET = 'DATASET-USER-KLINGER-GASKETS-20260713'
ARTIFACT = 'ART-KLINGER-CATALOGUE-2014'
PIPE_DATASET = 'DATASET-USER-PIPING-20260702'
PIPE_ARTIFACT = 'ART-TENARIS-CIVIL-2026'
PLATE_DATASET = 'DATASET-USER-STEEL-PLATE-20260702'
PLATE_ARTIFACT = 'ART-MACSTEEL-VRN-2021'
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
    for name, family, dataset_id, artifact_id in reports:
        dataset, artifact = datasets[dataset_id], artifacts[artifact_id]
        path = root / 'reports' / name
        payload = path.read_bytes()
        report = json.loads(payload)
        if report['dataset_sha256'].lower() != dataset['sha256'].lower():
            raise ValueError(f'{name}: dataset checksum mismatch')
        if report['catalogue_sha256'].lower() != artifact['sha256'].lower():
            raise ValueError(f'{name}: catalogue checksum mismatch')
        groups = defaultdict(lambda: {'locators': [], 'lines': set(), 'count': 0})

        def add(kind, subject, locator, lines=(), count=1):
            entry = groups[(kind, tuple(subject))]
            if any(type(line) is not int or not 2 <= line <= int(dataset['row_count']) + 1 for line in lines):
                raise ValueError('Finding row locator outside registered dataset scope')
            entry['locators'].append(locator)
            entry['lines'].update(lines)
            entry['count'] += count

        if family == 'plate':
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
