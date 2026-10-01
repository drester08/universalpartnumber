"""NSK-specific staged source evidence; no canonical closure or grease default."""
import argparse
import hashlib
import json
from pathlib import Path
import pdfplumber
import check_nsk_6204zz as article

ROOT=Path(__file__).resolve().parents[2]
BROCHURE=ROOT/'registry/artifacts/nsk/NSK-APB-DGBB-20261001.pdf'
CATALOGUE=ROOT/'registry/artifacts/nsk/E1103C-partC-20261001.pdf'
BROCHURE_SHA='15E748AF493A8442A7CE3C82C243F2C82ACA5B0235F6B71B366F8CD03538CC61'
CATALOGUE_SHA='3C1ACFDA536BB6A77487D1FCF6812618E31C62582FB20089659D20B7AF07A6E2'
ARTICLE_REPORT_SHA='12E89CD3494AEFDDD02C45416D5643439D7204634478448574BDA976152E003B'
ROW='47 14 1 14 100 6 600 13.1 17 000 11 000 20 000 6204 ZZ VV DDU N NR 2.46 1.35 44.6 0.4 0.5 52.7 1.12 25 26.5 42 1 53.5 3.3 0.107'


def extract():
    for path,sha in [(BROCHURE,BROCHURE_SHA),(CATALOGUE,CATALOGUE_SHA)]:
        if hashlib.sha256(path.read_bytes()).hexdigest().upper()!=sha:
            raise ValueError('NSK staged PDF revision changed')
    with pdfplumber.open(BROCHURE) as pdf:
        if len(pdf.pages)!=12:
            raise ValueError('NSK brochure page scope changed')
        page=pdf.pages[9]
        full=' '.join(page.extract_text().split())
        if 'DESIGNATION SYSTEM SINGLE ROW DEEP GROOVE BALL BEARINGS' not in full:
            raise ValueError('NSK designation family changed')
        crop=page.crop((page.width*.08,page.height*.735,page.width*.5,page.height*.93))
        closure=' '.join(crop.extract_text().split())
        for cell in ('Z non-contact shield, one side only','ZZ non-contact shield, both sides','VV non-contact seal, both sides','DDU contact seal, both sides'):
            if cell not in closure:
                raise ValueError('NSK closure rows changed')
        family=' '.join(pdf.pages[4].extract_text().split())
        if '62 6200 to 6240 6244 to 6272' not in family or 'Table 1: Single row deep groove ball bearings series and size range' not in family:
            raise ValueError('NSK family-range context changed')
    with pdfplumber.open(CATALOGUE) as pdf:
        if len(pdf.pages)!=185:
            raise ValueError('NSK industrial catalogue page scope changed')
        # This publication contains overlapping duplicate text objects. Remove
        # same-position duplicates only; do not collapse repeated characters.
        design=' '.join(pdf.pages[3].dedupe_chars().extract_text().split())
        for context in ('SINGLE-ROW DEEP GROOVE BALL BEARINGS','ZZ: Shield on both sides','The grease designation is required when seals/shields are used on both sides.'):
            if context not in design:
                raise ValueError('NSK industrial designation scope changed')
        page=pdf.pages[11].dedupe_chars()
        lines=[' '.join(line.split()) for line in page.extract_text().splitlines()]
        rows=[line for line in lines if '6204' in line]
        if rows!=[ROW]:
            raise ValueError('NSK exact 6204 row changed or ambiguous')
        bore=' '.join(page.crop((page.width*.055,page.height*.398,page.width*.068,page.height*.5)).extract_text().split())
        if bore!='20':
            raise ValueError('NSK 6204 bore group label changed')
        full=' '.join(lines)
        for context in ('Bore Diameter 20','Basic Load Ratings','Limiting Speeds','approx.','When using bearings with rotating outer rings, contact NSK if they are sealed, shielded, or have snap rings.'):
            if context not in full:
                raise ValueError('NSK row header/footnote scope changed')
    return {'brochure_closure_rows':closure,'industrial_6204_row':rows[0],
        'bore_group_label_mm':bore,'grease_designation_requirement':'The grease designation is required when seals/shields are used on both sides.',
        'text_extraction_policy':'pdfplumber dedupe_chars on industrial pages; no character-pair string rewriting'}


def build_report():
    raw=(ROOT/'registry/reports/nsk-6204ZZ-source.json').read_bytes()
    if hashlib.sha256(raw).hexdigest().upper()!=ARTICLE_REPORT_SHA:
        raise ValueError('NSK article report revision changed')
    registered=json.loads(raw)
    if registered!=article.build_report() or registered['manufacturer_part_id']!='MP-NSK-6204ZZ':
        raise ValueError('NSK exact article scope changed')
    evidence=extract()
    return {'policy_version':'nsk-6204zz-staged-code-context-0.1','registered_new_sources':False,
        'manufacturer_part_id':'MP-NSK-6204ZZ','article_source_id':'SRC-NSK-6204ZZ',
        'article_sha256':article.SHA,'article_report_sha256':ARTICLE_REPORT_SHA,
        'sources':[{'publisher':'NSK Americas','url':'https://info.nskamericas.com/hubfs/DGBB/NSK_APB_Deep_Groove_Ball_Bearings.pdf',
            'local_path':'registry/artifacts/nsk/NSK-APB-DGBB-20261001.pdf','sha256':BROCHURE_SHA,'pages':12,'reviewed_physical_pages':[5,10]},
            {'publisher':'NSK Ltd.','url':'https://www.nsk.com/content/dam/nsk/common/catalogs/ctrgPdf/bearings/e1103c_partc.pdf',
            'local_path':'registry/artifacts/nsk/E1103C-partC-20261001.pdf','sha256':CATALOGUE_SHA,'pages':185,
            'reviewed_physical_pages':[4,12],'reviewed_printed_pages':['C006-C007','C022-C023']}],
        'extracted_evidence':evidence,
        'closure_research':{'both_sides':True,'contact_form':'non_contact','shield_material':None,
            'canonical_mapping_added':False,'basis':'NSK own single-row deep-groove designation table plus exact 6204 ZZ row'},
        'catalogue_context':{'d_mm':'20','D_mm':'47','B_mm':'14','dynamic_load_n':'14100','static_load_n':'6600',
            'grease_speed_per_minute':'17000','da_min_mm':'25','da_max_mm':'26.5','Da_max_mm':'42','mass_approx_kg':'0.107'},
        'limitations':['Two new private PDF captures are staged, not registered sources/artifacts or approved evidence.',
            'Selected pages inspected; no claim that all 185 catalogue pages were reviewed.',
            'Steel cage/material prose is not an explicit shield-metal definition in reviewed pages.',
            'No NTN definition, miniature-family shield definition or other article default is transferred.',
            'Catalogue row shares closure variants; mass and speed are scoped context, not supplied-article identity.',
            'NS7 is a designation example, not proof of supplied 6204ZZ grease.',
            'N/NR availability and blank designation explanations do not independently resolve exact locating construction.',
            'Independent extraction/interpretation review and source reuse terms outstanding.'],
        'identity_approved':False,'publisher_correction_obtained':False,
        'independent_extraction_review':'outstanding'}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write-snapshot',action='store_true')
    args=parser.parse_args()
    report=build_report()
    path=ROOT/'registry/reports/nsk-6204zz-code-research.json'
    if args.write_snapshot:
        path.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    elif json.loads(path.read_text(encoding='utf-8'))!=report:
        raise ValueError('NSK staged code research snapshot stale')
    print('NSK 6204 ZZ two-sided non-contact context retained; shield material and supplied lubricant unresolved.')
