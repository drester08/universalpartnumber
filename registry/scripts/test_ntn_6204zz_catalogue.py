"""Bounded catalogue evidence cannot silently correct or approve an article."""
import hashlib
import sqlite3
import unittest
from unittest.mock import patch
import check_ntn_6204zz_catalogue as c
import check_ntn_6204zz as intake


class CatalogueTests(unittest.TestCase):
    def test_exact_row_and_bore_group(self):
        evidence = c.extract()
        self.assertIn('6204 ZZ LLB LLU LLH N NR', evidence['6204_row_text'])
        self.assertEqual(evidence['bore_group_label_mm'], '20')
        self.assertIn('Non-contact shield type ZZ', evidence['zz_definition_column'])

    def test_no_correction_or_approval(self):
        report = c.build_report()
        self.assertFalse(report['publisher_correction_obtained'])
        self.assertFalse(report['identity_approved'])
        self.assertFalse(report['closure_research']['mapping_added'])
        self.assertEqual(report['metric_static_comparison']['difference_n'], '3100')

    def test_case_and_mass_context_retained(self):
        context = c.build_report()['catalogue_context']
        self.assertEqual((context['da_max_mm'],context['Da_max_mm']), ('28','42'))
        self.assertEqual(context['mass_approx_kg'], '0.106')
        self.assertEqual(context['static_load_kn'], '6.65')

    def test_changed_source_rejected(self):
        with patch.object(c.catalogue,'SHA','0'*64):
            with self.assertRaisesRegex(ValueError,'revision changed'):
                c.extract()

    def test_another_row_rejected(self):
        with patch.object(c,'ROW',c.ROW.replace('6204','6205')):
            with self.assertRaisesRegex(ValueError,'row changed'):
                c.extract()

    def test_wrong_article_or_rejected_observation_rejected(self):
        db = sqlite3.connect(':memory:')
        source = sqlite3.connect(c.ROOT/'registry/build/registry.sqlite')
        source.backup(db)
        source.close()
        try:
            article = intake.build_report()
            article['manufacturer_part_id'] = 'MP-NTN-6205ZZ'
            with self.assertRaisesRegex(ValueError,'namespace'):
                c.verify_custody(db,article)
            db.execute("UPDATE observations SET review_state='rejected' WHERE observation_id='OBS-NTN-6204ZZ-20261001'")
            with self.assertRaisesRegex(ValueError,'observation custody'):
                c.verify_custody(db,intake.build_report())
        finally:
            db.close()

    def test_prior_intake_report_unchanged(self):
        path = c.ROOT/'registry/reports/ntn-6204zz-source.json'
        before = path.read_bytes()
        c.build_report()
        self.assertEqual(path.read_bytes(),before)
        self.assertEqual(hashlib.sha256(before).hexdigest().upper(),c.ARTICLE_REPORT_SHA)


if __name__ == '__main__':
    unittest.main()
