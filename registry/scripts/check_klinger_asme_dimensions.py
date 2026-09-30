#!/usr/bin/env python3
"""Compare supplied Maxiflex tuples with historical catalogue tables.

Requires pypdf; operates read-only and never assigns component meanings.
"""

import argparse
import csv
import hashlib
import json
import re
from pathlib import Path

from pypdf import PdfReader


def compare_all(catalogue, dataset, report=None):
    reader = PdfReader(catalogue)
    expected = {}
    page_counts = {}
    for page in range(52, 60):
        text = reader.pages[page - 1].extract_text()
        if page <= 54:
            heading = r'Class (\d+) ASME B16\.20 to suit ASME (B16\.5|B16\.47 Series [AB]) fl\s*anges'
            sections = list(re.finditer(heading, text))
        elif page <= 56:
            sections = list(re.finditer(r'(?m)^PN(\d+)\s*$', text))
        else:
            sections = list(re.finditer(r'(?m)^Table ([A-Z])\s*$', text))
        count = 0
        for index, section in enumerate(sections):
            content = text[section.end():sections[index + 1].start() if index + 1 < len(sections) else len(text)]
            if page <= 54:
                flange = 'ASME ' + section[2] + ' Flanges'
                classification = 'Class ' + section[1]
            elif page <= 56:
                flange, classification = 'DIN Standard Flanges', 'PN' + section[1]
            else:
                flange, classification = 'BS 10 Standard Flanges', 'Table ' + section[1]
            nominal = r'(\d+(?:[.\s]+\d/\d)?|\d/\d)\s*[“”"]' if page not in (55, 56) else r'(\d+)'
            tuple_pattern = re.compile(nominal + r'\s+(\d+)\s*x\s*(\d+)\s*x\s*(\d+)(?:\s*x\s*(\d+))?')
            for match in tuple_pattern.finditer(content):
                size = ' '.join(match[1].replace('.', ' ').split())
                key = (flange, classification, size)
                if key in expected:
                    raise ValueError(f'Duplicate catalogue key: {key}')
                expected[key] = (tuple(match.group(i) or '' for i in range(2, 6)), page)
                count += 1
        page_counts[page] = count
    fields = ('Dimensions Outer Ring Dia (mm)', 'Dimensions Inner Ring Dia (mm)',
              'Dimensions Outer Ring Thk (mm)', 'Dimensions Inner Ring Thk (mm)')
    matched, conflicts, unsupported = 0, [], []
    seen = set()
    with dataset.open(encoding='utf-8-sig', newline='') as handle:
        for line, row in enumerate(csv.DictReader(handle), 2):
            if row['Description'] != 'Klinger Maxiflex Gasket':
                continue
            size = (row['Nominal Size (NB) Inch'] or row['Nominal Size (PN)']).strip().rstrip('“”"')
            key = (row['Flange Type'].strip(), row['Class / Table'].strip(), size)
            if key in seen:
                raise ValueError(f'Duplicate dataset key: {key}')
            seen.add(key)
            if key not in expected:
                unsupported.append({'csv_line': line, 'key': key})
                continue
            actual = tuple(row[f].strip() for f in fields)
            values, page = expected[key]
            if actual == values:
                matched += 1
            else:
                conflicts.append({'csv_line': line, 'key': key, 'actual': actual,
                                  'catalogue': values, 'page': page})
    result = {'page_counts': page_counts, 'catalogue_rows': len(expected),
              'dataset_rows': len(seen), 'matched_rows': matched, 'conflicts': conflicts,
              'unsupported_keys': unsupported, 'catalogue_only_keys': sorted(set(expected) - seen),
              'catalogue_sha256': hashlib.sha256(catalogue.read_bytes()).hexdigest(),
              'dataset_sha256': hashlib.sha256(dataset.read_bytes()).hexdigest(),
              'interpretation': 'Historical numeric tuple comparison only; component semantics and exact article identity remain unverified.'}
    expected_counts = {52: 95, 53: 80, 54: 66, 55: 120, 56: 61, 57: 124, 58: 108, 59: 20}
    if page_counts != expected_counts:
        raise ValueError(f'Catalogue extraction incomplete: {page_counts}')
    if len(seen) != 643:
        raise ValueError(f'Expected 643 Maxiflex rows in the supplied revision, found {len(seen)}')
    if report:
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'page_counts': page_counts, 'catalogue_rows': len(expected),
                      'dataset_rows': len(seen), 'matched_rows': matched,
                      'conflict_rows': len(conflicts), 'unsupported_rows': len(unsupported),
                      'catalogue_only_rows': len(set(expected) - seen),
                      'conflicts_by_class': {classification: sum(r['key'][1] == classification for r in conflicts)
                                             for classification in sorted({r['key'][1] for r in conflicts})}}, indent=2))
    return bool(conflicts or unsupported)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalogue", type=Path, required=True)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--all-tables", action="store_true", help="Compare Maxiflex catalogue pages 52–59")
    parser.add_argument("--report", type=Path, help="Save detailed all-table JSON evidence")
    args = parser.parse_args()
    if args.report and not args.all_tables:
        parser.error('--report requires --all-tables')
    if args.all_tables:
        return compare_all(args.catalogue, args.dataset, args.report)
    text = PdfReader(args.catalogue).pages[51].extract_text()
    classes = re.split(r"Class (\d+) ASME B16\.20", text)
    expected = {}
    pattern = re.compile(
        r'(\d+(?:\s+\d/\d)?|\d/\d)\s*[“”"]\s+'
        r'(\d+)\s*x\s*(\d+)\s*x\s*(\d+)\s*x\s*(\d+)'
    )
    for index in range(1, len(classes), 2):
        pressure_class, section = classes[index:index + 2]
        for match in pattern.finditer(section):
            size = " ".join(match[1].split())
            key = ("Class " + pressure_class, size)
            if key in expected:
                raise ValueError(f"Duplicate catalogue key: {key}")
            expected[key] = tuple(match.group(i) for i in range(2, 6))
    if len(expected) != 95:
        raise ValueError(f"Expected 95 rows on catalogue page 52, extracted {len(expected)}")
    fields = (
        "Dimensions Outer Ring Dia (mm)",
        "Dimensions Inner Ring Dia (mm)",
        "Dimensions Outer Ring Thk (mm)",
        "Dimensions Inner Ring Thk (mm)",
    )
    matches, conflicts, missing = [], [], []
    seen = set()
    with args.dataset.open(encoding="utf-8-sig", newline="") as handle:
        for line, row in enumerate(csv.DictReader(handle), 2):
            if row["Description"] != "Klinger Maxiflex Gasket":
                continue
            if row["Flange Type"].strip() != "ASME B16.5 Flanges":
                continue
            key = (row["Class / Table"].strip(), row["Nominal Size (NB) Inch"].strip().rstrip('"'))
            if key not in expected:
                missing.append({"csv_line": line, "key": key})
                continue
            if key in seen:
                raise ValueError(f"Duplicate dataset key in compared scope: {key}")
            seen.add(key)
            actual = tuple(row[field].strip() for field in fields)
            record = {"csv_line": line, "key": key, "actual": actual, "catalogue": expected[key]}
            (matches if actual == expected[key] else conflicts).append(record)
    absent = sorted(set(expected) - seen)
    print(json.dumps({"catalogue_page": 52, "catalogue_rows": len(expected),
                      "matched_rows": len(matches), "conflicts": conflicts,
                      "missing_catalogue_keys": absent,
                      "outside_page_scope": missing}, indent=2))
    return bool(conflicts or absent)


if __name__ == "__main__":
    raise SystemExit(main())
