import sqlite3
import unittest
from pathlib import Path


class ArtifactRevisionTests(unittest.TestCase):
    def setUp(self):
        self.db=sqlite3.connect(':memory:')
        self.db.executescript((Path(__file__).resolve().parents[1]/'schema.sql').read_text(encoding='utf-8'))
        self.db.execute("INSERT INTO sources(source_id,publisher_name,title,source_url,source_type,authority_tier,access_state,license_state,ingestion_status,retrieved_at) VALUES('S','Publisher','Title','https://example.test/','webpage',1,'public','review_required','reference_only','2026-10-01')")

    def tearDown(self): self.db.close()

    def insert(self,identity,digest,state='retrieved'):
        self.db.execute('INSERT INTO source_artifacts(artifact_id,source_id,artifact_url,sha256,retrieved_at,retrieval_state,local_path) VALUES(?,?,?,?,?,?,?)',(identity,'S','https://example.test/',digest,'2026-10-01',state,'private/'+identity if state=='retrieved' else None))

    def test_distinct_revisions_preserved_at_one_url(self):
        self.insert('A','A'*64);self.insert('B','B'*64)
        self.assertEqual(self.db.execute('SELECT count(*) FROM source_artifacts').fetchone()[0],2)
        self.assertEqual(self.db.execute('SELECT count(*) FROM sources').fetchone()[0],1)

    def test_identical_content_duplicate_rejected(self):
        self.insert('A','A'*64)
        with self.assertRaises(sqlite3.IntegrityError): self.insert('B','A'*64)

    def test_unknown_capture_duplicate_rejected(self):
        self.insert('A',None,'remote_only')
        with self.assertRaises(sqlite3.IntegrityError): self.insert('B',None,'remote_only')
        with self.assertRaises(sqlite3.IntegrityError): self.insert('C','','remote_only')

    def test_digest_case_cannot_bypass_uniqueness(self):
        self.insert('A','A'*64)
        with self.assertRaises(sqlite3.IntegrityError): self.insert('B','a'*64)
