#!/usr/bin/env python3
"""Build a deterministic, evidence-backed reviewer work queue."""

from __future__ import annotations

import argparse
import csv
import io
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numeric_rules


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
CSV_FIELDS = (
    "work_item_id",
    "priority",
    "queue_type",
    "readiness",
    "subject_type",
    "subject_id",
    "profile_id",
    "manufacturer_part_id",
    "source_id",
    "property_id",
    "summary",
    "next_action",
    "blocked_by",
    "policy_version",
)


def add_item(items: list[dict[str, str]], **values: str) -> None:
    item = {field: "" for field in CSV_FIELDS}
    item.update(values)
    item["policy_version"] = item["policy_version"] or "0.1"
    items.append(item)


def numeric_conflicts(
    connection: sqlite3.Connection,
) -> dict[tuple[str, str], tuple[str, str, str]]:
    governed_rules = numeric_rules.load_rules(connection)
    grouped: dict[
        tuple[str, str, str], set[numeric_rules.NumericValue]
    ] = defaultdict(set)
    labels: dict[tuple[str, str, str], str] = {}
    profiles: dict[tuple[str, str, str], str] = {}
    rows = connection.execute(
        """
        SELECT mp.manufacturer_part_id, mp.profile_id, sv.property_id,
               p.preferred_label, sv.normalized_number, u.quantity_kind,
               u.conversion_factor, u.conversion_offset
          FROM manufacturer_parts AS mp
          JOIN observations AS o
            ON o.manufacturer_part_id = mp.manufacturer_part_id
           AND o.review_state NOT IN ('rejected', 'superseded')
          JOIN specification_values AS sv ON sv.observation_id = o.observation_id
          JOIN identity_profile_properties AS ipp
            ON ipp.profile_id = mp.profile_id
           AND ipp.property_id = sv.property_id
           AND ipp.requirement = 'required'
           AND ipp.comparison_rule = 'numeric_exact'
          JOIN properties AS p ON p.property_id = sv.property_id
          JOIN units AS u ON u.unit_id = sv.unit_id
         WHERE sv.normalized_number IS NOT NULL
        """
    )
    for row in rows:
        value = numeric_rules.to_base_value(row)
        if value is None:
            continue
        key = (row["manufacturer_part_id"], row["profile_id"], row["property_id"])
        grouped[key].add(value)
        labels[key] = row["preferred_label"]
        profiles[key] = row["profile_id"]

    conflicts: dict[tuple[str, str], tuple[str, str, str]] = {}
    for (part_id, profile_id, property_id), values in grouped.items():
        if len(values) < 2:
            continue
        rule = governed_rules.get((profile_id, property_id))
        if rule is None or not numeric_rules.sets_compatible(values, values, rule):
            rendered = ", ".join(sorted(format(value.base_value, "f") for value in values))
            conflicts[(part_id, property_id)] = (
                profile_id,
                labels[(part_id, profile_id, property_id)],
                rendered,
            )
    return conflicts


def build_items(connection: sqlite3.Connection) -> list[dict[str, str]]:
    connection.row_factory = sqlite3.Row
    items: list[dict[str, str]] = []

    required_pairs = {
        (row["profile_id"], row["property_id"])
        for row in connection.execute(
            """
            SELECT profile_id, property_id
              FROM identity_profile_properties
             WHERE requirement = 'required'
            """
        )
    }
    insufficient_parts = {
        part_id
        for row in connection.execute(
            """
            SELECT left_part_id, right_part_id
              FROM pair_screenings
             WHERE result = 'insufficient_evidence'
            """
        )
        for part_id in (row["left_part_id"], row["right_part_id"])
    }

    for row in connection.execute(
        """
        SELECT m.mapping_id, m.mapping_basis, m.rationale, sv.raw_value,
               sv.property_id, cv.canonical_code, p.preferred_label,
               o.manufacturer_part_id, o.source_id, o.source_locator,
               mp.profile_id
          FROM specification_value_mappings AS m
          JOIN specification_values AS sv
            ON sv.specification_id = m.specification_id
          JOIN controlled_values AS cv
            ON cv.controlled_value_id = m.controlled_value_id
          JOIN properties AS p ON p.property_id = sv.property_id
          JOIN observations AS o ON o.observation_id = sv.observation_id
          JOIN manufacturer_parts AS mp
            ON mp.manufacturer_part_id = o.manufacturer_part_id
         WHERE m.mapping_state = 'proposed'
        """
    ):
        required = (row["profile_id"], row["property_id"]) in required_pairs
        add_item(
            items,
            work_item_id=f"RW-MAPPING-{row['mapping_id']}",
            priority="P0" if required else "P1",
            queue_type="terminology_mapping_review",
            readiness="ready",
            subject_type="specification_value_mapping",
            subject_id=row["mapping_id"],
            profile_id=row["profile_id"],
            manufacturer_part_id=row["manufacturer_part_id"],
            source_id=row["source_id"],
            property_id=row["property_id"],
            summary=(
                f"Review {row['preferred_label']}: {row['raw_value']!r} -> "
                f"{row['canonical_code']!r}"
            ),
            next_action=(
                f"Independently approve, reject, or revise the {row['mapping_basis']} "
                f"mapping. Source locator: {row['source_locator']}. Proposal: {row['rationale']}"
            ),
        )

    missing_by_part: dict[str, list[str]] = defaultdict(list)
    for row in connection.execute(
        """
        SELECT mp.manufacturer_part_id, mp.manufacturer_part_number, mp.profile_id,
               ipp.property_id, p.preferred_label
          FROM manufacturer_parts AS mp
          JOIN identity_profile_properties AS ipp
            ON ipp.profile_id = mp.profile_id
           AND ipp.requirement = 'required'
          JOIN properties AS p ON p.property_id = ipp.property_id
         WHERE NOT EXISTS (
               SELECT 1
                 FROM observations AS o
                 JOIN specification_values AS sv
                   ON sv.observation_id = o.observation_id
                  AND sv.property_id = ipp.property_id
                WHERE o.manufacturer_part_id = mp.manufacturer_part_id
                  AND o.review_state NOT IN ('rejected', 'superseded')
         )
        """
    ):
        missing_by_part[row["manufacturer_part_id"]].append(row["property_id"])
        add_item(
            items,
            work_item_id=(
                f"RW-EVIDENCE-{row['manufacturer_part_id']}-{row['property_id']}"
            ),
            priority=(
                "P1" if row["manufacturer_part_id"] in insufficient_parts else "P2"
            ),
            queue_type="required_evidence_gap",
            readiness="ready",
            subject_type="manufacturer_part_property",
            subject_id=(
                f"{row['manufacturer_part_id']}:{row['property_id']}"
            ),
            profile_id=row["profile_id"],
            manufacturer_part_id=row["manufacturer_part_id"],
            property_id=row["property_id"],
            summary=(
                f"Find primary evidence for {row['manufacturer_part_number']} — "
                f"{row['preferred_label']}"
            ),
            next_action=(
                "Locate an exact-article, first-party statement or record the field as "
                "unproven; do not infer from a family page or similar part."
            ),
        )

    unreviewed_by_part: Counter[str] = Counter()
    for row in connection.execute(
        """
        SELECT o.observation_id, o.manufacturer_part_id, o.source_id,
               o.source_locator, mp.profile_id, mp.manufacturer_part_number
          FROM observations AS o
          JOIN manufacturer_parts AS mp
            ON mp.manufacturer_part_id = o.manufacturer_part_id
         WHERE o.review_state = 'unreviewed'
        """
    ):
        unreviewed_by_part[row["manufacturer_part_id"]] += 1
        complete = not missing_by_part.get(row["manufacturer_part_id"])
        add_item(
            items,
            work_item_id=f"RW-OBSERVATION-{row['observation_id']}",
            priority="P1" if complete else "P2",
            queue_type="observation_review",
            readiness="ready",
            subject_type="observation",
            subject_id=row["observation_id"],
            profile_id=row["profile_id"],
            manufacturer_part_id=row["manufacturer_part_id"],
            source_id=row["source_id"],
            summary=f"Review source observation for {row['manufacturer_part_number']}",
            next_action=(
                "Check the exact source locator, transcription, units, qualifiers, and "
                f"article scope before accepting or rejecting it: {row['source_locator']}"
            ),
        )

    conflicts = numeric_conflicts(connection)
    conflict_count: Counter[str] = Counter(part_id for part_id, _ in conflicts)
    for (part_id, property_id), (profile_id, label, values) in conflicts.items():
        add_item(
            items,
            work_item_id=f"RW-CONFLICT-{part_id}-{property_id}",
            priority="P0",
            queue_type="source_conflict_resolution",
            readiness="ready",
            subject_type="manufacturer_part_property",
            subject_id=f"{part_id}:{property_id}",
            profile_id=profile_id,
            manufacturer_part_id=part_id,
            property_id=property_id,
            summary=f"Resolve contradictory {label} evidence ({values} in SI base units)",
            next_action=(
                "Recheck each exact-article source and qualifier; supersede or reject only "
                "with an auditable rationale."
            ),
        )

    unapproved_mapping_count: Counter[str] = Counter()
    for row in connection.execute(
        """
        SELECT o.manufacturer_part_id, COUNT(*) AS count
          FROM observations AS o
          JOIN specification_values AS sv ON sv.observation_id = o.observation_id
          JOIN properties AS p ON p.property_id = sv.property_id
         WHERE o.review_state NOT IN ('rejected', 'superseded')
           AND p.value_kind = 'code'
           AND (
               (SELECT COUNT(*)
                  FROM specification_value_mappings AS approved
                 WHERE approved.specification_id = sv.specification_id
                   AND approved.mapping_state = 'approved') != 1
               OR
               (SELECT COUNT(*)
                  FROM specification_value_mappings AS active
                 WHERE active.specification_id = sv.specification_id
                   AND active.mapping_state != 'rejected') != 1
           )
         GROUP BY o.manufacturer_part_id
        """
    ):
        unapproved_mapping_count[row["manufacturer_part_id"]] = row["count"]

    for row in connection.execute(
        """
        SELECT mp.manufacturer_part_id, mp.manufacturer_part_number, mp.profile_id
          FROM manufacturer_parts AS mp
         WHERE NOT EXISTS (
               SELECT 1
                 FROM identity_profile_properties AS ipp
                WHERE ipp.profile_id = mp.profile_id
                  AND ipp.requirement = 'required'
                  AND NOT EXISTS (
                      SELECT 1
                        FROM observations AS o
                        JOIN specification_values AS sv
                          ON sv.observation_id = o.observation_id
                         AND sv.property_id = ipp.property_id
                       WHERE o.manufacturer_part_id = mp.manufacturer_part_id
                         AND o.review_state NOT IN ('rejected', 'superseded')
                  )
         )
           AND NOT EXISTS (
               SELECT 1 FROM manufacturer_part_reviews AS r
                WHERE r.manufacturer_part_id = mp.manufacturer_part_id
           )
        """
    ):
        blockers: list[str] = []
        if unreviewed_by_part[row["manufacturer_part_id"]]:
            blockers.append(
                f"{unreviewed_by_part[row['manufacturer_part_id']]} unreviewed observation(s)"
            )
        if unapproved_mapping_count[row["manufacturer_part_id"]]:
            blockers.append(
                f"{unapproved_mapping_count[row['manufacturer_part_id']]} unapproved code mapping(s)"
            )
        if conflict_count[row["manufacturer_part_id"]]:
            blockers.append(
                f"{conflict_count[row['manufacturer_part_id']]} source conflict(s)"
            )
        add_item(
            items,
            work_item_id=f"RW-PART-{row['manufacturer_part_id']}",
            priority="P1",
            queue_type="complete_part_review",
            readiness="blocked" if blockers else "ready",
            subject_type="manufacturer_part",
            subject_id=row["manufacturer_part_id"],
            profile_id=row["profile_id"],
            manufacturer_part_id=row["manufacturer_part_id"],
            summary=f"Independently review complete evidence package for {row['manufacturer_part_number']}",
            next_action=(
                "When dependencies are cleared, record accepted, rejected, or needs-evidence "
                "with a named independent reviewer and policy version."
            ),
            blocked_by="; ".join(blockers),
        )

    for row in connection.execute(
        """
        SELECT screening_id, left_part_id, right_part_id, profile_id,
               missing_properties
          FROM pair_screenings
         WHERE result = 'insufficient_evidence'
        """
    ):
        add_item(
            items,
            work_item_id=f"RW-PAIR-{row['screening_id']}",
            priority="P1",
            queue_type="candidate_evidence_followup",
            readiness="ready",
            subject_type="pair_screening",
            subject_id=row["screening_id"],
            profile_id=row["profile_id"],
            summary=f"Resolve insufficient evidence for {row['left_part_id']} vs {row['right_part_id']}",
            next_action=(
                f"Research the missing identity fields ({row['missing_properties']}); "
                "do not promote the pair until all hard-stop fields are supported."
            ),
        )

    used_sources = {
        row[0]
        for row in connection.execute(
            "SELECT DISTINCT source_id FROM observations"
        )
    }
    for row in connection.execute(
        """
        SELECT a.artifact_id, a.source_id, a.retrieval_state, a.artifact_url,
               s.title
          FROM source_artifacts AS a
          JOIN sources AS s ON s.source_id = a.source_id
         WHERE a.retrieval_state IN ('remote_only', 'blocked')
        """
    ):
        add_item(
            items,
            work_item_id=f"RW-ARTIFACT-{row['artifact_id']}",
            priority="P2" if row["source_id"] in used_sources else "P3",
            queue_type="artifact_retrieval",
            readiness="ready",
            subject_type="source_artifact",
            subject_id=row["artifact_id"],
            source_id=row["source_id"],
            summary=f"Secure verifiable local evidence for {row['title']}",
            next_action=(
                f"Follow publisher access rules for the {row['retrieval_state']} artifact; "
                f"record bytes and SHA-256 only after successful retrieval: {row['artifact_url']}"
            ),
        )

    for row in connection.execute(
        """
        SELECT source_id, title, ingestion_status, license_state, source_url
          FROM sources
         WHERE ingestion_status IN ('license_review', 'blocked')
        """
    ):
        add_item(
            items,
            work_item_id=f"RW-SOURCE-GOVERNANCE-{row['source_id']}",
            priority="P3",
            queue_type="source_governance",
            readiness="ready",
            subject_type="source",
            subject_id=row["source_id"],
            source_id=row["source_id"],
            summary=f"Resolve access or licensing status for {row['title']}",
            next_action=(
                f"Verify permissible registry use before ingestion; current states are "
                f"ingestion={row['ingestion_status']}, licence={row['license_state']}. "
                f"Source: {row['source_url']}"
            ),
        )

    for row in connection.execute(
        """
        SELECT external_identifier_id, namespace, identifier_value,
               issuing_authority
          FROM external_identifiers
         WHERE verification_state = 'unverified'
        """
    ):
        add_item(
            items,
            work_item_id=f"RW-EXTERNAL-ID-{row['external_identifier_id']}",
            priority="P2",
            queue_type="external_identifier_verification",
            readiness="ready",
            subject_type="external_identifier",
            subject_id=row["external_identifier_id"],
            summary=f"Authority-verify {row['namespace']} {row['identifier_value']}",
            next_action=(
                f"Obtain an exact record from {row['issuing_authority']} or keep the "
                "identifier explicitly unverified."
            ),
        )

    for row in connection.execute(
        """
        SELECT dataset_id, title, verification_state, allowed_use, notes
          FROM source_datasets
         WHERE verification_state IN ('unverified', 'profiled')
        """
    ):
        add_item(
            items,
            work_item_id=f"RW-{row['dataset_id']}",
            priority="P1",
            queue_type="reference_dataset_validation",
            readiness="ready",
            subject_type="source_dataset",
            subject_id=row["dataset_id"],
            summary=f"Validate source provenance and field semantics for {row['title']}",
            next_action=(
                "Resolve the profiled structural issues against exact manufacturer or standards "
                f"sources before identity ingestion. Current use={row['allowed_use']}. {row['notes']}"
            ),
        )

    for row in connection.execute(
        """SELECT f.*, a.source_id, count(r.csv_line) AS affected_rows
             FROM dataset_findings f
             JOIN source_artifacts a ON a.artifact_id = f.artifact_id
             LEFT JOIN dataset_finding_rows r ON r.finding_id = f.finding_id
            GROUP BY f.finding_id"""
    ):
        add_item(
            items, work_item_id=f"RW-{row['finding_id']}", priority=row['priority'],
            queue_type='dataset_finding_review', readiness='ready',
            subject_type='dataset_finding', subject_id=row['finding_id'],
            source_id=row['source_id'], summary=row['summary'],
            next_action=(row['next_action'] + ' Evidence: ' + row['evidence_path'] +
                         '; locators=' + row['evidence_locators'] +
                         '. Row references are in dataset_finding_rows; this task cannot approve an article.'),
            policy_version=row['policy_version'],
        )

    items.sort(
        key=lambda item: (
            item["priority"],
            item["queue_type"],
            item["profile_id"],
            item["subject_id"],
        )
    )
    identifiers = [item["work_item_id"] for item in items]
    if len(identifiers) != len(set(identifiers)):
        raise RuntimeError("Generated duplicate review work-item identifiers")
    return items


def render_csv(items: list[dict[str, str]]) -> str:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=CSV_FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(items)
    return output.getvalue()


def render_summary(items: list[dict[str, str]]) -> str:
    by_type = Counter(item["queue_type"] for item in items)
    by_priority = Counter(item["priority"] for item in items)
    blocked = sum(item["readiness"] == "blocked" for item in items)
    lines = [
        "# Current UPN reviewer queue",
        "",
        "This report is generated deterministically from the governed registry seed data.",
        "It is a work list, not a set of reviewer decisions. Regenerate it whenever source data changes.",
        "",
        f"- Total work items: {len(items)}",
        f"- Ready: {len(items) - blocked}",
        f"- Blocked by explicit dependencies: {blocked}",
        "- No queue item authorizes UPN issuance.",
        "",
        "## Priority counts",
        "",
        "| Priority | Count |",
        "| --- | ---: |",
    ]
    lines.extend(f"| {priority} | {by_priority[priority]} |" for priority in sorted(by_priority))
    lines.extend(
        [
            "",
            "## Queue counts",
            "",
            "| Queue | Count |",
            "| --- | ---: |",
        ]
    )
    lines.extend(f"| {queue_type} | {by_type[queue_type]} |" for queue_type in sorted(by_type))
    lines.extend(
        [
            "",
            "## Priority meaning",
            "",
            "- P0 — blocks trustworthy normalization or contains contradictory identity evidence.",
            "- P1 — direct review or evidence work for a complete profile or plausible candidate pair.",
            "- P2 — required evidence, observation, artifact, or authority-verification work.",
            "- P3 — supporting source-access and licensing work.",
            "",
        ]
    )
    return "\n".join(lines)


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--database",
        type=Path,
        default=ROOT / "build" / "registry.sqlite",
        help="Built registry database (default: registry/build/registry.sqlite)",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--write-snapshot",
        action="store_true",
        help="Update the tracked CSV and Markdown queue snapshots",
    )
    mode.add_argument(
        "--check",
        action="store_true",
        help="Fail unless tracked queue snapshots match the database",
    )
    arguments = parser.parse_args()

    connection = sqlite3.connect(arguments.database)
    connection.row_factory = sqlite3.Row
    try:
        items = build_items(connection)
    finally:
        connection.close()

    csv_content = render_csv(items)
    summary_content = render_summary(items)
    csv_path = REPORTS / "review-queue.csv"
    summary_path = REPORTS / "review-queue-summary.md"
    if arguments.check:
        errors = []
        for path, expected in ((csv_path, csv_content), (summary_path, summary_content)):
            if not path.exists() or path.read_text(encoding="utf-8") != expected:
                errors.append(str(path))
        if errors:
            print("Review queue snapshot is stale: " + ", ".join(errors))
            return 1
        print(f"Review queue snapshot is current: {len(items)} deterministic work items.")
        return 0
    if arguments.write_snapshot:
        write_text(csv_path, csv_content)
        write_text(summary_path, summary_content)
        print(f"Wrote {len(items)} work items to {csv_path} and {summary_path}.")
        return 0

    print(summary_content)
    return 0


if __name__ == "__main__":
    sys.exit(main())
