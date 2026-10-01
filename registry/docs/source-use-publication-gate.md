# Source-use publication gate - 1 October 2026

Research for an exact SKF 6204-2Z article reached the official India marketplace. Inspection of its [terms](https://www.emarketplace.in.skf.com/terms-and-conditions), sections 6.1(k)-(l) and 7.3(vi), found restrictions on aggregation, systematic extraction and reutilization. Product-table intake stopped. The previously downloaded article and terms are privately preserved, not registered or published as a product dataset. Permission or an acceptable alternative source is required; this is an authorization hold, not a legal opinion.

`reports/skf-marketplace-authorization-hold.json` contains URLs, private capture paths/checksums, clause locators, hold status and next action, not the technical table. Its verifier checks both captured revisions and restriction cues. The existing `SRC-SKF-6205-2Z` record already has `restricted`/`reference_only` states and remains unchanged. No prior observation, interpretation or historical finding is erased or relabelled as authorized.

## Runtime enforcement

Previously the completeness audit did not check source-use state. `scripts/source_use_gates.py` now holds every manufacturer part whose active observation uses a source that is not both `license_verified` and `open`/`attribution`. Both metadata gates are required. `restricted`, `review_required`, `unknown`, reference-only, metadata-only and blocked sources cannot support accepted publication merely because their technical data is complete.

The audit reports held source IDs/states and rejects affected accepted parts. It also includes profiles with no required-field rows, so the source gate cannot be skipped by an empty/descriptive-only profile. The existing issuance audit propagates publication failure. Rejected/superseded observations are excluded; unreviewed research remains permitted. This does not change source/article counts, current research screens, reviewer decisions or UPN allocations.

Seven synthetic tests cover existing restricted SKF evidence, both license-state requirements, superseded evidence, source-only acceptance/issuance failures, unreviewed research, metadata-only hold reporting and changed capture bytes. No test represents a real permission grant or independent review.

## Limits and next work

This enforces registered metadata, not the legal truth of a permission claim. `license_verified` and an acceptable license state must only be set after genuine scope-specific authorization review; no such review is fabricated here. Versioned grant evidence, artifact scope, attribution duties, expiry/revocation and independent review binding still need implementation. Direct SQL writes are not an audit pass. Existing conditional guards also remain active.

Obtain permission or a rights-compatible exact manufacturer source before further SKF marketplace intake. Establish publisher/content provenance independently; a manufacturer-hosted marketplace is not automatically a factory certificate or endorsement of seller claims. Continue other primary-source research without bypassing the hold. No SKF 6204 part, structured technical dataset, observation, mapping, equivalence or UPN is added in this milestone.
