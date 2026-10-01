"""Retain JTEKT code-table categories without over-promoting partial closure."""
import argparse
import csv
import hashlib
import json
from html.parser import HTMLParser
from pathlib import Path
import check_jtekt_6205_zz

ROOT = Path(__file__).resolve().parents[2]
PATH = ROOT / 'registry/artifacts/jtekt/bearing-number-20261001.html'
SHA = 'ED41FF7A2565FF8B1DA23FED6B34379D1E9B73F7C6D1238F13B390020C5E6A9F'
EXPECTED = [
    ('(Shield)', 'Z', 'one side Fixed shield'), ('(Shield)', 'ZZ', 'both sides Fixed shield'),
    ('(Shield)', 'ZX', 'one side Removable shield'), ('(Shield)', 'ZZX', 'both sides Removable shield'),
    ('(Non-contact seal)', 'RU', 'one side'), ('(Non-contact seal)', '2RU', 'both sides'),
    ('(Non-contact seal)', 'ZU', 'one side'), ('(Non-contact seal)', '2ZU', 'both sides'),
    ('(Contact seal)', 'RS', 'one side'), ('(Contact seal)', '2RS', 'both sides'),
    ('(Contact seal)', 'RK', 'one side'), ('(Contact seal)', '2RK', 'both sides'),
    ('(Contact seal)', 'U', 'one side'), ('(Contact seal)', 'UU', 'both sides'),
    ('(Extremely light contact seal)', 'RD', 'one side'),
    ('(Extremely light contact seal)', '2RD', 'both sides')]


class Tables(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack, self.tables = [], []

    def handle_starttag(self, tag, attrs):
        if tag == 'table':
            self.stack.append({'html_line': self.getpos()[0], 'rows': [], 'row': None, 'cell': None})
        elif self.stack:
            table = self.stack[-1]
            if tag == 'tr':
                table['row'] = {'html_line': self.getpos()[0], 'cells': []}
            elif tag in {'td', 'th'} and table['row'] is not None:
                table['cell'] = []
            elif tag == 'br' and table['cell'] is not None:
                table['cell'].append(' ')

    def handle_data(self, text):
        if self.stack and self.stack[-1]['cell'] is not None:
            self.stack[-1]['cell'].append(text)

    def handle_endtag(self, tag):
        if not self.stack:
            return
        table = self.stack[-1]
        if tag in {'td', 'th'} and table['cell'] is not None:
            table['row']['cells'].append(' '.join(''.join(table['cell']).split()))
            table['cell'] = None
        elif tag == 'tr' and table['row'] is not None:
            table['rows'].append(table['row'])
            table['row'] = None
        elif tag == 'table':
            self.tables.append(self.stack.pop())


def parse(html):
    if 'Table 6-2' not in html or 'Bearing number' not in html:
        raise ValueError('JTEKT bearing-number page context changed')
    parser = Tables()
    parser.feed(html)
    if parser.stack:
        raise ValueError('Unclosed JTEKT table')
    candidates = [table for table in parser.tables if any(row['cells'] == ['ZZ', 'both sides Fixed shield'] for row in table['rows'])]
    if len(candidates) != 1:
        raise ValueError('JTEKT shield subtable missing or duplicated')
    table = candidates[0]
    if table['rows'][0]['cells'] != ['Codes', 'descriptions']:
        raise ValueError('JTEKT shield code headers changed')
    category, category_line, result = None, None, []
    for row in table['rows'][1:]:
        cells = row['cells']
        if len(cells) == 1:
            if cells[0]:
                category, category_line = cells[0], row['html_line']
        elif len(cells) == 2 and category:
            result.append({'category': category, 'category_html_line': category_line,
                'code': cells[0], 'description': cells[1], 'source_html_line': row['html_line']})
        else:
            raise ValueError('Unexpected JTEKT shield code row')
    if [(r['category'], r['code'], r['description']) for r in result] != EXPECTED:
        raise ValueError('JTEKT shield category/code/description scope changed')
    return {'table_html_line': table['html_line'], 'rows': result}


def build_report():
    raw = PATH.read_bytes()
    if hashlib.sha256(raw).hexdigest().upper() != SHA:
        raise ValueError('JTEKT code-source revision changed')
    table = parse(raw.decode('utf-8-sig'))
    zz = next(row for row in table['rows'] if row['code'] == 'ZZ')
    return {'source_id': 'SRC-JTEKT-BEARING-NUMBER', 'artifact_id': 'ART-JTEKT-BEARING-NUMBER',
        'source_sha256': SHA, 'manufacturer_namespace': 'JTEKT', 'table': 'Table 6-2',
        'shield_seal_subtable': table, 'related_manufacturer_part_id': 'MP-JTEKT-6205-ZZ',
        'related_specification_id': 'SPEC-JTEKT-6205-ZZ-CLOSURE',
        'partial_closure_context': {'source_code': zz['code'], 'source_description': zz['description'],
            'shield_sidedness': 'both_sides', 'shield_fixing': 'fixed',
            'shield_material': None, 'shield_contact_form': None,
            'complete_canonical_closure_mapping': False},
        'identity_approved': False, 'policy_version': 'jtekt-shield-code-context-0.1',
        'limitations': ['Manufacturer terminology context is not a new exact-article observation.',
            'The Shield category is separate from Non-contact seal; do not transfer the adjacent category label to ZZ.',
            'Both-side fixed shielding does not establish metal material or non-contact form on this page.',
            'No clearance, cage, material, tolerance, bore, grease or locating facts inferred from omitted suffixes.',
            'No canonical closure mapping, equivalence or UPN approved.',
            'Existing 6205 ZZ raw observation and source hash remain unchanged.',
            'Independent extraction/interpretation review remains outstanding.']}


def verify_custody(report):
    def read(name):
        with (ROOT / 'registry/data' / name).open(encoding='utf-8-sig', newline='') as handle:
            return list(csv.DictReader(handle))
    if report['source_id'] != 'SRC-JTEKT-BEARING-NUMBER' or report['source_sha256'] != SHA or report['related_manufacturer_part_id'] != check_jtekt_6205_zz.PART or report['identity_approved'] is not False:
        raise ValueError('JTEKT code context scope changed')
    expected_context = {'source_code': 'ZZ', 'source_description': 'both sides Fixed shield',
        'shield_sidedness': 'both_sides', 'shield_fixing': 'fixed', 'shield_material': None,
        'shield_contact_form': None, 'complete_canonical_closure_mapping': False}
    if report['partial_closure_context'] != expected_context:
        raise ValueError('JTEKT partial context promoted beyond source scope')
    article = check_jtekt_6205_zz.build_report()
    check_jtekt_6205_zz.verify_seed_bindings(article)
    sources = [r for r in read('source-register.csv') if r['source_id'] == report['source_id']]
    url = 'https://koyo.jtekt.co.jp/en/support/bearing-knowledge/6-3000.html'
    if len(sources) != 1 or sources[0]['source_url'] != url or sources[0]['publisher_name'] != 'JTEKT Corporation':
        raise ValueError('JTEKT code primary source changed')
    artifacts = [r for r in read('source-artifacts.csv') if r['artifact_id'] == report['artifact_id']]
    if len(artifacts) != 1 or artifacts[0]['source_id'] != report['source_id'] or artifacts[0]['sha256'] != SHA or artifacts[0]['retrieval_state'] != 'retrieved':
        raise ValueError('JTEKT code artifact custody changed')
    closure = [r for r in read('specification-values.csv') if r['specification_id'] == report['related_specification_id']]
    if len(closure) != 1 or closure[0]['observation_id'] != check_jtekt_6205_zz.OBS or closure[0]['raw_value'] != 'Shielded ZZ' or closure[0]['normalized_text']:
        raise ValueError('JTEKT partial closure context promoted or detached')
    if any(r['specification_id'] == closure[0]['specification_id'] for r in read('specification-value-mappings.csv')):
        raise ValueError('Full JTEKT closure mapping requires further primary evidence and policy revision')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write-snapshot', action='store_true')
    args = parser.parse_args()
    report = build_report()
    verify_custody(report)
    target = ROOT / 'registry/reports/jtekt-shield-code-context.json'
    if args.write_snapshot:
        target.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    elif json.loads(target.read_text(encoding='utf-8')) != report:
        raise ValueError('JTEKT code-context snapshot stale or altered')
    print('JTEKT ZZ: both-side fixed shield retained; metal/contact form still unproven.')
