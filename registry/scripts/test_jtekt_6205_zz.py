"""Exact-article namespace, source-field and non-inference regressions."""
import copy
import sqlite3
import shutil
import tempfile
import unittest
from contextlib import closing
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

import build_registry
import build_review_queue
import check_jtekt_6205_zz as checker
import screen_candidates


class JTEKTSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = checker.PATH.read_text(encoding='utf-8-sig')
        cls.report = checker.build_report()

    def test_exact_source_fields_and_case_sensitive_mounting_symbols(self):
        self.assertEqual(self.report['native_property_count'], 14)
        self.assertEqual(self.report['metric_boundary_dimensions_mm'], {'d': '25', 'D': '52', 'B': '15'})
        self.assertEqual(self.report['mounting_symbol_values_mm']['da(max.)'], '31.5')
        self.assertEqual(self.report['mounting_symbol_values_mm']['Da(max.)'], '47')
        self.assertTrue(all(r['html_line'] > 0 and r['ordinal'] > 0 for r in self.report['native_properties']))

    def test_wrong_article_and_construction_rejected(self):
        for old, new in [('<h1 class="page_ttl">6205 ZZ</h1>', '<h1 class="page_ttl">6205</h1>'),
                         ('Shielded ZZ</p>', 'Sealed 2RS</p>')]:
            with self.assertRaises(ValueError):
                checker.parse(self.raw.replace(old, new))

    def test_case_change_duplicate_missing_or_numeric_field_change_rejected(self):
        for old, new in [('Da(max.)</dt>', 'da(max.)</dt>'),
                         ('<dt>d</dt>', '<dt>unused</dt>'),
                         ('>25 mm</dd>', '>0 mm</dd>'),
                         ('0.128 kg', '0.128 lb')]:
            self.assertIn(old, self.raw)
            with self.assertRaises(ValueError):
                checker.parse(self.raw.replace(old, new))

    def test_source_revision_rejected(self):
        with patch.object(checker, 'SHA', '0'*64):
            with self.assertRaisesRegex(ValueError, 'revision changed'):
                checker.build_report()

    def test_ingestion_and_mutated_native_value(self):
        self.assertEqual(checker.verify_seed_bindings(self.report), 9)
        report = copy.deepcopy(self.report)
        next(r for r in report['native_properties'] if r['name'] == 'd')['value'] = '26 mm'
        with self.assertRaisesRegex(ValueError, 'ingestion differs'):
            checker.verify_seed_bindings(report)

    def test_numeric_units_and_invalid_values(self):
        self.assertEqual(checker.numeric('17.5 kN', 'kN'), '17.5')
        for value in ('17,5 kN', 'NaN kN', '-1 kN', '0 kN', '17.5 N'):
            with self.assertRaises(ValueError):
                checker.numeric(value, 'kN')

    def test_reference_qualifier_cannot_be_removed(self):
        with tempfile.TemporaryDirectory(prefix='upn-jtekt-qualifier-') as directory:
            root = Path(directory)
            data = root / 'registry/data'
            data.mkdir(parents=True)
            for name in ('source-register.csv', 'observations.csv', 'manufacturer-parts.csv',
                         'source-artifacts.csv', 'specification-values.csv'):
                shutil.copyfile(checker.ROOT / 'registry/data' / name, data / name)
            file = data / 'specification-values.csv'
            text = file.read_text(encoding='utf-8')
            old = 'Source reference mass; not measured supplied-item mass or identity evidence'
            self.assertIn(old, text)
            file.write_text(text.replace(old, 'Measured supplied item mass'), encoding='utf-8')
            with patch.object(checker, 'ROOT', root):
                with self.assertRaisesRegex(ValueError, 'qualifier changed'):
                    checker.verify_seed_bindings(self.report)

    def test_no_cross_brand_merge_or_inferred_fields(self):
        with tempfile.TemporaryDirectory(prefix='upn-jtekt-') as directory:
            path = Path(directory) / 'registry.sqlite'
            build_registry.build(path)
            with closing(sqlite3.connect(path)) as db:
                db.row_factory = sqlite3.Row
                rows = db.execute('SELECT * FROM specification_values WHERE observation_id=?', (checker.OBS,)).fetchall()
                self.assertEqual(len(rows), 9)
                by_prop = {r['property_id']: r for r in rows}
                closure = by_prop['PROP-BEARING-CLOSURE']
                self.assertEqual(closure['raw_value'], 'Shielded ZZ')
                self.assertIsNone(closure['normalized_text'])
                self.assertEqual(Decimal(by_prop['PROP-BASIC-STATIC-LOAD-RATING']['normalized_number']), Decimal('7850'))
                self.assertEqual(Decimal(by_prop['PROP-BASIC-DYNAMIC-LOAD-RATING']['normalized_number']), Decimal('17500'))
                self.assertFalse({'PROP-BORE-TYPE', 'PROP-CAGE-CONSTRUCTION', 'PROP-RADIAL-INTERNAL-CLEARANCE',
                    'PROP-BEARING-TOLERANCE-CLASS', 'PROP-BEARING-MATERIAL', 'PROP-SUPPLIED-LUBRICANT', 'PROP-LOCATING-FEATURE'} & set(by_prop))
                self.assertEqual(db.execute('SELECT count(*) FROM manufacturer_parts WHERE normalized_part_number=?', ('6205ZZ',)).fetchone()[0], 3)
                self.assertFalse(any(checker.PART in (r['left_part_id'], r['right_part_id']) for r in screen_candidates.screen(db, '2026-10-01')))
                tasks = build_review_queue.build_items(db)
                gaps = [t for t in tasks if t['manufacturer_part_id'] == checker.PART and t['queue_type'] == 'required_evidence_gap']
                self.assertEqual(len(gaps), 7)
                self.assertEqual(sum(t['manufacturer_part_id'] == checker.PART and t['queue_type'] == 'observation_review' for t in tasks), 1)
                self.assertEqual(db.execute('SELECT count(*) FROM upn_allocations').fetchone()[0], 0)


if __name__ == '__main__':
    unittest.main()
