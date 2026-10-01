import copy,json,unittest
from check_macsteel_angle_gap_details import ROOT,parse_detail,build_report


class GapDetailTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.offer=next(o for o in json.loads((ROOT/'registry/reports/macsteel-angle-catalogue.json').read_text(encoding='utf-8'))['offers'] if o['seller_sku']=='AE_S355RA_0008')
        cls.html=(ROOT/'registry/artifacts/macsteel/AE_S355RA_0008-gap-20261001.html').read_text(encoding='utf-8-sig')
    def test_ten_records_one_content_no_gap_closure(self):
        report=build_report()
        self.assertEqual(report['detail_count'],10)
        self.assertEqual(report['identical_pdf_content_count'],1)
        self.assertFalse(report['independent_corroboration'])
        self.assertTrue(all(r['outcome']=='seller_detail_agrees_generic_context_gap_remains' and not r['identity_approved'] for r in report['records']))
    def test_detail_conflict_preserved(self):
        html=self.html.replace('13.000m','12.000m')
        r=parse_detail(html,self.offer)
        self.assertIn('length_m',r['listing_differences'])
        self.assertFalse(r['exact_article_verified'])
    def test_wrong_sku_rejected(self):
        o=copy.deepcopy(self.offer);o['seller_sku']='AE_S355RA_0016'
        with self.assertRaises(ValueError):parse_detail(self.html,o)
    def test_unit_loss_rejected(self):
        with self.assertRaises(ValueError):parse_detail(self.html.replace('3.00mm','3.00'),self.offer)
    def test_technical_link_mismatch_rejected(self):
        with self.assertRaises(ValueError):parse_detail(self.html.replace('SpecSheets/AE_S355RA_0008.pdf','SpecSheets/DIFFERENT.pdf'),self.offer)
    def test_embedded_manufacturer_claim_not_promoted(self):
        html=self.html+'<script type="application/ld+json">{"mpn":"VERIFIED-MAKER"}</script>'
        r=parse_detail(html,self.offer)
        self.assertFalse(r['identity_approved'])
        self.assertNotIn('VERIFIED-MAKER',json.dumps(r))
