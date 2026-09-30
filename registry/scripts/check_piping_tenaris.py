#!/usr/bin/env python3
"""Compare supplied nominal pipe OD/wall values with Tenaris page 13.

Printed precision intervals are representation checks, never manufacturing tolerances.
Ambiguous source keys remain unresolved. Requires pypdf.
"""

import argparse
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path

from pypdf import PdfReader


def number(raw):
    if not re.fullmatch(r'\d+(?:[.,]\d+)?', raw.strip()):
        raise ValueError(f'Unsupported numeric representation: {raw!r}')
    return Decimal(raw.strip().replace(',', '.'))


def precision_compatible(left, right):
    a, b = number(left), number(right)
    return abs(a - b) <= (Decimal(1).scaleb(a.as_tuple().exponent) +
                          Decimal(1).scaleb(b.as_tuple().exponent)) / 2


def compare(catalogue, dataset):
    text = PdfReader(catalogue).pages[12].extract_text(extraction_mode='layout')
    pattern = re.compile(r'(\d+(?:\s+\d/\d)?|\d/\d)\s+(\d+)\s+(\d+,\d+)\s+'
                         r'(\d+,\d+)\s+(\d+,\d+)\s+(STD|XS|XXS|-)\s+(\d+|-)')
    entries = []
    index = defaultdict(list)
    for match in pattern.finditer(text):
        schedule = match[6] if match[7] == '-' else match[7]
        record = {'nps': ' '.join(match[1].split()), 'dn_raw': match[2], 'od_mm': match[3],
                  'wall_mm': match[4], 'weight_kg_per_m': match[5],
                  'wall_designation': match[6], 'schedule': match[7], 'page': 13}
        entries.append(record)
        index[(match[2], schedule)].append(record)
    if len(entries) != 57:
        raise ValueError(f'Expected 57 source table rows, extracted {len(entries)}')
    results, seen = [], set()
    with dataset.open(encoding='utf-8-sig', newline='') as handle:
        for line, row in enumerate(csv.DictReader(handle), 2):
            raw_schedule = row['Schedule Number'].strip()
            schedule = 'XXS' if raw_schedule == '(XXS)' else raw_schedule
            key = (row['Nominal Bore (mm)'].strip(), schedule)
            if key in seen:
                raise ValueError(f'Duplicate supplied key: {key}')
            seen.add(key)
            candidates = index.get(key, [])
            actual = {'od_mm': row['Outside Diameter (mm)'], 'wall_mm': row['Wall Thickness (mm)']}
            for value in actual.values():
                number(value)
            if not candidates:
                outcome = 'outside_source_key_scope'
            elif len(candidates) > 1:
                outcome = 'ambiguous_source_key'
            elif all(precision_compatible(actual[k], candidates[0][k]) for k in actual):
                outcome = 'printed_precision_compatible'
            else:
                outcome = 'dimension_conflict'
            results.append({'csv_line': line, 'key': key, 'raw_schedule': raw_schedule,
                            'actual': actual, 'source_candidates': candidates, 'outcome': outcome,
                            'construction_raw': row['Type'], 'specification_raw': row['MOC'],
                            'construction_conflict': row['MOC'] == 'ASTM A106' and row['Type'] == 'Welded'})
    if len(results) != 50:
        raise ValueError(f'Expected 50 supplied records, found {len(results)}')
    return {'source_page': 13, 'source_rows': len(entries), 'dataset_rows': len(results),
            'outcomes': dict(Counter(r['outcome'] for r in results)),
            'construction_conflicts': sum(r['construction_conflict'] for r in results),
            'source_ambiguous_keys': [key for key, records in sorted(index.items()) if len(records) > 1],
            'catalogue_sha256': hashlib.sha256(catalogue.read_bytes()).hexdigest(),
            'dataset_sha256': hashlib.sha256(dataset.read_bytes()).hexdigest(),
            'interpretation': 'Nominal OD/wall printed-precision comparison only; no manufacturing tolerance, material, route, exact article, mass or interchangeability validation.',
            'records': results}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--catalogue', type=Path, required=True)
    parser.add_argument('--dataset', type=Path, required=True)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    result = compare(args.catalogue, args.dataset)
    if args.report:
        args.report.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in result.items() if k != 'records'}, indent=2))
    return bool(result['construction_conflicts'] or any(r['outcome'] != 'printed_precision_compatible' for r in result['records']))


if __name__ == '__main__':
    raise SystemExit(main())
