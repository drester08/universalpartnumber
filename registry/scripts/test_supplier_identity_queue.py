import sqlite3
import unittest
from build_review_queue import supplier_identity_items


class SupplierIdentityQueueTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        self.db.row_factory = sqlite3.Row
        self.db.executescript('''
            CREATE TABLE organizations(organization_id TEXT, legal_name TEXT);
            CREATE TABLE sources(source_id TEXT, source_url TEXT);
            CREATE TABLE supplier_offers(supplier_offer_id TEXT, seller_sku TEXT,
              source_id TEXT, supplier_id TEXT, manufacturer_part_id TEXT,
              lifecycle_state TEXT);
            INSERT INTO organizations VALUES('SELLER', 'A distributor');
            INSERT INTO sources VALUES('SOURCE', 'https://example.test/catalog');
            INSERT INTO supplier_offers VALUES('OFFER-B', 'B', 'SOURCE','SELLER',NULL,'unknown');
            INSERT INTO supplier_offers VALUES('OFFER-A', 'A', 'SOURCE','SELLER','','obsolete');
            INSERT INTO supplier_offers VALUES('OFFER-C', 'C', 'SOURCE','SELLER','PART-C','active');
        ''')

    def tearDown(self):
        self.db.close()

    def test_null_and_blank_visible_in_stable_order(self):
        items = supplier_identity_items(self.db)
        self.assertEqual([i['subject_id'] for i in items], ['OFFER-A', 'OFFER-B'])
        self.assertTrue(all(i['readiness'] == 'ready' for i in items))
        self.assertTrue(all(i['manufacturer_part_id'] == '' for i in items))
        self.assertTrue(all(i['source_id'] == 'SOURCE' for i in items))
        self.assertTrue(all('issue a UPN' in i['next_action'] for i in items))

    def test_linked_offer_not_in_missing_link_queue(self):
        self.db.execute("UPDATE supplier_offers SET manufacturer_part_id='PART-B' WHERE supplier_offer_id='OFFER-B'")
        self.assertEqual([i['subject_id'] for i in supplier_identity_items(self.db)], ['OFFER-A'])

    def test_regression_removes_link_reopens_task(self):
        self.db.execute("UPDATE supplier_offers SET manufacturer_part_id=NULL WHERE supplier_offer_id='OFFER-C'")
        self.assertEqual(len(supplier_identity_items(self.db)), 3)

    def test_read_only_determinism(self):
        before = list(self.db.execute('SELECT * FROM supplier_offers'))
        self.assertEqual(supplier_identity_items(self.db), supplier_identity_items(self.db))
        self.assertEqual(before, list(self.db.execute('SELECT * FROM supplier_offers')))


if __name__ == '__main__':
    unittest.main()
