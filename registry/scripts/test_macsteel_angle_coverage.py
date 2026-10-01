import copy,json,unittest
from check_macsteel_angle_coverage import ROOT,screen,build_report


class AngleCoverageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.facts=json.loads((ROOT/'registry/reports/macsteel-angle-datasheet.json').read_text(encoding='utf-8'))['table_facts']
        cls.offers=json.loads((ROOT/'registry/reports/macsteel-angle-catalogue.json').read_text(encoding='utf-8'))['offers']
    def test_full_partition_no_approval(self):
        r=build_report()
        self.assertEqual(len(r['records']),136)
        self.assertEqual(r['outcome_counts'],{'nominal_context_candidate':126,'source_context_gap':10})
        self.assertEqual(len({x['seller_sku'] for x in r['records']}),136)
        self.assertTrue(all(not x['identity_approved'] and not x['delivery_condition_verified'] and not x['route_verified'] for x in r['records']))
    def test_cross_context_mass_not_borrowed(self):
        offer=next(o for o in self.offers if o['seller_sku']=='AE_S355RA_0008')
        r=screen(offer,self.facts)
        self.assertEqual(r['outcome'],'source_context_gap')
        self.assertEqual(r['same_context_candidates'],[])
        self.assertEqual(r['other_context_geometry_only'][0]['material_context'],'Mild steel (commercial quality)')
    def test_ambiguous_context_not_first_match(self):
        offer=self.offers[0];r=screen(offer,self.facts)
        duplicate=r['same_context_candidates'][0]
        self.assertEqual(screen(offer,self.facts+[duplicate])['outcome'],'ambiguous_context_candidate')
    def test_availability_star_retained(self):
        offer=next(o for o in self.offers if o['leg_a_mm']==120 and o['thickness_mm']==15)
        r=screen(offer,self.facts)
        self.assertTrue(r['availability_confirmation_required'])
        self.assertFalse(r['exact_article_verified'])
    def test_missing_table_does_not_use_other_context(self):
        offer=self.offers[0]
        r=screen(offer,[f for f in self.facts if f['pdf_table']==2])
        self.assertEqual(r['outcome'],'source_context_gap')
    def test_unknown_family_does_not_default_to_s355(self):
        offer=copy.deepcopy(self.offers[0]);offer['seller_sku']='UNKNOWN'
        with self.assertRaises(ValueError):screen(offer,self.facts)
