"""Intake facts retain uncertainty and exact article scope."""
import copy
import unittest
import check_ntn_6204zz as checker


class IntakeTests(unittest.TestCase):
    def test_exact_seed_bindings(self):
        self.assertEqual(checker.verify_seed_bindings(checker.build_report()), 12)

    def test_conflicting_fields_excluded(self):
        report = checker.build_report()
        self.assertEqual(report['excluded_fields'], ['Static Load Rating', 'da max'])
        self.assertEqual(len(report['quality_findings']), 2)
        self.assertFalse(report['identity_approved'])

    def test_approval_rejected(self):
        report = checker.build_report()
        report['identity_approved'] = True
        with self.assertRaisesRegex(ValueError, 'altered or promoted'):
            checker.verify_seed_bindings(report)

    def test_source_repair_rejected(self):
        report = copy.deepcopy(checker.build_report())
        report['quality_findings'][0]['corrected_value'] = '6650 N'
        with self.assertRaisesRegex(ValueError, 'altered or promoted'):
            checker.verify_seed_bindings(report)


if __name__ == '__main__':
    unittest.main()
