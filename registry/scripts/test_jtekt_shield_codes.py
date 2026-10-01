"""Manufacturer table category boundaries and non-inference guards."""
import copy
import unittest
from unittest.mock import patch
import check_jtekt_shield_codes as checker


class JTEKTCodesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = checker.PATH.read_text(encoding='utf-8-sig')
        cls.report = checker.build_report()

    def test_sixteen_codes_preserve_category_and_sidedness(self):
        rows = self.report['shield_seal_subtable']['rows']
        self.assertEqual(len(rows), 16)
        by_code = {r['code']: r for r in rows}
        self.assertEqual(by_code['ZZ']['category'], '(Shield)')
        self.assertEqual(by_code['ZZ']['description'], 'both sides Fixed shield')
        self.assertEqual(by_code['2RU']['category'], '(Non-contact seal)')
        self.assertTrue(all(r['source_html_line'] > r['category_html_line'] for r in rows))

    def test_partial_context_does_not_complete_closure(self):
        context = self.report['partial_closure_context']
        self.assertIsNone(context['shield_material'])
        self.assertIsNone(context['shield_contact_form'])
        self.assertFalse(context['complete_canonical_closure_mapping'])
        self.assertFalse(self.report['identity_approved'])
        checker.verify_custody(self.report)
        for field, value in [('shield_material', 'steel'), ('shield_contact_form', 'non_contact'),
                             ('complete_canonical_closure_mapping', True)]:
            report = copy.deepcopy(self.report)
            report['partial_closure_context'][field] = value
            with self.assertRaisesRegex(ValueError, 'beyond source scope'):
                checker.verify_custody(report)

    def test_wrong_category_not_silently_transferred(self):
        with self.assertRaisesRegex(ValueError, 'scope changed'):
            checker.parse(self.raw.replace('(Shield)', '(Non-contact seal)'))

    def test_changed_sidedness_missing_and_duplicate_table_rejected(self):
        with self.assertRaises(ValueError):
            checker.parse(self.raw.replace('both sides Fixed shield', 'one side Fixed shield'))
        with self.assertRaises(ValueError):
            checker.parse(self.raw + self.raw)

    def test_hash_revision_rejected(self):
        with patch.object(checker, 'SHA', '0'*64):
            with self.assertRaisesRegex(ValueError, 'revision changed'):
                checker.build_report()

    def test_detached_article_or_artifact_rejected(self):
        report = copy.deepcopy(self.report)
        report['artifact_id'] = 'ART-UNKNOWN'
        with self.assertRaisesRegex(ValueError, 'custody'):
            checker.verify_custody(report)
        report = copy.deepcopy(self.report)
        report['related_specification_id'] = 'SPEC-UNKNOWN'
        with self.assertRaisesRegex(ValueError, 'detached'):
            checker.verify_custody(report)


if __name__ == '__main__':
    unittest.main()
