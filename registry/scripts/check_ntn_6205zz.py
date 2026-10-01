"""Extract NTN's exact article page and quarantine conflicting source values."""
import argparse
import csv
import hashlib
import json
from decimal import Decimal
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SHA = '9C1EE760F042A1A6AAE56E1DEC21AD35A9817F66ADBDE3B1FBA86D5FD12B3F9D'
PATH = ROOT / 'registry/artifacts/ntn/6205zz-20261001.html'


class Parser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.rows, self.row, self.capture, self.value = [], None, None, None
        self.illustration_lines = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'tr' and a.get('itemprop') == 'additionalProperty':
            self.row = {'name': [], 'values': [], 'html_line': self.getpos()[0]}
        elif self.row is not None and tag == 'a' and a.get('data-imageasset') == '6205ZZ':
            self.row['illustration'] = True
        elif self.row is not None and tag == 'td' and a.get('itemprop') == 'name':
            self.capture = 'name'
        elif self.row is not None and tag == 'span' and a.get('itemprop') == 'value':
            self.value = {'measure': a.get('data-measure'), 'text': []}
            self.capture = 'value'

    def handle_data(self, text):
        if self.row is not None and self.capture == 'name':
            self.row['name'].append(text)
        elif self.capture == 'value' and self.value is not None:
            self.value['text'].append(text)

    def handle_endtag(self, tag):
        if tag == 'td' and self.capture == 'name':
            self.capture = None
        elif tag == 'span' and self.capture == 'value':
            self.value['text'] = ' '.join(''.join(self.value['text']).split())
            self.row['values'].append(self.value)
            self.value = None
            self.capture = None
        elif tag == 'tr' and self.row is not None:
            self.row['name'] = ' '.join(''.join(self.row['name']).split())
            if not self.row['name'] and not self.row['values'] and self.row.get('illustration'):
                self.illustration_lines.append(self.row['html_line'])
                self.row = None
                return
            if not self.row['name'] or not self.row['values']:
                raise ValueError('Empty native property row: ' + repr(self.row))
            self.rows.append(self.row)
            self.row = None


def parse(text):
    if '<h1>Item # 6205ZZ</h1>' not in text or '<span itemprop="sku">6205ZZ</span>' not in text or 'Single Row Radial Ball Bearing - Double Shielded' not in text:
        raise ValueError('Exact manufacturer article context changed')
    p = Parser()
    p.feed(text)
    if len(p.rows) != 26 or len({r['name'] for r in p.rows}) != 26 or len(p.illustration_lines) != 1:
        raise ValueError('Native property scope or uniqueness changed')
    return p.rows


def build_report():
    raw = PATH.read_bytes()
    if hashlib.sha256(raw).hexdigest().upper() != SHA:
        raise ValueError('NTN source revision changed')
    rows = parse(raw.decode('utf-8-sig'))
    by_name = {r['name']: r for r in rows}
    static = by_name['Static Load Rating']['values']
    if static != [{'measure': 'imperial', 'text': '1760 lbf'},
                  {'measure': 'metric', 'text': '7850 N'},
                  {'measure': 'metric', 'text': '11.60 kN'}]:
        raise ValueError('Static source displays changed; inspect before updating discrepancy')
    # Both metric cells are retained. No preferred corrected rating is chosen.
    values_n = [Decimal('7850'), Decimal('11.60') * 1000]
    dimension_fields = {}
    for label in ('d', 'D', 'B'):
        metric = [v['text'] for v in by_name[label]['values'] if v['measure'] == 'metric']
        if len(metric) != 1 or not metric[0].endswith(' mm'):
            raise ValueError('Ambiguous metric boundary dimension')
        number = Decimal(metric[0][:-3])
        if not number.is_finite() or number <= 0:
            raise ValueError('Invalid boundary dimension')
        dimension_fields[label] = str(number)
    return {'source_id': 'SRC-NTN-6205ZZ', 'source_sha256': SHA,
            'manufacturer_article': '6205ZZ', 'manufacturer_namespace': 'NTN',
            'native_property_count': len(rows), 'native_properties': rows,
            'metric_boundary_dimensions_mm': dimension_fields,
            'quality_findings': [{'issue_type': 'inconsistent_static_load_metric_units',
                'source_html_line': by_name['Static Load Rating']['html_line'],
                'retained_displays': static, 'metric_values_converted_to_n': [str(v) for v in values_n],
                'difference_n': str(abs(values_n[1] - values_n[0])), 'priority': 'P2',
                'corrected_value': None, 'rating_trusted': False},
                {'issue_type': 'ambiguous_da_max_values',
                 'source_html_line': by_name['da max']['html_line'],
                 'retained_displays': by_name['da max']['values'], 'corrected_value': None}],
            'limitations': ['Manufacturer-specific article number is not a cross-brand identity.',
                'Round bore does not prove cylindrical rather than tapered bore.',
                'Double Shielded does not explicitly prove non-contact metal shielding.',
                'Grease limiting speed does not establish the supplied grease formulation.',
                'No integral-locating-feature absence is inferred from a plain designation.',
                'Static rating and da max remain quarantined research facts, not trusted normalized values.',
                'Automatic extraction fidelity remains independently unreviewed.'],
            'identity_approved': False}


def verify_seed_bindings(report):
    """Bind the permitted ingestion to native fields; reject quarantined ingestion."""
    def read(name):
        with (ROOT / 'registry/data' / name).open(encoding='utf-8-sig', newline='') as handle:
            return list(csv.DictReader(handle))
    observations = [r for r in read('observations.csv')
                    if r['observation_id'] == 'OBS-NTN-6205ZZ-20261001']
    if len(observations) != 1 or observations[0]['source_id'] != report['source_id'] or observations[0]['raw_payload_sha256'] != SHA or observations[0]['manufacturer_part_id'] != 'MP-NTN-6205ZZ' or observations[0]['review_state'] != 'unreviewed':
        raise ValueError('NTN observation custody or review state changed')
    parts = [r for r in read('manufacturer-parts.csv') if r['manufacturer_part_id'] == 'MP-NTN-6205ZZ']
    if len(parts) != 1 or parts[0]['manufacturer_id'] != 'ORG-NTN-AMERICAS' or parts[0]['manufacturer_part_number'] != '6205ZZ':
        raise ValueError('NTN manufacturer namespace changed')
    by_name = {r['name']: r['values'] for r in report['native_properties']}
    def value(name, measure=None):
        values = [v['text'] for v in by_name[name] if measure is None or v['measure'] == measure]
        if len(values) != 1:
            raise ValueError('Ambiguous permitted source value: ' + name)
        return values[0]
    expected = {
        'PROP-BEARING-GEOMETRY': (value('Type') + '; Single Row Radial Ball Bearing', 'single_row_deep_groove_ball', '', ''),
        'PROP-BEARING-CLOSURE': (value('Enclosure'), '', '', ''),
        'PROP-RADIAL-INTERNAL-CLEARANCE': (value('Radial Internal Clearance'), 'cn', '', ''),
        'PROP-BEARING-TOLERANCE-CLASS': (value('Precision'), '', '', ''),
        'PROP-CAGE-CONSTRUCTION': ('Cage Type ' + value('Cage Type') + '; Cage Material ' + value('Cage Material'), 'pressed_steel', '', ''),
        'PROP-BEARING-MATERIAL': (value('Material'), '', '', ''),
        'PROP-LIMITING-SPEED-GREASE': (value('Limiting Speed - Grease'), '', '13000', 'UNIT-RPM'),
        'PROP-MASS': (value('Weight', 'metric'), '', '0.127', 'UNIT-KG'),
    }
    for label, prop in [('d', 'PROP-BORE-DIAMETER'), ('D', 'PROP-OUTSIDE-DIAMETER'), ('B', 'PROP-BEARING-WIDTH')]:
        expected[prop] = (label + ' ' + value(label, 'metric'), '', report['metric_boundary_dimensions_mm'][label], 'UNIT-MM')
    rows = [r for r in read('specification-values.csv') if r['observation_id'] == observations[0]['observation_id']]
    actual = {r['property_id']: tuple(r[f] for f in ('raw_value', 'normalized_text', 'normalized_number', 'unit_id')) for r in rows}
    if len(rows) != 11 or actual != expected:
        raise ValueError('NTN specification ingestion differs from source or includes quarantined fields')
    return len(rows)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--write-snapshot', action='store_true')
    args = p.parse_args()
    report = build_report()
    verify_seed_bindings(report)
    path = ROOT / 'registry/reports/ntn-6205zz-source.json'
    if args.write_snapshot:
        path.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    elif json.loads(path.read_text(encoding='utf-8')) != report:
        raise ValueError('NTN source snapshot stale or altered')
    print(f"NTN 6205ZZ: {report['native_property_count']} native property rows retained; source discrepancies not corrected or approved.")
