#!/usr/bin/env python3
"""Compare supplied Maxiflex ASME B16.5 tuples with catalogue page 52.

Requires pypdf; operates read-only and never assigns component meanings.
"""

import argparse
import csv
import json
import re
from pathlib import Path

from pypdf import PdfReader


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalogue", type=Path, required=True)
    parser.add_argument("--dataset", type=Path, required=True)
    args = parser.parse_args()
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
