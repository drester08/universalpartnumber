"""Extract bounded manufacturer construction context, never supplied articles."""
import argparse
import hashlib
import json
import re
from pathlib import Path
import pdfplumber

ROOT=Path(__file__).resolve().parents[1]
PDF=ROOT/'artifacts/klinger/Maxiprofile-South-Africa-20261001.pdf'
SHA='0C632A50EFF0BA9BD3FBA663340B4BA0C52E1B1032BA1592078E025D452597D8'
URL='https://www.klinger.co.za/wp-content/uploads/2024/08/KLINGER-Maxiprofile-1.pdf'
HISTORICAL=ROOT/'reports/klinger-maxiprofile-comparison.json'
HISTORICAL_SHA='8B6CAA9D3B69FC81C544815D810B3828D0971E046361C4C6A352AF9B18688C9C'
PATTERN=re.compile(r'(.+?) (\d+)°C (.+)')


def materials(text):
    rows=[]
    component=None
    for line in text.splitlines():
        if line.startswith('Sealing Face Maximum'):
            component='facing'
        elif line.startswith('Core Maximum'):
            component='core'
        match=PATTERN.fullmatch(line)
        if match:
            if component is None:
                raise ValueError('Orphan material table row')
            rows.append(dict(component=component,material_label_raw=match[1],
                             published_maximum_temperature_C_raw=match[2],
                             published_colour_raw=match[3],physical_page=2,
                             temperature_is_article_rating=False,
                             colour_is_verified_standard_conformity=False))
    if len(rows)!=19 or sum(r['component']=='facing' for r in rows)!=4:
        raise ValueError('Expected four facing and fifteen core rows')
    if len({(r['component'],r['material_label_raw']) for r in rows})!=19:
        raise ValueError('Duplicate component/material key')
    return rows


def build_report():
    prior_bytes=HISTORICAL.read_bytes()
    if hashlib.sha256(prior_bytes).hexdigest().upper()!=HISTORICAL_SHA:
        raise ValueError('Historical MaxiProfile comparison revision changed')
    if hashlib.sha256(PDF.read_bytes()).hexdigest().upper()!=SHA:
        raise ValueError('KLINGER PDF revision changed')
    with pdfplumber.open(PDF) as document:
        if len(document.pages)!=6:
            raise ValueError('KLINGER document page count changed')
        pages=[' '.join(p.extract_text().split()) for p in document.pages]
        raw_second=document.pages[1].extract_text()
    cues={0:['KLINGER Maxiprofile','serrated metal core','soft-facing material','Core design','parallel','Convex','refurbished'],
          1:['Facing materials','Sealing Face','Core','ASME B16.20'],
          2:['Maxiprofile Styles','LA1','LA2','LA3','CA1,2, & 3','seal element only','guide ring','stainless steel','Partition Bars','tack-welded'],
          3:['Gasket selection and installation','Maximum temperature and pressure values alone'],
          4:['Discontinuous operation','never re-use a gasket'],
          5:['Re-use','never re-use gaskets']}
    for page,expected in cues.items():
        if any(cue not in pages[page] for cue in expected):
            raise ValueError('KLINGER construction or safety scope changed')
    return dict(policy_version='klinger-maxiprofile-context-0.1',publisher='KLINGER South Africa',
                source_url=URL,source_sha256=SHA,
                local_path='registry/artifacts/klinger/Maxiprofile-South-Africa-20261001.pdf',
                document_pages=6,visually_reviewed_physical_pages=[1,2,3,4,5,6],
                publication_date=None,source_registered=False,identity_approved=False,
                historical_comparison_sha256=HISTORICAL_SHA,historical_findings_resolved=False,
                component_material_context=materials(raw_second),
                style_context=[dict(style='LA1',profile='parallel',ring_context='outer centring ring',physical_page=3),
                               dict(style='LA2',profile='parallel',ring_context='seal element only',physical_page=3),
                               dict(style='LA3',profile='parallel',ring_context='outer guide ring may differ from core material',physical_page=3),
                               dict(style='CA1/CA2/CA3',profile='convex',ring_context='corresponding LA configurations; exact article drawing required',physical_page=3)],
                partition_context=dict(physical_page=3,construction='profiled pass partitions tack-welded into place'),
                diagram_scope=dict(physical_page=2,components=['facing layers','serrated metal core'],
                                   supplied_tuple_component_mapping=False,
                                   note='Local serration geometry does not label the three historical supplied dimensions.'),
                maintenance_scope_question=dict(core_refurbishment_page=1,non_reuse_pages=[5,6],
                                                publisher_clarification_outstanding=True,
                                                reuse_permission_for_supplied_gaskets=False),
                required_article_evidence=['exact style and parallel/convex profile','core material grade',
                                           'facing material grade','guide ring material and attachment',
                                           'core/facing/overall thickness','labelled drawing and dimension roles',
                                           'partition geometry where present','flange standard/class/size and source revision'],
                limitations=['Manufacturer product-family context is not an exact supplied article.',
                             'Generic Nonas facing is not assigned to a specific KLINGERSIL grade.',
                             'Material-table maximum temperatures and general pressure figures are not universal joint ratings.',
                             'Printed colour table is not independent ASME conformity verification.',
                             'URL upload folder is not a verified publication date or current edition.',
                             'No fixed/floating ring assignment inferred from schematic appearance alone.',
                             'No historical CSV correction or component-name assignment.',
                             'Source reuse and independent extraction/applicability review remain outstanding.'])


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write-snapshot',action='store_true')
    args=parser.parse_args()
    report=build_report()
    target=ROOT/'reports/klinger-maxiprofile-context.json'
    if args.write_snapshot:
        target.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    elif json.loads(target.read_text(encoding='utf-8'))!=report:
        raise ValueError('KLINGER context snapshot stale')
    print('KLINGER Maxiprofile: 19 component material rows, four scoped style contexts; no article approval.')
