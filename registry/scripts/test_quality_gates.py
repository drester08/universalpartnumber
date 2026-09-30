#!/usr/bin/env python3
"""Exercise fail-closed registry constraints and publication gates."""

from __future__ import annotations

import sqlite3
import subprocess
import sys
import tempfile
from decimal import Decimal
from pathlib import Path

import build_registry
import build_review_queue
import numeric_rules
import screen_candidates
import upn
import validate_registry


ROOT = Path(__file__).resolve().parents[1]


def expect_integrity_error(connection: sqlite3.Connection, sql: str, values: tuple[object, ...]) -> None:
    try:
        connection.execute(sql, values)
    except sqlite3.IntegrityError:
        connection.rollback()
        return
    raise AssertionError("Expected SQLite integrity constraint to reject the record")


def main() -> int:
    first_upn = upn.format_upn(1)
    if first_upn != "UPN1-000000000001-6":
        raise AssertionError("UPN version-1 format changed from its fixed test vector")
    if not upn.valid_upn(first_upn) or upn.valid_upn(first_upn[:-1] + str((int(first_upn[-1]) + 1) % 10)):
        raise AssertionError("UPN version-1 check digit validation failed")
    try:
        upn.format_upn(0)
    except ValueError:
        pass
    else:
        raise AssertionError("Reserved zero UPN sequence was accepted")
    valid_niedax_eans = (
        "4013339903658",
        "4013339903665",
        "4013339903672",
        "4013339903689",
        "4013339903696",
        "4013339904006",
        "4013339904020",
        "4013339904044",
        "4013339904068",
        "4013339904082",
    )
    if not all(validate_registry.gs1_mod10_valid(value) for value in valid_niedax_eans):
        raise AssertionError("Manufacturer-derived Niedax EAN failed GS1 Mod-10 validation")
    if validate_registry.gs1_mod10_valid("4013339904007"):
        raise AssertionError("Invalid GS1 check digit was accepted")
    if not validate_registry.gs1_mod10_valid("662516721871"):
        raise AssertionError("Eaton exact-SKU UPC failed GS1 Mod-10 validation")
    if not validate_registry.gs1_mod10_valid("800388009257"):
        raise AssertionError("Legrand exact-SKU UPC failed GS1 Mod-10 validation")
    with tempfile.TemporaryDirectory(prefix="upn-quality-") as directory:
        database = Path(directory) / "registry.sqlite"
        build_registry.build(database)

        screening_connection = sqlite3.connect(database)
        screening_connection.row_factory = sqlite3.Row
        try:
            physical_part_trade_identifiers = screening_connection.execute(
                """
                SELECT count(*)
                  FROM manufacturer_part_identifiers
                 WHERE scheme IN ('gtin', 'ean', 'upc')
                """
            ).fetchone()[0]
            if physical_part_trade_identifiers:
                raise AssertionError("Commercial trade identifier was attached directly to a physical part")
            fabory_offer = screening_connection.execute(
                """
                SELECT so.order_quantity, so.order_unit, so.package_level, soi.identifier_scope
                  FROM supplier_offers AS so
                  JOIN supplier_offer_identifiers AS soi
                    ON soi.supplier_offer_id = so.supplier_offer_id
                 WHERE so.supplier_offer_id = 'OFFER-FABORY-01210080030'
                   AND soi.identifier_value = '8715492030054'
                """
            ).fetchone()
            if not fabory_offer or tuple(fabory_offer) != (200, "piece", "box", "box"):
                raise AssertionError("Fabory box quantity and EAN scope were not preserved as an offer")
            boellhoff_offer = screening_connection.execute(
                """
                SELECT order_quantity, order_unit, package_level
                  FROM supplier_offers
                 WHERE supplier_offer_id = 'OFFER-BOELLHOFF-401788VZD830'
                """
            ).fetchone()
            if not boellhoff_offer or tuple(boellhoff_offer) != (200, "piece", "pack"):
                raise AssertionError("Böllhoff order quantity was not preserved as an offer")
            obo_offer = screening_connection.execute(
                """
                SELECT so.order_quantity, so.order_unit, so.package_level, soi.identifier_scope
                  FROM supplier_offers AS so
                  JOIN supplier_offer_identifiers AS soi
                    ON soi.supplier_offer_id = so.supplier_offer_id
                 WHERE so.supplier_offer_id = 'OFFER-OBO-6209721'
                   AND soi.identifier_value = '4012196431731'
                """
            ).fetchone()
            if not obo_offer or tuple(obo_offer) != (3, "meter", "unknown", "unknown"):
                raise AssertionError("OBO measured sales unit and unresolved EAN scope were not preserved")
            niedax_offer = screening_connection.execute(
                """
                SELECT so.order_quantity, so.order_unit, soi.scheme, soi.identifier_value,
                       soi.identifier_scope
                  FROM supplier_offers AS so
                 JOIN supplier_offer_identifiers AS soi
                    ON soi.supplier_offer_id = so.supplier_offer_id
                 WHERE so.supplier_offer_id = 'OFFER-NIEDAX-KL100203F'
                   AND soi.scheme = 'ean'
                """
            ).fetchone()
            if not niedax_offer or tuple(niedax_offer) != (6, "meter", "ean", "4013339904006", "unknown"):
                raise AssertionError("Niedax order unit or manufacturer-defined EAN was misrepresented")
            niedax_raw_code = screening_connection.execute(
                """
                SELECT count(*)
                  FROM supplier_offer_identifiers
                 WHERE supplier_offer_id = 'OFFER-NIEDAX-KL100203F'
                   AND scheme = 'other'
                   AND identifier_value = '904006'
                """
            ).fetchone()[0]
            if niedax_raw_code != 1:
                raise AssertionError("Niedax six-digit catalogue EAN suffix was not preserved")
            eaton_offer = screening_connection.execute(
                """
                SELECT so.order_quantity, so.order_unit, so.package_level,
                       soi.scheme, soi.identifier_value, soi.identifier_scope
                  FROM supplier_offers AS so
                  JOIN supplier_offer_identifiers AS soi
                    ON soi.supplier_offer_id = so.supplier_offer_id
                 WHERE so.supplier_offer_id = 'OFFER-EATON-FT6X18X10-BLE'
                   AND soi.identifier_value = '662516721871'
                """
            ).fetchone()
            if not eaton_offer or tuple(eaton_offer) != (
                None,
                "unknown",
                "unknown",
                "upc",
                "662516721871",
                "unknown",
            ):
                raise AssertionError("Eaton UPC or unresolved commercial scope was misrepresented")
            eaton_required = screening_connection.execute(
                """
                SELECT ipp.property_id
                  FROM identity_profile_properties AS ipp
                 WHERE ipp.profile_id = 'PROFILE-WIRE-MESH-BASKET-STRAIGHT-STEEL-0.1'
                   AND ipp.requirement = 'required'
                   AND NOT EXISTS (
                       SELECT 1
                         FROM observations AS o
                         JOIN specification_values AS sv
                           ON sv.observation_id = o.observation_id
                        WHERE o.manufacturer_part_id = 'MP-EATON-FT6X18X10-BLE'
                          AND o.review_state NOT IN ('rejected', 'superseded')
                          AND sv.property_id = ipp.property_id
                   )
                 ORDER BY ipp.sequence_number
                """
            ).fetchall()
            if [row[0] for row in eaton_required] != [
                "PROP-CROSS-WIRE-DIAMETER",
                "PROP-TOP-LONGITUDINAL-WIRE-DIAMETER",
                "PROP-OTHER-LONGITUDINAL-WIRE-DIAMETER",
                "PROP-MESH-LONGITUDINAL-SPACING",
                "PROP-MESH-TRANSVERSE-SPACING",
                "PROP-SPLICES-INCLUDED",
            ]:
                raise AssertionError("Eaton wire-mesh identity gaps were not preserved explicitly")
            eaton_context = screening_connection.execute(
                """
                SELECT sv.property_id, sv.normalized_number, sv.unit_id
                  FROM observations AS o
                  JOIN specification_values AS sv
                    ON sv.observation_id = o.observation_id
                 WHERE o.manufacturer_part_id = 'MP-EATON-FT6X18X10-BLE'
                   AND sv.property_id IN (
                       'PROP-MINIMUM-WIRE-DIAMETER',
                       'PROP-REQUIRED-SPLICE-COUNT',
                       'PROP-USABLE-CROSS-SECTION'
                   )
                 ORDER BY sv.property_id, sv.specification_id
                """
            ).fetchall()
            if [tuple(row) for row in eaton_context] != [
                ("PROP-MINIMUM-WIRE-DIAMETER", "5", "UNIT-MM"),
                ("PROP-MINIMUM-WIRE-DIAMETER", "5", "UNIT-MM"),
                ("PROP-REQUIRED-SPLICE-COUNT", "4", None),
                ("PROP-USABLE-CROSS-SECTION", "107.3", "UNIT-IN2"),
            ]:
                raise AssertionError("Eaton contextual wire, splice, or area evidence was not preserved")
            if screening_connection.execute(
                """
                SELECT COUNT(*)
                  FROM observations AS o
                  JOIN specification_values AS sv
                    ON sv.observation_id = o.observation_id
                 WHERE o.manufacturer_part_id = 'MP-EATON-FT6X18X10-BLE'
                   AND sv.property_id = 'PROP-SPLICES-INCLUDED'
                """
            ).fetchone()[0]:
                raise AssertionError("A required splice count was misrepresented as packaged splice inclusion")
            area_units = screening_connection.execute(
                """
                SELECT unit_id, quantity_kind, conversion_factor
                  FROM units
                 WHERE unit_id IN ('UNIT-MM2', 'UNIT-IN2')
                 ORDER BY unit_id
                """
            ).fetchall()
            if [tuple(row) for row in area_units] != [
                ("UNIT-IN2", "area", "0.00064516"),
                ("UNIT-MM2", "area", "0.000001"),
            ]:
                raise AssertionError("Area units are malformed or not convertible to square metres")
            governed_rules = numeric_rules.load_rules(screening_connection)
            required_numeric_count = screening_connection.execute(
                """
                SELECT COUNT(*)
                  FROM identity_profile_properties
                 WHERE requirement = 'required' AND comparison_rule = 'numeric_exact'
                """
            ).fetchone()[0]
            if len(governed_rules) != required_numeric_count or required_numeric_count != 21:
                raise AssertionError("Every required numeric identity property must have exactly one governed rule")
            mapping_summary = screening_connection.execute(
                """
                SELECT COUNT(*) AS mapping_count,
                       SUM(CASE WHEN mapping_state = 'approved' THEN 1 ELSE 0 END) AS approved_count
                  FROM specification_value_mappings
                """
            ).fetchone()
            controlled_value_count = screening_connection.execute(
                "SELECT COUNT(*) FROM controlled_values"
            ).fetchone()[0]
            if tuple(mapping_summary) != (15, 0) or controlled_value_count != 11:
                raise AssertionError("Bearing terminology mappings are incomplete or prematurely approved")
            dataset_summary = screening_connection.execute(
                """
                SELECT COUNT(*),
                       SUM(CASE WHEN verification_state = 'profiled' THEN 1 ELSE 0 END),
                       SUM(CASE WHEN allowed_use = 'identity_evidence' THEN 1 ELSE 0 END)
                  FROM source_datasets
                """
            ).fetchone()
            if tuple(dataset_summary) != (4, 4, 0):
                raise AssertionError("User reference datasets were treated as verified identity evidence")
            review_items = build_review_queue.build_items(screening_connection)
            queue_counts = {
                queue_type: sum(item["queue_type"] == queue_type for item in review_items)
                for queue_type in {item["queue_type"] for item in review_items}
            }
            if (
                len(review_items) != 166
                or queue_counts.get("reference_dataset_validation") != 4
                or queue_counts.get("terminology_mapping_review") != 15
                or sum(item["readiness"] == "blocked" for item in review_items) != 11
            ):
                raise AssertionError("Deterministic reviewer queue omitted or misclassified governed work")
            screening_connection.execute("SAVEPOINT mapping_precedence")
            screening_connection.execute(
                """
                UPDATE specification_values
                   SET normalized_text = 'deliberately_wrong_unmapped_value'
                 WHERE specification_id = 'SPEC-SKF-6205-2Z-CLOSURE'
                """
            )
            mapped_parts = screen_candidates.load_parts(screening_connection)
            mapped_closure = mapped_parts["MP-SKF-6205-2Z"]["values"]["PROP-BEARING-CLOSURE"]
            if mapped_closure != {"double_non_contact_metal_shield"}:
                raise AssertionError("Candidate screening did not prefer the auditable controlled-value mapping")
            screening_connection.execute("ROLLBACK TO mapping_precedence")
            screening_connection.execute("RELEASE mapping_precedence")
            nominal_rule = governed_rules[
                ("PROFILE-WIRE-MESH-BASKET-STRAIGHT-STEEL-0.1", "PROP-NOMINAL-WIDTH")
            ]
            overall_rule = governed_rules[
                ("PROFILE-WIRE-MESH-BASKET-STRAIGHT-STEEL-0.1", "PROP-OVERALL-WIDTH")
            ]
            metric_450 = numeric_rules.NumericValue("length", Decimal("0.450"))
            inch_18 = numeric_rules.NumericValue("length", Decimal("0.4572"))
            if not numeric_rules.compatible(metric_450, inch_18, nominal_rule):
                raise AssertionError("Metric and inch nominal market classes were not normalized")
            if numeric_rules.compatible(metric_450, inch_18, overall_rule):
                raise AssertionError("Nominal-class tolerance leaked into exact overall geometry")
            if screen_candidates.compare_property(
                "PROFILE-WIRE-MESH-BASKET-STRAIGHT-STEEL-0.1",
                "PROP-OVERALL-WIDTH",
                "numeric_exact",
                {metric_450},
                {inch_18},
                {},
            ) != "missing":
                raise AssertionError("An ungoverned numeric identity property did not fail closed")
            legrand_offer = screening_connection.execute(
                """
                SELECT so.order_quantity, so.order_unit, so.package_level,
                       soi.scheme, soi.identifier_value, soi.identifier_scope
                  FROM supplier_offers AS so
                  JOIN supplier_offer_identifiers AS soi
                    ON soi.supplier_offer_id = so.supplier_offer_id
                 WHERE so.supplier_offer_id = 'OFFER-LEGRAND-US-CF150450BL'
                   AND soi.identifier_value = '800388009257'
                """
            ).fetchone()
            if not legrand_offer or tuple(legrand_offer) != (
                None,
                "unknown",
                "unknown",
                "upc",
                "800388009257",
                "unknown",
            ):
                raise AssertionError("Legrand UPC or unresolved commercial scope was misrepresented")
            legrand_wire_values = screening_connection.execute(
                """
                SELECT sv.property_id, sv.normalized_number, sv.unit_id
                  FROM specification_values AS sv
                  JOIN observations AS o ON o.observation_id = sv.observation_id
                 WHERE o.manufacturer_part_id = 'MP-LEGRAND-US-CF150450BL'
                   AND sv.property_id IN (
                       'PROP-CROSS-WIRE-DIAMETER',
                       'PROP-TOP-LONGITUDINAL-WIRE-DIAMETER',
                       'PROP-OTHER-LONGITUDINAL-WIRE-DIAMETER'
                   )
                 ORDER BY sv.property_id
                """
            ).fetchall()
            if [tuple(row) for row in legrand_wire_values] != [
                ("PROP-CROSS-WIRE-DIAMETER", "5.9", "UNIT-MM"),
                ("PROP-OTHER-LONGITUDINAL-WIRE-DIAMETER", "3.9", "UNIT-MM"),
                ("PROP-TOP-LONGITUDINAL-WIRE-DIAMETER", "5.9", "UNIT-MM"),
            ]:
                raise AssertionError("Cablofil's distinct load-bearing wire diameters were flattened")
            legrand_context = screening_connection.execute(
                """
                SELECT sv.property_id, sv.normalized_number, sv.unit_id
                  FROM specification_values AS sv
                  JOIN observations AS o ON o.observation_id = sv.observation_id
                 WHERE o.manufacturer_part_id = 'MP-LEGRAND-US-CF150450BL'
                   AND sv.property_id IN (
                       'PROP-REQUIRED-SPLICE-COUNT',
                       'PROP-USABLE-CROSS-SECTION'
                   )
                 ORDER BY sv.property_id, sv.specification_id
                """
            ).fetchall()
            if [tuple(row) for row in legrand_context] != [
                ("PROP-REQUIRED-SPLICE-COUNT", "4", None),
                ("PROP-REQUIRED-SPLICE-COUNT", "4", None),
                ("PROP-USABLE-CROSS-SECTION", "103.23", "UNIT-IN2"),
            ]:
                raise AssertionError("Legrand exact-size splice or fill-area context was not preserved")
            if screening_connection.execute(
                """
                SELECT COUNT(*)
                  FROM observations AS o
                  JOIN specification_values AS sv
                    ON sv.observation_id = o.observation_id
                 WHERE o.manufacturer_part_id = 'MP-LEGRAND-US-CF150450BL'
                   AND sv.property_id = 'PROP-SPLICES-INCLUDED'
                """
            ).fetchone()[0]:
                raise AssertionError("Legrand installation splice counts were misrepresented as package inclusion")
            niedax_family_counts = screening_connection.execute(
                """
                SELECT
                    (SELECT count(*) FROM manufacturer_parts WHERE manufacturer_part_id LIKE 'MP-NIEDAX-KL100%'),
                    (SELECT count(*) FROM supplier_offers WHERE supplier_offer_id LIKE 'OFFER-NIEDAX-KL100%'),
                    (SELECT count(*) FROM supplier_offer_identifiers
                      WHERE supplier_offer_id LIKE 'OFFER-NIEDAX-KL100%' AND scheme = 'ean'),
                    (SELECT count(*) FROM supplier_offer_identifiers
                      WHERE supplier_offer_id LIKE 'OFFER-NIEDAX-KL100%' AND scheme = 'other')
                """
            ).fetchone()
            if tuple(niedax_family_counts) != (10, 10, 10, 10):
                raise AssertionError("The complete Niedax KL 100 S/F width family was not preserved")
            niedax_variant_values = screening_connection.execute(
                """
                SELECT o.manufacturer_part_id, sv.property_id, sv.normalized_text
                  FROM specification_values AS sv
                  JOIN observations AS o ON o.observation_id = sv.observation_id
                 WHERE o.manufacturer_part_id IN ('MP-NIEDAX-KL100203S', 'MP-NIEDAX-KL100203F')
                   AND sv.property_id IN ('PROP-SURFACE-PROTECTION', 'PROP-SIDE-PERFORATION')
                 ORDER BY o.manufacturer_part_id, sv.property_id
                """
            ).fetchall()
            variant_map = {
                (row["manufacturer_part_id"], row["property_id"]): row["normalized_text"]
                for row in niedax_variant_values
            }
            for property_id in ("PROP-SURFACE-PROTECTION", "PROP-SIDE-PERFORATION"):
                if variant_map[("MP-NIEDAX-KL100203S", property_id)] == variant_map[("MP-NIEDAX-KL100203F", property_id)]:
                    raise AssertionError(f"Niedax S/F distinction was lost for {property_id}")
            direct_nsn = screening_connection.execute(
                """
                SELECT count(*)
                  FROM manufacturer_part_identifiers
                 WHERE manufacturer_part_id = 'MP-FABORY-01210080030'
                   AND identifier_value = '5305-12-337-0503'
                """
            ).fetchone()[0]
            if direct_nsn:
                raise AssertionError("NSN was incorrectly modeled as a manufacturer part identifier")
            nsn = screening_connection.execute(
                """
                SELECT ei.verification_state, mper.review_state
                  FROM external_identifiers AS ei
                  JOIN manufacturer_part_external_references AS mper
                    ON mper.external_identifier_id = ei.external_identifier_id
                 WHERE ei.namespace = 'NSN'
                   AND ei.identifier_value = '5305-12-337-0503'
                   AND mper.manufacturer_part_id = 'MP-FABORY-01210080030'
                """
            ).fetchone()
            if not nsn or tuple(nsn) != ("unverified", "unreviewed"):
                raise AssertionError("Unverified Fabory NSN assertion was not kept fail-closed")
            screenings = screen_candidates.screen(screening_connection, "2026-09-30")
        finally:
            screening_connection.close()
        by_pair = {
            (row["left_part_id"], row["right_part_id"]): row
            for row in screenings
        }
        material_specificity = by_pair[("MP-ATKORE-LEK103RHG", "MP-NIEDAX-KL100303F")]
        if "PROP-MATERIAL" in str(material_specificity["conflicting_properties"]).split(";"):
            raise AssertionError("Generic steel versus mild steel was incorrectly treated as a contradiction")
        if "PROP-MATERIAL" not in str(material_specificity["missing_properties"]).split(";"):
            raise AssertionError("Material specificity gap was not preserved as unresolved evidence")
        finish_specificity = by_pair[("MP-OBO-LCIS630", "MP-OGLAEND-1371512")]
        if "PROP-SURFACE-PROTECTION" in str(finish_specificity["conflicting_properties"]).split(";"):
            raise AssertionError("Generic versus specific hot-dip galvanizing was treated as a contradiction")
        if "PROP-SURFACE-PROTECTION" not in str(finish_specificity["missing_properties"]).split(";"):
            raise AssertionError("Finish specificity gap was not preserved as unresolved evidence")
        ladder_200mm = by_pair[("MP-OBO-LCIS620", "MP-OGLAEND-1371511")]
        if ladder_200mm["result"] != "hard_conflict":
            raise AssertionError("The 200 mm OBO/Øglænd pair did not remain fail-closed")
        expected_200mm_conflicts = {
            "PROP-SIDE-RAIL-HEIGHT",
            "PROP-RUNG-PROFILE",
            "PROP-RUNG-ATTACHMENT",
            "PROP-SIDE-RAIL-PROFILE",
            "PROP-SIDE-PERFORATION",
            "PROP-DUTY-SERIES",
        }
        actual_200mm_conflicts = set(str(ladder_200mm["conflicting_properties"]).split(";"))
        if not expected_200mm_conflicts.issubset(actual_200mm_conflicts):
            raise AssertionError("The 200 mm OBO/Øglænd identity conflicts were not preserved")
        fastener_pairs = (
            ("MP-BOSSARD-1049860", "MP-FABORY-01210080030"),
            ("MP-BOSSARD-1049860", "MP-WUERTH-00578-30"),
            ("MP-FABORY-01210080030", "MP-WUERTH-00578-30"),
        )
        for pair in fastener_pairs:
            if by_pair[pair]["result"] != "insufficient_evidence":
                raise AssertionError(f"Unproven ISO 4017 equivalence was not held for evidence: {pair}")
        boellhoff_fabory = by_pair[("MP-BOELLHOFF-401788VZD830", "MP-FABORY-01210080030")]
        if boellhoff_fabory["result"] != "insufficient_evidence":
            raise AssertionError("Generic Fabory zinc evidence was over-read against Böllhoff VZD")
        for pair in (
            ("MP-BOELLHOFF-401788VZD830", "MP-BOSSARD-1049860"),
            ("MP-BOELLHOFF-401788VZD830", "MP-WUERTH-00578-30"),
        ):
            if by_pair[pair]["result"] != "hard_conflict":
                raise AssertionError(f"Distinct passivation systems were not kept separate: {pair}")
            if "PROP-COATING-SPEC" not in str(by_pair[pair]["conflicting_properties"]).split(";"):
                raise AssertionError(f"Coating conflict was not recorded: {pair}")
        bossard_wuerth_missing = str(
            by_pair[("MP-BOSSARD-1049860", "MP-WUERTH-00578-30")]["missing_properties"]
        ).split(";")
        for property_id in (
            "PROP-THREAD-PITCH",
            "PROP-THREAD-DIRECTION",
            "PROP-COATING-SPEC",
            "PROP-PRODUCT-CLASS",
        ):
            if property_id not in bossard_wuerth_missing:
                raise AssertionError(f"Fastener evidence gap was not retained: {property_id}")
        fabory_wuerth_missing = str(
            by_pair[("MP-FABORY-01210080030", "MP-WUERTH-00578-30")]["missing_properties"]
        ).split(";")
        if "PROP-FASTENER-SURFACE" not in fabory_wuerth_missing:
            raise AssertionError("Generic electrolytic zinc versus blue zinc was treated as exact")
        wire_mesh_pair = by_pair[("MP-EATON-FT6X18X10-BLE", "MP-LEGRAND-US-CF150450BL")]
        if wire_mesh_pair["result"] != "hard_conflict":
            raise AssertionError("Eaton and Legrand wire-mesh sections were not held apart")
        for property_id in (
            "PROP-OVERALL-WIDTH",
            "PROP-OVERALL-HEIGHT",
            "PROP-LENGTH",
            "PROP-WIRE-JOINT",
        ):
            if property_id not in str(wire_mesh_pair["conflicting_properties"]).split(";"):
                raise AssertionError(f"Wire-mesh conflict was not recorded: {property_id}")
        for property_id in (
            "PROP-NOMINAL-WIDTH",
            "PROP-NOMINAL-HEIGHT",
            "PROP-SURFACE-PROTECTION",
        ):
            if property_id not in str(wire_mesh_pair["matched_properties"]).split(";"):
                raise AssertionError(f"Wire-mesh nominal or finish match was not retained: {property_id}")
        bearing_pair = by_pair[("MP-NSK-6205ZZ", "MP-SKF-6205-2Z")]
        if bearing_pair["result"] != "hard_conflict":
            raise AssertionError("Matching 6205 boundary dimensions were mistaken for proven bearing identity")
        for property_id in (
            "PROP-BEARING-GEOMETRY",
            "PROP-BORE-DIAMETER",
            "PROP-OUTSIDE-DIAMETER",
            "PROP-BEARING-WIDTH",
            "PROP-BEARING-CLOSURE",
            "PROP-RADIAL-INTERNAL-CLEARANCE",
            "PROP-LOCATING-FEATURE",
        ):
            if property_id not in str(bearing_pair["matched_properties"]).split(";"):
                raise AssertionError(f"Shared 6205 bearing evidence was not retained: {property_id}")
        if "PROP-BEARING-TOLERANCE-CLASS" not in str(bearing_pair["conflicting_properties"]).split(";"):
            raise AssertionError("SKF and NSK tolerance-class designations were not kept distinct")
        for property_id in (
            "PROP-BORE-TYPE",
            "PROP-CAGE-CONSTRUCTION",
            "PROP-BEARING-MATERIAL",
            "PROP-SUPPLIED-LUBRICANT",
        ):
            if property_id not in str(bearing_pair["missing_properties"]).split(";"):
                raise AssertionError(f"Bearing evidence gap was not retained: {property_id}")

        initial_audit = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "audit_completeness.py"), "--database", str(database)],
            capture_output=True,
            text=True,
            check=False,
        )
        if "CF150/450BL: 14/15 required properties" not in initial_audit.stdout:
            raise AssertionError("Legrand wire-mesh completeness was not audited")
        if "source_conflicts=Overall height" not in initial_audit.stdout:
            raise AssertionError("The conflicting official Legrand height values were not surfaced")
        if "FT6X18X10 BLE: 9/15 required properties" not in initial_audit.stdout or (
            "source_conflicts=Section length" not in initial_audit.stdout
        ):
            raise AssertionError("The conflicting official Eaton length values were not surfaced")
        if "6205-2Z: 12/12 required properties" not in initial_audit.stdout:
            raise AssertionError("SKF bearing completeness was not audited")
        if "6205ZZ: 9/12 required properties" not in initial_audit.stdout:
            raise AssertionError("NSK bearing evidence gaps were not audited")

        connection = sqlite3.connect(database)
        try:
            connection.execute(
                "UPDATE observations SET review_state = 'accepted' WHERE observation_id = 'OBS-SKF-6205-2Z-20260930'"
            )
            connection.execute(
                """
                INSERT INTO manufacturer_part_reviews
                  (review_id, manufacturer_part_id, decision, rationale, reviewer, decided_at, policy_version)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "TEST-SKF-MAPPING-REVIEW",
                    "MP-SKF-6205-2Z",
                    "accepted",
                    "Deliberately premature acceptance with proposed terminology mappings",
                    "quality-gate-test",
                    "2026-09-30",
                    "0.1",
                ),
            )
            connection.commit()
        finally:
            connection.close()
        unapproved_mapping_audit = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "audit_completeness.py"), "--database", str(database)],
            capture_output=True,
            text=True,
            check=False,
        )
        if unapproved_mapping_audit.returncode != 1 or "unapproved_code_mappings=9" not in (
            unapproved_mapping_audit.stdout
        ):
            raise AssertionError(
                "Accepted part with unapproved terminology mappings was not rejected:\n"
                f"{unapproved_mapping_audit.stdout}\n{unapproved_mapping_audit.stderr}"
            )
        connection = sqlite3.connect(database)
        try:
            connection.execute("DELETE FROM manufacturer_part_reviews WHERE review_id = 'TEST-SKF-MAPPING-REVIEW'")
            connection.execute(
                "UPDATE observations SET review_state = 'unreviewed' WHERE observation_id = 'OBS-SKF-6205-2Z-20260930'"
            )
            connection.commit()
        finally:
            connection.close()

        issuance_audit = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "audit_issuance.py"), "--database", str(database)],
            capture_output=True,
            text=True,
            check=False,
        )
        if issuance_audit.returncode != 0:
            raise AssertionError(f"Empty issuance ledger did not pass cleanly:\n{issuance_audit.stdout}")

        connection = sqlite3.connect(database)
        try:
            connection.execute(
                """
                INSERT INTO items_of_supply
                  (item_id, upn, profile_id, preferred_name, lifecycle_state, created_at, reviewed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "TEST-ISSUED-ITEM",
                    first_upn,
                    "PROFILE-CABLE-LADDER-STRAIGHT-STEEL-0.1",
                    "Deliberately unreviewed issued item",
                    "issued",
                    "2026-09-30",
                    "2026-09-30",
                ),
            )
            connection.execute(
                """
                INSERT INTO upn_allocations
                  (allocation_id, sequence_number, upn, item_id, allocated_by, allocated_at, allocation_state)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                ("TEST-ALLOCATION", 1, first_upn, "TEST-ISSUED-ITEM", "quality-gate-test", "2026-09-30", "active"),
            )
            connection.commit()
        finally:
            connection.close()
        invalid_issuance = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "audit_issuance.py"), "--database", str(database)],
            capture_output=True,
            text=True,
            check=False,
        )
        if invalid_issuance.returncode != 1 or "latest item review is not independently approved" not in invalid_issuance.stdout or (
            "issued item has no active manufacturer-part membership" not in invalid_issuance.stdout
        ):
            raise AssertionError(
                "Issued UPN without review and membership was not rejected:\n"
                f"{invalid_issuance.stdout}\n{invalid_issuance.stderr}"
            )
        connection = sqlite3.connect(database)
        try:
            connection.execute("DELETE FROM upn_allocations WHERE allocation_id = 'TEST-ALLOCATION'")
            connection.execute("DELETE FROM items_of_supply WHERE item_id = 'TEST-ISSUED-ITEM'")
            connection.commit()
        finally:
            connection.close()

        second_upn = upn.format_upn(2)
        connection = sqlite3.connect(database)
        try:
            connection.execute(
                """
                INSERT INTO items_of_supply
                  (item_id, profile_id, preferred_name, lifecycle_state, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    "TEST-RESERVED-ITEM",
                    "PROFILE-CABLE-LADDER-STRAIGHT-STEEL-0.1",
                    "Deliberately inconsistent reservation",
                    "candidate",
                    "2026-09-30",
                ),
            )
            connection.execute(
                """
                INSERT INTO upn_allocations
                  (allocation_id, sequence_number, upn, item_id, allocated_by, allocated_at, allocation_state)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                ("TEST-RESERVATION", 2, second_upn, "TEST-RESERVED-ITEM", "quality-gate-test", "2026-09-30", "reserved"),
            )
            connection.commit()
        finally:
            connection.close()
        inconsistent_reservation = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "audit_issuance.py"), "--database", str(database)],
            capture_output=True,
            text=True,
            check=False,
        )
        if inconsistent_reservation.returncode != 1 or "missing or invalid UPN syntax/check digit" not in (
            inconsistent_reservation.stdout
        ):
            raise AssertionError(
                "Allocation whose item omitted the reserved UPN escaped audit:\n"
                f"{inconsistent_reservation.stdout}\n{inconsistent_reservation.stderr}"
            )
        connection = sqlite3.connect(database)
        try:
            connection.execute("DELETE FROM upn_allocations WHERE allocation_id = 'TEST-RESERVATION'")
            connection.execute("DELETE FROM items_of_supply WHERE item_id = 'TEST-RESERVED-ITEM'")
            connection.commit()
        finally:
            connection.close()

        third_upn = upn.format_upn(3)
        connection = sqlite3.connect(database)
        try:
            connection.execute(
                """
                INSERT INTO items_of_supply
                  (item_id, upn, profile_id, preferred_name, lifecycle_state, created_at, reviewed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "TEST-UNANCHORED-ITEM",
                    third_upn,
                    "PROFILE-CABLE-LADDER-STRAIGHT-STEEL-0.1",
                    "Deliberately unanchored issued item",
                    "issued",
                    "2026-09-30",
                    "2026-09-30T12:00:00Z",
                ),
            )
            connection.execute(
                """
                INSERT INTO upn_allocations
                  (allocation_id, sequence_number, upn, item_id, allocated_by, allocated_at, allocation_state)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                ("TEST-UNANCHORED-ALLOCATION", 3, third_upn, "TEST-UNANCHORED-ITEM", "quality-gate-test", "2026-09-30", "active"),
            )
            connection.execute(
                """
                INSERT INTO match_candidates
                  (match_candidate_id, left_part_id, right_part_id, algorithm_version, score, blocking_keys, generated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                ("TEST-CANDIDATE", "MP-LEGRAND-ZL450G", "MP-LEGRAND-ZL600G", "quality-gate-test", "1", "test", "2026-09-30"),
            )
            connection.execute(
                """
                INSERT INTO equivalence_decisions
                  (decision_id, match_candidate_id, decision, rationale, reviewer, decided_at, policy_version)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                ("TEST-EQUIVALENCE", "TEST-CANDIDATE", "same_item", "Deliberately invalid test decision", "quality-gate-test", "2026-09-30", "0.1"),
            )
            connection.execute(
                """
                INSERT INTO item_reviews
                  (item_review_id, item_id, decision, rationale, reviewer, decided_at, policy_version, independence_attested)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                ("TEST-ITEM-REVIEW", "TEST-UNANCHORED-ITEM", "approved", "Deliberately invalid test approval", "quality-gate-test", "2026-09-30", "1.0", 1),
            )
            for part_id in ("MP-LEGRAND-ZL450G", "MP-LEGRAND-ZL600G"):
                connection.execute(
                    """
                    INSERT INTO item_memberships
                      (item_id, manufacturer_part_id, equivalence_decision_id, valid_from)
                    VALUES (?, ?, ?, ?)
                    """,
                    ("TEST-UNANCHORED-ITEM", part_id, "TEST-EQUIVALENCE", "2026-09-30"),
                )
            connection.commit()
        finally:
            connection.close()
        unanchored_issuance = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "audit_issuance.py"), "--database", str(database)],
            capture_output=True,
            text=True,
            check=False,
        )
        if unanchored_issuance.returncode != 1 or "issued item has no accepted anchor-part membership" not in (
            unanchored_issuance.stdout
        ):
            raise AssertionError(
                "Issued item without an accepted anchor part escaped audit:\n"
                f"{unanchored_issuance.stdout}\n{unanchored_issuance.stderr}"
            )
        connection = sqlite3.connect(database)
        try:
            connection.execute("DELETE FROM item_memberships WHERE item_id = 'TEST-UNANCHORED-ITEM'")
            connection.execute("DELETE FROM item_reviews WHERE item_id = 'TEST-UNANCHORED-ITEM'")
            connection.execute("DELETE FROM equivalence_decisions WHERE decision_id = 'TEST-EQUIVALENCE'")
            connection.execute("DELETE FROM match_candidates WHERE match_candidate_id = 'TEST-CANDIDATE'")
            connection.execute("DELETE FROM upn_allocations WHERE allocation_id = 'TEST-UNANCHORED-ALLOCATION'")
            connection.execute("DELETE FROM items_of_supply WHERE item_id = 'TEST-UNANCHORED-ITEM'")
            connection.commit()
        finally:
            connection.close()

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
            connection.execute("DELETE FROM manufacturer_part_reviews WHERE review_id = 'TEST-REVIEW'")
            connection.execute(
                "UPDATE observations SET review_state = 'accepted' "
                "WHERE manufacturer_part_id = 'MP-LEGRAND-US-CF150450BL'"
            )
            connection.execute(
                """
                INSERT INTO specification_values
                  (specification_id, observation_id, property_id, raw_value, normalized_text)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    "TEST-LEGRAND-SPLICE",
                    "OBS-LEGRAND-US-CF150450BL-PAGE",
                    "PROP-SPLICES-INCLUDED",
                    "Deliberate test completion value",
                    "false",
                ),
            )
            connection.execute(
                """
                INSERT INTO manufacturer_part_reviews
                  (review_id, manufacturer_part_id, decision, rationale, reviewer, decided_at, policy_version)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "TEST-CONFLICT-REVIEW",
                    "MP-LEGRAND-US-CF150450BL",
                    "accepted",
                    "Deliberately invalid review over conflicting height evidence",
                    "quality-gate-test",
                    "2026-09-30",
                    "0.1",
                ),
            )
            connection.commit()
        finally:
            connection.close()

        conflict_audit = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "audit_completeness.py"), "--database", str(database)],
            capture_output=True,
            text=True,
            check=False,
        )
        if conflict_audit.returncode != 1 or "source_conflicts=Overall height" not in conflict_audit.stdout:
            raise AssertionError(
                "Accepted part with contradictory source evidence was not rejected:\n"
                f"{conflict_audit.stdout}\n{conflict_audit.stderr}"
            )

        connection = sqlite3.connect(database)
        try:
            connection.execute("PRAGMA foreign_keys = ON")
            expect_integrity_error(
                connection,
                """
                INSERT INTO specification_value_mappings
                  (mapping_id, specification_id, property_id, controlled_value_id,
                   mapping_basis, mapping_state, rationale, proposed_by, proposed_at, policy_version)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "TEST-MAPPING-PROPERTY-MISMATCH",
                    "SPEC-SKF-6205-2Z-GEOMETRY",
                    "PROP-BEARING-CLOSURE",
                    "CV-BEARING-CLOSURE-DOUBLE-NONCONTACT-METAL",
                    "source_exact",
                    "proposed",
                    "Deliberately mismatched property",
                    "quality-gate-test",
                    "2026-09-30",
                    "0.1",
                ),
            )
            expect_integrity_error(
                connection,
                """
                INSERT INTO specification_value_mappings
                  (mapping_id, specification_id, property_id, controlled_value_id,
                   mapping_basis, mapping_state, rationale, proposed_by, proposed_at,
                   reviewer, reviewed_at, policy_version)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "TEST-MAPPING-NONINDEPENDENT",
                    "SPEC-SKF-6205-2Z-TOLERANCE",
                    "PROP-BEARING-TOLERANCE-CLASS",
                    "CV-BEARING-TOLERANCE-P0",
                    "expert_interpretation",
                    "approved",
                    "Deliberately non-independent approval",
                    "same-person",
                    "2026-09-30",
                    "same-person",
                    "2026-09-30",
                    "0.1",
                ),
            )
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
            connection.execute(
                """
                INSERT INTO items_of_supply
                  (item_id, profile_id, preferred_name, lifecycle_state, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    "TEST-CANDIDATE-ITEM",
                    "PROFILE-CABLE-LADDER-STRAIGHT-STEEL-0.1",
                    "Test candidate item",
                    "candidate",
                    "2026-09-30",
                ),
            )
            connection.commit()
            expect_integrity_error(
                connection,
                """
                INSERT INTO item_reviews
                  (item_review_id, item_id, decision, rationale, reviewer, decided_at,
                   policy_version, independence_attested)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "TEST-NONINDEPENDENT-REVIEW",
                    "TEST-CANDIDATE-ITEM",
                    "approved",
                    "Deliberately invalid approval",
                    "quality-gate-test",
                    "2026-09-30",
                    "1.0",
                    0,
                ),
            )
            expect_integrity_error(
                connection,
                """
                INSERT INTO item_memberships
                  (item_id, manufacturer_part_id, valid_from)
                VALUES (?, ?, ?)
                """,
                ("TEST-CANDIDATE-ITEM", "MP-NIEDAX-KL100203S", "2026-09-30"),
            )
            connection.execute("DELETE FROM items_of_supply WHERE item_id = 'TEST-CANDIDATE-ITEM'")
            connection.commit()
            expect_integrity_error(
                connection,
                """
                INSERT INTO external_identifiers
                  (external_identifier_id, namespace, identifier_value, issuing_authority,
                   identifier_scope, verification_state, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "TEST-EXT-ID",
                    "NSN",
                    "0000-00-000-0000",
                    "Test authority",
                    "item_of_supply",
                    "authority_verified",
                    "Invalid verified identifier without an authority source",
                ),
            )
        finally:
            connection.close()

    print(
        "Quality-gate tests passed: specificity gaps and source conflicts stayed unresolved; "
        "incomplete review, contradictory evidence, unapproved terminology mappings, unverified artifacts, "
        "inconsistent reservations, unanchored items, and unnumbered or unreviewed issued UPN items were rejected."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
