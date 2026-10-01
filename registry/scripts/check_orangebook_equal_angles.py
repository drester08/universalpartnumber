"""Reproduce manufacturer nominal geometry screening without article approval."""
import argparse
import hashlib
import json
import re
from collections import Counter
from decimal import Decimal
from html.parser import HTMLParser
from pathlib import Path
from check_macsteel_angle_coverage import build_report as prior_coverage, key

ROOT = Path(__file__).resolve().parents[2]
SOURCE_ID = 'SRC-AM-ORANGEBOOK-EQUAL-ANGLES'
URL = 'https://orangebook.arcelormittal.com/node/220'
SHA = '26C8D7ED30A84135A914E22C6A689E51B5628EAB0A9442429AB50971E4B498DF'
ARTIFACT = ROOT / 'registry/artifacts/arcelormittal/orangebook-equal-angle-node220.html'


class TableParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tables, self.active, self.row, self.cell = [], False, None, None
        self.body = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'table':
            self.active = 'table-data' in attrs.get('class', '').split()
            if self.active:
                self.tables.append([])
        elif self.active and tag == 'tbody':
            self.body = True
        elif self.active and tag == 'tr':
            self.row = []
        elif self.active and tag in ('td', 'th'):
            if self.body and any(attrs.get(k, '1') != '1' for k in ('rowspan', 'colspan')):
                raise ValueError('Unsupported body cell span; do not shift columns')
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
        elif tag == 'tbody':
            self.body = False
        elif tag == 'table':
            self.active = False


def parse(text):
    if 'Equal leg angles - L - S355 - 1. Section properties' not in text:
        raise ValueError('Manufacturer family/grade context changed')
    parser = TableParser()
    parser.feed(text)
    if len(parser.tables) != 1 or len(parser.tables[0]) != 197:
        raise ValueError('Manufacturer table scope changed')
    table = parser.tables[0]
    if (table[1][:6] != ['Size', 'Thickness', '', 'Mass per metre', 'Radius', 'Distance to centroid']
            or table[2][4:7] != ['Root', 'Toe', '']
            or table[3][:7] != ['h x h', 't', '', '', 'r1', 'r2', 'c']
            or table[4] != ['mm', 'mm', '', 'kg/m', 'mm', 'mm', 'cm', 'cm4', 'cm4',
                             'cm4', 'cm', 'cm', 'cm', 'cm3', 'cm4', '', 'cm2']):
        raise ValueError('Manufacturer headers/units changed')
    facts, seen, size, size_row = [], set(), None, None
    for row_number, cells in enumerate(table[5:], 1):
        if len(cells) != 17 or cells[2] != '':
            raise ValueError('Malformed manufacturer data row')
        if cells[0]:
            match = re.fullmatch(r'(\d+)x(\d+)', cells[0])
            if not match or match[1] != match[2]:
                raise ValueError('Invalid equal-leg size')
            size, size_row = match.groups(), row_number
        if size is None:
            raise ValueError('Blank size without preceding designation')
        # Only size inherits from a labelled group; missing measurements never do.
        fields = dict(zip(('thickness_mm', 'mass_kg_per_m', 'root_radius_mm',
                           'toe_radius_mm', 'centroid_distance_cm'),
                          (cells[1], *cells[3:7])))
        for value in fields.values():
            if not re.fullmatch(r'\d+(?:\.\d+)?', value) or Decimal(value) <= 0:
                raise ValueError('Missing or invalid nominal measurement')
        fact = {'leg_a_mm': size[0], 'leg_b_mm': size[1], **fields,
                'source_id': SOURCE_ID, 'source_grade_context': 'S355',
                'html_table': 1, 'html_data_row': row_number,
                'designation_data_row': size_row, 'raw_size_cell': cells[0],
                'measurement_columns': {'thickness_mm': 2, 'mass_kg_per_m': 4,
                    'root_radius_mm': 5, 'toe_radius_mm': 6, 'centroid_distance_cm': 7}}
        if key(fact) in seen:
            raise ValueError('Duplicate nominal geometry key')
        seen.add(key(fact))
        facts.append(fact)
    return facts


def screen(offer, facts):
    candidates = [f for f in facts if key(f) == tuple(Decimal(v) for v in offer['nominal_geometry_mm'])]
    return {'seller_sku': offer['seller_sku'], 'nominal_geometry_mm': offer['nominal_geometry_mm'],
            'seller_grade_statement': offer['raw_grade_statement'],
            'earlier_context_outcome': offer['outcome'],
            'outcome': 'nominal_geometry_candidate' if len(candidates) == 1 else 'no_geometry_candidate',
            'manufacturer_catalogue_candidates': candidates,
            'seller_table_mass_comparisons': [
                {'seller_pdf_table': s['pdf_table'], 'seller_mass_kg_per_m': s['mass_kg_per_m'],
                 'manufacturer_mass_kg_per_m': f['mass_kg_per_m'],
                 'exact_displayed_values_agree': Decimal(s['mass_kg_per_m']) == Decimal(f['mass_kg_per_m'])}
                for s in offer['same_context_candidates'] for f in candidates],
            'seller_article_manufacturer_verified': False, 'exact_grade_verified': False,
            'delivery_condition_verified': False, 'exact_article_verified': False,
            'identity_approved': False, 'earlier_context_gap_closed': False}


def build_report():
    raw = ARTIFACT.read_bytes()
    if hashlib.sha256(raw).hexdigest().upper() != SHA:
        raise ValueError('Manufacturer artifact revision changed')
    facts = parse(raw.decode('utf-8'))
    prior = prior_coverage()
    path = ROOT / 'registry/reports/macsteel-angle-coverage.json'
    if json.loads(path.read_text(encoding='utf-8')) != prior:
        raise ValueError('Prior supplier coverage report no longer reproduces')
    records = [screen(o, facts) for o in prior['records']]
    gap_records = [r for r in records if r['earlier_context_outcome'] == 'source_context_gap']
    offer_keys = {tuple(Decimal(v) for v in r['nominal_geometry_mm']) for r in records}
    return {'report_date': '2026-10-01', 'source_url': URL, 'source_sha256': SHA,
            'source_grade_context': 'S355', 'source_facts': facts,
            'source_fact_count': len(facts), 'supplier_offer_count': len(records),
            'parent_report_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
            'outcome_counts': dict(Counter(r['outcome'] for r in records)),
            'earlier_gap_outcome_counts': dict(Counter(r['outcome'] for r in gap_records)),
            'records': records, 'earlier_gap_records': gap_records,
            'source_only_facts': [f for f in facts if key(f) not in offer_keys],
            'identity_approved': False,
            'limitations': ['Nominal design-table facts are not current saleable manufacturer articles.',
                'S355 does not establish S355JR or JR+AR for any captured seller offer.',
                'ArcelorMittal publication does not prove that ArcelorMittal made the seller stock.',
                'Displayed mass differences are retained, not automatically classified as physical conflicts.',
                'Absent sizes mean absent from this table, not globally unavailable.',
                'Lengths, tolerances, production route and certificates remain unverified.',
                'Automatic extraction fidelity is not independently reviewed.',
                'Reuse licensing remains subject to review; no raw manufacturer HTML is published.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write-snapshot', action='store_true')
    args = parser.parse_args()
    report = build_report()
    path = ROOT / 'registry/reports/orangebook-equal-angle-screening.json'
    if args.write_snapshot:
        path.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    elif json.loads(path.read_text(encoding='utf-8')) != report:
        raise ValueError('Manufacturer screening snapshot stale or altered')
    print(f"{report['source_fact_count']} manufacturer facts; {report['outcome_counts']}; earlier gaps: {report['earlier_gap_outcome_counts']}. No approval.")
