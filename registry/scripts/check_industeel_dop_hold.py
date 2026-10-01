"""Verify retained declaration/reuse evidence, without extracting performance tables."""
import argparse
import hashlib
import json
from pathlib import Path
from pypdf import PdfReader
from check_skf_marketplace_hold import TermsText

ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT/'artifacts/industeel/s355jr-dop-rev6-captured20261001.pdf'
TERMS = ROOT/'artifacts/industeel/legal-mentions-captured20261001.html'
PDF_SHA = '26371B8D3BB6B10AAEDA6F482DDD597C02FC47C16EC61ED62A5A28E15173AA62'
TERMS_SHA = '4904AF500D8BD779E7F623E1BA3A3CF1CFC07C26EF49E8DACBF446FB0ADC4FB6'
REPORT = ROOT/'reports/industeel-dop-authorization-hold.json'


def build_report(pdf=PDF, terms=TERMS):
    for path, expected in ((pdf,PDF_SHA),(terms,TERMS_SHA)):
        if hashlib.sha256(path.read_bytes()).hexdigest().upper() != expected:
            raise ValueError('Industeel authorization evidence revision changed')
    if not pdf.read_bytes().startswith(b'%PDF-'):
        raise ValueError('Retained declaration is not a PDF')
    reader = PdfReader(pdf)
    if len(reader.pages) != 2 or reader.metadata.title != 'DOPIL_S355JR_1.0045 CE Eng.':
        raise ValueError('Declaration identity/page count changed')
    parser = TermsText()
    parser.feed(terms.read_text(encoding='utf-8'))
    text = ' '.join(' '.join(parser.parts).split())
    if 'Copyright and intellectual property' not in text or 'without express authorization' not in text or 'without the prior written consent' not in text:
        raise ValueError('Publisher reuse restriction cues missing')
    return dict(policy_version='industeel-dop-authorization-hold-0.1',
                source_url='https://industeel.arcelormittal.com/fichier/dopil_s355jr_1-0045-en/',
                private_pdf_path='registry/artifacts/industeel/s355jr-dop-rev6-captured20261001.pdf',
                source_sha256=PDF_SHA, document_identifier='DOPIL_S355JR_1.0045',
                document_revision='6', document_language='English', page_count=2,
                stated_manufacturer='INDUSTEEL France', stated_production_site='Châteauneuf',
                printed_signature_date='2025-11-04', publication_date=None,
                captured_date='2026-10-01', pdf_pages_visually_reviewed=[1,2],
                terms_url='https://industeel.arcelormittal.com/legal-mentions/',
                private_terms_path='registry/artifacts/industeel/legal-mentions-captured20261001.html',
                terms_sha256=TERMS_SHA, terms_stated_update_date='2024-04-15',
                terms_locator='English Copyright and intellectual property section',
                status='authorization_hold_pending_scope_specific_permission',
                source_registered=False, article_ingested=False, performance_table_extracted=False,
                supplied_dataset_rows_compared=False, manufacturer_authenticity_independently_verified=False,
                declared_certification_independently_verified=False, reuse_permission=False,
                identity_approved=False, application_suitability_approved=False, production_upn_allowed=False,
                next_action='Obtain permitted-use review and independently verify declaration authenticity, revision, manufacturer/site, thickness bounds and exact stock provenance before technical intake. Do not transfer a grade-family declaration into supplied-stock certification or cross-manufacturer identity.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write-snapshot', action='store_true')
    args = parser.parse_args()
    report = build_report()
    if args.write_snapshot:
        REPORT.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    elif json.loads(REPORT.read_text(encoding='utf-8')) != report:
        raise ValueError('Industeel hold snapshot stale or altered')
    print('Industeel declaration custody verified privately; performance intake and reuse remain held.')
