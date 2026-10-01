"""Verify ten seller assertions without treating shared generic PDFs as corroboration."""
import argparse,csv,hashlib,json,re
from decimal import Decimal
from check_macsteel_cq_pair import DetailParser
from check_macsteel_angle_coverage import ROOT,build_report as coverage_report
from check_macsteel_angle_datasheet import SHA,extract_pdf

HASHES = {
    "AE_S355RA_0008": "C4E79F8C5D3DA194363DFD78CD88F58F1BAEBE81EFB87FF4670D522185B54FD5",
    "AE_S355RA_0016": "5693A61CF7461308BBB9D4603695B8E3DD52257F31A3AC7D3AEEDB587F5CC31B",
    "AE_S355RA_0023": "5699A3EDE1AAE0616CF46F045617394B24009D1591B4C2B97D11E53E379AE025",
    "AE_S355RA_0593": "B485B27CCF6784E900E94A60BF487273C7686AFA4E464B6009FA6365ADECD74A",
    "AE_S355RA_0030": "1211C9EB3D13AA1DC1D3BE7ED41E223381CBA703092A901659A1AFDD199C7F94",
    "AE_S355RA_0034": "633DA4335698D17AD5B5F20A52429F4698D3F42153B38CD2060F7DE3A5EAF4F4",
    "AE_S355RA_0032": "5CE0259419CFA2AE4F2403A276650EBF0CD280815B3748C88AE9305F17235F04",
    "AE_S355RA_0039": "E14BE42B7C66F027691A2860927D9339D3694033D7C0F3DA121EC453D8201D81",
    "AE_S355RA_0044": "FCFBA80340D0F6A81612467A20E92036AD63343619D8F19F367D516DC9FD3EF9",
    "AE_S355RA_0049": "6CACDB4A520AE683DF7C6895558DA8F23610BC2903D1F4F99EC4C6C81B92B520"
}


def parse_detail(html,offer):
    parser=DetailParser();parser.feed(html)
    sku=offer['seller_sku']
    if parser.skus!=[sku] or len(parser.heading)!=1 or len(parser.cells)!=10:
        raise ValueError('Ambiguous detail identity or specification block')
    specs={}
    for i,name in enumerate(('Size','Grade','Thickness','UOM','Length')):
        if parser.cells[2*i]!=('spec-name',name) or parser.cells[2*i+1][0]!='spec-value':
            raise ValueError('Specification schema revised')
        specs[name]=parser.cells[2*i+1][1]
    size=re.fullmatch(r'(\d+\.\d+) X (\d+\.\d+)',specs['Size'])
    thickness=re.fullmatch(r'(\d+\.\d+)mm',specs['Thickness'])
    length=re.fullmatch(r'(\d+\.\d+)m',specs['Length'])
    if not size or not thickness or not length:
        raise ValueError('Unsupported dimension format or missing units')
    values=[Decimal(size[1]),Decimal(size[2]),Decimal(thickness[1]),Decimal(length[1])]
    if min(values)<=0:raise ValueError('Invalid visible dimensions')
    actual=dict(zip(('leg_a_mm','leg_b_mm','thickness_mm','length_m'),values))
    diffs=[k for k,v in actual.items() if v!=Decimal(str(offer[k]))]
    if specs['Grade']!=offer['grade_statement']:diffs.append('grade_statement')
    if parser.heading[0]!=offer['offered_name']:diffs.append('offered_name')
    links=sorted(set(parser.links))
    if links!=['https://shop.macsteel.co.za/SpecSheets/'+sku+'.pdf']:
        raise ValueError('Technical link changed or ambiguous')
    return {'seller_sku':sku,'heading':parser.heading[0],'visible_specifications':specs,
            'detail_locator':'h1; span[id^=sku-]; named td.spec-name/td.spec-value pairs',
            'linked_pdf_url':links[0],'listing_differences':diffs,
            'exact_article_verified':False,'identity_approved':False}


def build_report():
    prior=coverage_report()
    gaps={r['seller_sku']:r for r in prior['records'] if r['outcome']=='source_context_gap'}
    if set(gaps)!=set(HASHES):raise ValueError('Gap scope changed')
    captured=json.loads((ROOT/'registry/reports/macsteel-angle-catalogue.json').read_text(encoding='utf-8'))
    offers={o['seller_sku']:o for o in captured['offers']}
    with (ROOT/'registry/data/source-artifacts.csv').open(encoding='utf-8-sig',newline='') as f:
        artifacts={a['artifact_id']:a for a in csv.DictReader(f)}
    records=[]
    for sku,expected in HASHES.items():
        suffix=sku.split('_')[-1]
        for kind,digest,extension in [('HTML',expected,'html'),('PDF',SHA,'pdf')]:
            path='registry/artifacts/macsteel/'+sku+'-gap-20261001.'+extension
            data=(ROOT/path).read_bytes();a=artifacts['ART-MACSTEEL-GAP-'+suffix+'-'+kind]
            if hashlib.sha256(data).hexdigest().upper()!=digest or a['sha256']!=digest or a['local_path']!=path or a['retrieval_state']!='retrieved':
                raise ValueError('Custody mismatch: '+sku+' '+kind)
            if kind=='HTML':detail=parse_detail(data.decode('utf-8-sig'),offers[sku])
            if kind=='HTML' and a['artifact_url']!=offers[sku]['detail_url']:
                raise ValueError('Detail URL/custody mismatch')
            if kind=='PDF':
                if a['artifact_url']!=detail['linked_pdf_url']:raise ValueError('PDF link/custody mismatch')
        detail.update({'detail_source_id':'SRC-MACSTEEL-GAP-'+suffix+'-HTML',
                       'pdf_source_id':'SRC-MACSTEEL-GAP-'+suffix+'-PDF',
                       'pdf_sha256':SHA,'generic_pdf_context_candidate_count':0,
                       'outcome':'seller_detail_agrees_generic_context_gap_remains' if not detail['listing_differences'] else 'listing_detail_conflict'})
        records.append(detail)
    facts=extract_pdf(ROOT/'registry/artifacts/macsteel/AE_S355RA_0008-gap-20261001.pdf')
    earlier=json.loads((ROOT/'registry/reports/macsteel-angle-datasheet.json').read_text(encoding='utf-8'))
    if facts!=earlier['table_facts']:raise ValueError('Shared PDF transcription changed')
    return {'report_date':'2026-10-01','detail_hashes':HASHES,'records':records,
            'detail_count':len(records),'identical_pdf_content_count':1,'new_pdf_urls':10,
            'independent_corroboration':False,'identity_approved':False,
            'limitations':['Ten seller grade assertions are not independent manufacturer verification',
                           'Ten PDF links return the already reviewed generic sheet; same content is not ten independent sources',
                           'All ten S355JR table context gaps remain open',
                           'EA does not establish order quantity or package level',
                           'Maker, grade certificate, route, tolerances and current stock remain unverified']}


def main():
    p=argparse.ArgumentParser();p.add_argument('--write-snapshot',action='store_true');args=p.parse_args()
    report=build_report();output=ROOT/'registry/reports/macsteel-angle-gap-details.json'
    if args.write_snapshot:output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    elif json.loads(output.read_text(encoding='utf-8'))!=report:raise ValueError('Detail-gap report stale or altered')
    print('Verified10seller details and10identical generic PDF links; all10context gaps remain open.')


if __name__=='__main__':main()
