# Manufacturer source-publication resolution history

Policy: `manufacturer-source-resolution-0.1`. Implemented research governance; no real decisions have been made. The current ledger has zero events and both NTN findings remain open.

## Purpose and boundaries

`data/manufacturer-source-resolution-events.json` stores an ordered event history separate from immutable source findings. `scripts/manufacturer_source_resolutions.py` validates and replays it without writing to the database. The findings snapshot retains every original issue, all display cells and the complete decision history. The registry builder checks the ledger against the newly built database before replacing a prior database; queue generation checks it again.

This does not change observations, specifications, mappings, manufacturer-part reviews, equivalence decisions or UPN allocations. Approved research resolutions are not approved physical identities. Publisher-correction status in the research report describes the reviewed disposition, not an automatically applied replacement rating or dimension.

## Distinct dispositions

| Reviewed disposition | Research state | Publication status | Active original research task |
| --- | --- | --- | --- |
| Publisher corrected | resolved | corrected | Removed from active queue; preserved in history |
| Manufacturer clarified | resolved | clarified | Removed from active queue; preserved in history |
| Local interpretation | interpreted | unresolved | Retained |
| Waived | waived | unresolved | Removed from active queue; preserved in history |
| Reopened | open | unresolved | Restored with the same stable ID |

A proposal alone closes nothing. It creates an independent resolution-review task in addition to any remaining original research task. Rejection retains the previous research state and proposal history. A new proposal for a resolved/waived finding requires reopening first. Local interpretations may be revised by later proposals, preserving each decision.

## Evidence and review requirements

Every proposal binds the stable finding ID plus a digest of its subject, observation, original displays, exact report pointer/HTML line and registered evidence hashes. A changed input revision stops replay for explicit reconciliation; this policy does not yet implement cross-revision migration.

Proposals require a disposition, interpretation, residual-risk statement, rationale and at least one source/artifact/locator reference, including waivers. Each reference binds the exact manufacturer-part ID and case-sensitive source field. Artifact registry state, source linkage, cache containment and actual file SHA-256 are rechecked. Blocked sources, remote-only evidence and missing/changed bytes fail closed.

Publisher correction and manufacturer clarification require new bytes beyond the original article/corroboration, an accepted exact-article observation bound to the same hash, authority tier 1, publisher name matching the registered maker's legal name and HTTPS source/artifact URLs within its registered website domain. Lookalike domain suffixes do not qualify. This deliberately narrow maker rule does not infer parent-company or authorized-distributor relationships. Broader relationships need separate governed provenance, not a relaxed name comparison. A family catalogue alone cannot satisfy these dispositions.

An approval or rejection references the active proposal, requires a named actor different from the proposer (case-insensitive), and true independence and exact-scope attestations. Evidence is revalidated at review. These are recorded attestations, not authenticated identities or automated proof that a source locator truly supports the interpretation. A human independent reviewer must inspect the exact article, field meaning, revision and variant scope. Accepted observations are an additional gate, not a substitute for that review.

## Event format and procedure

The ledger has exactly `policy_version` and `events`. Each event contains:

- `event_id`: unique `MRE-` plus 24 uppercase hexadecimal characters.
- `previous_event_id` and `previous_event_sha256`: empty for the first event; thereafter the previous global event ID and canonical JSON digest.
- `finding_id` and `finding_evidence_sha256`: the retained finding and `evidence_binding(finding)` digest.
- `action`, `actor`, UTC `occurred_at`, `rationale`, `policy_version`, and action-specific `payload`.

Supported payloads:

- `propose`: `disposition`, nonempty `evidence`, `interpretation`, `residual_risk`. Evidence entries contain `source_id`, `artifact_id`, `artifact_sha256`, `source_locator`, `manufacturer_part_id`, `source_field`, and `observation_id` (empty only for contextual evidence that is not claimed as exact-article primary correction/clarification).
- `approve` / `reject`: `proposal_event_id`, `independence_attested: true`, `scope_attested: true`.
- `reopen`: `decision_event_id` referring to the latest approved decision, with an explicit rationale.

Unknown fields, duplicate JSON keys/IDs, unsupported actions/policies, backward or timezone-less timestamps, conflicting active proposals and detached reviews fail closed. Append events through reviewed file changes; never rewrite or delete existing history. The chain detects edits against following events but is not a digital signature, trusted timestamp, or protection against coordinated full-history/tip rewriting. Version control and independent review remain necessary; do not call the file cryptographically immutable.

After adding a real reviewed event, rebuild the registry, regenerate findings and queue snapshots, and rerun all tests and quality gates. Preserve new raw evidence privately and archive the dated ledger and reports. Do not invent reviewer approvals merely to clear the queue.

## Current verification and limits

Twenty synthetic regression tests cover proposal/review/waiver/reopen, stable task restoration, non-closing local interpretation, old-catalogue rejection as correction, reviewer independence, attestations, history edits, field scope, artifact custody, timestamps, duplicate JSON keys, new-primary correction gates and preservation of a previous database on invalid history.

The implementation does not authenticate reviewers, semantically parse correction documents, migrate finding revisions, monitor corrected URLs, or apply corrected specifications. Supplier and bulk-dataset findings do not yet use this ledger. The global research and independent-review work remains open.
