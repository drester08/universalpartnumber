# UPN registry workspace

This directory is the evidence and data foundation for the Universal Part Number registry. It is not yet a populated global parts database and contains no production-issued UPNs.

## What is here

- `schema.sql` — relational schema for sources, taxonomies, manufacturers, parts, observations, evidence, candidate matches, and reviewed equivalence decisions.
- `data/source-register.csv` — initial authoritative-source register with access and licensing constraints.
- `data/domain-seed.csv` — UPN's initial cross-industry domain vocabulary. These are navigation domains, not claims of equivalence.
- `docs/data-model.md` — entity boundaries and why they matter.
- `docs/matching-policy.md` — conservative workflow for deciding whether two manufacturer part numbers describe the same item of supply.
- `docs/provenance-policy.md` — minimum evidence rules and trust tiers.
- `docs/research-plan.md` — staged path from source discovery to reviewed records.
- `docs/cable-ladder-straight-steel-profile.md` — first class-specific identity profile, evidence, hard stops, and unresolved fields.
- `scripts/validate_registry.py` — dependency-free validation for the seed data and SQLite schema.
- `scripts/build_registry.py` — creates a fresh local SQLite database from the reviewed seed files.
- `scripts/audit_completeness.py` — reports missing identity fields and prevents incomplete observations from being accepted.
- `scripts/screen_candidates.py` — reproducibly screens cross-manufacturer pairs and records hard conflicts before review.
- `scripts/verify_artifacts.py` — hashes locally retained evidence and rejects missing or mislabelled cache records.
- `scripts/test_quality_gates.py` — proves incomplete reviews, unverified artifacts, and unnumbered issued items fail closed.

Run both checks from the repository root:

```powershell
python registry/scripts/validate_registry.py
python registry/scripts/build_registry.py
python registry/scripts/audit_completeness.py
python registry/scripts/screen_candidates.py --check registry/data/pair-screenings.csv
python registry/scripts/verify_artifacts.py
python registry/scripts/test_quality_gates.py
```

The generated database is written to `registry/build/registry.sqlite` and is intentionally excluded from Git; the schema and CSV inputs are the reproducible source of truth.

## Current status

Foundation and pilot data only. The schema, policies, ingestion checks, artifact verification, candidate screening, and fail-closed publication gates are operational. Source licensing must be resolved before bulk ingestion, and every manufacturer observation still requires independent review.

The pilot contains 22 manufacturer parts: six Legrand Swifts and four each from Øglænd LOE55, Niedax KL, OBO Bettermann LCIS 60, and Atkore/Unistrut NEMA 3 20B. The Niedax profiles contain all 14 required fields, including an explicit statement that splice plates are ordered separately. The Legrand, Øglænd, and OBO profiles remain at 13 of 14 because splice inclusion is unstated. The Atkore profiles contain 10 of 14; rung profile, rung attachment, side perforation, and splice inclusion remain unknown. All records remain `unreviewed`, and no UPN has been issued.

Thirteen pairs pass coarse blocking. Each is reproducibly classified `hard_conflict`, including five new Atkore comparisons. Version 0.2 of the screen distinguishes an actual contradiction from compatible but unequal evidence specificity: generic `steel` versus `mild steel`, for example, is unresolved rather than falsely conflicting. Similarity scores are diagnostic only and never override an identity conflict. Missing evidence is represented as a gap, never guessed.

## Non-negotiable rule

A similar description is not identity. UPN equivalence requires compatible identity-defining properties, traceable evidence, and a recorded human decision. Application suitability and substitution are separate decisions.
