#!/usr/bin/env python3
"""Compare 24 supplied gasket-family matrices with historical soft-cut geometry.

This tests geometry only, never material suitability or exact article identity.
Requires pypdf. Source inputs are read-only.
"""

import argparse
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from pypdf import PdfReader


PAGE_COUNTS = {102: 40, 103: 39, 104: 38, 105: 36, 106: 37, 107: 40,
               108: 39, 109: 36, 110: 41, 111: 41, 112: 42, 113: 41}
FIELDS = ('Dimensions Outer Ring Dia (mm)', 'Dimensions Inner Ring Dia (mm)',
          'Dimensions Outer Ring Thk (mm)', 'Dimensions Inner Ring Thk (mm)')
EXCLUDED = {'Klinger Maxiflex Gasket', 'Klinger MaxiProfile Gasket'}


def extract(catalogue):
    expected, counts = {}, {}
    reader = PdfReader(catalogue)
    headings = re.compile(r'(?m)^(?:ASME (B16\.21|B16\.47) (?:([AB]) )?Class (\d+)'
                          r'|PN(\d+)|(?:BS10 )?Table ([A-Z]))(?: \(continued\))?\s*$')
    pattern = re.compile(r'(?m)^\s*(\d+(?:\s+\d/\d)?|\d/\d)\s*(?:\(\d+\))?\s+'
                         r'(\d+)\s*x\s*(\d+)\s+(\d+)\s*x\s*(\d+)\s+'
                         r'(\d+)(\*?)\s+(\d+)\s+(\d+)\s*$')
    for page in PAGE_COUNTS:
        text = reader.pages[page - 1].extract_text()
        sections = list(headings.finditer(text))
        count = 0
        for i, heading in enumerate(sections):
            content = text[heading.end():sections[i+1].start() if i+1 < len(sections) else len(text)]
            if heading[1]:
                flange = 'ASME ' + heading[1] + ' Flanges'
                classification = ((heading[2] + ' ') if heading[2] else '') + 'Class ' + heading[3]
            elif heading[4]:
                flange, classification = 'DIN Standard Flanges', 'PN' + heading[4]
            else:
                flange, classification = 'BS10 Flanges', 'Table ' + heading[5]
            for match in pattern.finditer(content):
                key = (flange, classification, ' '.join(match[1].split()))
                if key in expected:
                    raise ValueError(f'Duplicate catalogue key: {key}')
                expected[key] = {'page': page, 'ibc': (match[2], match[3], '', ''),
                                 'full_face': (match[4], match[5], '', ''),
                                 'bolt_holes': match[6], 'hole_diameter_mm': match[8],
                                 'bolt_pcd_mm': match[9], 'footnote_marker': match[7]}
                if match[7]:
                    expected[key]['footnote'] = 'Catalogue permits four bolt holes for cast iron and copper alloy flanges; the printed eight-hole value is not unconditional.'
                count += 1
        counts[page] = count
    if counts != PAGE_COUNTS:
        raise ValueError(f'Catalogue extraction incomplete: {counts}')
    return expected, counts


def compare(catalogue, dataset):
    expected, counts = extract(catalogue)
    families = defaultdict(Counter)
    seen = defaultdict(dict)
    duplicates = []
    cases = {}
    with dataset.open(encoding='utf-8-sig', newline='') as handle:
        for line, row in enumerate(csv.DictReader(handle), 2):
            family = row['Description']
            if family in EXCLUDED:
                continue
            size = (row['Nominal Size (NB) Inch'] or row['Nominal Size (PN)']).strip().rstrip('“”"')
            key = (row['Flange Type'].strip(), row['Class / Table'].strip(), ' '.join(size.split()))
            actual = tuple(row[f].strip() for f in FIELDS)
            families[family]['rows'] += 1
            if key in seen[family]:
                duplicates.append({'family': family, 'key': key, 'csv_lines': [seen[family][key], line]})
            else:
                seen[family][key] = line
            source = expected.get(key)
            if source is None:
                outcome = 'unsupported_key'
            elif actual == source['full_face']:
                outcome = 'full_face_od_id_agreement'
            elif actual == source['ibc']:
                outcome = 'ibc_od_id_agreement'
            else:
                outcome = 'dimension_conflict'
            families[family][outcome] += 1
            case_key = (key, actual, outcome)
            if case_key not in cases:
                cases[case_key] = {'key': key, 'actual': actual, 'outcome': outcome,
                                   'source': source, 'csv_references': []}
            cases[case_key]['csv_references'].append({'family': family, 'csv_line': line})
    if len(families) != 24 or any(c['rows'] != 470 for c in families.values()):
        raise ValueError(f'Expected 24 families of 470 rows: {dict(families)}')
    missing = [{'family': f, 'keys': sorted(set(expected) - set(keys))} for f, keys in sorted(seen.items())]
    totals = sum(families.values(), Counter())
    return {'page_counts': counts, 'catalogue_keys': len(expected), 'totals': dict(totals),
            'families': {f: dict(c) for f, c in sorted(families.items())},
            'duplicates': duplicates, 'catalogue_only_keys_by_family': missing,
            'cases': list(cases.values()),
            'catalogue_sha256': hashlib.sha256(catalogue.read_bytes()).hexdigest(),
            'dataset_sha256': hashlib.sha256(dataset.read_bytes()).hexdigest(),
            'interpretation': 'Historical OD/ID comparison only. No inference of drilling, thickness, material, construction, availability, suitability or exact article identity.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--catalogue', type=Path, required=True)
    parser.add_argument('--dataset', type=Path, required=True)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    result = compare(args.catalogue, args.dataset)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: result[k] for k in ('page_counts', 'catalogue_keys', 'totals', 'duplicates')}, indent=2))
    issues = Counter()
    for case in result['cases']:
        if case['outcome'] in ('dimension_conflict', 'unsupported_key'):
            issues[(case['outcome'], *case['key'][:2])] += len(case['csv_references'])
    print(json.dumps({'issues_by_class': [{'outcome': k[0], 'flange': k[1], 'class': k[2], 'rows': v}
                                         for k, v in sorted(issues.items())]}, indent=2))
    return bool(result['duplicates'] or result['totals'].get('dimension_conflict') or
                result['totals'].get('unsupported_key') or any(m['keys'] for m in result['catalogue_only_keys_by_family']))


if __name__ == '__main__':
    raise SystemExit(main())
