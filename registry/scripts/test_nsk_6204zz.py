import copy
import json
import shutil
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch
import build_registry
import build_review_queue
import check_nsk_6204zz as c
import screen_candidates


class NSKArticleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = c.PATH.read_text(encoding='utf-8-sig')
        cls.report = c.build_report()

    def test_snapshot_and_seed_bindings(self):
        self.assertEqual(self.report['native_row_count'], 24)
        self.assertEqual(c.verify_seed_bindings(self.report), 15)
        self.assertEqual(self.report, json.loads((c.ROOT / 'registry/reports/nsk-6204ZZ-source.json').read_text(encoding='utf-8')))
        self.assertTrue(all(r['html_line'] > 0 for r in self.report['native_rows']))

    def test_series_variant_or_wrong_construction_rejected(self):
        for old, new in [('<div class="series">6204ZZ</div>', '<div class="series">6204ZZ Series</div>'),
                         ('<div class="series">6204ZZ</div>', '<div class="series">6204ZZC3</div>'),
                         ('Single-Row Deep Groove Ball Bearings                    </div>', 'Double-Row Ball Bearings</div>')]:
            self.assertIn(old, self.raw)
            with self.assertRaises(ValueError):
                c.parse(self.raw.replace(old, new))

    def test_native_values_units_and_case_not_silently_changed(self):
        for old, new in [('>14100</td>', '>14000</td>'), ('>P0</td>', '>ISO NORMAL CLASS</td>'),
                         ('Da (max.)', 'da (max.)'), ('>CN</td>', '>C3</td>'), ('<td class="attr-data">N</td>', '<td class="attr-data">kN</td>')]:
            self.assertIn(old, self.raw)
            with self.assertRaises(ValueError):
                c.parse(self.raw.replace(old, new))

    def test_source_revision_rejected(self):
        with patch.object(c, 'SHA', '0' * 64):
            with self.assertRaises(ValueError):
                c.build_report()

    def test_report_promotion_rejected(self):
        for field, value in [('identity_approved', True), ('unresolved_semantic_properties', []), ('manufacturer_part_id', 'MP-NSK-6205ZZ')]:
            report = copy.deepcopy(self.report)
            report[field] = value
            with self.assertRaises(ValueError):
                c.verify_seed_bindings(report)

    def test_approximate_mass_qualifier_cannot_be_removed(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            data = root / 'registry/data'
            data.mkdir(parents=True)
            for name in ('source-register.csv', 'source-artifacts.csv', 'manufacturer-parts.csv', 'observations.csv', 'specification-values.csv', 'specification-value-mappings.csv'):
                shutil.copyfile(c.ROOT / 'registry/data' / name, data / name)
            path = data / 'specification-values.csv'
            path.write_text(path.read_text(encoding='utf-8').replace('Approximate source mass; not measured article identity', 'Measured identity mass'), encoding='utf-8')
            with patch.object(c, 'ROOT', root):
                with self.assertRaisesRegex(ValueError, 'qualifiers'):
                    c.verify_seed_bindings(self.report)

    def test_unknown_properties_and_no_identity_promotion(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'registry.sqlite'
            build_registry.build(path)
            with closing(sqlite3.connect(path)) as db:
                db.row_factory = sqlite3.Row
                values = screen_candidates.load_parts(db)[c.PART]['values']
                self.assertFalse({'PROP-BEARING-CLOSURE', 'PROP-LOCATING-FEATURE', 'PROP-BORE-TYPE', 'PROP-BEARING-MATERIAL', 'PROP-SUPPLIED-LUBRICANT'} & set(values))
                self.assertFalse(any(c.PART in (r['left_part_id'], r['right_part_id']) for r in screen_candidates.screen(db, '2026-10-01')))
                gaps = [t for t in build_review_queue.build_items(db) if t['manufacturer_part_id'] == c.PART and t['queue_type'] == 'required_evidence_gap']
                self.assertEqual({t['property_id'] for t in gaps}, set(self.report['missing_required_properties']))
                self.assertEqual(db.execute('SELECT count(*) FROM upn_allocations').fetchone()[0], 0)


if __name__ == '__main__':
    unittest.main()
