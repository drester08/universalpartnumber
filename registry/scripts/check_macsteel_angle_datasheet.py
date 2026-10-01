"""Extract generic equal-angle tables without promoting seller or item identity."""
import argparse
import csv
import hashlib
import json
import re
from decimal import Decimal
from pathlib import Path
import pdfplumber
from check_macsteel_angle_offers import parse_listing, FILES

ROOT = Path(__file__).resolve().parents[2]
SHA = 'E3DCBF06039844BB99ADD88B77153F37543EC30EF617368C44383748D4AEB1A1'
PDFS = ['AE_S355RA_0061.pdf', 'AE_S355RA_0064.pdf']
HEADERS = [
    ['Dimensions','2mm','2.5mm','3mm','4mm','5mm','6mm','8mm'],
    ['Dimensions','4mm','5mm','6mm','8mm','10mm','12mm','15mm','16mm','18mm','20mm','24mm'],
]
CONTEXTS = ['Mild steel (commercial quality)', 'SANS 50025/EN 10025 Grade S355JR']


def extract_tables(tables):
    if len(tables) != 2:
        raise ValueError('Expected two separate material tables')
    records = []
    for index, table in enumerate(tables):
        if table[0] != HEADERS[index] or len(table) != [6,9][index]:
            raise ValueError('Table shape or thickness header changed')
        seen = set()
        for row_index, row in enumerate(table[1:], 2):
            if len(row) != len(table[0]):
                raise ValueError('Sparse table width changed')
            match = re.fullmatch(r'(\d+) x (\d+)', row[0])
            if not match or match[1] != match[2] or row[0] in seen:
                raise ValueError('Invalid or duplicate equal-angle dimension')
            seen.add(row[0])
            for column, mass in enumerate(row[1:], 2):
                if mass == '':
                    continue
                if not re.fullmatch(r'\d+\.\d{3}\*?', mass) or Decimal(mass.rstrip('*')) <= 0:
                    raise ValueError('Invalid mass field')
                records.append({
                    'material_context': CONTEXTS[index], 'leg_a_mm': match[1],
                    'leg_b_mm': match[2], 'thickness_mm': table[0][column-1][:-2],
                    'mass_kg_per_m': mass.rstrip('*'), 'raw_mass': mass,
                    'availability_footnote_applies': mass.endswith('*'),
                    'pdf_page': 1, 'pdf_table': index+1,
                    'pdf_row': row_index, 'pdf_column': column,
                })
    if [sum(r['pdf_table'] == i for r in records) for i in (1,2)] != [23,32]:
        raise ValueError('Unexpected populated cell counts')
    return records


def extract_pdf(path):
    with pdfplumber.open(path) as pdf:
        if len(pdf.pages) != 1:
            raise ValueError('Unexpected page count')
        page = pdf.pages[0]
        text = ' '.join(page.extract_text().split())
        for required in ['Mass per metre (kg/m)', 'SANS 50025/EN 10025 Grade S355JR',
                         'Please confirm availability with your local Macsteel Trading branch',
                         'roll-formed', 'Please contact our Structural Steel Division for sizes not listed above.']:
            if required not in text:
                raise ValueError('Missing material/unit/qualification context: ' + required)
        return extract_tables(page.extract_tables())


def correlate(offers, facts):
    result = []
    for offer in offers:
        candidates = [f for f in facts if f['pdf_table'] == 2 and
                      all(Decimal(f[field]) == Decimal(str(offer[field]))
                          for field in ('leg_a_mm','leg_b_mm','thickness_mm'))]
        if len(candidates) != 1:
            raise ValueError('Offer key not uniquely supported by generic table')
        result.append({'seller_sku': offer['seller_sku'], 'length_m': offer['length_m'],
                       'listing_locator': offer['source_locator'],
                       'generic_table_candidate': candidates[0],
                       'outcome': 'nominal_geometry_candidate',
                       'exact_article_verified': False, 'identity_approved': False})
    return result


def build_report():
    for name in PDFS:
        path = ROOT / 'registry/artifacts/macsteel' / name
        if hashlib.sha256(path.read_bytes()).hexdigest().upper() != SHA:
            raise ValueError('PDF revision mismatch: ' + name)
    with (ROOT / 'registry/data/source-artifacts.csv').open(encoding='utf-8-sig', newline='') as handle:
        artifacts = {r['artifact_id']: r for r in csv.DictReader(handle)}
    for suffix, name in zip(('0061','0064'), PDFS):
        record = artifacts['ART-MACSTEEL-AE' + suffix + '-PDF']
        if record['sha256'] != SHA or record['retrieval_state'] != 'retrieved' or record['local_path'] != 'registry/artifacts/macsteel/' + name:
            raise ValueError('PDF custody metadata not bound to inspected bytes')
    facts = extract_pdf(ROOT / 'registry/artifacts/macsteel' / PDFS[0])
    listing = (ROOT / 'registry/artifacts/macsteel/equal-angle-page4.html').read_bytes()
    if hashlib.sha256(listing).hexdigest().upper() != FILES['equal-angle-page4.html']:
        raise ValueError('Listing revision mismatch')
    offers = parse_listing(listing.decode('utf-8-sig'))
    return {
        'pdf_sha256': SHA, 'listing_sha256': FILES['equal-angle-page4.html'],
        'linked_source_ids': ['SRC-MACSTEEL-AE0061-PDF','SRC-MACSTEEL-AE0064-PDF'],
        'identical_pdf_bytes': True, 'independent_sources': False,
        'scope': 'Generic equal-angle family sheet; not exact seller SKU or manufacturing certificate',
        'table_facts': facts, 'table_fact_count': len(facts),
        'offer_candidates': correlate(offers, facts), 'offer_candidate_count': len(offers),
        'identity_approved': False,
        'qualifications': [
            'Sparse blank cells mean no listed value, not zero mass or unavailability',
            'Availability stars on 100x100x15 and 120x120x15 require local branch confirmation',
            'PDF S355JR context does not independently establish listing JR+AR delivery condition',
            'General PDF roll-formed/bending narrative does not establish production route for individual SKUs',
            'No lengths, seller SKUs, manufacturing mill, dimensional tolerances or exact article certificate established by this PDF',
            'Same-byte URLs count as one content source, not independent corroboration',
        ],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--write-snapshot', action='store_true')
    args = parser.parse_args()
    report = build_report()
    output = ROOT / 'registry/reports/macsteel-angle-datasheet.json'
    if args.write_snapshot:
        output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    elif json.loads(output.read_text(encoding='utf-8')) != report:
        raise ValueError('Generic angle report is stale or altered')
    print('Verified 55 generic table facts and 30 nominal seller candidates; no identity approval.')


if __name__ == '__main__':
    main()
