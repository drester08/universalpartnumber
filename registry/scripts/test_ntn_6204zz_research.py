import json
import unittest
from unittest.mock import patch
import check_ntn_6204zz_research as c
import check_ntn_6205zz


class NTN6204ResearchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = c.PATH.read_text(encoding='utf-8-sig')

    def test_snapshot_and_dimension_context_only(self):
        report = c.build_report()
        self.assertEqual(report,json.loads((c.ROOT/'registry/reports/ntn-6204zz-pre-ingestion.json').read_text(encoding='utf-8')))
        self.assertEqual(report['native_property_count'],26)
        self.assertTrue(all(r['nominal_values_equal'] for r in report['boundary_context_comparison']['comparisons']))
        self.assertFalse(report['identity_approved'])
        self.assertFalse(report['registered_source'])
        self.assertFalse(report['boundary_context_comparison']['canonical_pair_screen_created'])

    def test_static_conflict_and_ambiguous_mounting_preserved(self):
        report = c.build_report()
        findings = report['quality_findings']
        self.assertEqual(findings[0]['metric_values_converted_to_n'],['6650','9750'])
        self.assertEqual(findings[0]['difference_n'],'3100')
        self.assertTrue(all(f['corrected_value'] is None for f in findings))
        self.assertEqual([v['text'] for v in findings[1]['retained_displays'] if v['measure']=='metric'],['28.000 mm','42.000 mm'])

    def test_variant_and_other_article_rejected(self):
        for article in ('6204ZZC3','EC-6204ZZ','AC-6204ZZ','6205ZZ'):
            with self.assertRaises(ValueError):
                c.parse(self.raw.replace('6204ZZ',article))

    def test_no_silent_source_correction(self):
        for old,new in [('9.75 kN','6.65 kN'),('28.000 mm','42.000 mm'),('ISO Class 0','P0')]:
            self.assertIn(old,self.raw)
            with self.assertRaises(ValueError):
                c.parse(self.raw.replace(old,new))

    def test_hash_revision_rejected(self):
        with patch.object(c,'SHA','0'*64):
            with self.assertRaises(ValueError):
                c.build_report()

    def test_parser_default_keeps_existing_6205_evidence_unchanged(self):
        expected=json.loads((c.ROOT/'registry/reports/ntn-6205zz-source.json').read_text(encoding='utf-8'))
        self.assertEqual(check_ntn_6205zz.build_report(),expected)


if __name__=='__main__':
    unittest.main()
