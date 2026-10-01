"""Exact NSK proposal may unblock research, never approve incomplete identity."""
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import build_registry
import screen_candidates
import check_nsk_6204zz_closure_mapping as c


class NSKClosureProposalTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        with sqlite3.connect(c.ROOT/'build/registry.sqlite') as source:
            source.backup(self.db)
        self.db.row_factory = sqlite3.Row
        self.addCleanup(self.db.close)

    def test_evidence_bound_proposed_only(self):
        report = c.verify(self.db)
        self.assertEqual(report['mapping']['mapping_state'], 'proposed')
        self.assertFalse(report['identity_approved'])
        self.assertEqual(report['historical_applicability_review'], 'outstanding')
        self.assertEqual(self.db.execute('SELECT count(*) FROM upn_allocations').fetchone()[0], 0)

    def test_new_pair_has_five_identity_gaps(self):
        pair = next(r for r in screen_candidates.screen(self.db,'2026-10-01') if (r['left_part_id'],r['right_part_id']) == ('MP-NSK-6204ZZ','MP-NTN-6204ZZ'))
        self.assertEqual(pair['result'], 'insufficient_evidence')
        self.assertEqual(set(pair['missing_properties'].split(';')), {'PROP-BORE-TYPE','PROP-BEARING-TOLERANCE-CLASS','PROP-BEARING-MATERIAL','PROP-SUPPLIED-LUBRICANT','PROP-LOCATING-FEATURE'})
        self.assertEqual(pair['conflicting_properties'], 'none')

    def test_rejected_mapping_does_not_inherit_ntn_definition(self):
        self.db.execute("UPDATE specification_value_mappings SET mapping_state='rejected' WHERE mapping_id=?", (c.EXPECTED['mapping_id'],))
        self.assertFalse(screen_candidates.load_parts(self.db)['MP-NSK-6204ZZ']['values'].get('PROP-BEARING-CLOSURE'))
        self.assertFalse(any('MP-NSK-6204ZZ' in (r['left_part_id'],r['right_part_id']) for r in screen_candidates.screen(self.db,'2026-10-01')))

    def test_approval_or_moved_specification_rejected(self):
        for field,value in [('mapping_state','approved'),('specification_id','SPEC-NSK-6205ZZ-CLOSURE')]:
            with self.subTest(field=field):
                row = dict(c.EXPECTED)
                row[field] = value
                with self.assertRaisesRegex(ValueError,'scope/state/evidence'):
                    c.verify_mapping_row(row)

    def test_revised_source_custody_rejected(self):
        self.db.execute('UPDATE source_artifacts SET sha256=? WHERE source_id=?', ('0'*64,c.SOURCE))
        with self.assertRaisesRegex(ValueError,'source custody'):
            c.verify(self.db)

    def test_reuse_gate_cannot_disappear(self):
        self.db.execute("UPDATE sources SET ingestion_status='reference_only' WHERE source_id=?", (c.SOURCE,))
        with self.assertRaisesRegex(ValueError,'scope/reuse'):
            c.verify(self.db)

    def test_observation_cannot_change_article(self):
        self.db.execute("UPDATE observations SET manufacturer_part_id='MP-NSK-6205ZZ' WHERE observation_id=?", (c.OBS,))
        with self.assertRaisesRegex(ValueError,'observation scope'):
            c.verify(self.db)

    def test_raw_article_is_unchanged(self):
        c.verify(self.db)
        row = self.db.execute("SELECT raw_value,normalized_text FROM specification_values WHERE specification_id='SPEC-NSK-6204ZZ-CLOSURE'").fetchone()
        self.assertEqual(tuple(row), ('ZZ: Shield on both sides',None))

    def test_failed_build_preserves_existing_database(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'registry.sqlite'
            path.write_bytes(b'existing output')
            with patch.object(c,'verify',side_effect=ValueError('Deliberate custody failure')):
                with self.assertRaisesRegex(ValueError,'custody failure'):
                    build_registry.build(path)
            self.assertEqual(path.read_bytes(),b'existing output')
            self.assertFalse(path.with_suffix('.tmp').exists())

    def test_controlled_value_meaning_rejected(self):
        self.db.execute("UPDATE controlled_values SET canonical_code='rubber_seal' WHERE controlled_value_id=?", (c.EXPECTED['controlled_value_id'],))
        with self.assertRaisesRegex(ValueError,'controlled meaning'):
            c.verify(self.db)

    def test_revised_evidence_report_rejected(self):
        with patch.object(c,'REPORT_SHA','0'*64):
            with self.assertRaisesRegex(ValueError,'report revision'):
                c.verify(self.db)


if __name__ == '__main__':
    unittest.main()
