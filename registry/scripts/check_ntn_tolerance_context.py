"""Bind a proposed NTN tolerance interpretation to three primary PDF sections."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import pdfplumber
import check_ntn_6205zz

ROOT = Path(__file__).resolve().parents[2]
INPUTS = {
    'codes': ('2203E_a05', 'SRC-NTN-2203-CODES', '3EABA02BE96756BA448998C2B4788112705AA9700F59C939DE9990555CBE9316', 4),
    'tolerances': ('2203E_a06', 'SRC-NTN-2203-TOLERANCES', '513E2F846BE67207A83B83C20EDBA923B52F8266DAC2D0CDA9A6800D06BE02EC', 11),
    'family': ('2203E_b02', 'SRC-NTN-2203-DGBB', '3252B19D458DB91A5E02DBDB2F6D8ABD6A0AAC22EB17DAA1119B429B672C93C3', 14),
}


def read_pdf(kind):
    name, source, sha, pages = INPUTS[kind]
    path = ROOT / f'registry/artifacts/ntn/{name}-20261001.pdf'
    if hashlib.sha256(path.read_bytes()).hexdigest().upper() != sha:
        raise ValueError('NTN source revision changed: ' + source)
    pdf = pdfplumber.open(path)
    if len(pdf.pages) != pages:
        pdf.close()
        raise ValueError('NTN source page count changed: ' + source)
    return pdf


def extract():
    with read_pdf('codes') as pdf:
        page = pdf.pages[2]
        p0 = ' '.join(page.crop((page.width*.86, page.height*.20, page.width*.90, page.height*.26)).extract_text().split())
        if '(P0) JIS Class 0' not in p0:
            raise ValueError('NTN P0 definition changed')
        if 'Codes in ( ) are not shown in nominal numbers.' not in page.extract_text():
            raise ValueError('Omitted-code footnote changed')
    with read_pdf('tolerances') as pdf:
        page = pdf.pages[0]
        tables = page.extract_tables()
        comparison = [t for t in tables if t[0][0] == 'Standard' and t[0][1] == 'Applicable standard']
        applicability = [t for t in tables if t[0][0] == 'Bearing type']
        if len(comparison) != 1 or len(applicability) != 1:
            raise ValueError('Tolerance table scope ambiguous')
        selected = {r[1]: {'normal_column': r[2].replace('\n', ' '), 'bearing_type': r[-1].replace('\n', ' ')} for r in comparison[0][1:] if r[1] in ('JIS B 1514-1', 'ISO 492', 'DIN 620')}
        expected = {'JIS B 1514-1': {'normal_column': 'Class 0, 6', 'bearing_type': 'Radial bearings'},
                    'ISO 492': {'normal_column': 'Normal class Class 6X', 'bearing_type': 'Radial bearings'},
                    'DIN 620': {'normal_column': 'P0', 'bearing_type': 'All types'}}
        if selected != expected:
            raise ValueError('Manufacturer crosswalk cells changed')
        deep_groove = applicability[0][1]
        if deep_groove[0] != 'Deep groove ball bearings' or deep_groove[2] != 'JIS B 1514-1\n(ISO 492)' or deep_groove[3] != 'Class 0':
            raise ValueError('Deep-groove tolerance applicability changed')
        text = ' '.join(page.extract_text().split())
        if 'have the same specification level.' not in text or 'slightly different from those of ABMA standards.' not in text:
            raise ValueError('Crosswalk qualification missing')
    with read_pdf('family') as pdf:
        page = pdf.pages[0]
        text = ' '.join(page.crop((page.width*.76, page.height*.36, page.width*.955, page.height*.47)).extract_text().split())
        if 'pre-lubricated with grease and enclosed by seals or shields.' not in text or 'the greases which can be used.' not in text:
            raise ValueError('Family lubricant context changed')
    return {'ntn_p0_definition': 'P0: JIS Class 0', 'comparison_normal_column_cells': selected,
            'deep_groove_class_zero_applicability': True,
            'manufacturer_crosswalk_scope': 'Manufacturer tables only; mixed cells retained and normative editions not inspected.',
            'abma_qualification': 'Manufacturer notes slight differences in JIS versus ABMA tolerance and allowance.',
            'lubricant_context': 'Family overview describes grease-prelubricated enclosed bearings and refers to a list of possible greases; exact 6205ZZ formulation is not established.'}


def build_report():
    evidence = extract()
    article = check_ntn_6205zz.build_report()
    check_ntn_6205zz.verify_seed_bindings(article)
    with (ROOT / 'registry/data/specification-value-mappings.csv').open(encoding='utf-8-sig', newline='') as handle:
        mappings = [r for r in csv.DictReader(handle) if r['mapping_id'] == 'MAP-NTN-6205ZZ-TOLERANCE']
    if len(mappings) != 1 or mappings[0]['specification_id'] != 'SPEC-NTN-6205ZZ-TOLERANCE' or mappings[0]['mapping_state'] != 'proposed' or mappings[0]['mapping_basis'] != 'manufacturer_definition' or mappings[0]['controlled_value_id'] != 'CV-BEARING-TOLERANCE-P0':
        raise ValueError('NTN tolerance proposal changed')
    return {'sources': [{'source_id': v[1], 'sha256': v[2], 'page_count': v[3]} for v in INPUTS.values()],
        'evidence': evidence, 'article_source_id': article['source_id'], 'article_sha256': article['source_sha256'],
        'locators': {'codes': 'PDF 3 / A-50-A-51 Table 5.2', 'tolerances': 'PDF 1 / A-54-A-55 Tables 6.1/6.2 and notes', 'family': 'PDF 1 / B-17 Design features and characteristics'},
        'proposal': {'mapping_id': mappings[0]['mapping_id'], 'raw_value_retained': 'ISO Class 0', 'canonical_code': 'p0', 'state': 'proposed'},
        'limits': ['Manufacturer wording interpretation is proposed, not an approved semantic crosswalk.',
                  'ISO uses Normal in the comparison table; the article ISO Class 0 wording is retained rather than edited.',
                  'Normal/Class 6X and Class 0/6 mixed cells are not flattened into universal one-to-one mappings.',
                  'No exact-article grease, cylindrical bore or locating-feature absence is inferred from suffix absence.',
                  'Existing article rating/mounting publication questions remain unresolved.',
                  'Independent extraction review remains outstanding.'],
        'identity_approved': False, 'new_specification_rows': 0}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write-snapshot', action='store_true')
    args = parser.parse_args()
    report = build_report()
    target = ROOT / 'registry/reports/ntn-tolerance-context.json'
    if args.write_snapshot:
        target.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    elif json.loads(target.read_text(encoding='utf-8')) != report:
        raise ValueError('NTN tolerance snapshot stale or altered')
    print('NTN tolerance context reproduced: P0 mapping proposed; raw wording and identity gaps retained.')
