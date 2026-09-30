# Reviewer workflow

The reviewer queue turns unresolved registry evidence into a deterministic work list. It does not make decisions and it never issues a UPN.

## Queue inputs

`scripts/build_review_queue.py` reads the built registry and creates work items for:

- proposed terminology mappings;
- missing required identity properties;
- unreviewed source observations;
- contradictory numeric evidence;
- complete evidence packages awaiting independent part review;
- candidate pairs that need more evidence;
- remote-only or blocked artifacts;
- unresolved source licensing or access;
- unverified external identifiers.
- supplied bulk datasets that remain unverified or structure-only.
- seller offers without an established manufacturer-part link.

Seller identity tasks remain research-ready, not item-approval-ready. Stable offer IDs
keep them visible even when commercial price or lifecycle is unknown. They disappear
from this particular queue only after a manufacturer-part link is recorded; that
link does not bypass the separate observation, completeness, equivalence or issuance
gates. Seller SKUs and embedded `mpn` metadata are not proof of manufacturing identity.

Every work-item identifier is derived from a stable registry identifier. No current date, random value, or operator-dependent ordering is used, so the same evidence produces the same queue.

## Readiness and priority

`readiness=ready` means the named task can be worked now. `readiness=blocked` means the row remains visible but its `blocked_by` dependencies must be cleared first. A blocked complete-part review must not be interpreted as review-ready.

- **P0** — resolve before trusting a normalization or conflicted identity field.
- **P1** — review or research directly connected to a complete evidence package or plausible candidate pair.
- **P2** — required evidence, observation, artifact, or external-authority work.
- **P3** — supporting source-access or licensing work.

Priority is triage guidance, not permission to weaken evidence rules.

## Review sequence

1. Open the cited exact source and confirm the article, locator, transcription, units, and qualifiers.
2. For terminology mappings, compare the raw source term with the controlled value definition. The reviewer must differ from the proposer.
3. Accept, reject, or supersede observations and mappings with a concise evidence-backed rationale.
4. Resolve all required-field gaps and source conflicts before part acceptance.
5. Review a complete manufacturer-part evidence package independently under the recorded policy version.
6. Promote a cross-manufacturer pair only after hard-stop identity fields are compatible and a human `same_item` decision is recorded.
7. Issue no UPN until the allocation, item review, membership, evidence, and independence gates all pass.

## Reproducibility

After building the database, verify that the committed queue is current:

```powershell
python registry/scripts/build_review_queue.py --check
```

When governed seed data changes, intentionally regenerate the snapshots:

```powershell
python registry/scripts/build_review_queue.py --write-snapshot
```

The tracked outputs are `reports/review-queue.csv` and `reports/review-queue-summary.md`.
