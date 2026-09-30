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
3. Resolve missing identity fields and source conflicts across the 38 pilot parts, especially package-included splice hardware, Atkore rung construction, Eaton geometry and length, Legrand height, and the SKF/NSK bearing tolerance and evidence gaps.
4. Extend artifact retrieval with per-publisher access rules; nineteen artifacts are verified locally while fifteen evidence records remain remote-only or blocked.
5. Add a fifth narrow part class and continue expanding manufacturers while measuring false-negative risk in the blocking keys.
6. Work the deterministic reviewer queue, starting with P0 terminology mappings and source conflicts; keep every independent decision in the governed ledgers.
7. Independently review the ten complete Niedax evidence profiles exposed by the queue; completeness alone must not change their status.

## Completed foundation

- Reproducible CSV-to-SQLite ingestion, foreign-key and integrity checks.
- Evidence-completeness audit and fail-closed quality-gate tests.
- Thirty-eight manufacturer or branded parts with primary-source observations across four identity profiles.
- Ten complete-but-unreviewed Niedax profiles with explicit splice-supply evidence.
- Versioned cross-manufacturer screening with 22 reproducible outcomes and property-specific cross-unit comparison.
- Permanent opaque UPN allocation syntax, reproducible canonical-item ledgers, and a fail-closed issuance audit; no UPN is issued yet.
- Property-scoped controlled terminology and independently reviewable source-term mappings; the initial bearing mappings remain proposed.
- A deterministic reviewer queue covering terminology, evidence gaps, observations, conflicts, artifacts, source governance, external identifiers, and complete-part review dependencies.
- Four checksummed user-supplied catalogues covering plate, structural steel, gaskets, and piping are registered as structure research only; their field conflicts and profile implications are documented without treating their rows as verified identity evidence.
- Local verification of nineteen cached artifacts and four reference datasets without committing raw copyrighted or sensitive source files to Git.
- Historical numerical comparison of every supplied gasket row: 11,161 agreements under supported keys, 52 differences and 949 unsupported keys across 12,162 records. Missing construction, drilling, material and thickness evidence still prevents exact-article ingestion and equivalence approval.
