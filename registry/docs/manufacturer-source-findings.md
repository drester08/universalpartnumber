# Manufacturer publication research findings

Status: research intake 0.1 with resolution governance 0.1; not identity evidence approval. The current resolution ledger is empty, so both actual NTN questions remain open.

The first intake exposes two previously retained NTN 6205ZZ publication issues as separate P2 research-ready tasks. The contradictory metric static-load cells and multiple values under case-sensitive `da max` remain open even though a second manufacturer catalogue corroborates one rating and distinguishes the mounting symbols. Corroboration is not a publisher correction.

## Evidence and identity

`build_manufacturer_source_findings.py` binds two immutable research reports by SHA-256 and joins their registered sources/artifacts to the exact manufacturer-namespaced part and observation. It checks retained raw source hashes and HTML line locators. Each finding includes the article report JSON pointer, all retained display cells, corroborating report/hash, source IDs/URLs and artifact IDs/hashes. It does not independently approve extraction fidelity.

Stable `MRF-` identifiers hash the manufacturer ID, manufacturer-part ID, article-source ID, case-sensitive source field and issue type. Evidence order, line movement or changing report bytes are not the semantic task identity. Report-byte revisions still fail closed and require deliberate reconciliation before a new queue snapshot is accepted. Reordering the two issues leaves their IDs stable while updating their exact pointers.

The generated `manufacturer-source-findings.json` is an inspectable research snapshot. Queue generation derives from the checksum-bound input reports and registry custody rather than trusting an editable copy of that output. The queue type is `manufacturer_source_publication_research`; work IDs are `RW-` plus the finding ID. Both tasks are P2 and ready to research, not ready to approve identity. Their publication values are descriptive fields, not mandatory identity dimensions in the current bearing profile.

## Persistence and hard stops

- Accepting an observation can approve transcription, but does not correct a publisher's contradictory table.
- Approving a terminology mapping or assigning manufacturer provenance cannot close a source-publication issue.
- An altered input report, missing source/artifact, changed manufacturer namespace, changed observation hash, rejected/superseded observation or unexpected issue scope stops generation for explicit reconciliation. No task is silently dropped.
- A supplied corrected-value flag or a claim that catalogue corroboration is a publisher correction stops this open-issue adapter. Resolutions are recorded separately in the governed event ledger; historical issue displays are never rewritten.
- Neither finding is a verified physical incompatibility, an automatic correction, a cross-brand equivalence decision or permission to issue a UPN.

## Next action and resolution limits

For static load, seek an exact-article corrected publication or explicit manufacturer clarification of the metric cells and rating basis. For `da max`, seek an exact drawing/table clarifying lowercase and uppercase symbols and all variant/installation context. Preserve prior bytes, retained cells and source revisions.

`manufacturer-source-resolutions.md` describes the separate resolution/waiver event ledger and its guards. Each decision retains the stable finding, evidence revision, reviewer-independence and exact-scope attestations, disposition and rationale. Local interpretation leaves the publication question open; a waiver explicitly leaves the publication unresolved. New publisher corrections/clarifications require accepted checksum-bound exact-article evidence. Neither closes identity gaps or approves equivalence. Extending intake to other makers should preserve this distinction.

Run after rebuilding the registry:

```powershell
python registry/scripts/build_manufacturer_source_findings.py
python registry/scripts/build_review_queue.py --check
```

Thirteen intake regression tests cover scope, two-question persistence, registry custody, namespace separation, non-closing observation/mapping acceptance, stable IDs, changed-input rejection and read-only derivation. The intake milestone grew the general queue from 424 to 426 tasks. Twenty additional resolution tests use synthetic decisions only; no real finding has been resolved or waived.
