"""Reproduce seller-offer capture from private, checksummed Macsteel HTML.

--write generates research output and mechanically appends missing offer seeds.
It never creates manufacturer parts, identity approvals, prices or UPNs.
"""
import argparse
import csv
import hashlib
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin

ROOT = Path(__file__).resolve().parents[2]
BASE = 'https://shop.macsteel.co.za/'
FILES = {
    'equal-angle-page4.html': '49E5F632B59A082C1B17657FB3F528728F5393BB1895ED6354FE931F9458D62E',
    'angle-60-60-5-6m.html': '1BD66FCFB54F97BC2B3D4A90D265832D8C5B82FB8A7312943AA8794348F7234C',
    'angle-60-60-5-13m.html': '4D99CCD07EE8852F99089B0D72B683D35C7396CE56D21C35B47607B6E5440DB6',
    'shop-terms.html': 'CC13D442827197E8434CFD610BBF5FC09D0C9013AD08D07211ADDB0814EBF58D',
}


def clean(value):
    return ' '.join(value.split())


class ListingParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.rows = []
        self.row = None
        self.cell = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'tr' and 'product-item' in attrs.get('class', '').split():
            if self.row is not None:
                raise ValueError('Nested product row')
            self.row = {'product_id': attrs['data-productid'], 'cells': []}
        elif self.row is not None and tag == 'td':
            self.cell = {'class': attrs.get('class', ''), 'text': '', 'links': []}
        elif self.cell is not None and tag == 'a' and attrs.get('href'):
            self.cell['links'].append(attrs['href'])

    def handle_data(self, data):
        if self.cell is not None:
            self.cell['text'] += data

    def handle_endtag(self, tag):
        if tag == 'td' and self.cell is not None:
            self.row['cells'].append(self.cell)
            self.cell = None
        elif tag == 'tr' and self.row is not None:
            self.rows.append(self.row)
            self.row = None


def parse_listing(html):
    parser = ListingParser()
    parser.feed(html)
    records = []
    seen = set()
    for row in parser.rows:
        cells = row['cells']
        if len(cells) != 9 or cells[0]['class'] != 'sku' or cells[1]['class'] != 'name':
            raise ValueError('Changed product-row schema')
        sku, name = clean(cells[0]['text']), clean(cells[1]['text'])
        if not re.fullmatch(r'AE_S355RA_\d{4}', sku) or sku in seen:
            raise ValueError('Unexpected or duplicate seller SKU')
        seen.add(sku)
        match = re.fullmatch(r'ANGLE EQUAL S355 JR\+AR EN 10025-2 AS ROLLED (\d+) x (\d+) x (\d+) (\d+\.\d+)Mtr', name)
        if not match or len(cells[1]['links']) != 1:
            raise ValueError('Unrecognized equal-angle description or detail link')
        dimensions = list(map(float, match.groups()))
        if dimensions[0] != dimensions[1] or min(dimensions) <= 0:
            raise ValueError('Invalid equal-angle dimensions')
        if clean(cells[3]['text']) != 'Log in For Price':
            raise ValueError('Price presentation changed; inspect before ingestion')
        records.append({
            'seller_sku': sku, 'offered_name': name,
            'detail_url': urljoin(BASE, cells[1]['links'][0]),
            'source_locator': 'tr.product-item[data-productid="' + row['product_id'] + '"]',
            'leg_a_mm': dimensions[0], 'leg_b_mm': dimensions[1],
            'thickness_mm': dimensions[2], 'length_m': dimensions[3],
            'grade_statement': 'S355 JR+AR EN 10025-2 AS ROLLED',
            'manufacturer_identity_verified': False,
        })
    if len(records) != 30:
        raise ValueError('Expected exactly 30 retained snapshot rows')
    return records


def seed(record):
    sku = record['seller_sku']
    return dict(zip([
        'supplier_offer_id','supplier_id','manufacturer_part_id','source_id',
        'seller_sku','normalized_sku','offered_name','brand_name','order_quantity',
        'order_unit','package_level','lifecycle_state'], [
        'OFFER-MACSTEEL-' + sku.replace('_', '-'), 'ORG-MACSTEEL-SA', '',
        'SRC-MACSTEEL-ANGLE-P4', sku, sku.replace('_', ''), record['offered_name'],
        '', '', 'unknown', 'unknown', 'unknown']))


def main():
    args = argparse.ArgumentParser()
    args.add_argument('--write', action='store_true')
    write = args.parse_args().write
    html = {}
    for name, expected in FILES.items():
        data = (ROOT / 'registry/artifacts/macsteel' / name).read_bytes()
        if hashlib.sha256(data).hexdigest().upper() != expected:
            raise ValueError('Evidence revision changed: ' + name)
        html[name] = data.decode('utf-8-sig')
    records = parse_listing(html['equal-angle-page4.html'])
    expected = [seed(r) for r in records]
    path = ROOT / 'registry/data/supplier-offers.csv'
    with path.open(encoding='utf-8-sig', newline='') as handle:
        reader = csv.DictReader(handle)
        fields = reader.fieldnames
        existing = list(reader)
    actual = [r for r in existing if r['supplier_id'] == 'ORG-MACSTEEL-SA']
    report = {'snapshot_sha256': FILES, 'scope': 'One retained equal-angle listing page; not full catalogue coverage',
              'offers': records, 'offer_count': len(records), 'identity_approved': False,
              'warnings': ['Seller SKU is not proven manufacturer MPN',
                           'JSON-LD zero price and InStock are not accepted commercial evidence',
                           'Technical length is not billing unit or package quantity',
                           'No user CSV rows merged or corrected']}
    output = ROOT / 'registry/reports/macsteel-angle-offers.json'
    if write:
        if actual and actual != expected:
            raise ValueError('Existing seller records differ; refusing overwrite')
        if not actual:
            with path.open('a', encoding='utf-8', newline='') as handle:
                csv.DictWriter(handle, fields).writerows(expected)
        output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    elif actual != expected or json.loads(output.read_text(encoding='utf-8')) != report:
        raise ValueError('Offer seeds or research report differ from retained evidence')
    print('Verified 30 seller offers; manufacturer identity, price, stock and UPN remain unapproved.')


if __name__ == '__main__':
    main()
