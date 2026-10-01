# Supplier research finding intake — version 0.1

The reviewer queue now includes fourteen explicit angle research tasks: ten seller material-context gaps and four distinct published-mass discrepancies affecting nine offers. These are **open research questions**, not validated physical conflicts, accepted manufacturer articles or same-item decisions. All existing missing-maker tasks remain separate.

## Evidence and grain

`registry/scripts/build_supplier_research_findings.py` derives `registry/reports/supplier-research-findings.json` from two checksum-bound retained reports:

- `macsteel-angle-coverage.json`: SHA-256 `B9BB5AA678DA1307680FEAB93294AF6C5203CD34B701311DC611F6C5A06003BA`.
- `angle-mass-discrepancies.json`: SHA-256 `9C944525325D93AFF3A8B9BAC91DDCEFE5A782E99ABB60A8B1E536A7A905A2A7`.

Each material-context gap is keyed to one seller SKU. Each mass discrepancy is keyed to nominal geometry and seller material-table context, with a list of affected offers. Repeated lengths/SKUs do not inflate the four section-level discrepancies into nine independent findings. The same offer can legitimately have multiple different research questions.

Every finding has a semantic stable ID, issue type, P2 priority, open research state, exact report path/hash/JSON pointer, registered source IDs and related registry offer IDs/SKUs. The adapter validates all 136 coverage offer references, their listing-source relationship and mass-finding geometry/material-context linkage. Duplicate or missing offers, unknown sources, promoted/contradictory evidence and input revision changes fail closed.

`build_review_queue.py` regenerates these findings directly from the bound inputs, rather than trusting an editable queue or copied findings JSON. Tasks appear as `supplier_research_material_context_gap` and `supplier_research_published_mass_discrepancy`, with the full evidence hash/locator and offer references in their next actions. The overall queue contains 417 tasks.

## Reviewer meaning and lifecycle

“Ready” means the retained evidence can be researched now; it does not mean complete article evidence or permission to issue a UPN. P2 is evidence work. The mass findings do not receive physical-conflict status because rounding convention, material-context equivalence and exact section geometry remain unresolved. The draft angle profile is not attached to seller offers as though their route/grade had been proven.

Assigning a manufacturer link does not close a material or mass question. Source changes deliberately require new evidence reconciliation: update and verify the underlying research, review changes to the finding set and hashes, then regenerate both findings and queue snapshots. Do not remove tasks merely to reduce the count. The adapter currently has no independent closure/waiver decision ledger; formal research-resolution governance is outstanding. New evidence can support future resolution, but cannot bypass existing article/equivalence/item approval gates.

## Verification scope

Twelve tests cover task counts and locators, offer relationships, maker-link independence, missing/duplicate references, source mismatches, missing publishers, detached mass geometry, tampered input revisions, semantic ID stability across ordering and decimal serialization, and read-only deterministic generation. Existing registry/queue quality gates also assert the ten-plus-four task categories.

This intake adapter binds already retained report evidence. It is **not** independent source-fidelity review, re-extraction of the PDFs, a certification check or global coverage assurance. The 25 Orange Book geometry absences and other supplier families are not yet included as dedicated finding categories; absence from one design table must not be called global unavailability.
