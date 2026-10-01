"""NSK context research preserves construction and designation limits."""
import hashlib
import sqlite3
import unittest
from unittest.mock import patch
import check_nsk_6204zz_code_research as c


class NSKCodeResearchTests(unittest.TestCase):
    def test_partial_closure_not_full_mapping(self):
        report=c.build_report()
        self.assertEqual(report['closure_research']['contact_form'],'non_contact')
        self.assertTrue(report['closure_research']['both_sides'])
        self.assertIsNone(report['closure_research']['shield_material'])
        self.assertFalse(report['closure_research']['canonical_mapping_added'])
        self.assertFalse(report['registered_new_sources'])
        self.assertFalse(report['identity_approved'])

    def test_exact_row_and_metric_context(self):
        report=c.build_report()
        self.assertEqual(report['catalogue_context']['dynamic_load_n'],'14100')
        self.assertEqual(report['catalogue_context']['static_load_n'],'6600')
        self.assertEqual(report['catalogue_context']['da_max_mm'],'26.5')
        self.assertEqual(report['catalogue_context']['Da_max_mm'],'42')
        self.assertIn('6204 ZZ VV DDU',report['extracted_evidence']['industrial_6204_row'])

    def test_revised_source_rejected(self):
        with patch.object(c,'CATALOGUE_SHA','0'*64):
            with self.assertRaisesRegex(ValueError,'PDF revision'):
                c.extract()

    def test_other_article_row_rejected(self):
        with patch.object(c,'ROW',c.ROW.replace('6204','6205')):
            with self.assertRaisesRegex(ValueError,'row changed'):
                c.extract()

    def test_prior_article_snapshot_unchanged(self):
        path=c.ROOT/'registry/reports/nsk-6204ZZ-source.json'
        before=path.read_bytes()
        c.build_report()
        self.assertEqual(path.read_bytes(),before)
        self.assertEqual(hashlib.sha256(before).hexdigest().upper(),c.ARTICLE_REPORT_SHA)

    def test_grease_requirement_is_not_a_default(self):
        report=c.build_report()
        self.assertIn('required',report['extracted_evidence']['grease_designation_requirement'])
        self.assertNotIn('supplied_grease',report['catalogue_context'])
        self.assertTrue(any('NS7 is a designation example' in limit for limit in report['limitations']))

    def test_no_registered_mapping_or_upn_added(self):
        with sqlite3.connect(c.ROOT/'registry/build/registry.sqlite') as db:
            self.assertEqual(db.execute("SELECT mapping_state FROM specification_value_mappings WHERE specification_id='SPEC-NSK-6204ZZ-CLOSURE'").fetchone()[0],'proposed')
            self.assertEqual(db.execute('SELECT count(*) FROM upn_allocations').fetchone()[0],0)


if __name__=='__main__':
    unittest.main()
