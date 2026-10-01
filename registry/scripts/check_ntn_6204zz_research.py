"""Quarantine exact NTN 6204ZZ evidence and compare dimensions without identity promotion."""
import argparse
import hashlib
import json
from decimal import Decimal
from pathlib import Path
import check_ntn_6205zz
import check_nsk_6204zz

ROOT = Path(__file__).resolve().parents[2]
PATH = ROOT / 'registry/artifacts/ntn/6204zz-20261001.html'
SHA = '3F2253DB6EEA5B032A410C39E2C939FBB786C7014CD0E4F8FE96E83A24F25003'
URL = 'https://bearingfinder.ntnamericas.com/item/deep-groove-ball-bearings/single-row-radial-ball-bearings/6204zz'
EXPECTED = [
    ('Ordering Options', [('general','Find a Distributor'),('general','Contact NTN Customer Support Specialist'),('general','Order through NTN DOL (Authorized Distributors Only)')]),
    ('Type', [('general','Deep Groove Ball Bearing')]), ('Bore Type', [('general','Round')]),
    ('Material', [('general','High Carbon Chrome Steel')]), ('Cage Type', [('general','Pressed')]),
    ('Cage Material', [('general','Steel')]), ('Ball Material', [('general','Steel')]),
    ('Limiting Speed - Grease', [('general','16000 RPM')]), ('Precision', [('general','ISO Class 0')]),
    ('Configuration', [('general','One')]), ('Factor', [('general','13.2')]),
    ('Radial Internal Clearance', [('general','CN')]),
    ('Static Load Rating', [('imperial','1500 lbf'),('metric','6650 N'),('metric','9.75 kN')]),
    ('Dynamic Load Rating', [('imperial','3190 lbf'),('metric','14200 N'),('metric','14.20 kN')]),
    ('Enclosure', [('general','Double Shielded')]), ('Weight', [('imperial','0.227 lb'),('metric','0.103 kg')]),
    ('Operating Temperature Range', [('imperial','-40 to 250 ºF'),('metric','-40 to 120 ºC')]),
    ('d', [('imperial','0.7874 in'),('metric','20.000 mm')]),
    ('D', [('imperial','1.8504 in'),('metric','47.000 mm')]),
    ('B', [('imperial','0.5512 in'),('metric','14.000 mm')]),
    ('r', [('imperial','0.0394 in'),('metric','1.000 mm')]),
    ('r1', [('imperial','0.0197 in'),('metric','0.500 mm')]),
    ('da min', [('imperial','0.9843 in'),('metric','25.000 mm')]),
    ('da max', [('imperial','1.1024 in'),('imperial','1.6535 in'),('metric','28.000 mm'),('metric','42.000 mm')]),
    ('Da max', [('imperial','1.6535 in'),('metric','42.000 mm')]),
    ('ras max', [('imperial','0.0394 in'),('metric','1.000 mm')])]


def parse(html):
    if '<h1>Item # 6204ZZ</h1>' not in html or '<span itemprop="sku">6204ZZ</span>' not in html or '<span itemprop="name">Single Row Radial Ball Bearing - Double Shielded</span>' not in html:
        raise ValueError('NTN exact 6204ZZ article context changed')
    parser = check_ntn_6205zz.Parser(illustration_article='6204ZZ')
    parser.feed(html)
    actual = [(r['name'], [(v['measure'],v['text']) for v in r['values']]) for r in parser.rows]
    if actual != EXPECTED or len(parser.illustration_lines) != 1:
        raise ValueError('NTN 6204ZZ native values, scope or illustration changed')
    return parser.rows


def build_report():
    raw = PATH.read_bytes()
    if hashlib.sha256(raw).hexdigest().upper() != SHA:
        raise ValueError('NTN 6204ZZ source revision changed')
    rows = parse(raw.decode('utf-8-sig'))
    by_name = {r['name']:r for r in rows}
    nsk = check_nsk_6204zz.build_report()
    check_nsk_6204zz.verify_seed_bindings(nsk)
    nsk_by_name = {r['cells'][0]:r for r in nsk['native_rows']}
    comparisons = []
    for label in ('d','D','B'):
        value = next(v['text'] for v in by_name[label]['values'] if v['measure']=='metric')
        nsk_row = nsk_by_name[label]
        if nsk_row['cells'][2] != 'mm' or not value.endswith(' mm'):
            raise ValueError('Boundary dimension unit changed')
        comparisons.append({'symbol':label, 'ntn_source_display':value,
            'nsk_source_display':nsk_row['cells'][1]+' mm',
            'ntn_html_line':by_name[label]['html_line'], 'nsk_html_line':nsk_row['html_line'],
            'nominal_values_equal':Decimal(value[:-3])==Decimal(nsk_row['cells'][1])})
    static = by_name['Static Load Rating']
    da = by_name['da max']
    return {'research_status':'quarantined_pre_ingestion', 'registered_source':False,
        'manufacturer_namespace':'NTN', 'manufacturer_article':'6204ZZ', 'source_url':URL,
        'private_source_path':'registry/artifacts/ntn/6204zz-20261001.html', 'source_sha256':SHA,
        'retrieved_at':'2026-10-01', 'policy_version':'ntn-6204zz-research-0.1',
        'native_property_count':26, 'native_properties':rows,
        'quality_findings':[
            {'issue_type':'inconsistent_static_load_metric_units', 'source_html_line':static['html_line'],
             'retained_displays':static['values'], 'metric_values_converted_to_n':['6650','9750'],
             'difference_n':'3100', 'corrected_value':None, 'rating_trusted':False},
            {'issue_type':'ambiguous_da_max_values', 'source_html_line':da['html_line'],
             'retained_displays':da['values'], 'corrected_value':None}],
        'boundary_context_comparison':{'related_registered_part':'MP-NSK-6204ZZ',
            'nsk_source_sha256':nsk['source_sha256'], 'comparisons':comparisons,
            'canonical_pair_screen_created':False, 'same_item_approved':False},
        'identity_approved':False, 'publisher_correction_obtained':False,
        'limitations':['This privately captured research source is not yet a registry source, part or observation.',
            'Twenty-six rows include one commercial ordering row; no ordering offer is created.',
            'Matching 20 x 47 x 14 mm does not establish bearing identity or substitution suitability.',
            'Static load metric cells conflict; neither is selected as corrected truth.',
            'Two da max metric cells remain under the same source label; Da max is a separate row.',
            'Round bore does not establish cylindrical bore; supplied grease and locating feature remain unstated.',
            'ISO Class 0 is not automatically normalized to NSK P0; closure is not inherited from NTN 6205ZZ.',
            'Earlier NTN 6205ZZ findings and resolution ledger are unchanged; recurrence is not publisher correction.',
            'Independent extraction review, source registration and governed intake remain outstanding.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write-snapshot', action='store_true')
    args = parser.parse_args()
    report = build_report()
    target = ROOT / 'registry/reports/ntn-6204zz-pre-ingestion.json'
    if args.write_snapshot:
        target.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    elif json.loads(target.read_text(encoding='utf-8')) != report:
        raise ValueError('NTN 6204ZZ research snapshot stale or altered')
    print('NTN 6204ZZ: 26 source rows retained; two publication issues quarantined; dimension context only.')
