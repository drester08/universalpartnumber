"""Verify persistence, namespace and evidence custody of manufacturer research."""
import copy
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import build_registry
import build_review_queue
import build_manufacturer_source_findings as checker


class ManufacturerSourceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='upn-manufacturer-findings-')
        self.path = Path(self.temp.name) / 'registry.sqlite'
        build_registry.build(self.path)
        self.db = sqlite3.connect(self.path)
        self.db.row_factory = sqlite3.Row
        self.article = checker.load_report('ntn-6205zz-source.json')
        self.corroboration = checker.load_report('ntn-shield-seal-corroboration.json')

    def tearDown(self):
        self.db.close()
        self.temp.cleanup()

    def derive(self):
        return checker.derive(self.db, self.article, self.corroboration)

    def test_two_questions_retained_without_approval(self):
        findings = self.derive()
        self.assertEqual(len(findings), 2)
        self.assertEqual({f['subject_key']['source_field'] for f in findings}, {'Static Load Rating', 'da max'})
        for finding in findings:
            self.assertEqual(finding['review_state'], 'open_research')
            self.assertFalse(finding['publisher_correction_obtained'])
            self.assertFalse(finding['physical_conflict_verified'])
            self.assertFalse(finding['identity_approved'])
            self.assertEqual(len(finding['evidence']), 2)
            self.assertTrue(finding['source_html_line'] > 0)

    def test_queue_has_both_stable_tasks(self):
        items = build_review_queue.build_items(self.db)
        findings = [i for i in items if i['queue_type'] == 'manufacturer_source_publication_research']
        self.assertEqual(len(items), 469)
        self.assertEqual({i['work_item_id'] for i in findings}, {'RW-' + f['finding_id'] for f in checker.build_report(self.db)['findings']})
        self.assertTrue(all(i['readiness'] == 'ready' and i['priority'] == 'P2' for i in findings))
        self.assertTrue(all('SHA-256' in i['next_action'] and 'Article HTML line' in i['next_action'] for i in findings))

    def test_observation_acceptance_does_not_correct_publication(self):
        expected = self.derive()
        self.db.execute("UPDATE observations SET review_state='accepted' WHERE observation_id='OBS-NTN-6205ZZ-20261001'")
        self.assertEqual(self.derive(), expected)

    def test_mapping_acceptance_does_not_correct_publication(self):
        expected = self.derive()
        self.db.execute("UPDATE specification_value_mappings SET mapping_state='approved', reviewer='independent-test-reviewer', reviewed_at='2026-10-01' WHERE mapping_id LIKE 'MAP-NTN-6205ZZ-%'")
        self.assertEqual(self.derive(), expected)

    def test_same_article_text_different_maker_rejected(self):
        # Remove NSK's separate row in this disposable fixture so the database's
        # own duplicate maker/article constraint does not pre-empt the adapter.
        self.db.execute("DELETE FROM manufacturer_parts WHERE manufacturer_part_id='MP-NSK-6205ZZ'")
        self.db.execute("UPDATE manufacturer_parts SET manufacturer_id='ORG-NSK' WHERE manufacturer_part_id='MP-NTN-6205ZZ'")
        with self.assertRaisesRegex(ValueError, 'namespace'):
            self.derive()

    def test_missing_artifact_custody_rejected(self):
        self.db.execute("DELETE FROM source_artifacts WHERE artifact_id='ART-NTN-6205ZZ'")
        with self.assertRaisesRegex(ValueError, 'custody'):
            self.derive()

    def test_observation_hash_change_rejected(self):
        self.db.execute("UPDATE observations SET raw_payload_sha256=? WHERE observation_id='OBS-NTN-6205ZZ-20261001'", ('0'*64,))
        with self.assertRaisesRegex(ValueError, 'observation custody'):
            self.derive()

    def test_corroboration_is_not_publisher_correction(self):
        self.corroboration['publisher_correction_obtained'] = True
        with self.assertRaisesRegex(ValueError, 'publisher correction'):
            self.derive()

    def test_corrected_issue_cannot_silently_disappear(self):
        self.article['quality_findings'][0]['corrected_value'] = '7850 N'
        with self.assertRaisesRegex(ValueError, 'corrected'):
            self.derive()

    def test_duplicate_issue_rejected(self):
        self.article['quality_findings'][1] = copy.deepcopy(self.article['quality_findings'][0])
        with self.assertRaisesRegex(ValueError, 'issue scope'):
            self.derive()

    def test_semantic_ids_ignore_evidence_order(self):
        ids = {f['finding_id'] for f in self.derive()}
        self.article['quality_findings'].reverse()
        self.assertEqual({f['finding_id'] for f in self.derive()}, ids)

    def test_input_revision_fails_closed(self):
        root = Path(self.temp.name) / 'changed-reports'
        (root / 'reports').mkdir(parents=True)
        (root / 'reports/ntn-6205zz-source.json').write_text('{}', encoding='utf-8')
        with patch.object(checker, 'ROOT', root):
            with self.assertRaisesRegex(ValueError, 'revision changed'):
                checker.load_report('ntn-6205zz-source.json')

    def test_read_only_deterministic_derivation(self):
        before = self.db.total_changes
        self.assertEqual(self.derive(), self.derive())
        self.assertEqual(self.db.total_changes, before)

    def test_6204_questions_have_separate_identity_and_evidence(self):
        findings = checker.derive(self.db, checker.load_report('ntn-6204zz-source.json'), None, '6204ZZ')
        self.assertEqual(len(findings), 2)
        self.assertTrue(all(len(f['evidence']) == 1 and f['observation_id'] == 'OBS-NTN-6204ZZ-20261001' for f in findings))
        self.assertFalse({f['finding_id'] for f in findings} & {f['finding_id'] for f in self.derive()})
        self.assertEqual(checker.build_report(self.db)['finding_count'], 4)

    def test_6204_cannot_inherit_6205_corroboration(self):
        with self.assertRaisesRegex(ValueError, 'cannot be inherited'):
            checker.derive(self.db, checker.load_report('ntn-6204zz-source.json'), self.corroboration, '6204ZZ')

    def test_wrong_article_report_rejected(self):
        with self.assertRaisesRegex(ValueError, 'scope changed'):
            checker.derive(self.db, self.article, None, '6204ZZ')


if __name__ == '__main__':
    unittest.main()
