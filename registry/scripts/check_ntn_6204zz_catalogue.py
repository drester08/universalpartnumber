"""Retain exact NTN 6204 catalogue context without correcting article cells."""
import argparse
import hashlib
import json
import sqlite3
from decimal import Decimal
from pathlib import Path
import pdfplumber
import check_ntn_shield_seal as catalogue
import check_ntn_6204zz as article_checker

ROOT = Path(__file__).resolve().parents[2]
ARTICLE_REPORT_SHA = 'AA2461CE23CAF12EE57C63A7860664241C167E0F145DB2AAC8AC1CE72A62EC67'
ROW = '47 14 1 0.5 14.2 6.65 0.505 13.2 16 000 18 000 12 000 10 000 6204 ZZ LLB LLU LLH N NR 44.6 2.46 1.35 0.4 52.7 1.12 25 28 42 53.5 3.3 1.2 1 0.5 0.106'


def extract(path=catalogue.PATH):
    if hashlib.sha256(path.read_bytes()).hexdigest().upper() != catalogue.SHA:
        raise ValueError('NTN catalogue revision changed')
    with pdfplumber.open(path) as pdf:
        if len(pdf.pages) != 12:
            raise ValueError('Catalogue page scope changed')
        design = pdf.pages[2]
        crop = design.crop((design.width*.109, design.height*.40, design.width*.196, design.height*.78))
        definition = ' '.join(crop.extract_text().split())
        for value in ('Non-contact shield type ZZ', 'Metal shield plate is affixed to the outer ring', 'V-groove and labyrinth clearance.'):
            if value not in definition:
                raise ValueError('ZZ construction column changed')
        if 'double shielded and double sealed bearings' not in ' '.join(design.extract_text().split()):
            raise ValueError('Double-shield construction scope missing')
        dimensions = pdf.pages[5]
        text = ' '.join(dimensions.extract_text().split())
        rows = [' '.join(line.split()) for line in dimensions.extract_text().splitlines() if '6204' in line]
        if rows != [ROW]:
            raise ValueError('Exact 6204 row changed or ambiguous')
        for heading in ('d 10-20 mm', 'Basic load rating', 'Installation-related dimensions', 'double sealed and double shielded type bearings', 'Does not include bearings with snap rings'):
            if heading not in text:
                raise ValueError('Catalogue header/footnote changed: ' + heading)
        bore_group = dimensions.crop((dimensions.width*.046, dimensions.height*.828, dimensions.width*.064, dimensions.height*.925))
        if ' '.join(bore_group.extract_text().split()) != '20':
            raise ValueError('6204 bore group label changed')
        mass_header = dimensions.crop((dimensions.width*.895, dimensions.height*.336, dimensions.width*.96, dimensions.height*.434))
        mass_text = ' '.join(mass_header.extract_text().split())
        if 'Mass3)' not in mass_text or 'kg' not in mass_text or '(approx.)' not in mass_text:
            raise ValueError('Approximate mass context changed')
    return {'zz_definition_column': definition, '6204_row_text': rows[0],
            'bore_group_label_mm': '20', 'mass_header_text': mass_text}


def verify_custody(connection, article):
    connection.row_factory = sqlite3.Row
    rows = connection.execute('SELECT s.publisher_name,s.source_url,a.artifact_id,a.sha256,a.retrieval_state FROM sources s JOIN source_artifacts a USING(source_id) WHERE s.source_id=?', ('SRC-NTN-SHIELD-SEAL-3015',)).fetchall()
    if len(rows) != 1 or tuple(rows[0]) != ('NTN Corporation','https://www.ntnglobal.com/en/products/catalog/pdf/3015E.pdf','ART-NTN-SHIELD-SEAL-3015',catalogue.SHA,'retrieved'):
        raise ValueError('Catalogue registered custody changed')
    part = connection.execute('SELECT manufacturer_id,manufacturer_part_number FROM manufacturer_parts WHERE manufacturer_part_id=?', (article['manufacturer_part_id'],)).fetchone()
    if part is None or tuple(part) != ('ORG-NTN-AMERICAS','6204ZZ'):
        raise ValueError('Exact manufacturer article namespace changed')
    obs = connection.execute('SELECT manufacturer_part_id,source_id,raw_payload_sha256,review_state FROM observations WHERE observation_id=?', (article['observation_id'],)).fetchone()
    if obs is None or tuple(obs)[:3] != ('MP-NTN-6204ZZ','SRC-NTN-6204ZZ',article['source_sha256']) or obs['review_state'] in ('rejected','superseded'):
        raise ValueError('Article observation custody changed')


def build_report():
    raw = (ROOT/'registry/reports/ntn-6204zz-source.json').read_bytes()
    if hashlib.sha256(raw).hexdigest().upper() != ARTICLE_REPORT_SHA:
        raise ValueError('Registered article report revision changed')
    article = json.loads(raw)
    if article != article_checker.build_report():
        raise ValueError('Exact article extraction changed')
    parsed = extract()
    with sqlite3.connect(ROOT/'registry/build/registry.sqlite') as db:
        verify_custody(db, article)
    return {'policy_version':'ntn-6204zz-catalogue-context-0.1',
        'source_id':'SRC-NTN-SHIELD-SEAL-3015','source_sha256':catalogue.SHA,
        'article_source_id':article['source_id'],'article_sha256':article['source_sha256'],
        'article_report_sha256':ARTICLE_REPORT_SHA,'manufacturer_part_id':'MP-NTN-6204ZZ',
        'catalogue_label':'CAT.No.3015-5/E 25.12.00 IP/IP',
        'definition_pdf_page':3,'definition_printed_pages':'3-4',
        'dimension_pdf_page':6,'dimension_printed_pages':'9-10',
        'extracted_evidence':parsed,
        'catalogue_context':{'d_mm':'20','D_mm':'47','B_mm':'14','dynamic_load_kn':'14.2',
            'static_load_kn':'6.65','grease_speed_per_minute':'16000','da_min_mm':'25',
            'da_max_mm':'28','Da_max_mm':'42','mass_approx_kg':'0.106'},
        'metric_static_comparison':{'catalogue_n':str(Decimal('6.65')*1000),
            'article_n_display':'6650','article_kn_display':'9.75','article_kn_converted_n':'9750',
            'difference_n':'3100','agreement_with_first_display':True,'publisher_correction':False},
        'closure_research':{'supported_interpretation':'double_non_contact_metal_shield',
            'basis':'Exact 6204 row ZZ column plus Table 1 construction and double-shield scope footnotes',
            'mapping_added':False,'independent_review':'outstanding'},
        'limitations':['Catalogue context is not an independently approved supplied article.',
            'Neither static display is removed or promoted; existing publication tasks and their evidence remain unchanged.',
            'Case-sensitive da max 28 and Da max 42 remain separate; original article cells are not reassigned.',
            'Approximate 0.106 kg catalogue mass is not a replacement for article 0.103 kg.',
            'N/NR availability does not prove exact article locating construction.',
            'Performance-test grease applies to tested 6305/6304 samples, not supplied 6204ZZ lubricant.',
            'No bore type, material standard, tolerance interpretation, equivalence or UPN approved.'],
        'identity_approved':False,'publisher_correction_obtained':False,
        'independent_extraction_review':'outstanding'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write-snapshot', action='store_true')
    args = parser.parse_args()
    report = build_report()
    target = ROOT/'registry/reports/ntn-6204zz-catalogue-context.json'
    if args.write_snapshot:
        target.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    elif json.loads(target.read_text(encoding='utf-8')) != report:
        raise ValueError('6204 catalogue research snapshot stale')
    print('Exact NTN 6204 catalogue context reproduced; source conflicts remain unresolved.')
