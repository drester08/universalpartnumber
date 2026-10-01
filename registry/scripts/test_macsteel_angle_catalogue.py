import unittest
from check_macsteel_angle_catalogue import catalogue, parse_page, ROOT


class AngleCatalogueTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.page=(ROOT/'registry/artifacts/macsteel/equal-angle-20261001-page1.html').read_text(encoding='utf-8-sig')

    def test_all_five_pages_and_nominal_duplicates_preserved(self):
        r=catalogue()
        self.assertEqual(r['offer_count'],136)
        self.assertEqual(r['family_counts'],{'CQ':44,'S355RA':92})
        self.assertEqual(len({o['seller_sku'] for o in r['offers']}),136)
        self.assertEqual(sum(o['alternate_name_format'] for o in r['offers']),7)
        self.assertFalse(r['identity_approved'])
        group=r['same_nominal_key_groups'][0]
        self.assertEqual(group['seller_skus'],['AE_CQ_0096000006000','AE_CQ_0096000007200'])
        self.assertFalse(group['identity_approved'])

    def test_wrong_page_rejected(self):
        with self.assertRaises(ValueError): parse_page(self.page,2)

    def test_unknown_pagination_rejected(self):
        with self.assertRaises(ValueError): parse_page(self.page.replace('data-page="5"','data-page="6"'),1)

    def test_grade_prefix_conflict_rejected(self):
        with self.assertRaises(ValueError): parse_page(self.page.replace('AE_CQ_0001','AE_S355RA_0001'),1)

    def test_unequal_legs_rejected(self):
        with self.assertRaises(ValueError): parse_page(self.page.replace('25 x 25 x 2','25 x 30 x 2'),1)

    def test_changed_price_requires_review(self):
        with self.assertRaises(ValueError): parse_page(self.page.replace('Log in For Price','Free'),1)


if __name__=='__main__': unittest.main()
