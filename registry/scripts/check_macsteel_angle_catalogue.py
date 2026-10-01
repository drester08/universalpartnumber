"""Capture five dated listing pages without collapsing seller identities."""
import argparse
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from decimal import Decimal
from urllib.parse import urljoin, urlparse
from check_macsteel_angle_offers import ROOT, BASE, ListingParser, clean, seed

HASHES = [
    '276DE6948BE6071E4A89C8CD026F46D0711A5975D1B21F735312BB44215A838A',
    'F6B273EA85D7BF9DD1F726EBBED58766971B521CBCCB8D6472A356587AF81744',
    'B51D32C7A5FEA4803761DE2DA52ACA4304CAC93EF1902251D3EF1E114109079E',
    '70B1240B817BBD25648277CB89D42281E241FE3EA90D01EF993F74552669B128',
    '98C2AF6C6FACE915CB89123BB603B54CAD46F254B86E7C1D4D8652FC42A87490',
]


def parse_page(html, page):
    if not 1 <= page <= 5 or not re.search(r'<li class="current-page"><span>' + str(page) + r'</span>', html):
        raise ValueError('Pagination/current page not established')
    if max(map(int, re.findall(r'data-page="(\d+)"', html))) != [5,5,5,5,4][page-1]:
        raise ValueError('Pagination horizon changed')
    parser = ListingParser()
    parser.feed(html)
    if len(parser.rows) != [30,30,30,30,16][page-1]:
        raise ValueError('Page row count changed')
    records = []
    for row in parser.rows:
        cells = row['cells']
        if len(cells) != 9 or cells[0]['class'] != 'sku' or cells[1]['class'] != 'name':
            raise ValueError('Unexpected row layout')
        sku, name = clean(cells[0]['text']), clean(cells[1]['text'])
        if not re.fullmatch(r'AE_(CQ|S355RA)_\d+', sku):
            raise ValueError('Unknown seller SKU family')
        number = r'(\d+(?:\.\d+)?)'
        pattern = r'ANGLE EQUAL (COMMERCIAL QUALITY|S355 JR\+AR EN 10025-2 AS ROLLED) ' + number + ' x ' + number + ' x ' + number + r' (\d+\.\d+)Mtr'
        match = re.fullmatch(pattern, name)
        variant = False
        if not match:
            match = re.fullmatch(r'ANGLE EQUAL (COMMERCIAL QUALITY|S355 JR\+AR EN 10025-2 ASROLLED) (\d+\.\d+) x (\d+\.\d+) x (\d+\.\d+) x (\d+\.\d+) m', name)
            variant = True
        if not match:
            raise ValueError('Unknown description structure: ' + name)
        grade, *dimensions = match.groups()
        a,b,t,length = map(Decimal, dimensions)
        if min(a,b,t,length) <= 0 or a != b:
            raise ValueError('Invalid equal-angle dimensions')
        if (sku.startswith('AE_CQ_')) != (grade == 'COMMERCIAL QUALITY'):
            raise ValueError('SKU/description material-family conflict')
        if len(cells[1]['links']) != 1 or clean(cells[3]['text']) != 'Log in For Price':
            raise ValueError('Detail or commercial display changed')
        detail = urljoin(BASE, cells[1]['links'][0])
        if urlparse(detail).netloc != urlparse(BASE).netloc:
            raise ValueError('Off-publisher detail URL')
        records.append({'seller_sku':sku,'offered_name':name,'detail_url':detail,
                        'source_id':'SRC-MACSTEEL-ANGLE-P4' if page==4 else f'SRC-MACSTEEL-AE20261001-P{page}', 'page':page,
                        'source_locator':'tr.product-item[data-productid="'+row['product_id']+'"]',
                        'grade_statement':grade,'alternate_name_format':variant,
                        'leg_a_mm':float(a),'leg_b_mm':float(b),'thickness_mm':float(t),'length_m':float(length),
                        'manufacturer_identity_verified':False})
    return records


def catalogue():
    records = []
    with (ROOT/'registry/data/source-artifacts.csv').open(encoding='utf-8-sig',newline='') as f:
        artifacts={r['artifact_id']:r for r in csv.DictReader(f)}
    for page, expected in enumerate(HASHES, 1):
        path = f'registry/artifacts/macsteel/equal-angle-20261001-page{page}.html'
        data = (ROOT/path).read_bytes()
        if hashlib.sha256(data).hexdigest().upper() != expected:
            raise ValueError('Listing revision changed')
        artifact=artifacts[f'ART-MACSTEEL-AE20261001-P{page}']
        if artifact['sha256']!=expected or artifact['local_path']!=path or artifact['retrieval_state']!='retrieved':
            raise ValueError('Listing custody mismatch')
        records.extend(parse_page(data.decode('utf-8-sig'),page))
    if len({r['seller_sku'] for r in records}) != len(records):
        raise ValueError('Repeated SKUs across pages; snapshot may have shifted')
    groups=defaultdict(list)
    for r in records:
        context='CQ' if r['seller_sku'].startswith('AE_CQ_') else 'S355JR+AR'
        groups[(context,r['leg_a_mm'],r['leg_b_mm'],r['thickness_mm'],r['length_m'])].append(r['seller_sku'])
    return {'snapshot_date':'2026-10-01','page_hashes':HASHES,
            'scope':'All five observed category pages at capture; not global completeness or stock verification',
            'offer_count':len(records),'family_counts':dict(Counter('CQ' if r['seller_sku'].startswith('AE_CQ_') else 'S355RA' for r in records)),
            'offers':records,'same_nominal_key_groups':[{'nominal_key':list(k),'seller_skus':v,'identity_approved':False} for k,v in sorted(groups.items()) if len(v)>1],
            'identity_approved':False,'warnings':['Same nominal key does not prove duplicate article or interchangeability','CQ is not a verified material grade','Five sequential requests are not an atomic supplier snapshot','No maker, stock, price, package or billing assertions approved']}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--write-snapshot',action='store_true')
    args=parser.parse_args()
    report=catalogue()
    with (ROOT/'registry/reports/macsteel-angle-offers.json').open(encoding='utf-8') as f:
        old={r['seller_sku'] for r in json.load(f)['offers']}
    path=ROOT/'registry/data/supplier-offers.csv'
    with path.open(encoding='utf-8-sig',newline='') as f:
        reader=csv.DictReader(f); fields=reader.fieldnames; actual=list(reader)
    by_id={r['supplier_offer_id']:r for r in actual}
    expected=[]; missing=[]
    for r in report['offers']:
        offer=seed(r)
        offer['source_id']='SRC-MACSTEEL-ANGLE-P4' if r['seller_sku'] in old else r['source_id']
        expected.append(offer)
        existing=by_id.get(offer['supplier_offer_id'])
        if existing is None: missing.append(offer)
        elif existing != offer: raise ValueError('Offer changed; refusing to overwrite history')
    if not old.issubset({r['seller_sku'] for r in report['offers']}):
        raise ValueError('Earlier offers disappeared; resolve before expanding seeds')
    if {r['supplier_offer_id'] for r in actual if r['supplier_id']=='ORG-MACSTEEL-SA'} - {r['supplier_offer_id'] for r in expected}:
        raise ValueError('Unexpected Macsteel records outside captured scope')
    output=ROOT/'registry/reports/macsteel-angle-catalogue.json'
    if args.write_snapshot:
        if missing:
            with path.open('a',encoding='utf-8',newline='') as f: csv.DictWriter(f,fields).writerows(missing)
        output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    elif missing or json.loads(output.read_text(encoding='utf-8'))!=report:
        raise ValueError('Catalogue seeds or report are stale')
    print(f"Verified {report['offer_count']} seller offers; {len(report['same_nominal_key_groups'])} same-nominal-key groups remain unapproved.")


if __name__=='__main__': main()
