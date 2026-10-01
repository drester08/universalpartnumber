"""Screen all captured offers within their stated material context, not across it."""
import argparse,hashlib,json
from collections import Counter
from decimal import Decimal
from check_macsteel_angle_catalogue import catalogue,ROOT

INPUT_HASHES={
    'macsteel-angle-datasheet.json':'F3E760746EC50F1D6270180B67F77AD9C6DF0B063934CEEE4CCEB5FCEF158E54',
    'macsteel-angle-catalogue.json':'421209BBDB39F3F244DEBDCD743EA09300B3D584713387A1639CC13FEF509173',
}


def key(record):
    return tuple(Decimal(str(record[k])) for k in ('leg_a_mm','leg_b_mm','thickness_mm'))


def screen(offer,facts):
    if not offer['seller_sku'].startswith(('AE_CQ_','AE_S355RA_')):
        raise ValueError('Unknown material-context routing for seller SKU')
    table=1 if offer['seller_sku'].startswith('AE_CQ_') else 2
    matches=[f for f in facts if f['pdf_table']==table and key(f)==key(offer)]
    other=[f for f in facts if f['pdf_table']!=table and key(f)==key(offer)]
    outcome='nominal_context_candidate' if len(matches)==1 else 'source_context_gap' if not matches else 'ambiguous_context_candidate'
    return {'seller_sku':offer['seller_sku'],'source_id':offer['source_id'],
            'listing_locator':offer['source_locator'],'length_m':offer['length_m'],
            'raw_grade_statement':offer['grade_statement'],
            'requested_table_context':table,'nominal_geometry_mm':[str(x) for x in key(offer)],
            'outcome':outcome,'same_context_candidates':matches,
            'other_context_geometry_only':other,
            'availability_confirmation_required':any(f['availability_footnote_applies'] for f in matches),
            'delivery_condition_verified':False,'route_verified':False,
            'exact_article_verified':False,'identity_approved':False}


def build_report():
    inputs={}
    for name,digest in INPUT_HASHES.items():
        raw=(ROOT/'registry/reports'/name).read_bytes()
        if hashlib.sha256(raw).hexdigest().upper()!=digest:
            raise ValueError('Parent report revision changed: '+name)
        inputs[name]=json.loads(raw)
    captured=catalogue()
    if captured!=inputs['macsteel-angle-catalogue.json']:
        raise ValueError('Parent catalogue no longer reproduces retained HTML')
    source=inputs['macsteel-angle-datasheet.json']
    for suffix in ('0061','0064'):
        raw=(ROOT/f'registry/artifacts/macsteel/AE_S355RA_{suffix}.pdf').read_bytes()
        if hashlib.sha256(raw).hexdigest().upper()!=source['pdf_sha256']:
            raise ValueError('Parent PDF revision changed')
    records=[screen(o,source['table_facts']) for o in captured['offers']]
    counts=dict(Counter(r['outcome'] for r in records))
    if len(records)!=136 or counts!={'nominal_context_candidate':126,'source_context_gap':10}:
        raise ValueError('Coverage outcomes revised; inspect source before replacement')
    return {'report_date':'2026-10-01','parent_report_hashes':INPUT_HASHES,
            'pdf_sha256':source['pdf_sha256'], 'offer_count':len(records),'outcome_counts':counts,
            'records':records,'identity_approved':False,
            'limitations':['Generic family observations; not exact saleable article evidence',
                           'CQ does not establish a specific steel grade',
                           'S355JR table does not verify listing JR+AR delivery condition',
                           'Geometry found in another material context is not grade or mass evidence',
                           'Length remains a seller assertion and is not independently verified by section table',
                           'Previous source transcription remains independently unreviewed']}


def main():
    p=argparse.ArgumentParser();p.add_argument('--write-snapshot',action='store_true');a=p.parse_args()
    report=build_report();path=ROOT/'registry/reports/macsteel-angle-coverage.json'
    if a.write_snapshot:path.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    elif json.loads(path.read_text(encoding='utf-8'))!=report:raise ValueError('Coverage report stale or altered')
    print('Screened136offers:126nominal-context candidates;10context gaps; no identity approval.')


if __name__=='__main__':main()
