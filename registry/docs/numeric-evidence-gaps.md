# Numeric evidence gaps and splice counting scope

The read-only diagnostic `scripts/build_numeric_evidence_gaps.py` produces `reports/numeric-evidence-gaps.json`. It finds three active normalized numeric records without explicit usable conversion metadata, out of 301 records. The other 298 pass conversion readiness, not source-truth or identity review. This report preserves raw values, installation qualifiers, source locators, observation hashes and registered artifact states. It never supplies a missing unit or creates an approval.

## Three separate requirements

All three gaps use `PROP-REQUIRED-SPLICE-COUNT` and retain the number four. They concern Eaton Flextray splices, Legrand EDRN splices and Legrand SWK sets. These are installation/classification requirements, not evidence of accessories supplied with a tray section. The Legrand methods remain separate records; a set must not silently become a single component or an equivalent connector assembly.

The Eaton source artifact is registered as `blocked`; the Legrand guide is `remote_only`. None of these observations declares a source byte checksum. The earlier shorthand that both sources were remote-only was imprecise; the diagnostic retains their actual different states. A declared hash, if added later, would still need artifact/custody verification, not merely a nonblank field.

## Source checks on 1 October 2026

The official Eaton PDF was readable as browser-extracted text: `https://www.eaton.com/content/dam/eaton/products/support-systems/cable-management/flextray-wire-mesh-basket/choosing-right-wire-basket-tray-wp302016en.pdf`. Its first-page chart places four required splices at the nominal six-inch height and eighteen-inch width intersection, under UL Classification. NC and NM are distinct chart exceptions, not numeric zeros. The second page identifies publication WP302016EN, August 2025. These browser findings corroborate context but do not bind the older observation to retained original bytes.

Direct retrieval failed with a closed connection, then a single alternate client timed out after 45 seconds with zero bytes. PDF screenshot retrieval was also incomplete. No private original, checksum, new registered artifact, complete visual review or machine-bound chart extraction is claimed. The Legrand asset route was inaccessible through the browser tool; its existing wording remains unverified against an original in this turn. Both sources retain restricted/reference-only reuse states.

## Next action and verification

Obtain an accessible authorized original for each source, independently review the exact article/joint and counted-object scope, then record any unit normalization with evidence and explicit qualifiers. Do not assign `UNIT-EA` simply because a field contains an integer. Do not convert required installation quantity into packaged inclusion, erase method differences or infer equivalence.

Five tests cover the actual three scoped gaps, no database mutation/approval, rejected and superseded observation exclusion, invalid versus missing metadata and separate methods under one source. The CLI opens SQLite read-only and rejects a stale/altered snapshot. This diagnostic is not a new publication gate or an authenticated review workflow. Existing counts, source records, reviewer queue, facts, mappings and approvals remain unchanged; no CSV seed was edited.

Verification: all 458 tests passed in 81.107 seconds. Registry build/validation, report reproduction, zero-allocation issuance audit and whitespace checks passed. The scoped data-quality review confirmed specification-record grain, distinct counting methods and missing custody/normalization; no trend history or physical equivalence is inferred.
