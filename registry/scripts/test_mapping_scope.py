"""Normalization is bound to an observation's specification, never raw suffix text."""
import sqlite3
import unittest
import screen_candidates


class MappingScopeTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        self.addCleanup(self.db.close)
        self.db.row_factory = sqlite3.Row
        # Minimal synthetic query fixture, not registry parts or approved evidence.
        self.db.executescript('''
          CREATE TABLE manufacturer_parts(manufacturer_part_id TEXT, manufacturer_id TEXT,
            profile_id TEXT, manufacturer_part_number TEXT);
          CREATE TABLE observations(observation_id TEXT, manufacturer_part_id TEXT, review_state TEXT);
          CREATE TABLE specification_values(specification_id TEXT, observation_id TEXT, property_id TEXT,
            raw_value TEXT, normalized_text TEXT, normalized_number TEXT, unit_id TEXT);
          CREATE TABLE properties(property_id TEXT, value_kind TEXT);
          CREATE TABLE units(unit_id TEXT, quantity_kind TEXT, conversion_factor TEXT, conversion_offset TEXT);
          CREATE TABLE specification_value_mappings(specification_id TEXT, controlled_value_id TEXT, mapping_state TEXT);
          CREATE TABLE controlled_values(controlled_value_id TEXT, canonical_code TEXT);
        ''')
        self.db.execute("INSERT INTO properties VALUES ('closure', 'code')")
        self.db.execute("INSERT INTO controlled_values VALUES ('metal-shield', 'double_non_contact_metal_shield')")
        for part, maker, family in [('mapped', 'maker-a', 'deep-groove'),
                                     ('same-maker-other-family', 'maker-a', 'track-roller'),
                                     ('other-maker', 'maker-b', 'deep-groove'),
                                     ('same-maker-same-family', 'maker-a', 'deep-groove')]:
            self.db.execute('INSERT INTO manufacturer_parts VALUES (?, ?, ?, ?)', (part, maker, family, 'synthetic ZZ'))
            self.db.execute('INSERT INTO observations VALUES (?, ?, ?)', ('obs-' + part, part, 'unreviewed'))
            self.db.execute('INSERT INTO specification_values VALUES (?, ?, ?, ?, NULL, NULL, NULL)',
                            ('spec-' + part, 'obs-' + part, 'closure', 'ZZ'))
        self.db.execute("INSERT INTO specification_value_mappings VALUES ('spec-mapped', 'metal-shield', 'proposed')")

    def values(self, part):
        return screen_candidates.load_parts(self.db)[part]['values'].get('closure', set())

    def test_mapping_applies_only_to_its_exact_specification(self):
        self.assertEqual(self.values('mapped'), {'double_non_contact_metal_shield'})

    def test_same_manufacturer_other_family_does_not_inherit(self):
        self.assertEqual(self.values('same-maker-other-family'), set())

    def test_other_manufacturer_does_not_inherit(self):
        self.assertEqual(self.values('other-maker'), set())

    def test_same_family_same_manufacturer_still_needs_own_evidence(self):
        self.assertEqual(self.values('same-maker-same-family'), set())

    def test_rejected_mapping_cannot_supply_canonical_value(self):
        self.db.execute("UPDATE specification_value_mappings SET mapping_state='rejected'")
        self.assertEqual(self.values('mapped'), set())

    def test_rejected_or_superseded_observation_cannot_supply_value(self):
        for state in ('rejected', 'superseded'):
            self.db.execute("UPDATE observations SET review_state=? WHERE observation_id='obs-mapped'", (state,))
            self.assertEqual(self.values('mapped'), set())


if __name__ == '__main__':
    unittest.main()
