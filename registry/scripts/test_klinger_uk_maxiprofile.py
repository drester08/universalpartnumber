import tempfile
import unittest
from pathlib import Path
import check_klinger_uk_maxiprofile as module


class UKMaxiprofileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = module.build_report()

    def test_scope_and_date(self):
        r = self.report
        self.assertEqual(r['printed_issue_date'], '2019-08-28')
        self.assertEqual(r['visually_reviewed_physical_pages'], [1, 2, 3])
        for key in ('source_registered', 'identity_approved', 'application_suitability_approved',
                    'production_upn_allowed', 'dimensional_tuple_roles_resolved',
                    'certificate_claims_independently_verified'):
            self.assertFalse(r[key])

    def test_component_counts(self):
        rows = self.report['component_material_context']
        self.assertEqual(sum(r['component'] == 'facing' for r in rows), 4)
        self.assertEqual(sum(r['component'] == 'core' for r in rows), 21)
        self.assertTrue(all(not r['temperature_is_article_rating'] for r in rows))

    def test_differences_are_not_silently_normalized(self):
        r = self.report
        self.assertEqual(len(r['research_label_comparisons']), 14)
        self.assertEqual(r['temperature_disagreement_count'], 7)
        item = next(c for c in r['research_label_comparisons'] if c['uk_label_raw'] == 'Stainless Steel 316L')
        self.assertEqual((item['uk_temperature_C_raw'], item['sa_temperature_C_raw']), ('800', '650'))
        self.assertTrue(all(not c['label_mapping_approved'] for c in r['research_label_comparisons']))

    def test_no_coercion_of_grade_groups(self):
        self.assertIn('Hastelloy B-2/B-3', self.report['unmatched_uk_labels'])
        self.assertIn('Titanium Gr 2', self.report['unmatched_uk_labels'])
        self.assertIn('KLINGERsil C-4430', self.report['unmatched_uk_labels'])

    def test_style_text_scope(self):
        self.assertEqual(self.report['style_context']['LA3'], 'floating guide ring')
        self.assertIn('not explicitly established', self.report['style_context']['LA1'])

    def test_changed_evidence_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            fake = Path(directory) / 'changed.pdf'
            fake.write_bytes(b'not source bytes')
            with self.assertRaisesRegex(ValueError, 'revision changed'):
                module.build_report(pdf=fake)


if __name__ == '__main__':
    unittest.main()
