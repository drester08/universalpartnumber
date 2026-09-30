# UPN registry workspace

This directory is the evidence and data foundation for the Universal Part Number registry. It is not yet a populated global parts database and contains no production-issued UPNs.

## What is here

- `schema.sql` — relational schema for sources, taxonomies, manufacturers, parts, observations, evidence, candidate matches, and reviewed equivalence decisions.
- `data/source-register.csv` — initial authoritative-source register with access and licensing constraints.
- `data/domain-seed.csv` — UPN's initial cross-industry domain vocabulary. These are navigation domains, not claims of equivalence.
- `data/supplier-offers.csv` and `data/supplier-offer-identifiers.csv` — commercial seller SKUs, package levels, quantities, and trade-item identifiers kept separate from physical-part identity.
- `data/external-identifiers.csv`, `data/manufacturer-part-external-references.csv`, and `data/external-identifier-evidence.csv` — governed crosswalks to systems such as NSN, with source assertions kept distinct from issuing-authority verification.
- `docs/data-model.md` — entity boundaries and why they matter.
- `docs/matching-policy.md` — conservative workflow for deciding whether two manufacturer part numbers describe the same item of supply.
- `docs/provenance-policy.md` — minimum evidence rules and trust tiers.
- `docs/research-plan.md` — staged path from source discovery to reviewed records.
- `docs/cable-ladder-straight-steel-profile.md` — first class-specific identity profile, evidence, hard stops, and unresolved fields.
- `docs/iso4017-hex-fastener-profile.md` — second identity profile and a documented exact-article comparison that remains short of equivalence.
- `docs/wire-mesh-basket-straight-steel-profile.md` — third identity profile and an exact Eaton SKU that deliberately remains incomplete where official evidence is silent.
- `docs/external-identifiers.md` — fail-closed policy for GTIN/EAN packaging scope, NSNs, and future external item-of-supply crosswalks.
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

The pilot contains 35 branded or manufacturer parts across three identity profiles and ten catalogue organizations: nine manufacturers plus Fabory Nederland B.V. as a distributor and stated catalogue controller. Thirty-one supplier offers explicitly separate seller SKUs, measured order quantities, package levels, and trade identifiers from the physical part records. Unknown EAN, UPC, or GTIN scope remains explicit rather than being assumed to identify one piece. The cable-ladder profile contains 30 parts: six Legrand Swifts, five Øglænd LOE55, ten Niedax KL, five OBO Bettermann LCIS 60, and four Atkore/Unistrut NEMA 3 20B. The Niedax profiles contain all 14 required fields, including an explicit statement that splice plates are ordered separately. The Legrand, Øglænd, and OBO profiles remain at 13 of 14 because splice inclusion is unstated. The Atkore profiles contain 10 of 14; rung profile, rung attachment, side perforation, and splice inclusion remain unknown.

The ISO 4017 profile contains exact Bossard, Würth, Fabory-branded, and Böllhoff M8 × 30 articles. It requires thread direction, bringing the class to 15 required identity properties. Böllhoff and Würth each have 14 of 15, Fabory has 13 of 15, and Bossard has 12 of 15. The wire-mesh profile contains exact Eaton Flextray article `FT6X18X10 BLE`, with seven of eleven required properties evidenced. Wire diameter, both grid spacings, and splice inclusion remain unknown; the page's ambiguous `107.3" actual area` text is intentionally not normalized as square inches. Twenty pairs pass profile-specific coarse blocking across the two profiles that have screening algorithms: 16 are `hard_conflict` and four are `insufficient_evidence`. The single wire-mesh record is audited but cannot produce a cross-manufacturer pair, and no screening algorithm is claimed for that profile yet. Böllhoff's VZD coating is demonstrably different from Bossard's stated blue passivation and Würth's A2K finish, so those pairs fail closed rather than becoming equivalence candidates. The Fabory PDF proves a 200-piece full-box offer, so its EAN is scoped to that box rather than treated as the identifier of one screw. All records remain `unreviewed`, and no UPN has been issued.

The registry now builds 27 relational tables from 56 governed sources and 50 observations. Fourteen cached manufacturer artifacts pass SHA-256 verification; six records remain remote-only or blocked. GS1-labelled EAN, UPC, and GTIN values are rejected during validation unless their length and Mod-10 check digit are valid. Eaton's UPC is attached to the supplier offer with unknown packaging scope, not directly to the physical-part identity. Fabory's NSN `5305-12-337-0503` is preserved as an unreviewed supplier assertion with secondary corroboration, not as an authority-verified manufacturer identifier; exact NMCRL verification remains outstanding. The screening engine is profile-aware. Cable-ladder screen 0.2 and ISO 4017 screen 0.1 distinguish contradictions from compatible but unequal evidence specificity: generic `steel` versus `mild steel`, generic electrolytic zinc versus a named zinc finish, or generic blue zinc plating versus a specific A2K passivation remains unresolved rather than falsely conflicting. Explicitly different coating systems remain hard conflicts. Similarity scores are diagnostic only and never override an identity conflict. Missing evidence is represented as a gap, never guessed.

## Non-negotiable rule

A similar description is not identity. UPN equivalence requires compatible identity-defining properties, traceable evidence, and a recorded human decision. Application suitability and substitution are separate decisions.
