import copy
import hashlib
from pathlib import Path
import tempfile
import unittest

import standard_relationships as rules


class RelationshipTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        path = self.root / 'registry/artifacts/test/source.txt'
        path.parent.mkdir(parents=True)
        path.write_bytes(b'SYNTHETIC TEST evidence, not a real manufacturer statement')
        self.path = path
        node = lambda name: dict(kind='standard_reference', namespace='TEST', identifier=name, edition=None)
        self.capture = dict(policy_version=rules.VERSION, scope='research_only', assertions=[dict(
            assertion_id='TEST-REL-1', subject=node('A'), target=node('B'),
            relation='successor_standard', context='Synthetic research fixture only',
            qualifiers=['Exact article geometry still required'], review_state='unreviewed',
            evidence=dict(source_url='https://example.invalid/test', artifact_path='registry/artifacts/test/source.txt',
                          sha256=hashlib.sha256(path.read_bytes()).hexdigest(), locator='Synthetic first line'))])

    @property
    def assertion(self):
        return self.capture['assertions'][0]

    def check(self):
        return rules.validate(self.capture, self.root)

    def test_unknown_editions_and_direction_preserved(self):
        result = self.check()['assertions'][0]
        self.assertEqual(result['unknown_standard_editions'], ['subject', 'target'])
        self.assertEqual(result['subject']['identifier'], 'A')
        self.assertEqual(result['target']['identifier'], 'B')

    def test_no_approvals_or_inferred_links(self):
        result = self.check()
        for key, value in result.items():
            if isinstance(value, bool):
                self.assertFalse(value, key)
        self.assertTrue(result['assertions'][0]['source_bytes_match'])

    def test_four_relationship_types_remain_distinct(self):
        for relation in rules.RELATIONS:
            with self.subTest(relation=relation):
                self.assertion['relation'] = relation
                self.assertion['subject']['kind'] = 'product_family' if relation == 'declared_conformance' else 'standard_reference'
                self.assertEqual(self.check()['assertions'][0]['relation'], relation)

    def test_family_conformance_not_an_article(self):
        self.assertion['relation'] = 'declared_conformance'
        self.assertion['subject']['kind'] = 'product_family'
        self.assertEqual(self.check()['assertions'][0]['subject']['kind'], 'product_family')

    def test_identity_and_approved_states_rejected(self):
        self.assertion['relation'] = 'same_item'
        with self.assertRaises(ValueError): self.check()
        self.assertion['relation'] = 'successor_standard'
        self.assertion['review_state'] = 'approved'
        with self.assertRaises(ValueError): self.check()

    def test_changed_source_rejected(self):
        self.path.write_bytes(b'changed source')
        with self.assertRaises(ValueError): self.check()

    def test_missing_or_escaping_artifact_rejected(self):
        for path in ('registry/artifacts/missing.txt', '../source.txt', 'registry/artifacts/../source.txt',
                     'C:/source.txt', 'registry\\artifacts\\test\\source.txt'):
            self.assertion['evidence']['artifact_path'] = path
            with self.subTest(path=path), self.assertRaises(ValueError): self.check()

    def test_wrong_endpoints_and_self_relation_rejected(self):
        self.assertion['subject']['kind'] = 'manufacturer_part'
        with self.assertRaises(ValueError): self.check()
        self.assertion['subject'] = copy.deepcopy(self.assertion['target'])
        with self.assertRaises(ValueError): self.check()

    def test_namespace_and_edition_not_flattened(self):
        self.assertion['subject']['identifier'] = 'B'
        self.assertion['subject']['namespace'] = 'OTHER-TEST'
        self.assertion['subject']['edition'] = '2000'
        result = self.check()['assertions'][0]
        self.assertEqual(result['subject']['namespace'], 'OTHER-TEST')
        self.assertEqual(result['subject']['edition'], '2000')
        self.assertEqual(result['unknown_standard_editions'], ['target'])

    def test_unknown_fields_blank_context_and_qualifiers_rejected(self):
        original = copy.deepcopy(self.assertion)
        for field, value in (('context', ' '), ('qualifiers', ['x','x']), ('qualifiers', ['']), ('identity_approved', True)):
            self.capture['assertions'][0] = copy.deepcopy(original)
            self.assertion[field] = value
            with self.subTest(field=field, value=value), self.assertRaises(ValueError): self.check()

    def test_duplicate_ids_and_credentials_rejected(self):
        self.capture['assertions'].append(copy.deepcopy(self.assertion))
        with self.assertRaises(ValueError): self.check()
        self.capture['assertions'].pop()
        self.assertion['evidence']['source_url'] = 'https://user:password@example.invalid/source'
        with self.assertRaises(ValueError): self.check()

    def test_input_not_mutated(self):
        before = copy.deepcopy(self.capture)
        self.check()
        self.assertEqual(self.capture, before)

    def test_malformed_types_fail_as_validation_errors(self):
        original = copy.deepcopy(self.capture)
        for field in ('relation', 'subject'):
            self.capture = copy.deepcopy(original)
            if field == 'subject':
                self.assertion['subject']['kind'] = []
            else:
                self.assertion[field] = []
            with self.subTest(field=field), self.assertRaises(ValueError): self.check()
        self.capture = copy.deepcopy(original)
        self.capture['assertions'] = []
        with self.assertRaises(ValueError): self.check()


if __name__ == '__main__':
    unittest.main()
