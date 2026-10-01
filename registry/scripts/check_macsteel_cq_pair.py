"""Reproduce visible detail assertions for two unresolved CQ seller records."""
import argparse,csv,hashlib,json,re
from html.parser import HTMLParser
from check_macsteel_angle_offers import ROOT,clean

HASHES={'AE_CQ_0096000006000':'9BE46BA774BC78107E22E6B520CAF20DBE1490D7FEE7F081E83BE3C13D366613',
        'AE_CQ_0096000007200':'9104C6599A35BAC28FFF9159515A56B4DD265EF6EBC404A00490F4ADA7621D25'}


class DetailParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.target=None;self.buffer='';self.heading=[];self.skus=[];self.cells=[];self.links=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='h1':self.target='heading';self.buffer=''
        elif tag=='span' and a.get('id','').startswith('sku-'):self.target='sku';self.buffer=''
        elif tag=='td' and a.get('class') in ('spec-name','spec-value'):self.target=a['class'];self.buffer=''
        elif tag=='a' and '/SpecSheets/' in a.get('href',''):self.links.append(a['href'])
    def handle_data(self,data):
        if self.target:self.buffer+=data
    def handle_endtag(self,tag):
        if (tag=='h1' and self.target=='heading') or (tag=='span' and self.target=='sku') or (tag=='td' and self.target in ('spec-name','spec-value')):
            if self.target=='heading':self.heading.append(clean(self.buffer))
            elif self.target=='sku':self.skus.append(clean(self.buffer))
            else:self.cells.append((self.target,clean(self.buffer)))
            self.target=None


def parse(html,sku):
    p=DetailParser();p.feed(html)
    if len(p.heading)!=1 or p.skus!=[sku] or len(p.cells)!=10:
        raise ValueError('Missing or ambiguous article heading/SKU/specification block')
    names=['Size','Grade','Thickness','UOM','Length']
    values={}
    for i,name in enumerate(names):
        if p.cells[2*i]!=('spec-name',name) or p.cells[2*i+1][0]!='spec-value':
            raise ValueError('Specification schema changed')
        values[name]=p.cells[2*i+1][1]
    if values!={'Size':'50.00 X 50.00','Grade':'COMMERCIAL QUALITY','Thickness':'5.00mm','UOM':'EA','Length':'6.000m'}:
        raise ValueError('Visible specification revised; inspect before replacing observations')
    if p.heading[0]!='ANGLE EQUAL COMMERCIAL QUALITY 50.00 x 50.00 x 5.00 x 6.000 m':
        raise ValueError('Heading revised')
    return {'seller_sku':sku,'heading':p.heading[0],'visible_specifications':values,
            'detail_locator':'h1; span[id^=sku-]; td.spec-name/td.spec-value',
            'linked_datasheet_urls':sorted(set(p.links)),
            'exact_article_verified':False,'manufacturer_identity_verified':False}


def build_report():
    with (ROOT/'registry/data/source-artifacts.csv').open(encoding='utf-8-sig',newline='') as f:
        artifacts={r['artifact_id']:r for r in csv.DictReader(f)}
    details=[]
    for sku,digest in HASHES.items():
        path='registry/artifacts/macsteel/'+sku+'-20261001.html'
        data=(ROOT/path).read_bytes()
        a=artifacts['ART-MACSTEEL-CQ-'+sku[-4:]]
        if hashlib.sha256(data).hexdigest().upper()!=digest or a['sha256']!=digest or a['local_path']!=path or a['retrieval_state']!='retrieved':
            raise ValueError('Detail custody/revision mismatch')
        record=parse(data.decode('utf-8-sig'),sku);record['source_id']=a['source_id'];details.append(record)
    with (ROOT/'registry/reports/macsteel-angle-catalogue.json').open(encoding='utf-8') as f:
        listing={r['seller_sku']:r for r in json.load(f)['offers']}
    for detail in details:
        row=listing[detail['seller_sku']]
        if row['length_m']!=6 or row['offered_name']!=detail['heading']:
            raise ValueError('Listing/detail disagreement')
    return {'snapshot_date':'2026-10-01','detail_hashes':HASHES,'details':details,
            'outcome':'two_visible_seller_records_same_nominal_specification',
            'identity_approved':False,'merged':False,
            'open_questions':['Why seller codes differ is not established','No maker or article certificate','No suffix-based length correction','EA does not establish minimum order or package quantity','Shared linked datasheet does not prove identical articles']}


def main():
    p=argparse.ArgumentParser();p.add_argument('--write-snapshot',action='store_true');args=p.parse_args()
    report=build_report();output=ROOT/'registry/reports/macsteel-cq-pair.json'
    if args.write_snapshot:output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    elif json.loads(output.read_text(encoding='utf-8'))!=report:raise ValueError('CQ pair report stale')
    print('Verified two visible 6m detail records; no suffix correction or identity merge.')


if __name__=='__main__':main()
