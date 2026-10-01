import unittest
from check_macsteel_cq_pair import ROOT,parse,build_report

class CQPairTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sku='AE_CQ_0096000007200'
        cls.html=(ROOT/'registry/artifacts/macsteel'/ (cls.sku+'-20261001.html')).read_text(encoding='utf-8-sig')
    def test_same_visible_length_not_suffix_decode(self):
        r=build_report()
        self.assertFalse(r['merged']);self.assertFalse(r['identity_approved'])
        self.assertEqual([x['visible_specifications']['Length'] for x in r['details']],['6.000m','6.000m'])
    def test_revised_length_rejected(self):
        with self.assertRaises(ValueError):parse(self.html.replace('6.000m','7.200m'),self.sku)
    def test_wrong_sku_rejected(self):
        with self.assertRaises(ValueError):parse(self.html,'AE_CQ_0096000006000')
    def test_missing_units_rejected(self):
        with self.assertRaises(ValueError):parse(self.html.replace('5.00mm','5.00'),self.sku)
