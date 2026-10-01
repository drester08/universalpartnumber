"""Reproduce manufacturer-definition corroboration without correcting article data."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import pdfplumber
import check_ntn_6205zz

ROOT = Path(__file__).resolve().parents[2]
PATH = ROOT / 'registry/artifacts/ntn/3015E-20261001.pdf'
SHA = '7F1357233C6089610F0E5246EB427553487A14101EB38E15E0D32BB59B405924'
ROW = '52 15 1 0.5 15.5 7.85 0.550 13.9 13 000 15 000 11 000 8 900 6205 ZZ LLB LLU LLH N NR 49.73 2.46 1.35 0.4 57.9 1.12 30 32 47 58.5 3.3 1.2 1 0.5 0.128'


def extract(path=PATH):
    if hashlib.sha256(path.read_bytes()).hexdigest().upper() != SHA:
        raise ValueError('NTN catalogue revision changed')
    with pdfplumber.open(path) as pdf:
        if len(pdf.pages) != 12:
            raise ValueError('NTN catalogue page count changed')
        page = pdf.pages[2]
        crop = page.crop((page.width * .109, page.height * .40, page.width * .196, page.height * .78))
        definition = ' '.join(crop.extract_text().split())
        for expected in ('Non-contact shield type ZZ', 'Metal shield plate is affixed to the outer ring', 'V-groove and labyrinth clearance.'):
            if expected not in definition:
                raise ValueError('ZZ table column definition changed')
        if 'double shielded and double sealed bearings' not in ' '.join(page.extract_text().split()):
            raise ValueError('Double-shield footnote missing')
        rows = [' '.join(line.split()) for line in pdf.pages[6].extract_text().splitlines() if '6205' in line]
        if rows != [ROW]:
            raise ValueError('6205 catalogue row changed or ambiguous')
        full_table = ' '.join(pdf.pages[6].extract_text().split())
        for heading in ('Basic load rating', 'Installation-related dimensions', 'double sealed and double shielded', 'Does not include bearings with snap rings'):
            if heading not in full_table:
                raise ValueError('6205 scope heading/footnote changed: ' + heading)
    return {'definition_column_text': definition, '6205_row_text': rows[0]}


def build_report():
    parsed = extract()
    article = check_ntn_6205zz.build_report()
    check_ntn_6205zz.verify_seed_bindings(article)
    with (ROOT / 'registry/data/specification-value-mappings.csv').open(encoding='utf-8-sig', newline='') as handle:
        mappings = [r for r in csv.DictReader(handle) if r['mapping_id'] == 'MAP-NTN-6205ZZ-CLOSURE']
    if len(mappings) != 1 or mappings[0]['specification_id'] != 'SPEC-NTN-6205ZZ-CLOSURE' or mappings[0]['mapping_state'] != 'proposed' or mappings[0]['controlled_value_id'] != 'CV-BEARING-CLOSURE-DOUBLE-NONCONTACT-METAL' or mappings[0]['mapping_basis'] != 'manufacturer_definition':
        raise ValueError('NTN closure proposal custody/state changed')
    return {'source_id': 'SRC-NTN-SHIELD-SEAL-3015', 'source_sha256': SHA,
        'article_source_id': article['source_id'], 'article_sha256': article['source_sha256'],
        'catalogue_label': 'CAT.No.3015-5/E 25.12.00 IP/IP',
        'pdf_page_count': 12, 'definition_pdf_page': 3, 'definition_printed_pages': '3-4',
        'dimension_pdf_page': 7, 'dimension_printed_pages': '11-12',
        'extracted_evidence': parsed,
        'closure_proposal': {'mapping_id': mappings[0]['mapping_id'], 'state': 'proposed', 'canonical_code': 'double_non_contact_metal_shield'},
        'catalogue_6205_context': {'bore_diameter_mm': '25', 'outside_diameter_mm': '52', 'width_mm': '15',
            'static_load_rating_kn': '7.85', 'da_max_mm': '32', 'Da_max_mm': '47', 'mass_approx_kg': '0.128'},
        'interpretation': ['ZZ construction and double-shield scope support a proposed manufacturer-specific closure mapping.',
            'The catalogue corroborates 7850 N, but does not remove the article page 11.60 kN cell or supply a publisher correction.',
            'The catalogue distinguishes lowercase da max 32 mm from uppercase Da max 47 mm; the article page remains malformed.',
            'The catalogue row lists multiple closure and snap-ring variants; N and NR availability does not prove the purchased article has either feature.',
            'Test grease belongs to 6305 and 6304 performance tests, not to supplied 6205ZZ lubricant.',
            'Approximate catalogue mass is not assigned to the exact shielded article; grease and variant context remain unresolved.'],
        'identity_approved': False, 'publisher_correction_obtained': False,
        'independent_extraction_review': 'outstanding'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write-snapshot', action='store_true')
    args = parser.parse_args()
    report = build_report()
    target = ROOT / 'registry/reports/ntn-shield-seal-corroboration.json'
    if args.write_snapshot:
        target.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    elif json.loads(target.read_text(encoding='utf-8')) != report:
        raise ValueError('NTN corroboration report stale or altered')
    print('NTN catalogue corroboration reproduced; closure mapping proposed, not approved; article discrepancies retained.')
