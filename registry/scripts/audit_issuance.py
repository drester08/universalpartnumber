#!/usr/bin/env python3
"""Fail closed unless every allocated or issued UPN has a valid review chain."""

from __future__ import annotations

import argparse
import sqlite3
import subprocess
import sys
from pathlib import Path

import upn


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=ROOT / "build" / "registry.sqlite")
    arguments = parser.parse_args()
    if not arguments.database.exists():
        print(f"Database not found: {arguments.database}. Run build_registry.py first.")
        return 2

    errors: list[str] = []
    completeness = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "audit_completeness.py"),
            "--database",
            str(arguments.database),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if completeness.returncode != 0:
        errors.append("manufacturer-part publication gate is not clean")

    connection = sqlite3.connect(arguments.database)
    connection.row_factory = sqlite3.Row
    try:
        items = connection.execute(
            """
            SELECT item_id, upn, profile_id, lifecycle_state, reviewed_at
              FROM items_of_supply
             WHERE upn IS NOT NULL
                OR lifecycle_state = 'issued'
                OR EXISTS (
                    SELECT 1
                      FROM upn_allocations
                     WHERE upn_allocations.item_id = items_of_supply.item_id
                )
             ORDER BY item_id
            """
        ).fetchall()
        for item in items:
            item_id = item["item_id"]
            identifier = item["upn"]
            if identifier is None or not upn.valid_upn(identifier):
                errors.append(f"{item_id}: missing or invalid UPN syntax/check digit")
                continue
            allocation = connection.execute(
                """
                SELECT sequence_number, upn, allocation_state
                  FROM upn_allocations
                 WHERE item_id = ?
                """,
                (item_id,),
            ).fetchone()
            if allocation is None:
                errors.append(f"{item_id}: UPN has no permanent allocation record")
            else:
                expected = upn.format_upn(int(allocation["sequence_number"]))
                if allocation["upn"] != identifier or expected != identifier:
                    errors.append(f"{item_id}: allocation sequence and UPN do not agree")
                expected_state = {
                    "candidate": "reserved",
                    "under_review": "reserved",
                    "issued": "active",
                    "deprecated": "retired",
                    "withdrawn": "retired",
                }[item["lifecycle_state"]]
                if allocation["allocation_state"] != expected_state:
                    errors.append(
                        f"{item_id}: allocation state {allocation['allocation_state']} "
                        f"does not match {item['lifecycle_state']} lifecycle"
                    )

            if item["lifecycle_state"] != "issued":
                continue
            review = connection.execute(
                """
                SELECT decision, independence_attested, decided_at
                  FROM item_reviews
                 WHERE item_id = ?
                 ORDER BY decided_at DESC, item_review_id DESC
                 LIMIT 1
                """,
                (item_id,),
            ).fetchone()
            if review is None or review["decision"] != "approved" or review["independence_attested"] != 1:
                errors.append(f"{item_id}: latest item review is not independently approved")
            elif item["reviewed_at"] is None or item["reviewed_at"] < review["decided_at"]:
                errors.append(f"{item_id}: reviewed_at predates the approving item review")

            memberships = connection.execute(
                """
                SELECT im.manufacturer_part_id, im.equivalence_decision_id, im.part_review_id,
                       mp.profile_id
                  FROM item_memberships AS im
                  JOIN manufacturer_parts AS mp
                    ON mp.manufacturer_part_id = im.manufacturer_part_id
                 WHERE im.item_id = ? AND im.valid_to IS NULL
                """,
                (item_id,),
            ).fetchall()
            if not memberships:
                errors.append(f"{item_id}: issued item has no active manufacturer-part membership")
                continue
            if not any(row["part_review_id"] is not None for row in memberships):
                errors.append(f"{item_id}: issued item has no accepted anchor-part membership")
            member_ids = {row["manufacturer_part_id"] for row in memberships}
            for membership in memberships:
                part_id = membership["manufacturer_part_id"]
                if membership["profile_id"] != item["profile_id"]:
                    errors.append(f"{item_id}/{part_id}: profile mismatch")
                if membership["part_review_id"] is not None:
                    part_review = connection.execute(
                        """
                        SELECT review_id, decision
                          FROM manufacturer_part_reviews
                         WHERE manufacturer_part_id = ?
                         ORDER BY decided_at DESC, review_id DESC
                         LIMIT 1
                        """,
                        (part_id,),
                    ).fetchone()
                    if (
                        part_review is None
                        or part_review["review_id"] != membership["part_review_id"]
                        or part_review["decision"] != "accepted"
                    ):
                        errors.append(f"{item_id}/{part_id}: anchor membership lacks latest accepted part review")
                else:
                    decision = connection.execute(
                        """
                        SELECT ed.decision, mc.left_part_id, mc.right_part_id
                          FROM equivalence_decisions AS ed
                          JOIN match_candidates AS mc
                            ON mc.match_candidate_id = ed.match_candidate_id
                         WHERE ed.decision_id = ?
                        """,
                        (membership["equivalence_decision_id"],),
                    ).fetchone()
                    if decision is None or decision["decision"] != "same_item":
                        errors.append(f"{item_id}/{part_id}: equivalence membership lacks same-item decision")
                    elif part_id not in {decision["left_part_id"], decision["right_part_id"]}:
                        errors.append(f"{item_id}/{part_id}: equivalence decision does not cover this part")
                    elif not {decision["left_part_id"], decision["right_part_id"]}.issubset(member_ids):
                        errors.append(f"{item_id}/{part_id}: equivalence counterpart is not an active item member")
    finally:
        connection.close()

    if errors:
        print("UPN issuance gate failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"UPN issuance gate passed: {len(items)} allocated or issued item(s) have valid review chains.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
