"""Construction variants and maintenance scope remain separate from identity."""
import unittest
from unittest.mock import patch
import check_klinger_maxiprofile_context as c


class KlingerContextTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=c.build_report()

    def test_material_components_not_flattened(self):
        rows=self.report['component_material_context']
        self.assertEqual(len(rows),19)
        self.assertEqual(sum(r['component']=='core' for r in rows),15)
        self.assertEqual({r['material_label_raw'] for r in rows if r['component']=='facing'}, {'Graphite','PTFE','Nonas','Mica'})

    def test_raw_published_rows_preserved_without_rating_approval(self):
        row=next(r for r in self.report['component_material_context'] if r['material_label_raw']=='Inconel 625')
        self.assertEqual(row['published_maximum_temperature_C_raw'],'450')
        self.assertEqual(row['published_colour_raw'],'Gold')
        self.assertTrue(all(not r['temperature_is_article_rating'] and not r['colour_is_verified_standard_conformity'] for r in self.report['component_material_context']))

    def test_styles_and_ring_material_scope(self):
        rows=self.report['style_context']
        self.assertEqual(rows[1]['style'],'LA2')
        self.assertEqual(rows[1]['ring_context'],'seal element only')
        self.assertEqual(rows[3]['profile'],'convex')
        self.assertIn('differ',rows[2]['ring_context'])

    def test_diagram_does_not_map_csv_tuple(self):
        self.assertFalse(self.report['diagram_scope']['supplied_tuple_component_mapping'])
        self.assertIn('attachment',self.report['required_article_evidence'][3])

    def test_refurbishment_does_not_approve_reuse(self):
        question=self.report['maintenance_scope_question']
        self.assertTrue(question['publisher_clarification_outstanding'])
        self.assertFalse(question['reuse_permission_for_supplied_gaskets'])
        self.assertEqual(question['non_reuse_pages'],[5,6])

    def test_no_article_or_date_promotion(self):
        self.assertFalse(self.report['identity_approved'])
        self.assertFalse(self.report['source_registered'])
        self.assertIsNone(self.report['publication_date'])
        self.assertEqual(self.report['visually_reviewed_physical_pages'],list(range(1,7)))
        self.assertFalse(self.report['historical_findings_resolved'])
        with patch.object(c,'HISTORICAL_SHA','0'*64):
            with self.assertRaisesRegex(ValueError,'Historical MaxiProfile'):
                c.build_report()

    def test_altered_source_revision_rejected(self):
        with patch.object(c,'SHA','0'*64):
            with self.assertRaisesRegex(ValueError,'revision changed'):
                c.build_report()

    def test_missing_material_rows_rejected(self):
        with self.assertRaisesRegex(ValueError,'four facing'):
            c.materials('Sealing Face Maximum\nGraphite 550°C Grey stripe')


if __name__=='__main__':
    unittest.main()
