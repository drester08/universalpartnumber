import tempfile
import unittest
from pathlib import Path
import check_jtekt_shield_catalogue as c


class CatalogueTests(unittest.TestCase):
    def test_reproduces_snapshot(self):
        import json
        self.assertEqual(c.build_report(), json.loads((c.ROOT / 'registry/reports/jtekt-shield-catalogue.json').read_text(encoding='utf-8')))

    def test_partial_scope(self):
        report = c.build_report()
        self.assertIsNone(report['partial_closure_context']['shield_material'])
        self.assertFalse(report['partial_closure_context']['complete_canonical_closure_mapping'])
        self.assertFalse(report['catalogue_row_context']['exact_ZZ_mass_corroborated'])
        self.assertFalse(report['identity_approved'])

    def test_adjacent_seal_category_rejected(self):
        with self.assertRaises(ValueError):
            c.interpret('Sealed Non-contact type 2RU type', [c.ROW], '(Refer.) Mass Open type (kg)')

    def test_duplicate_article_rejected(self):
        with self.assertRaises(ValueError):
            c.interpret('Shielded Non-contact type ZZ type', [c.ROW, c.ROW], '(Refer.) Mass Open type (kg)')

    def test_mass_scope_cannot_disappear(self):
        with self.assertRaises(ValueError):
            c.interpret('Shielded Non-contact type ZZ type', [c.ROW], '(Refer.) Mass (kg)')

    def test_revision_fails_closed(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'changed.pdf'
            path.write_bytes(b'changed revision')
            with self.assertRaises(ValueError):
                c.extract(path)


if __name__ == '__main__':
    unittest.main()
