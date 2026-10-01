import copy
import unittest
import applicability_rules as a
import check_kamprofile_design as c
from test_kamprofile_design import fixture


def contract():
    return dict(policy_version=a.VERSION, scope='research_capture_structure', rules=[
        dict(rule_id='TEST-RING', selector='ring.state', states=['present', 'absent'], branches={
            'present': dict(required=['ring.material', 'ring.thickness'], forbidden=[]),
            'absent': dict(required=[], forbidden=['ring.material', 'ring.thickness'])})])


class ApplicabilityTests(unittest.TestCase):
    def test_present_requires_details(self):
        result = a.evaluate({'ring': {'state': 'present'}}, contract())
        self.assertEqual(result['rules'][0]['status'], 'incomplete_branch_structure')
        self.assertEqual(result['issues'], ['ring.material: missing', 'ring.thickness: missing'])

    def test_absent_is_explicit_and_rejects_zero_false(self):
        for value in (0, False, {'designation': 'TEST'}, ['TEST']):
            with self.subTest(value=value):
                r = a.evaluate({'ring': {'state': 'absent', 'material': value}}, contract())
                self.assertIn('ring.material: contradicts absent state', r['issues'])

    def test_absent_empty_details_are_not_evidence(self):
        for value in (None, '', '  ', {}, []):
            r = a.evaluate({'ring': {'state': 'absent', 'material': value}}, contract())
            self.assertEqual(r['status'], 'resolved_research_structure')
            self.assertFalse(r['source_truth_verified'])

    def test_unknown_blank_multiple_wrong_type_selectors(self):
        for state in (None, '', ' ', 'unknown', 'PRESENT', ['present', 'absent'], {'state': 'absent'}, 0, False):
            with self.subTest(state=state):
                r = a.evaluate({'ring': {'state': state, 'material': 'TEST', 'thickness': 'TEST'}}, contract())
                self.assertEqual(r['rules'][0]['status'], 'unresolved_applicability')
                self.assertTrue(r['issues'])
                self.assertEqual(r['rules'][0]['required_fields'], [])

    def test_missing_or_scalar_parent_is_unresolved(self):
        for value in ({}, {'ring': None}, {'ring': 'absent'}, None, []):
            self.assertEqual(a.evaluate(value, contract())['rules'][0]['status'], 'unresolved_applicability')

    def test_required_zero_false_not_missing_but_not_typed(self):
        r = a.evaluate({'ring': {'state': 'present', 'material': False, 'thickness': 0}}, contract())
        self.assertEqual(r['status'], 'resolved_research_structure')
        self.assertFalse(r['identity_approved'])

    def test_no_input_or_contract_mutation(self):
        value, rules = {'ring': {'state': 'absent'}}, contract()
        before = copy.deepcopy((value, rules))
        a.evaluate(value, rules)
        self.assertEqual((value, rules), before)

    def test_empty_contract_cannot_succeed(self):
        rules = contract()
        rules['rules'] = []
        with self.assertRaises(ValueError):
            a.evaluate({}, rules)

    def test_version_and_scope_rejected(self):
        for key, value in [('policy_version', 'future'), ('scope', 'production_identity')]:
            rules = contract()
            rules[key] = value
            with self.assertRaises(ValueError):
                a.evaluate({}, rules)

    def test_nonexhaustive_or_extra_branches_rejected(self):
        for mode in ('missing', 'extra'):
            rules = contract()
            branches = rules['rules'][0]['branches']
            if mode == 'missing':
                del branches['absent']
            else:
                branches['unknown'] = dict(required=[], forbidden=[])
            with self.assertRaises(ValueError):
                a.evaluate({}, rules)

    def test_duplicate_rule_and_selector_rejected(self):
        rules = contract()
        rules['rules'].append(copy.deepcopy(rules['rules'][0]))
        with self.assertRaises(ValueError):
            a.evaluate({}, rules)
        rules['rules'][1]['rule_id'] = 'TEST-OTHER'
        with self.assertRaises(ValueError):
            a.evaluate({}, rules)

    def test_conflicting_actions_and_invalid_paths_rejected(self):
        for path in ('ring.material', 'ring[0]', '../ring', 'ring..material'):
            rules = contract()
            rules['rules'][0]['branches']['present']['forbidden'] = [path]
            with self.assertRaises(ValueError):
                a.evaluate({}, rules)

    def test_selector_dependency_and_overlap_rejected(self):
        for path in ('ring', 'ring.state', 'ring.state.detail', 'ring.material.grade'):
            rules = contract()
            rules['rules'][0]['branches']['present']['required'].append(path)
            with self.assertRaises(ValueError):
                a.evaluate({}, rules)

    def test_multiple_controllers_for_one_target_rejected(self):
        rules = contract()
        other = copy.deepcopy(rules['rules'][0])
        other.update(rule_id='TEST-OTHER', selector='other.state')
        rules['rules'].append(other)
        with self.assertRaisesRegex(ValueError, 'Multiple selectors'):
            a.evaluate({}, rules)

    def test_adapter_still_requires_positive_typed_thickness(self):
        value = fixture()
        value['guide_ring'] = dict(state='present', material=value['core_material'],
                                   attachment='TEST', geometry_definition='TEST',
                                   thickness=dict(value='0', unit='mm'))
        report = c.assess_capture(value)
        self.assertEqual(report['applicability']['status'], 'resolved_research_structure')
        self.assertEqual(report['status'], 'incomplete_research_structure')
        self.assertTrue(any('guide_ring.thickness.value: expected positive' in x for x in report['issues']))

    def test_source_bound_adapter_three_rules_no_activation(self):
        design = c.load_design()
        rules = a.kamprofile_contract(design)
        self.assertEqual(len(rules['rules']), 3)
        value = fixture()
        report = c.assess_capture(value)
        self.assertEqual(report['applicability']['status'], 'resolved_research_structure')
        for flag in ('source_truth_verified', 'identity_approved', 'application_suitability_approved', 'production_upn_allowed'):
            self.assertFalse(report['applicability'][flag])
            self.assertFalse(report[flag])


if __name__ == '__main__':
    unittest.main()
