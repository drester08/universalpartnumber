"""Check narrow manually transcribed pipe observations against preserved CSV rows.

Checks internal transcription/dataset consistency, not live source truth or identity.
"""
import csv
import hashlib
import json
from pathlib import Path

from check_piping_tenaris import precision_compatible

ROOT = Path(__file__).resolve().parents[1]


def check():
    document = json.loads((ROOT / 'reports/pipe-independent-observations.json').read_text(encoding='utf-8'))
    with (ROOT / 'data/source-datasets.csv').open(encoding='utf-8-sig', newline='') as handle:
        dataset = next(r for r in csv.DictReader(handle) if r['dataset_id'] == document['dataset_id'])
    path = ROOT.parent / dataset['local_path']
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != dataset['sha256'].lower() or digest != document['dataset_sha256']:
        raise ValueError('Dataset revision mismatch')
    with (ROOT / 'data/source-register.csv').open(encoding='utf-8-sig', newline='') as handle:
        sources = {r['source_id'] for r in csv.DictReader(handle)}
    with path.open(encoding='utf-8-sig', newline='') as handle:
        rows = list(csv.DictReader(handle))
    seen, lines = set(), set()
    for observation in document['observations']:
        line = observation['csv_line']
        if type(line) is not int or not 2 <= line <= len(rows) + 1:
            raise ValueError('Out-of-range logical record')
        key = (observation['source_id'], line)
        if key in seen or key[0] not in sources or not observation['locator'].strip():
            raise ValueError('Duplicate or unregistered/unlocated observation')
        seen.add(key)
        lines.add(line)
        row = rows[line - 2]
        if row['Nominal Bore (mm)'] != observation['dn'] or row['Schedule Number'] != observation['schedule']:
            raise ValueError('Nominal key differs from supplied record')
        if not all(precision_compatible(row[column], observation[field]) for column, field in (
                ('Outside Diameter (mm)', 'od_mm'), ('Wall Thickness (mm)', 'wall_mm'))):
            raise ValueError('Nominal geometry differs from supplied record')
    return len(seen), len(lines)


if __name__ == '__main__':
    observations, rows = check()
    print(f'Corroboration consistency passed: {observations} observations across {rows} supplied records. Remote sources/transcription remain unreviewed; no identity approval.')
