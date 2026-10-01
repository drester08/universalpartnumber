"""Verify report lineage, offer integrity and non-adjudicative research tasks."""
import copy
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import build_registry
import build_review_queue
import build_supplier_research_findings as checker


class SupplierResearchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='upn-supplier-research-')
        self.path = Path(self.temp.name) / 'registry.sqlite'
        build_registry.build(self.path)
        self.db = sqlite3.connect(self.path)
        self.db.row_factory = sqlite3.Row
        self.coverage = checker.load_report('macsteel-angle-coverage.json')
        self.mass = checker.load_report('angle-mass-discrepancies.json')

    def tearDown(self):
        self.db.close()
        self.temp.cleanup()

    def derive(self):
        return checker.derive(self.db, self.coverage, self.mass)

    def test_scope_offer_references_and_no_approval(self):
        f = self.derive()
        self.assertEqual(len(f), 14)
        gaps = [r for r in f if r['issue_type'] == 'material_context_gap']
        mass = [r for r in f if r['issue_type'] == 'published_mass_discrepancy']
        self.assertEqual((len(gaps), len(mass)), (10, 4))
        self.assertEqual(sum(len(r['related_offers']) for r in mass), 9)
        for r in f:
            self.assertIs(r['identity_approved'], False)
            self.assertEqual(r['review_state'], 'open_research')
            report = self.coverage if r in gaps else self.mass
            record = report['records'][int(r['evidence_pointer'].split('/')[-1])]
            self.assertEqual(record['outcome'] if r in gaps else record['comparison']['outcome'],
                             'source_context_gap' if r in gaps else 'not_explained_by_displayed_nearest_rounding')

    def test_queue_exposes_all_findings_without_deduping_distinct_questions(self):
        items = build_review_queue.build_items(self.db)
        research = [i for i in items if i['subject_type'] == 'supplier_research_finding']
        self.assertEqual(len(research), 14)
        self.assertTrue(all(i['priority'] == 'P2' and i['readiness'] == 'ready' for i in research))
        self.assertTrue(all('SHA-256' in i['next_action'] and 'Related offers:' in i['next_action'] for i in research))
        self.assertEqual(len(items), 434)

    def test_link_assignment_does_not_close_research(self):
        before = self.derive()
        offer = before[0]['related_offers'][0]['supplier_offer_id']
        self.db.execute('UPDATE supplier_offers SET manufacturer_part_id=? WHERE supplier_offer_id=?',
                        ('MP-SKF-6205-2Z', offer))
        self.assertEqual(self.derive(), before)

    def test_missing_offer_fails_closed(self):
        sku = self.coverage['records'][0]['seller_sku']
        self.db.execute('DELETE FROM supplier_offers WHERE seller_sku=?', (sku,))
        with self.assertRaisesRegex(ValueError, 'Coverage offer'):
            self.derive()

    def test_duplicate_coverage_rejected(self):
        self.coverage['records'].append(copy.deepcopy(self.coverage['records'][0]))
        with self.assertRaisesRegex(ValueError, 'ambiguous'):
            self.derive()

    def test_source_mismatch_rejected(self):
        self.coverage['records'][0]['source_id'] = 'SRC-MACSTEEL-AE0061-PDF'
        with self.assertRaisesRegex(ValueError, 'identity/source'):
            self.derive()

    def test_unknown_finding_source_rejected(self):
        self.db.execute("DELETE FROM sources WHERE source_id='SRC-AM-ORANGEBOOK-EQUAL-ANGLES'")
        with self.assertRaisesRegex(ValueError, 'Missing finding source'):
            self.derive()

    def test_mass_detached_from_geometry_rejected(self):
        record = next(r for r in self.mass['records'] if r['comparison']['outcome'] == 'not_explained_by_displayed_nearest_rounding')
        record['affected_seller_skus'] = ['AE_S355RA_0061']
        with self.assertRaisesRegex(ValueError, 'geometry'):
            self.derive()

    def test_report_revision_change_rejected(self):
        root = Path(self.temp.name) / 'report-root'
        (root / 'reports').mkdir(parents=True)
        name = 'macsteel-angle-coverage.json'
        (root / 'reports' / name).write_text('{}', encoding='utf-8')
        with patch.object(checker, 'ROOT', root):
            with self.assertRaisesRegex(ValueError, 'revision changed'):
                checker.load_report(name)

    def test_semantic_ids_stable_when_record_order_changes(self):
        expected = {f['finding_id'] for f in self.derive()}
        self.coverage['records'].reverse()
        self.mass['records'].reverse()
        self.assertEqual({f['finding_id'] for f in self.derive()}, expected)

    def test_semantic_geometry_ids_ignore_decimal_serialization(self):
        a = {'nominal_geometry_mm': ['25', '25', '3'], 'seller_pdf_table': 1}
        b = {'nominal_geometry_mm': ['25.0', '25.00', '3.000'], 'seller_pdf_table': 1}
        self.assertEqual(checker.finding_id('published_mass_discrepancy', a),
                         checker.finding_id('published_mass_discrepancy', b))

    def test_read_only_and_deterministic(self):
        before = self.db.total_changes
        self.assertEqual(self.derive(), self.derive())
        self.assertEqual(self.db.total_changes, before)


if __name__ == '__main__':
    unittest.main()
