"""Retain bounded JTEKT catalogue evidence without approving article identity."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import pdfplumber
import check_jtekt_shield_codes

ROOT = Path(__file__).resolve().parents[2]
PATH = ROOT / 'registry/artifacts/jtekt/catbs004en_b-20261001.pdf'
SHA = 'BCD21D456A473132E87F42C1D78E54750E62E247F400491AC2C4D745779D6412'
URL = 'https://koyo.jtekt.co.jp/en/support/catalog-download/uploads/catbs004en_b.pdf'
ROW = '25 52 15 1 17.5 7.85 0.550 13.9 13 000 12 000 8 400 15 000 6205 ZZ 6205 2RU 6205 2RD 6205 2RS 30 31.5 47 1 0.128'


def interpret(header, rows, mass_header):
    if header != 'Shielded Non-contact type ZZ type':
        raise ValueError('Bounded ZZ construction column changed')
    if rows != [ROW]:
        raise ValueError('Exact 6205 catalogue row changed or duplicated')
    if mass_header != '(Refer.) Mass Open type (kg)':
        raise ValueError('Open-type mass scope changed')
    return {'zz_header': header, '6205_row': rows[0], 'mass_header': mass_header}


def extract(path=PATH):
    if hashlib.sha256(path.read_bytes()).hexdigest().upper() != SHA:
        raise ValueError('JTEKT catalogue revision changed')
    with pdfplumber.open(path) as pdf:
        if len(pdf.pages) != 226:
            raise ValueError('JTEKT catalogue page count changed')
        page = pdf.pages[3]
        header = ' '.join(page.crop((90, 65, 146, 114)).extract_text().split())
        text = ' '.join(page.extract_text().split())
        if 'Table 1 Comparison of shielded and sealed bearing performance' not in text:
            raise ValueError('ZZ Table 1 context missing')
        page = pdf.pages[11]
        rows = [' '.join(line.split()) for line in page.extract_text().splitlines() if '6205' in line]
        mass = ' '.join(page.crop((750, 185, 792, 224)).extract_text().split())
        # The narrow rightmost column must explicitly retain its open-type scope.
        return interpret(header, rows, mass)


def build_report():
    earlier = check_jtekt_shield_codes.build_report()
    check_jtekt_shield_codes.verify_custody(earlier)
    evidence = extract()
    for name, key, value in [('source-register.csv', 'source_id', 'SRC-JTEKT-BS004-B'),
                             ('source-artifacts.csv', 'artifact_id', 'ART-JTEKT-BS004-B')]:
        with (ROOT / 'registry/data' / name).open(encoding='utf-8-sig', newline='') as f:
            selected = [r for r in csv.DictReader(f) if r[key] == value]
        url_key = 'source_url' if key == 'source_id' else 'artifact_url'
        if len(selected) != 1 or selected[0][url_key] != URL:
            raise ValueError('JTEKT catalogue custody changed')
        if key == 'artifact_id' and (selected[0]['sha256'] != SHA or selected[0]['source_id'] != 'SRC-JTEKT-BS004-B' or selected[0]['retrieval_state'] != 'retrieved'):
            raise ValueError('JTEKT catalogue artifact binding changed')
        if key == 'source_id' and selected[0]['publisher_name'] != 'JTEKT Corporation':
            raise ValueError('JTEKT catalogue publisher changed')
    return {'source_id': 'SRC-JTEKT-BS004-B', 'artifact_id': 'ART-JTEKT-BS004-B',
        'source_sha256': SHA, 'policy_version': 'jtekt-shield-catalogue-0.1',
        'related_manufacturer_part_id': 'MP-JTEKT-6205-ZZ',
        'definition_pdf_page': 4, 'definition_printed_page': 'B6',
        'article_pdf_page': 12, 'article_printed_pages': 'B22-B23',
        'extracted_evidence': evidence,
        'partial_closure_context': {'shield_sidedness': 'both_sides', 'shield_fixing': 'fixed',
            'shield_contact_form': 'non_contact', 'shield_material': None,
            'complete_canonical_closure_mapping': False},
        'catalogue_row_context': {'d_mm': '25', 'D_mm': '52', 'B_mm': '15',
            'dynamic_load_kn': '17.5', 'static_load_kn': '7.85',
            'grease_limiting_speed_min_inverse': '13000',
            'open_type_reference_mass_kg': '0.128', 'exact_ZZ_mass_corroborated': False},
        'identity_approved': False, 'independent_review': 'outstanding',
        'limitations': ['Three complete relevant PDF pages visually reviewed; not the whole 226-page document.',
            'Non-contact shield definition is bounded to the ZZ column, not transferred from seals.',
            'No shield material is inferred from the drawing.',
            'Mass column explicitly applies to open type, not the exact ZZ article.',
            'Standard cage discussion permits application-specific alternatives; no exact cage assigned.',
            'No exact grease formulation, clearance, tolerance, bore, material or locating default assigned.',
            'Earlier raw article observations and mappings remain unchanged.',
            'No equivalence, source correction or UPN approval.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write-snapshot', action='store_true')
    args = parser.parse_args()
    report = build_report()
    target = ROOT / 'registry/reports/jtekt-shield-catalogue.json'
    if args.write_snapshot:
        target.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    elif json.loads(target.read_text(encoding='utf-8')) != report:
        raise ValueError('JTEKT catalogue snapshot stale or altered')
    print('JTEKT ZZ non-contact context reproduced; material unknown; open-type mass not promoted.')
