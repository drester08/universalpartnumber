# MPS supplier pipe evidence registration

## Current status — 1 October 2026

The original Mining Pressure Systems technical manual is now registered as `SRC-MPS-TECHNICAL-MANUAL` and `ART-MPS-TECHNICAL-MANUAL`. It is supplier/fabricator context (authority tier 2), not identification of the manufacturer of supplied stock. Publication date is unknown. Source reuse is `review_required` and ingestion is `license_review`.

The private original PDF has SHA-256 `FE5731D47330DAD79637F05CC44E969100B62651852E23F64DBAE147794DED4B`. Registration binds the immutable 144-row research snapshot and 50-row nominal OD/wall comparison to these original bytes. Earlier staged flags describe their historical milestones and are deliberately unchanged. The current registration report is `reports/mps-pipe-registration.json`.

No manufacturer-part observation or specification was added. A generic supplier table cannot identify a mill, an actual supplied article or its certificate. All 50 supplied A106/Welded contradictions and earlier Tenaris source-specific findings remain open. No ID, mass, construction, equivalence or UPN is approved.

## Six new review tasks

The generated queue adds source-reuse governance, one independent extraction/applicability review and four publisher questions:

- DN 80 schedule 160 printed internal diameter.
- DN 400 schedule 10 printed internal diameter.
- DN 600 schedule 160 printed internal diameter.
- DN 50 schedules 40/80 repeated approximate mass.

All five scoped research tasks carry the immutable research checksum. Calculated arithmetic is not a publisher correction. The original source errors remain unchanged. Independent review and new publisher evidence are outstanding, not simulated approvals. These supplier questions are separate from the four NTN manufacturer-article questions and do not enter that article-specific resolution ledger.

## Validation

`scripts/check_mps_pipe_registration.py` verifies exact source metadata, authority/reuse gates, unknown publication date, one original artifact, unchanged PDF/report hashes and reproduction of all supplied nominal comparisons. It rejects promotion into manufacturer-part observations. The database builder runs this check before replacing its previous database. Eight regression tests exercise registration, task coverage, authority/date/reuse/custody/revision tampering and failed-build preservation.

Current baseline: 131 sources, 76 cached evidence records, 17 remote/blocked records, four supplied datasets, five draft profiles, 42 manufacturer parts, 168 supplier offers and 68 observations. All 26 mappings are proposed. The screen remains 25 research pairs. The queue has 466 tasks (455 ready, 11 blocked). No actual independent decision or production UPN exists.

Next obtain independent extraction and source-reuse review, publisher clarification and actual-stock manufacturer/certificate evidence. Nominal dimensional agreement is research context, not proof of interchangeability.
