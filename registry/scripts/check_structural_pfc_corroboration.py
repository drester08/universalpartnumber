"""Compare source-specific PFC nominal values without merging articles."""
import argparse
import csv
import hashlib
import json
import re
from collections import Counter
from decimal import Decimal
from html.parser import HTMLParser
from pathlib import Path
from pypdf import PdfReader
from check_structural_pfc import compare as british_compare, screen
from check_structural_heavy import DATASET_SHA, FIELDS

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    'macsteel': ('SRC-MACSTEEL-PFC', 'macsteel/parallel-flange-channel-mar2021.pdf',
                '821403b9d527f3298feb15db08f09bf63a1ae82eeee011549a1fdcc97074ac18'),
    'orangebook': ('SRC-AM-ORANGEBOOK-PFC', 'arcelormittal/orangebook-pfc-node259.html',
                  '8ab616883fad0699993f9e9fabfea4a76d06aeeeaebadc74f96c5b02a47e70d8'),
}


def validate_observations(rows, expected):
    if len(rows) != expected:
        raise ValueError('Unexpected source row count')
    keys = set()
    for row in rows:
        key = tuple(Decimal(row[k]) for k in ('designation_height', 'designation_width'))
        values = [Decimal(row[k]) for k in FIELDS]
        if key in keys or any(not x.is_finite() or x <= 0 for x in (*key, *values)):
            raise ValueError('Invalid or duplicate source nominal key/value')
        keys.add(key)
    return rows


def extract_macsteel(path):
    pdf = PdfReader(path)
    if len(pdf.pages) != 1:
        raise ValueError('Unexpected Macsteel page count')
    text = pdf.pages[0].extract_text(extraction_mode='layout')
    headings = ['Size dimensions (mm)', 'Kg /m', 'Web dimensions (mm)',
                'Flange dimensions (mm)', 'Height (mm)', 'Width (mm)']
    header = next((x for x in text.splitlines() if 'Size dimensions (mm)' in x), '')
    if not all(h in header for h in headings) or [header.index(h) for h in headings] != sorted(header.index(h) for h in headings):
        raise ValueError('Unexpected Macsteel table headings')
    if 'SANS 50025 / EN 10025 S355JR' not in text:
        raise ValueError('Missing Macsteel grade context')
    rows = []
    for line in text.splitlines():
        if not re.match(r'^\s*\d+ x \d+\s', line):
            continue
        t = line.split()
        if len(t) != 8 or t[1] != 'x':
            raise ValueError('Malformed Macsteel table row')
        height, _, width, mass, web, flange, depth, b = t
        rows.append({'designation': f'{height} x {width}', 'designation_height': height,
                     'designation_width': width, 'mass_kg_per_m': mass, 'depth_mm': depth,
                     'width_mm': b, 'web_mm': web, 'flange_mm': flange,
                     'source_id': SOURCES['macsteel'][0], 'pdf_page': 1,
                     'source_grade_context': 'SANS 50025 / EN 10025 S355JR'})
    return validate_observations(rows, 6)


class NominalTableParser(HTMLParser):
    """Read only the explicitly identified table, preserving empty cells."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tables = []
        self.active = False
        self.row = None
        self.cell = None
    def handle_starttag(self, tag, attrs):
        if tag == 'table':
            classes = dict(attrs).get('class', '').split()
            self.active = 'table-data' in classes
            if self.active:
                self.tables.append([])
        elif self.active and tag == 'tr':
            self.row = []
        elif self.active and tag in ('td', 'th'):
            self.cell = []
    def handle_data(self, data):
        if self.active and self.cell is not None:
            self.cell.append(data)
    def handle_endtag(self, tag):
        if self.active and tag in ('td', 'th') and self.cell is not None:
            self.row.append(' '.join(''.join(self.cell).split()))
            self.cell = None
        elif self.active and tag == 'tr' and self.row is not None:
            self.tables[-1].append(self.row)
            self.row = None
        elif tag == 'table':
            self.active = False


def parse_orangebook(text):
    parser = NominalTableParser()
    parser.feed(text)
    if len(parser.tables) != 1 or len(parser.tables[0]) != 21:
        raise ValueError('Unexpected Orange Book table scope')
    table = parser.tables[0]
    if (table[1][2:5] != ['Mass per metre', 'Depth of section', 'Width of section']
            or table[2][5:7] != ['Web', 'Flange']
            or table[4][2:9] != ['kg/m', 'mm', 'mm', 'mm', 'mm', 'mm', 'mm']
            or table[4][11] != 'cm'
            or 'Is the distance from the centre of the web to the shear centre' not in text
            or 'PFC - S355' not in text):
        raise ValueError('Unexpected Orange Book field meanings/units')
    rows = []
    for index, cells in enumerate(table[5:], 1):
        if len(cells) != 30 or cells[1] != '':
            raise ValueError('Malformed Orange Book table row')
        match = re.fullmatch(r'(\d+)x(\d+)x(\d+)', cells[0])
        if not match:
            raise ValueError('Unexpected Orange Book designation')
        h, b, label = match.groups()
        fields = dict(zip(('mass_kg_per_m', 'depth_mm', 'width_mm', 'web_mm', 'flange_mm',
                           'root_radius_mm', 'depth_between_fillets_mm'), cells[2:9]))
        fields['shear_centre_distance_cm'] = cells[11]
        if any(not Decimal(v).is_finite() or Decimal(v) <= 0 for v in fields.values()):
            raise ValueError('Invalid Orange Book dimensions')
        rows.append({'designation': cells[0], 'designation_height': h, 'designation_width': b,
                     'designation_mass_label': label, **fields, 'source_id': SOURCES['orangebook'][0],
                     'html_table': 1, 'html_data_row': index, 'source_grade_context': 'S355'})
    return validate_observations(rows, 16)


def compare():
    observations = {}
    for name, (_, relative, sha) in SOURCES.items():
        path = ROOT / 'artifacts' / relative
        if hashlib.sha256(path.read_bytes()).hexdigest() != sha:
            raise ValueError('PFC corroboration source revision mismatch')
        observations[name] = extract_macsteel(path) if name == 'macsteel' else parse_orangebook(path.read_text(encoding='utf-8'))
    dataset = ROOT / 'artifacts/user-reference-csvs/Structural Steel - Rev01 - 02 July 2026.csv'
    if hashlib.sha256(dataset.read_bytes()).hexdigest() != DATASET_SHA:
        raise ValueError('PFC corroboration dataset revision mismatch')
    prior_path = ROOT / 'reports/structural-pfc-comparison.json'
    prior = json.loads(prior_path.read_text(encoding='utf-8'))
    if prior != british_compare():
        raise ValueError('Stale earlier British PFC evidence')
    with dataset.open(encoding='utf-8-sig', newline='') as f:
        rows = list(csv.DictReader(f))
    if len(rows) != 805:
        raise ValueError('Unexpected dataset scope')
    records, outside = [], []
    earlier = {x['csv_line']: x for x in prior['records']}
    for line, row in enumerate(rows, 2):
        if row['Type/Section/Channels/Angle/Bars/UC/I-Beams'] != 'Parallel Flange':
            outside.append(line)
            continue
        records.append({'csv_line': line, 'source_screens': {name: screen(row, values) for name, values in observations.items()},
                        'british_screen': earlier[line], 'exact_article_verified': False})
    if len(records) != 6 or len(outside) != 799:
        raise ValueError('Unexpected supplied PFC family scope')
    return {'dataset_sha256': DATASET_SHA, 'dataset_rows': 805, 'selected_rows': 6,
            'source_sha256': {name: values[2] for name, values in SOURCES.items()},
            'earlier_report_sha256': hashlib.sha256(prior_path.read_bytes()).hexdigest(),
            'source_observations': observations, 'outside_family_scope_csv_lines': outside, 'records': records,
            'outcomes': {name: dict(Counter(x['source_screens'][name]['outcome'] for x in records)) for name in SOURCES},
            'limitations': ['Source-specific nominal candidate screening, not same-item or substitution approval.',
                            'Macsteel PDF fully rendered/reviewed; extraction fidelity independently unreviewed.',
                            'Orange Book shear-centre distance is not the British centroid-distance property.',
                            'Macsteel grade context S355JR and Orange Book S355 are not automatically equated.',
                            'Distinct publishers do not prove independent upstream geometry lineage.',
                            'Earlier British conflicts and selected-table coverage gaps remain open.',
                            'No source-defined manufacturer article number or current availability verified.',
                            'New corroboration report not yet integrated into generic findings.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write-snapshot', action='store_true')
    args = parser.parse_args()
    result = compare()
    content = json.dumps(result, indent=2) + '\n'
    path = ROOT / 'reports/structural-pfc-corroboration.json'
    if args.write_snapshot:
        path.write_text(content, encoding='utf-8', newline='')
    elif path.read_text(encoding='utf-8') != content:
        raise ValueError('Stale PFC corroboration snapshot')
    print(f"PFC corroboration: {result['outcomes']}. No identity approval.")
