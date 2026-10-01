import copy
import unittest
import pdfplumber
from check_macsteel_angle_datasheet import ROOT, build_report, extract_tables, correlate


class AngleDatasheetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with pdfplumber.open(ROOT / 'registry/artifacts/macsteel/AE_S355RA_0061.pdf') as pdf:
            cls.tables = pdf.pages[0].extract_tables()

    def test_all_sparse_cells_and_qualifiers(self):
        facts = extract_tables(self.tables)
        self.assertEqual(len(facts), 55)
        starred = [f for f in facts if f['availability_footnote_applies']]
        self.assertEqual([(f['leg_a_mm'],f['thickness_mm']) for f in starred], [('100','15'),('120','15')])
        self.assertFalse(any(f['leg_a_mm']=='25' and f['thickness_mm']=='4' for f in facts))

    def test_changed_units_rejected(self):
        tables = copy.deepcopy(self.tables)
        tables[1][0][1] = '4cm'
        with self.assertRaises(ValueError): extract_tables(tables)

    def test_duplicate_geometry_rejected(self):
        tables = copy.deepcopy(self.tables)
        tables[1][2][0] = tables[1][1][0]
        with self.assertRaises(ValueError): extract_tables(tables)

    def test_shifted_sparse_columns_rejected(self):
        tables = copy.deepcopy(self.tables)
        tables[1][1].pop()
        with self.assertRaises(ValueError): extract_tables(tables)

    def test_zero_mass_rejected(self):
        tables = copy.deepcopy(self.tables)
        tables[1][1][1] = '0.000'
        with self.assertRaises(ValueError): extract_tables(tables)

    def test_shared_content_and_no_identity_promotion(self):
        report = build_report()
        self.assertTrue(report['identical_pdf_bytes'])
        self.assertFalse(report['independent_sources'])
        self.assertFalse(report['identity_approved'])
        self.assertEqual(report['offer_candidate_count'], 30)
        self.assertTrue(all(not r['exact_article_verified'] for r in report['offer_candidates']))
        masses = [r['generic_table_candidate']['mass_kg_per_m'] for r in report['offer_candidates'] if r['seller_sku'] in ('AE_S355RA_0061','AE_S355RA_0064')]
        self.assertEqual(masses, ['4.568','4.568'])

    def test_ambiguous_geometry_not_selected(self):
        facts = extract_tables(self.tables)
        offer = {'seller_sku':'EXAMPLE','length_m':6,'source_locator':'example',
                 'leg_a_mm':60,'leg_b_mm':60,'thickness_mm':5}
        duplicate = [f for f in facts if f['leg_a_mm']=='60' and f['thickness_mm']=='5'][0]
        with self.assertRaises(ValueError): correlate([offer], facts + [duplicate])


if __name__ == '__main__':
    unittest.main()
