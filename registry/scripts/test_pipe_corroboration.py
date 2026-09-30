"""Test narrow pipe observation consistency and rejection paths."""
import json
import unittest
from unittest.mock import patch

import check_pipe_corroboration as checker


class CorroborationTests(unittest.TestCase):
    def test_current_observations(self):
        self.assertEqual(checker.check(), (6, 4))

    def reject(self, change, message):
        payload = json.loads((checker.ROOT / 'reports/pipe-independent-observations.json').read_text(encoding='utf-8'))
        change(payload)
        with patch.object(checker.json, 'loads', return_value=payload):
            with self.assertRaisesRegex(ValueError, message):
                checker.check()

    def test_wrong_revision(self):
        self.reject(lambda p: p.update(dataset_sha256='0' * 64), 'revision mismatch')

    def test_duplicate_observation(self):
        self.reject(lambda p: p['observations'].append(p['observations'][0]), 'Duplicate')

    def test_bad_locator(self):
        self.reject(lambda p: p['observations'][0].update(csv_line=52), 'Out-of-range')

    def test_wrong_nominal_key(self):
        self.reject(lambda p: p['observations'][0].update(dn='65'), 'Nominal key')

    def test_wrong_geometry(self):
        self.reject(lambda p: p['observations'][0].update(od_mm='73.0'), 'Nominal geometry')


if __name__ == '__main__':
    unittest.main()
