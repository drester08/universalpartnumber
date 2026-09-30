#!/usr/bin/env python3
"""Compare the supplied MaxiProfile revision with historical catalogue pages 68–70.

Requires pypdf. Does not modify inputs or establish physical component meanings.
"""

import argparse
import csv
import hashlib
import json
import re
from pathlib import Path

from pypdf import PdfReader


def compare(catalogue, dataset):
    expected = {}
    page_counts = {}
    reader = PdfReader(catalogue)
    heading = re.compile(r'Class (\d+)\s+to suit ASME B16\.5 fl\s*anges|(?m:^PN(\d+)\s*$)')
    for page in (68, 69, 70):
        text = reader.pages[page - 1].extract_text()
        sections = list(heading.finditer(text))
        count = 0
        for i, section in enumerate(sections):
            content = text[section.end():sections[i + 1].start() if i + 1 < len(sections) else len(text)]
            is_asme = section[1] is not None
            classification = 'Class ' + section[1] if is_asme else 'PN' + section[2]
            flange = 'ASME B16.5 Flanges' if is_asme else 'DIN Standard Flanges'
            nominal = r'(\d+(?:[.\s]+\d/\d)?|\d/\d)\s*[“”"]' if is_asme else r'(\d+)'
            pattern = re.compile(nominal + r'\s+(\d+)\s*x\s*(\d+)\s*x\s*(\d+)')
            for match in pattern.finditer(content):
                size = ' '.join(match[1].replace('.', ' ').split())
                key = (flange, classification, size)
                if key in expected:
                    raise ValueError(f'Duplicate catalogue key: {key}')
                expected[key] = (tuple(match.group(n) for n in (2, 3, 4)) + ('',), page)
                count += 1
        page_counts[page] = count
    if page_counts != {68: 95, 69: 90, 70: 54}:
        raise ValueError(f'Catalogue extraction incomplete: {page_counts}')
    fields = ('Dimensions Outer Ring Dia (mm)', 'Dimensions Inner Ring Dia (mm)',
              'Dimensions Outer Ring Thk (mm)', 'Dimensions Inner Ring Thk (mm)')
    matches, conflicts, unsupported = [], [], []
    seen = set()
    with dataset.open(encoding='utf-8-sig', newline='') as handle:
        for line, row in enumerate(csv.DictReader(handle), 2):
            if row['Description'] != 'Klinger MaxiProfile Gasket':
                continue
            size = (row['Nominal Size (NB) Inch'] or row['Nominal Size (PN)']).strip().rstrip('“”"')
            size = ' '.join(size.replace('.', ' ').split())
            key = (row['Flange Type'].strip(), row['Class / Table'].strip(), size)
            if key in seen:
                raise ValueError(f'Duplicate dataset key: {key}')
            seen.add(key)
            actual = tuple(row[f].strip() for f in fields)
            record = {'csv_line': line, 'key': key, 'actual': actual}
            if key not in expected:
                unsupported.append(record)
                continue
            values, page = expected[key]
            record.update(catalogue=values, page=page)
            (matches if actual == values else conflicts).append(record)
    if len(seen) != 239:
        raise ValueError(f'Expected 239 MaxiProfile rows in supplied revision, found {len(seen)}')
    return {'family': 'Klinger MaxiProfile Gasket', 'page_counts': page_counts,
            'catalogue_rows': len(expected), 'dataset_rows': len(seen),
            'matched_rows': len(matches), 'matched_records': matches,
            'conflicts': conflicts, 'unsupported_keys': unsupported,
            'catalogue_only_keys': sorted(set(expected) - seen),
            'catalogue_sha256': hashlib.sha256(catalogue.read_bytes()).hexdigest(),
            'dataset_sha256': hashlib.sha256(dataset.read_bytes()).hexdigest(),
            'interpretation': 'Historical numeric tuple agreement only. Component meanings, style, materials, thickness and exact article identity remain unverified.'}


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
    print(json.dumps({k: result[k] for k in ('family', 'page_counts', 'catalogue_rows',
                                          'dataset_rows', 'matched_rows')}, indent=2))
    print(json.dumps({k: result[k] for k in ('conflicts', 'unsupported_keys', 'catalogue_only_keys')}, indent=2))
    return bool(result['conflicts'] or result['unsupported_keys'] or result['catalogue_only_keys'])


if __name__ == '__main__':
    raise SystemExit(main())
