"""Checksum-bound NSK exact-article intake; variants and unknown fields remain separate."""
import argparse
import csv
import hashlib
import json
import re
from pathlib import Path
from check_jtekt_shield_codes import Tables

ROOT = Path(__file__).resolve().parents[2]
PATH = ROOT / 'registry/artifacts/nsk/6204ZZ-20261001.html'
SHA = '6AA72C0BD671B2E0A21269F5F303D5CCB48DF0D6662419D678E57D70CAD04EA9'
URL = 'https://www.nsk.com/sg-en/engineering/products/bearings/ball-bearings/deep-groove-ball-bearings/single-row-deep-groove-ball-bearings/6204zz-apn.html'
PART, OBS = 'MP-NSK-6204ZZ', 'OBS-NSK-6204ZZ-20261001'
EXPECTED = [
    ['', '6204ZZ', '', ''], ['d', '20', 'mm', 'Bore diameter'],
    ['D', '47', 'mm', 'Outside diameter'], ['B', '14', 'mm', 'Width'],
    ['r (min.)', '1', 'mm', 'Chamfer dimension'],
    ['Cr', '14100', 'N', 'Basic dynamic load rating'],
    ['C0r', '6600', 'N', 'Basic static load rating'],
    ['Grease', '17000', 'min-1', 'Grease lubrication'],
    ['da (min.)', '25', 'mm', 'Diameter of shaft abutment'],
    ['da (max.)', '26.5', 'mm', 'Diameter of shaft abutment'],
    ['Da (max.)', '42', 'mm', 'Diameter of housing abutment'],
    ['ra (max.)', '1', 'mm', 'Radius of shaft or housing fillet'],
    ['Dx (min.)', '0', 'mm', 'Diameter of snap ring recess in the housing'],
    ['Cy (max.)', '0', 'mm', 'Distance from outer ring side face to snap ring back face'],
    ['fo', '13.1', '', 'Factor'], ['z', '8', '', 'Number of Balls'],
    ['Dw', '7.938', 'mm', 'Ball Diameter'], ['(approx.)', '0.107', 'kg', ''],
    ['Types', '62 series', ''], ['Design', '( ): None-N, NR', ''],
    ['Cage', '( ): Pressed steel cage', ''], ['Seals,Shields', 'ZZ: Shield on both sides', ''],
    ['Radial Internal Clearance', 'CN', ''], ['Tolerance', 'P0', '']]


class ProductTables(Tables):
    def handle_starttag(self, tag, attrs):
        super().handle_starttag(tag, attrs)
        if tag == 'table':
            self.stack[-1]['classes'] = dict(attrs).get('class', '').split()


def parse(html):
    if not re.search(r'<div class="series">\s*6204ZZ\s*</div>', html) or '<title>6204ZZ | NSK</title>' not in html:
        raise ValueError('NSK exact article changed; family/variant page not accepted')
    if not re.search(r'itemprop="name"[^>]*>\s*Single-Row Deep Groove Ball Bearings\s*</div>', html):
        raise ValueError('NSK exact construction heading changed')
    parser = ProductTables()
    parser.feed(html)
    if parser.stack:
        raise ValueError('NSK unclosed table')
    tables = [t for t in parser.tables if 'nsk-table-product-attr' in t['classes']]
    rows = [r for t in tables for r in t['rows']]
    if len(tables) != 9 or [r['cells'] for r in rows] != EXPECTED:
        raise ValueError('NSK native table values/order/scope changed')
    return rows


def build_report():
    raw = PATH.read_bytes()
    if hashlib.sha256(raw).hexdigest().upper() != SHA:
        raise ValueError('NSK source revision changed')
    rows = parse(raw.decode('utf-8-sig'))
    return {'source_id': 'SRC-NSK-6204ZZ', 'artifact_id': 'ART-NSK-6204ZZ',
        'source_sha256': SHA, 'manufacturer_part_id': PART, 'article': '6204ZZ',
        'policy_version': 'nsk-6204zz-intake-0.1', 'native_row_count': len(rows), 'native_rows': rows,
        'identity_approved': False, 'missing_required_properties': ['PROP-BORE-TYPE', 'PROP-BEARING-MATERIAL', 'PROP-SUPPLIED-LUBRICANT'],
        'unresolved_semantic_properties': ['PROP-BEARING-CLOSURE', 'PROP-LOCATING-FEATURE'],
        'limitations': ['Exact Singapore-region product page; not 6204ZZ Series or clearance/tolerance variants.',
            'Closure sidedness retained raw; no full non-contact metal mapping inherited from 6205ZZ.',
            'Design wording retained exactly; no absent-suffix or zero-dimension inference of locating construction.',
            'Approximate mass remains approximate; ratings and speed are manufacturer context, not identity approval.',
            'Grease speed does not identify supplied grease; no bore type or bearing material inferred.',
            'Four terminology mappings proposed only; independent extraction and reuse review outstanding.',
            'No source correction, cross-brand merge or permanent UPN.']}


def verify_seed_bindings(report):
    def read(name):
        with (ROOT / 'registry/data' / name).open(encoding='utf-8-sig', newline='') as f:
            return list(csv.DictReader(f))
    if report != build_report():
        raise ValueError('NSK report scope or native values altered')
    def one(name, key, value):
        rows = [r for r in read(name) if r[key] == value]
        if len(rows) != 1:
            raise ValueError('NSK missing/duplicate custody record')
        return rows[0]
    source = one('source-register.csv', 'source_id', report['source_id'])
    artifact = one('source-artifacts.csv', 'artifact_id', report['artifact_id'])
    part = one('manufacturer-parts.csv', 'manufacturer_part_id', PART)
    observation = one('observations.csv', 'observation_id', OBS)
    if source['source_url'] != URL or source['publisher_name'] != 'NSK Ltd.' or source['authority_tier'] != '1' or source['ingestion_status'] != 'reference_only':
        raise ValueError('NSK primary source changed')
    if (artifact['artifact_url'], artifact['source_id'], artifact['sha256'], artifact['retrieval_state']) != (URL, report['source_id'], SHA, 'retrieved'):
        raise ValueError('NSK artifact custody changed')
    if artifact['local_path'] != 'registry/artifacts/nsk/6204ZZ-20261001.html':
        raise ValueError('NSK artifact path changed')
    if (part['manufacturer_id'], part['manufacturer_part_number'], part['profile_id']) != ('ORG-NSK', '6204ZZ', 'PROFILE-BEARING-DGBB-1R-DOUBLE-METAL-SHIELD-0.1'):
        raise ValueError('NSK article namespace/profile changed')
    if (observation['manufacturer_part_id'], observation['source_id'], observation['raw_payload_sha256'], observation['review_state']) != (PART, report['source_id'], SHA, 'unreviewed'):
        raise ValueError('NSK observation custody changed')
    native = {r['cells'][0]: r['cells'] for r in report['native_rows']}
    expected = {'GEOMETRY': ('PROP-BEARING-GEOMETRY', 'Single-Row Deep Groove Ball Bearings', 'single_row_deep_groove_ball', '', '', 'Exact article heading; unreviewed terminology'),
        'CLOSURE': ('PROP-BEARING-CLOSURE', native['Seals,Shields'][1], '', '', '', 'Sidedness only; contact form and material not canonically assigned'),
        'LOCATING': ('PROP-LOCATING-FEATURE', native['Design'][1], '', '', '', 'Exact design wording retained; construction interpretation outstanding')}
    for suffix, label, prop, code in [('CLEARANCE', 'Radial Internal Clearance', 'PROP-RADIAL-INTERNAL-CLEARANCE', 'cn'),
        ('TOLERANCE', 'Tolerance', 'PROP-BEARING-TOLERANCE-CLASS', 'p0'), ('CAGE', 'Cage', 'PROP-CAGE-CONSTRUCTION', 'pressed_steel')]:
        expected[suffix] = (prop, native[label][1], code, '', '', 'Exact article property; mapping proposed not approved')
    for suffix, label, prop, unit in [('BORE', 'd', 'PROP-BORE-DIAMETER', 'UNIT-MM'), ('OD', 'D', 'PROP-OUTSIDE-DIAMETER', 'UNIT-MM'),
        ('WIDTH', 'B', 'PROP-BEARING-WIDTH', 'UNIT-MM'), ('DYNAMIC', 'Cr', 'PROP-BASIC-DYNAMIC-LOAD-RATING', 'UNIT-N'),
        ('STATIC', 'C0r', 'PROP-BASIC-STATIC-LOAD-RATING', 'UNIT-N'), ('SPEED', 'Grease', 'PROP-LIMITING-SPEED-GREASE', 'UNIT-RPM'),
        ('BALL-COUNT', 'z', 'PROP-BALL-COUNT', 'UNIT-EA'), ('BALL-DIAMETER', 'Dw', 'PROP-BALL-DIAMETER', 'UNIT-MM'), ('MASS', '(approx.)', 'PROP-MASS', 'UNIT-KG')]:
        cells = native[label]
        qualifier = {'MASS': 'Approximate source mass; not measured article identity', 'SPEED': 'Grease lubrication speed; supplied grease not identified',
            'DYNAMIC': 'Manufacturer rating; standard and calculation basis unstated', 'STATIC': 'Manufacturer rating; standard and calculation basis unstated'}.get(suffix, 'Exact article numeric field; unreviewed')
        expected[suffix] = (prop, ' '.join(c for c in cells if c), '', cells[1], unit, qualifier)
    actual_rows = [r for r in read('specification-values.csv') if r['observation_id'] == OBS]
    actual = {r['specification_id'].removeprefix('SPEC-NSK-6204ZZ-'): tuple(r[k] for k in ('property_id','raw_value','normalized_text','normalized_number','unit_id','qualifier')) for r in actual_rows}
    if len(actual_rows) != 15 or actual != expected:
        raise ValueError('NSK ingestion differs from native source or qualifiers')
    maps = [r for r in read('specification-value-mappings.csv') if r['specification_id'] in {r['specification_id'] for r in actual_rows}]
    closure = [r for r in maps if r['specification_id'] == 'SPEC-NSK-6204ZZ-CLOSURE']
    if len(closure) != 1:
        raise ValueError('NSK separately governed closure proposal absent or duplicated')
    import check_nsk_6204zz_closure_mapping
    check_nsk_6204zz_closure_mapping.verify_mapping_row(closure[0])
    maps = [r for r in maps if r not in closure]
    allowed = {'GEOMETRY':'CV-BEARING-GEOMETRY-SR-DGBB', 'CLEARANCE':'CV-BEARING-CLEARANCE-CN', 'TOLERANCE':'CV-BEARING-TOLERANCE-P0', 'CAGE':'CV-BEARING-CAGE-PRESSED-STEEL'}
    if len(maps) != 4 or {r['specification_id'].removeprefix('SPEC-NSK-6204ZZ-'):r['controlled_value_id'] for r in maps} != allowed or any(r['mapping_state'] != 'proposed' or r['mapping_basis'] != 'source_exact' for r in maps):
        raise ValueError('NSK mapping scope/state changed or unsupported closure promoted')
    return 15


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write-snapshot', action='store_true')
    args = parser.parse_args()
    report = build_report()
    verify_seed_bindings(report)
    target = ROOT / 'registry/reports/nsk-6204ZZ-source.json'
    if args.write_snapshot:
        target.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    elif json.loads(target.read_text(encoding='utf-8')) != report:
        raise ValueError('NSK report stale or altered')
    print('NSK 6204ZZ: 24 native rows retained; 15 unreviewed facts; no identity approval.')
