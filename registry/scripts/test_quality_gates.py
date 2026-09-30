#!/usr/bin/env python3
"""Exercise fail-closed registry constraints and publication gates."""

from __future__ import annotations

import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

import build_registry


ROOT = Path(__file__).resolve().parents[1]


def expect_integrity_error(connection: sqlite3.Connection, sql: str, values: tuple[object, ...]) -> None:
    try:
        connection.execute(sql, values)
    except sqlite3.IntegrityError:
        connection.rollback()
        return
    raise AssertionError("Expected SQLite integrity constraint to reject the record")


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="upn-quality-") as directory:
        database = Path(directory) / "registry.sqlite"
        build_registry.build(database)
        connection = sqlite3.connect(database)
        try:
            connection.execute(
                """
                INSERT INTO manufacturer_part_reviews
                  (review_id, manufacturer_part_id, decision, rationale, reviewer, decided_at, policy_version)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "TEST-REVIEW",
                    "MP-LEGRAND-ZL600G",
                    "accepted",
                    "Deliberately invalid test review",
                    "quality-gate-test",
                    "2026-09-30",
                    "0.1",
                ),
            )
            connection.commit()
        finally:
            connection.close()

        audit = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "audit_completeness.py"), "--database", str(database)],
            capture_output=True,
            text=True,
            check=False,
        )
        if audit.returncode != 1 or "Publication gate failed" not in audit.stdout:
            raise AssertionError(f"Incomplete accepted part was not rejected:\n{audit.stdout}\n{audit.stderr}")

        connection = sqlite3.connect(database)
        try:
            expect_integrity_error(
                connection,
                """
                INSERT INTO source_artifacts
                  (artifact_id, source_id, artifact_url, retrieved_at, retrieval_state)
                VALUES (?, ?, ?, ?, ?)
                """,
                ("TEST-ARTIFACT", "SRC-OGLAEND-LOE-SYSTEM", "https://example.invalid/evidence.pdf", "2026-09-30", "retrieved"),
            )
            expect_integrity_error(
                connection,
                """
                INSERT INTO items_of_supply
                  (item_id, profile_id, preferred_name, lifecycle_state)
                VALUES (?, ?, ?, ?)
                """,
                ("TEST-ITEM", "PROFILE-CABLE-LADDER-STRAIGHT-STEEL-0.1", "Invalid issued item", "issued"),
            )
        finally:
            connection.close()

    print("Quality-gate tests passed: incomplete review, unverified artifact, and unnumbered issued item were rejected.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
