# Manufacturer equal-angle geometry screening

Research snapshot: 1 October 2026. Not an approved part catalogue or final equivalence decision.

The [ArcelorMittal Orange Book](https://orangebook.arcelormittal.com/node/220) supplies 192 nominal equal-angle section rows under **S355**. This is a distinct publication from the shared Macsteel sheet. Distinct publishers do not necessarily mean independent upstream engineering data.

## Results

All 136 captured Macsteel equal-angle offers were screened by exact nominal leg dimensions and thickness. There are 111 geometry candidates and 25 offers without a geometry candidate in this particular table. An absence is not evidence of global unavailability.

Of the ten earlier S355JR-context gaps, seven have a geometry candidate here. Three do not: the 40 × 40 × 3 offer and both 50 × 50 × 3 offers. The earlier material-context gaps remain open for all ten, because the manufacturer table only states S355.

The report also retains displayed mass comparisons against available same-context rows in the earlier seller PDF. A difference in displayed mass is not automatically a physical conflict: rounding, tabulation conventions and differing section definitions require review. No dimensional comparison establishes manufacturer, tolerances, length, production route, delivery condition or certification of seller stock.

## Reproducibility and provenance

- Script: `registry/scripts/check_orangebook_equal_angles.py`.
- Report: `registry/reports/orangebook-equal-angle-screening.json`.
- Tests: `registry/scripts/test_orangebook_equal_angles.py`.
- Source: `SRC-AM-ORANGEBOOK-EQUAL-ANGLES`; artifact: `ART-AM-ORANGEBOOK-EQUAL-ANGLES`.
- Private artifact: `registry/artifacts/arcelormittal/orangebook-equal-angle-node220.html`.
- SHA-256: `26C8D7ED30A84135A914E22C6A689E51B5628EAB0A9442429AB50971E4B498DF`.

The source contains explicit empty size cells for grouped rows, not HTML body rowspans. Only the size designation is carried forward, with its original data-row locator recorded. No mass, radius, thickness or centroid value inherits. Body spans, missing measurements, duplicate geometry keys, unit changes and header/context drift fail closed.

Selected retained properties are leg dimensions (mm), thickness (mm), mass (kg/m), root and toe radii (mm), and distance to centroid (cm). Remaining engineering properties are outside this extraction scope. Source facts have table, data-row, designation-row and measurement-column locators. The raw page remains private; reuse licensing and independent extraction-fidelity review are outstanding.

## Outstanding work

Obtain seller-stock manufacturer linkage and exact grade/delivery-condition evidence before any article ingestion or equivalence promotion. Review displayed mass differences and independent extraction fidelity. Research primary sources for sizes absent from this table. No UPN has been issued and no equivalence has been approved by this work.
