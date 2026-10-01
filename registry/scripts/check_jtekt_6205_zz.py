"""Reproduce exact JTEKT 6205 ZZ article fields and conservative seed intake."""
import argparse
import csv
import hashlib
import json
import re
from decimal import Decimal
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PATH = ROOT / 'registry/artifacts/jtekt/6205-ZZ-20261001.html'
SHA = '900D5F9E0ECA6275769BA774B7C2326353052BD8E032C0916A865306546A5230'
SOURCE = 'SRC-JTEKT-6205-ZZ'
PART = 'MP-JTEKT-6205-ZZ'
OBS = 'OBS-JTEKT-6205-ZZ-20261001'
SOURCE_URL = 'https://koyo.jtekt.co.jp/en/products/detail/?pno=6205+ZZ'
EXPECTED = [('d', '25 mm'), ('D', '52 mm'), ('B', '15 mm'), ('r(min.)', '1 mm'),
    ('Basic load ratings : Cr', '17.5 kN'), ('Basic load ratings : C0r', '7.85 kN'),
    ('Fatigue load limit : Cu', '0.550 kN'), ('factor : f0', '13.9'),
    ('Limiting speeds(Grease lub.)', '13000 min-1'), ('da(min.)', '30 mm'),
    ('da(max.)', '31.5 mm'), ('Da(max.)', '47 mm'), ('ra(max.)', '1 mm'),
    ('Mass(Refer.)', '0.128 kg')]


class Parser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.rows = []
        self.row = None
        self.capture = None
        self.headings = []
        self.contexts = []
        self.context = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        classes = attrs.get('class', '').split()
        if tag == 'h1' and 'page_ttl' in classes:
            self.context = {'tag': tag, 'text': [], 'html_line': self.getpos()[0], 'kind': 'heading'}
        elif tag == 'p' and 'page_text' in classes:
            self.context = {'tag': tag, 'text': [], 'html_line': self.getpos()[0], 'kind': 'context'}
        if tag == 'dl' and 'conf_input' in classes:
            if self.row is not None:
                raise ValueError('Nested native JTEKT field')
            self.row = {'name': [], 'value': [], 'html_line': self.getpos()[0],
                        'ordinal': len(self.rows) + 1}
        elif self.row is not None and tag in {'dt', 'dd'}:
            self.capture = 'name' if tag == 'dt' else 'value'

    def handle_data(self, text):
        if self.row is not None and self.capture:
            self.row[self.capture].append(text)
        if self.context:
            self.context['text'].append(text)

    def handle_endtag(self, tag):
        if self.context and tag == self.context['tag']:
            self.context['text'] = ' '.join(''.join(self.context['text']).split())
            (self.headings if self.context['kind'] == 'heading' else self.contexts).append(self.context)
            self.context = None
        if self.row is not None and tag in {'dt', 'dd'}:
            self.capture = None
        elif self.row is not None and tag == 'dl':
            for key in ('name', 'value'):
                self.row[key] = ' '.join(''.join(self.row[key]).split())
                if not self.row[key]:
                    raise ValueError('Empty native JTEKT field')
            self.rows.append(self.row)
            self.row = None


def parse(html):
    parser = Parser()
    parser.feed(html)
    if len(parser.headings) != 1 or parser.headings[0]['text'] != '6205 ZZ':
        raise ValueError('JTEKT exact article heading changed')
    context = 'Deep groove ball bearings - Single-row - Shielded/sealed type - Shielded ZZ'
    if not parser.contexts or parser.contexts[0]['text'] != context:
        raise ValueError('JTEKT exact article construction context changed')
    if parser.row is not None or len(parser.rows) != 14 or [(r['name'], r['value']) for r in parser.rows] != EXPECTED:
        raise ValueError('JTEKT native field scope/value/order changed')
    if len({r['name'] for r in parser.rows}) != 14:
        raise ValueError('Duplicate JTEKT field; case-sensitive symbols required')
    return parser


def numeric(value, unit):
    match = re.fullmatch(r'(\d+(?:\.\d+)?)' + (' ' + re.escape(unit) if unit else ''), value)
    if match is None:
        raise ValueError('Invalid or ambiguous JTEKT numeric field/unit')
    number = Decimal(match[1])
    if not number.is_finite() or number <= 0:
        raise ValueError('Invalid JTEKT positive numeric value')
    return str(number)


def build_report():
    raw = PATH.read_bytes()
    if hashlib.sha256(raw).hexdigest().upper() != SHA:
        raise ValueError('JTEKT source revision changed')
    parsed = parse(raw.decode('utf-8-sig'))
    by_name = {r['name']: r for r in parsed.rows}
    return {'source_id': SOURCE, 'artifact_id': 'ART-JTEKT-6205-ZZ', 'source_sha256': SHA,
        'manufacturer_namespace': 'JTEKT', 'brand': 'Koyo', 'manufacturer_article': '6205 ZZ',
        'heading': parsed.headings[0], 'construction_context': parsed.contexts[0],
        'native_property_count': len(parsed.rows), 'native_properties': parsed.rows,
        'metric_boundary_dimensions_mm': {label: numeric(by_name[label]['value'], 'mm') for label in ('d', 'D', 'B')},
        'mounting_symbol_values_mm': {label: numeric(by_name[label]['value'], 'mm') for label in ('da(min.)', 'da(max.)', 'Da(max.)', 'ra(max.)')},
        'ingestion_policy': 'jtekt-exact-article-intake-0.1', 'identity_approved': False,
        'limitations': ['Nine facts ingested as unreviewed exact-article research; fourteen native numeric fields retained.',
            'Shielded ZZ is retained raw; contact form, metal construction and sidedness are not canonically inferred.',
            'Bore type, cage, clearance, tolerance, material, supplied lubricant and locating evidence are absent.',
            'Grease limiting speed does not establish supplied grease or formulation.',
            'Mounting dimensions and mass are source reference values, not measured article identity.',
            'Cr/C0r calculation standards and basis are not stated on this page.',
            'No suffix absence, CAD drawing image or product calculator supplies missing identity facts.',
            'Independent transcription review and publisher reuse terms remain outstanding.',
            'JTEKT values cannot correct or resolve NTN manufacturer publication findings.']}


def verify_seed_bindings(report):
    def read(name):
        with (ROOT / 'registry/data' / name).open(encoding='utf-8-sig', newline='') as handle:
            return list(csv.DictReader(handle))
    if report['source_id'] != SOURCE or report['source_sha256'] != SHA or report['manufacturer_article'] != '6205 ZZ' or report['manufacturer_namespace'] != 'JTEKT' or report['identity_approved'] is not False:
        raise ValueError('JTEKT source report scope changed')
    sources = [r for r in read('source-register.csv') if r['source_id'] == SOURCE]
    if len(sources) != 1 or sources[0]['publisher_name'] != 'JTEKT Corporation' or sources[0]['source_url'] != SOURCE_URL or sources[0]['ingestion_status'] != 'reference_only':
        raise ValueError('JTEKT registered primary source changed')
    observations = [r for r in read('observations.csv') if r['observation_id'] == OBS]
    if len(observations) != 1 or observations[0]['manufacturer_part_id'] != PART or observations[0]['source_id'] != SOURCE or observations[0]['raw_payload_sha256'] != SHA or observations[0]['review_state'] != 'unreviewed':
        raise ValueError('JTEKT observation custody/review changed')
    parts = [r for r in read('manufacturer-parts.csv') if r['manufacturer_part_id'] == PART]
    if len(parts) != 1 or parts[0]['manufacturer_id'] != 'ORG-JTEKT' or parts[0]['manufacturer_part_number'] != '6205 ZZ' or parts[0]['profile_id'] != 'PROFILE-BEARING-DGBB-1R-DOUBLE-METAL-SHIELD-0.1':
        raise ValueError('JTEKT article manufacturer namespace changed')
    artifacts = [r for r in read('source-artifacts.csv') if r['artifact_id'] == report['artifact_id']]
    if len(artifacts) != 1 or artifacts[0]['source_id'] != SOURCE or artifacts[0]['artifact_url'] != SOURCE_URL or artifacts[0]['sha256'] != SHA or artifacts[0]['retrieval_state'] != 'retrieved' or artifacts[0]['local_path'] != 'registry/artifacts/jtekt/6205-ZZ-20261001.html':
        raise ValueError('JTEKT source artifact custody changed')
    values = {r['name']: r['value'] for r in report['native_properties']}
    expected = {'PROP-BEARING-GEOMETRY': ('Deep groove ball bearings - Single-row', 'single_row_deep_groove_ball', '', ''),
        'PROP-BEARING-CLOSURE': ('Shielded ZZ', '', '', '')}
    for label, prop, unit, unit_id in [('d', 'PROP-BORE-DIAMETER', 'mm', 'UNIT-MM'),
        ('D', 'PROP-OUTSIDE-DIAMETER', 'mm', 'UNIT-MM'), ('B', 'PROP-BEARING-WIDTH', 'mm', 'UNIT-MM'),
        ('Basic load ratings : Cr', 'PROP-BASIC-DYNAMIC-LOAD-RATING', 'kN', 'UNIT-N'),
        ('Basic load ratings : C0r', 'PROP-BASIC-STATIC-LOAD-RATING', 'kN', 'UNIT-N'),
        ('Limiting speeds(Grease lub.)', 'PROP-LIMITING-SPEED-GREASE', 'min-1', 'UNIT-RPM'),
        ('Mass(Refer.)', 'PROP-MASS', 'kg', 'UNIT-KG')]:
        number = numeric(values[label], unit)
        if unit == 'kN':
            number = str(Decimal(number) * 1000)
        expected[prop] = (label + ' ' + values[label], '', number, unit_id)
    rows = [r for r in read('specification-values.csv') if r['observation_id'] == OBS]
    actual = {r['property_id']: tuple(r[f] for f in ('raw_value', 'normalized_text', 'normalized_number', 'unit_id')) for r in rows}
    if len(rows) != 9 or actual != expected:
        raise ValueError('JTEKT ingestion differs from native source or infers absent fields')
    protected_qualifiers = {
        'PROP-BEARING-CLOSURE': 'No canonical contact/material/sidedness mapping without manufacturer definition',
        'PROP-BASIC-DYNAMIC-LOAD-RATING': 'Manufacturer article value; kN converted to N; standard and calculation basis unstated',
        'PROP-BASIC-STATIC-LOAD-RATING': 'Manufacturer article value; kN converted to N; not a correction of NTN publication',
        'PROP-LIMITING-SPEED-GREASE': 'Speed under grease lubrication; supplied grease formulation not established',
        'PROP-MASS': 'Source reference mass; not measured supplied-item mass or identity evidence',
    }
    if any(r['property_id'] in protected_qualifiers and r['qualifier'] != protected_qualifiers[r['property_id']] for r in rows):
        raise ValueError('JTEKT source reference or non-inference qualifier changed')
    return len(rows)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write-snapshot', action='store_true')
    args = parser.parse_args()
    report = build_report()
    verify_seed_bindings(report)
    target = ROOT / 'registry/reports/jtekt-6205-ZZ-source.json'
    if args.write_snapshot:
        target.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    elif json.loads(target.read_text(encoding='utf-8')) != report:
        raise ValueError('JTEKT source snapshot stale or altered')
    print('JTEKT 6205 ZZ: 14 native fields retained; 9 unreviewed facts bound; no identity approval.')
