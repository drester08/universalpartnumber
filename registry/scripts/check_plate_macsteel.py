"""Screen all supplied plate rows against selected Macsteel family evidence.

Research interpretations only: no approved aliases, article identity or corrections.
"""
import argparse
import csv
import hashlib
import json
from collections import Counter
from decimal import Decimal
from pathlib import Path
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / 'artifacts/user-reference-csvs/Steel Plate - Rev01 - 02 July 2026.csv'
CATALOGUE = ROOT / 'artifacts/macsteel/vrn-product-catalogue-2021.pdf'
DATASET_SHA = 'e428eaca527f60af33902eaa6711a3b85e0be6a1578bbb499df3d84bf3b8b42f'
CATALOGUE_SHA = 'ac36016b2bcc22a42ae5de6e49b0d7486f4a58fca82ff9104e357ff396a22517'
FAMILIES = {
    'SANS 50025 / EN 10025 S275 JR+AR': ('family_designation_supported', 14, 'S275JR', 'AR'),
    'SANS 50025 / EN 10025 S355 JR+AR': ('family_designation_supported', 14, 'S355JR', 'AR'),
    'SANS 50025 / EN 10025 S355 JO+AR': ('grade_character_review', 14, 'S355J0', 'AR'),
    'B.S 1501/151 GRADE 430A': ('specification_scope_review', 17, 'BS1501-161-430A', None),
    'W200': ('unverified_product_name', 10, 'VRN200', None),
    'EN 10025-2-S235JR+AR / CQ': ('outside_selected_family_scope', None, None, None),
}


def classify(row, line):
    outcome, page, grade, condition = FAMILIES[row['MOC']]
    dimensions = {key: row[column] for key, column in (
        ('length_mm', 'Length (mm)'), ('width_mm', 'Width (mm)'), ('thickness_mm', 'Thickness (mm)'))}
    values = [Decimal(v) for v in dimensions.values()]
    if any(v <= 0 for v in values):
        raise ValueError('Nonpositive plate dimension')
    expected = values[0] * values[1] * values[2] * Decimal('0.00000785')
    actual = Decimal(row['Mass per sheet (kg)'])
    discrepancy = abs(actual - expected) / expected > Decimal('0.005')
    return {'csv_line': line, 'moc_raw': row['MOC'], 'dimensions_raw': dimensions,
            'family_outcome': outcome, 'source_pdf_page': page,
            'research_candidate_grade': grade, 'research_candidate_delivery_condition': condition,
            'interpretation_status': 'unreviewed', 'exact_article_verified': False,
            'mass_recorded_kg': row['Mass per sheet (kg)'],
            'mass_calculated_kg': str(expected.normalize()), 'mass_discrepancy': discrepancy}


def compare():
    if hashlib.sha256(DATASET.read_bytes()).hexdigest() != DATASET_SHA:
        raise ValueError('Dataset revision mismatch')
    if hashlib.sha256(CATALOGUE.read_bytes()).hexdigest() != CATALOGUE_SHA:
        raise ValueError('Catalogue revision mismatch')
    pdf = PdfReader(CATALOGUE)
    if len(pdf.pages) != 48:
        raise ValueError('Unexpected catalogue page count')
    for index, required in ((9, ('VRN 200', 'not guaranteed')),
                            (13, ('S355J0', 'Approximate equivalents', 'EN 10029')),
                            (16, ('BS 1501-161-430A', '151 / 161'))):
        text = pdf.pages[index].extract_text(extraction_mode='layout')
        if not all(token in text for token in required):
            raise ValueError('Reviewed source page extraction changed')
    with DATASET.open(encoding='utf-8-sig', newline='') as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != 395:
        raise ValueError('Expected395 supplied records')
    records = [classify(row, line) for line, row in enumerate(rows, 2)]
    return {'dataset_sha256': DATASET_SHA, 'catalogue_sha256': CATALOGUE_SHA,
            'source_id': 'SRC-MACSTEEL-VRN-2021', 'source_pdf_pages_reviewed': [10, 14, 17],
            'dataset_rows': len(records), 'family_outcomes': dict(Counter(r['family_outcome'] for r in records)),
            'mass_assumed_density_kg_per_m3': 7850, 'mass_screening_relative_threshold': '0.005',
            'mass_discrepancies': sum(r['mass_discrepancy'] for r in records), 'records': records,
            'limitations': ['Selected supplier family pages only; no exact stock-size/article comparison.',
                            'Suggested grades/conditions are unreviewed interpretations, not approved mappings.',
                            'Family wording does not verify the supplied SANS standard claim or any certificate.',
                            'JO/J0,151/161 andW200/VRN200 remain unresolved; raw strings unchanged.',
                            'Calculated mass uses an assumed density; discrepancy is not a correction approval.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write-snapshot', action='store_true')
    args = parser.parse_args()
    result = compare()
    path = ROOT / 'reports/plate-macsteel-screening.json'
    content = json.dumps(result, indent=2, ensure_ascii=True) + '\n'
    if args.write_snapshot:
        path.write_text(content, encoding='utf-8', newline='')
    elif path.read_text(encoding='utf-8') != content:
        raise ValueError('Stale plate screening snapshot')
    print(f"Plate screening: {result['dataset_rows']} rows; {result['family_outcomes']}; {result['mass_discrepancies']} mass discrepancies. No article approval.")
