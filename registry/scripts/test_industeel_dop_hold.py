import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import check_industeel_dop_hold as hold


class IndusteelHoldTests(unittest.TestCase):
    def test_actual_capture_scope_is_not_approval(self):
        report = hold.build_report()
        self.assertEqual(report['document_revision'], '6')
        self.assertEqual(report['printed_signature_date'], '2025-11-04')
        self.assertIsNone(report['publication_date'])
        self.assertEqual(report['pdf_pages_visually_reviewed'], [1,2])
        for key in ('source_registered','article_ingested','performance_table_extracted','supplied_dataset_rows_compared','declared_certification_independently_verified','reuse_permission','identity_approved','application_suitability_approved','production_upn_allowed'):
            self.assertIs(report[key], False)

    def test_changed_pdf_bytes_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'source.pdf'
            path.write_bytes(hold.PDF.read_bytes()+b'changed')
            with self.assertRaisesRegex(ValueError, 'revision changed'):
                hold.build_report(pdf=path)

    def test_changed_terms_bytes_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'terms.html'
            path.write_bytes(hold.TERMS.read_bytes()+b'changed')
            with self.assertRaisesRegex(ValueError, 'revision changed'):
                hold.build_report(terms=path)

    def test_wrong_pdf_identity_rejected(self):
        with patch.object(hold, 'PdfReader') as reader:
            reader.return_value.pages = [object(),object()]
            reader.return_value.metadata.title = 'OTHER'
            with self.assertRaisesRegex(ValueError, 'identity/page count changed'):
                hold.build_report()

    def test_report_is_reproducible_without_table_parser(self):
        self.assertEqual(hold.build_report(), hold.build_report())
        self.assertFalse(hasattr(hold, 'extract_performance'))


if __name__ == '__main__':
    unittest.main()
