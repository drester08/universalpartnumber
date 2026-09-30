import unittest
from pathlib import Path
from check_macsteel_angle_offers import parse_listing, seed, ROOT


class AngleOfferTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = (ROOT / 'registry/artifacts/macsteel/equal-angle-page4.html').read_text(encoding='utf-8-sig')

    def test_complete_snapshot(self):
        rows = parse_listing(self.html)
        self.assertEqual(len(rows), 30)
        by_sku = {r['seller_sku']: r for r in rows}
        self.assertEqual(by_sku['AE_S355RA_0061']['length_m'], 6)
        self.assertEqual(by_sku['AE_S355RA_0064']['length_m'], 13)
        for row in rows:
            offer = seed(row)
            self.assertEqual(offer['manufacturer_part_id'], '')
            self.assertEqual(offer['order_quantity'], '')
            self.assertEqual(offer['order_unit'], 'unknown')
            self.assertEqual(offer['lifecycle_state'], 'unknown')

    def test_duplicate_sku_rejected(self):
        with self.assertRaises(ValueError):
            parse_listing(self.html.replace('AE_S355RA_0080', 'AE_S355RA_0084'))

    def test_unequal_description_rejected(self):
        with self.assertRaises(ValueError):
            parse_listing(self.html.replace('60 x 60 x 10', '60 x 50 x 10'))

    def test_billing_inference_not_from_length(self):
        rows = parse_listing(self.html)
        for row in rows:
            self.assertEqual(seed(row)['package_level'], 'unknown')
            self.assertFalse(row['manufacturer_identity_verified'])


if __name__ == '__main__':
    unittest.main()
