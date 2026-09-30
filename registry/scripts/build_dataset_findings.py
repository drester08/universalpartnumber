#!/usr/bin/env python3
"""Derive source-dataset review findings from checksummed comparison reports.

Does not correct source rows, decide identity or issue UPNs.
"""

import argparse
import csv
import hashlib
import io
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATASET = 'DATASET-USER-KLINGER-GASKETS-20260713'
ARTIFACT = 'ART-KLINGER-CATALOGUE-2014'
FINDING_FIELDS = ('finding_id', 'dataset_id', 'dataset_sha256', 'artifact_id',
                  'issue_type', 'priority', 'subject_key', 'summary', 'next_action',
                  'evidence_path', 'evidence_sha256', 'evidence_locators', 'policy_version')
ROW_FIELDS = ('finding_id', 'csv_line')
ACTION = {
    'dimension_conflict': 'Verify the exact drawing and source edition, retain the raw value and record a separately reviewed correction; do not silently replace dimensions.',
    'unsupported_key': 'Confirm flange standard, class and size against exact source evidence; do not relabel by matching diameters or assume absence from this catalogue proves invalidity.',
    'duplicate_key': 'Determine the intended article and missing class/size assignment; retain both raw records until the duplicate is independently resolved.',
    'coverage_gap': 'Determine whether missing source keys are intentional scope exclusions or omitted records; do not synthesize articles from source tables.'}


def csv_text(fields, records):
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator='\n')
    writer.writeheader()
    writer.writerows(records)
    return stream.getvalue()


def derive(root=ROOT):
    with (root / 'data/source-datasets.csv').open(encoding='utf-8-sig', newline='') as handle:
        dataset = next(r for r in csv.DictReader(handle) if r['dataset_id'] == DATASET)
    with (root / 'data/source-artifacts.csv').open(encoding='utf-8-sig', newline='') as handle:
        artifact = next(r for r in csv.DictReader(handle) if r['artifact_id'] == ARTIFACT)
    findings, row_refs = [], []
    for name, family in (('klinger-maxiflex-comparison.json', 'Klinger Maxiflex Gasket'),
                         ('klinger-maxiprofile-comparison.json', 'Klinger MaxiProfile Gasket'),
                         ('klinger-softcut-comparison.json', 'softcut')):
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
            if any(not isinstance(line, int) or not 2 <= line <= int(dataset['row_count']) + 1 for line in lines):
                raise ValueError('Finding row locator outside registered dataset scope')
            entry['locators'].append(locator)
            entry['lines'].update(lines)
            entry['count'] += count

        if family != 'softcut':
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
            identifier = 'DF-' + hashlib.sha256((DATASET + ':' + kind + ':' + subject_key).encode()).hexdigest()[:24].upper()
            findings.append(dict(zip(FINDING_FIELDS, (
                identifier, DATASET, dataset['sha256'].lower(), ARTIFACT, kind,
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
