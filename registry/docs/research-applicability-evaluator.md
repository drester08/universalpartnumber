# Shared research applicability evaluator - 1 October 2026

`scripts/applicability_rules.py` implements version `research-applicability-0.1` for explicit-state capture rules. Each rule declares one selector path, a complete allowed state domain, and required/forbidden detail paths for every state. Missing, unknown, differently cased, non-text or multi-valued selectors produce unresolved applicability; populated details cannot choose the branch on their behalf.

Contracts must be nonempty, versioned and scoped to `research_capture_structure`. Duplicate IDs/selectors, missing/extra state branches, invalid paths, contradictory branch actions, overlapping detail paths and multiple controllers or selector dependencies are rejected. Dependencies/composed boolean predicates are deliberately unsupported in this version rather than partially evaluated.

Zero and false are present values. Null, blank/whitespace text and empty lists/objects are not present detail evidence. The evaluator only checks structural presence/absence; it does not validate material grades, positive dimensions, units or source truth. A zero thickness can pass the presence branch and still fail the capture's typed dimension check. This separation prevents absence handling from silently turning numeric zero into missing information.

The source-bound kamprofile design now adapts its guide-ring, partition and connection branches to the shared evaluator. It keeps existing typed material/thickness/geometry/evidence checks. Assessment output includes per-rule selected state, active detail paths, issues and structural status. The draft JSON and its source bindings are unchanged. No new attachment facts or mutually exclusive connection restrictions are inferred.

All outputs keep source-truth, identity, suitability and UPN permission false. Structural resolution is not applicability truth, source approval or a part review. Sixteen synthetic tests cover contract rejection, selector ambiguity, missing/forbidden details, zero/false semantics, input preservation, source-bound adaptation and continued typed checks. Existing twelve gasket-design tests still exercise the integrated capture path. Synthetic references are never ingested as real articles.

## Production boundary and next work

The prior SQL conditional guard remains active and unchanged. This evaluator does not release any SQL profile, manufacturer part, candidate, accepted publication or UPN. Registered source/article counts, review queue and historical screens remain unchanged. It is a shared research implementation, not finished ingestion/screening/issuance integration.

Next define governed SQL property bindings, versioned source/review-bound predicate metadata and selector-value mappings. Separate identity construction conditions from application suitability. Unknown/conflicting evidence must remain unresolved. Independently review each rule's semantics and exact article applicability; integrate the same engine through ingestion, screening, publication and issuance with stale-review, mutation and bypass tests before replacing the fail-closed guard.
