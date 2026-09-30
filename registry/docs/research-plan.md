# Research and ingestion plan

## Phase 1 — Authority map

Maintain the source register, verify licences, and map relevant standards, classifications, unit systems, regulatory sources, and manufacturer families. Store metadata before content.

## Phase 2 — Domain pilots

Choose one narrow class in each priority domain. Define its identity properties and hard-stop conflicts using official standards and primary manufacturer documents. Cable ladder is the first candidate because the public site already uses it as an explanatory example; those example codes are not yet verified registry records.

## Phase 3 — Evidence capture

Collect manufacturer catalogues and datasheets, checksum retained files, record exact locators, and preserve raw observations. Do not scrape or republish sources whose terms are unresolved.

## Phase 4 — Normalization

Map terminology to stable properties, values to controlled codes, and units to UNECE codes. Store raw and normalized values side by side. Run unit, range, uniqueness, and completeness checks.

## Phase 5 — Candidate generation and review

Generate candidates with class-specific blocking keys and versioned fingerprints. Route all merges through reviewed equivalence decisions. Sample rejected and low-score candidates to detect false negatives.

## Phase 6 — Publication

Publish only reviewed items, evidence summaries that licensing permits, change history, and a clear correction path. Track source coverage and freshness publicly; never imply exhaustive coverage.

## Immediate backlog

1. Verify redistribution terms for IEC CDD, UNECE Recommendation 20, GS1 GPC, UNSPSC, and NATO public documents.
2. Review the draft cable-ladder identity-property profile with manufacturers, engineers, and procurement users.
3. Resolve whether splice hardware is included with the ten Legrand and Øglænd pilot parts.
4. Extend artifact retrieval with per-publisher access rules; Øglænd and Niedax PDFs are verified, while the Legrand and Eaton PDFs remain blocked.
5. Add a fourth manufacturer with a materially different construction family and measure false-negative risk in the blocking keys.
6. Design the reviewer queue; immutable part-review and equivalence-decision tables now exist.
7. Independently review the four complete Niedax evidence profiles; completeness alone must not change their status.

## Completed foundation

- Reproducible CSV-to-SQLite ingestion, foreign-key and integrity checks.
- Evidence-completeness audit and fail-closed quality-gate tests.
- Fourteen manufacturer parts from three manufacturers with primary-source observations.
- Four complete-but-unreviewed Niedax profiles with explicit splice-supply evidence.
- Versioned cross-manufacturer pair screening with three reproducible hard-conflict records.
- Local verification of two cached artifacts without committing copyrighted PDFs to Git.
