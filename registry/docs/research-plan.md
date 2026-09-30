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
2. Define the cable-ladder identity-property profile.
3. Locate primary manufacturer evidence for the two example codes currently shown on the public site.
4. Add a source-artifact downloader that respects access rules and records checksums.
5. Implement CSV-to-SQLite ingestion and evidence completeness tests.
6. Design a reviewer queue and immutable decision log.
