import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import source_use_gates as gates
import check_skf_marketplace_hold as hold

ROOT = Path(__file__).resolve().parents[1]


class SourceUseGateTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        with sqlite3.connect(ROOT/'build/registry.sqlite') as original:
            original.backup(self.db)
        self.addCleanup(self.db.close)

    def test_existing_restricted_skf_evidence_is_held(self):
        records = gates.part_holds(self.db)['MP-SKF-6205-2Z']
        self.assertIn(dict(source_id='SRC-SKF-6205-2Z', license_state='restricted', ingestion_status='reference_only'), records)

    def test_verified_state_and_acceptable_license_both_required(self):
        for license_state, status in [('restricted', 'license_verified'), ('open', 'reference_only'),
                                      ('review_required', 'license_verified'), ('unknown', 'license_verified')]:
            self.db.execute('UPDATE sources SET license_state=?,ingestion_status=? WHERE source_id=?',
                            (license_state, status, 'SRC-SKF-6205-2Z'))
            self.assertIn('MP-SKF-6205-2Z', gates.part_holds(self.db))
        self.db.execute("UPDATE sources SET license_state='attribution',ingestion_status='license_verified' WHERE source_id='SRC-SKF-6205-2Z'")
        self.assertNotIn('MP-SKF-6205-2Z', gates.part_holds(self.db))

    def test_rejected_superseded_evidence_not_active_hold(self):
        self.db.execute("UPDATE observations SET review_state='superseded' WHERE manufacturer_part_id='MP-SKF-6205-2Z'")
        self.assertNotIn('MP-SKF-6205-2Z', gates.part_holds(self.db))

    def run_audit(self, script):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'test.sqlite'
            target = sqlite3.connect(path)
            try:
                self.db.backup(target)
            finally:
                target.close()
            return subprocess.run([sys.executable, str(ROOT/'scripts'/script), '--database', str(path)],
                                  capture_output=True, text=True)

    def test_conditional_free_accepted_profile_still_blocked_by_source(self):
        # Isolate source gate: no required/conditional fields remain in this
        # disposable fixture, so a prior completeness query would skip it.
        part, profile = self.db.execute("SELECT manufacturer_part_id,profile_id FROM manufacturer_parts WHERE manufacturer_part_id='MP-SKF-6205-2Z'").fetchone()
        self.db.execute("UPDATE identity_profile_properties SET requirement='descriptive' WHERE profile_id=?", (profile,))
        self.db.execute("INSERT INTO manufacturer_part_reviews VALUES ('TEST-LICENSE',?,'accepted','SYNTHETIC ONLY','TEST','2026-10-01','TEST')", (part,))
        self.db.commit()
        for script in ('audit_completeness.py', 'audit_issuance.py'):
            result = self.run_audit(script)
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)

    def test_unreviewed_research_remains_allowed(self):
        result = self.run_audit('audit_completeness.py')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('Source-use hold:', result.stdout)

    def test_hold_report_never_ingests_product_data(self):
        report = hold.build_report()
        for key in ('source_registered', 'article_ingested', 'structured_product_table_generated', 'reuse_permission',
                    'identity_approved', 'application_suitability_approved', 'production_upn_allowed'):
            self.assertFalse(report[key])
        self.assertNotIn('native_properties', report)

    def test_changed_terms_or_product_bytes_rejected(self):
        for field in ('TERMS_SHA', 'PRODUCT_SHA'):
            with patch.object(hold, field, '0'*64):
                with self.assertRaisesRegex(ValueError, 'revision changed'):
                    hold.build_report()


if __name__ == '__main__':
    unittest.main()
