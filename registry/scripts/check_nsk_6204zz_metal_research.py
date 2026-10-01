"""Bounded NSK manufacturer closure evidence; no article defaults or approvals."""
import argparse
import hashlib
import json
from pathlib import Path
import pdfplumber

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT/'artifacts/nsk/EN-DGBB-Europe-20261001.pdf'
SHA = '516844D7485922BE5888829573F5AB67E13052B0365203C52F78AE068A37B865'
URL = 'https://www.nsk.com/content/dam/nsk-marketing/projects-completed/literature/product-brochures/deep-grooves-bbs_product-brochure/en_deep-grooves-bbs_product-brochure/preview-pdf_deep-grooves-bbs_product-brochure_en/EN_Deep%20Grooves%20BBs_Product_Brochure_low-res.pdf'
REGISTRATION_SHA = '1C51FD8B1373CCA3659C86AE88F7DD15CAE7BB146D54CB7583BAA7BA4B41D11F'
CLOSURE_ROWS = ['Shields and Seals', 'Blank Open bearing', 'Z Single metal shield',
                'ZZ Double metal shields', 'V Single non-contact seal',
                'VV Double non-contact seals', 'DW Single light-contact seal',
                'DDW Double light-contact seals', 'DU Single contact seal',
                'DDU Double contact seals']


def extract():
    if hashlib.sha256(PATH.read_bytes()).hexdigest().upper() != SHA:
        raise ValueError('NSK Europe original PDF revision changed')
    with pdfplumber.open(PATH) as pdf:
        if len(pdf.pages) != 16:
            raise ValueError('NSK Europe page count changed')
        page = pdf.pages[8]
        full = ' '.join(page.extract_text().split())
        for scope in ('62 Metric light series', '04 : 20 mm', 'DEEP GROOVE BALL BEARINGS 9', '62 05 T1X ZZ NR C3 E NS7 S'):
            if scope not in full:
                raise ValueError('NSK Europe designation family or example changed')
        table = page.crop((page.width*.31, page.height*.58, page.width*.66, page.height*.8))
        rows = [' '.join(line.split()) for line in table.extract_text().splitlines()]
        if rows != CLOSURE_ROWS:
            raise ValueError('NSK Europe shield/seal table boundary changed')
        page = pdf.pages[6]
        shield = ' '.join(page.crop((page.width*.73, page.height*.25, page.width*.91, page.height*.43)).extract_text().split())
        if shield != 'ZZ Non-contact shield':
            raise ValueError('NSK Europe ZZ figure classification changed')
        page = pdf.pages[10]
        special = ' '.join(page.crop((page.width*.49, page.height*.54, page.width*.92, page.height*.82)).extract_text().split())
        if 'NSK have also developed shielded high capacity bearings.' not in special or 'Glass Reinforced Polyamide' not in ' '.join(page.extract_text().split()):
            raise ValueError('NSK Europe special-design boundary changed')
        back = ' '.join(pdf.pages[15].extract_text().split())
        if 'Ref: DGB/H/E/01.15' not in back or 'Copyright NSK 2009' not in back:
            raise ValueError('NSK Europe publication reference changed')
    return dict(closure_rows=rows, zz_figure_label=shield,
                family='62 Metric light series', bore_code='04 : 20 mm',
                illustrative_designation='62 05 T1X ZZ NR C3 E NS7 S',
                publication_reference='DGB/H/E/01.15', copyright_year=2009)


def build_report():
    raw = (ROOT/'reports/nsk-6204zz-code-registration.json').read_bytes()
    if hashlib.sha256(raw).hexdigest().upper() != REGISTRATION_SHA:
        raise ValueError('NSK current registration revision changed')
    prior = json.loads(raw)
    if prior['manufacturer_part_id'] != 'MP-NSK-6204ZZ' or prior['registered_new_sources'] is not True:
        raise ValueError('NSK registered article/context scope changed')
    evidence = extract()
    return dict(policy_version='nsk-6204zz-metal-research-0.1', manufacturer_part_id='MP-NSK-6204ZZ',
                source_url=URL, local_path='registry/artifacts/nsk/EN-DGBB-Europe-20261001.pdf',
                source_sha256=SHA, page_count=16, reviewed_physical_pages=[7,8,9,11,16],
                extracted_evidence=evidence, registration_report_sha256=REGISTRATION_SHA,
                closure_hypothesis=dict(both_sides=True, contact_form='non_contact', material_class='metal',
                                        metal_grade=None, canonical_code='double_non_contact_metal_shield'),
                ready_for_scoped_mapping_proposal=True, canonical_mapping_added=False,
                registered_new_source=False, identity_approved=False, independent_review='outstanding',
                limitations=['Historical brochure; current supplied-article applicability requires review.',
                             'General designation table and ZZ figure support closure terminology, not exact metal grade.',
                             'Nitrile sealing-material prose is not assigned to a metal shield.',
                             'No glass-reinforced polyamide cage or low-torque grease from special designs transferred.',
                             'NS7 and the 6205 example are not supplied 6204ZZ defaults.',
                             'Blank retention wording is not promoted to exact locating construction.',
                             'No new article specifications, equivalence decision or UPN.',
                             'Source reuse and independent interpretation review outstanding.'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write-snapshot', action='store_true')
    args = parser.parse_args()
    report = build_report()
    path = ROOT/'reports/nsk-6204zz-metal-research.json'
    if args.write_snapshot:
        path.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    elif json.loads(path.read_text(encoding='utf-8')) != report:
        raise ValueError('NSK metal research snapshot stale')
    print('NSK own scoped ZZ metal/non-contact evidence reproduced; proposal and independent review outstanding.')
