# UPN registry workspace

This directory is the evidence and data foundation for the Universal Part Number registry. It is not yet a populated global parts database and contains no production-issued UPNs.

Current baseline (1 October 2026): 122 sources, 67 cached evidence records, four supplied datasets, five draft profiles, 39 manufacturer parts, 168 supplier offers and 62 observations. The screen contains 24 pairs and the reviewer queue contains 426 tasks (415 ready, 11 blocked). All 17 terminology mappings remain proposed. See `docs/research-plan.md` for current priorities; milestone counts below are historical. `docs/schaeffler-retrieval-lead.md` records an unverified source-discovery lead and does not add article evidence or queue tasks.

Manufacturer publication resolution governance is implemented in `docs/manufacturer-source-resolutions.md`. An empty event ledger preserves both actual NTN issues as open. Evidence-bound independent research decisions can distinguish correction, clarification, local interpretation and waiver, and can be reopened without deleting original source facts. No real decision or identity approval has been entered.

Current ten-gap detail follow-up: `docs/macsteel-angle-gap-details.md` records ten matching seller detail assertions and ten linked PDFs identical to the earlier generic sheet. One content source does not become twelve independent confirmations. All ten material-context gaps remain open. Sources115/cache60records/queue403; no maker link, mass transfer, correction or UPN.

Current full angle-context screen: `docs/macsteel-angle-coverage.md` partitions all136captured offers into126nominal-context candidates and10S355JRtable gaps. Geometries appearing only under CQ are not transferred into S355JRproperties. Earlier30offer screen remains unchanged. Sources95/cache40/offers168/queue403unchanged; identity, route and delivery condition unapproved.

Current detail follow-up: `docs/macsteel-cq-pair.md` establishes that both nominally duplicated CQ50x50x5seller pages explicitly state6m. The7200suffix is not a verified length; article identity and maker remain unresolved. Two new private detail artifacts bring sources95andcached artifacts40. Queue403unchanged; no offer correction/merge or UPN.

Current category expansion: `docs/macsteel-angle-catalogue.md` records136distinct seller offers across all five observed equal-angle pages, adding106without overwriting earlier30. One same-nominal-key pair remains separate and unapproved. Sources93; cached artifacts38; total supplier offers168; missing-maker tasks136; queue403. Generic PDF correlation still covers only the original30offers. Older milestone counts below are historical snapshots.

Current 2026-10-01: linked angle PDFs are cached and fully visually inspected; identical bytes represent one generic section sheet, not two independent article sources. `docs/macsteel-angle-datasheet.md` documents55sparse table facts and30nominal offer candidates without identity approval. Cache33records; remote/blocked17; queue297including all30missing-maker tasks. Older milestone counts below are historical snapshots.

Unknown-maker offers now have explicit deterministic review tasks: 30 supplier/manufacturer provenance tasks plus two linked angle PDF retrievals bring the queue to 299. Source register now 89; 31 cached artifacts and 19 remote/blocked records. The two PDF links return HTTP200 with application/pdf headers, but body/content verification remains outstanding. See `docs/reviewer-workflow.md`; a seller-to-manufacturer link alone never approves equivalence or issuance.

Seller-article expansion: `docs/macsteel-angle-offers.md` records 30 actual Macsteel equal-angle seller SKUs from one checksummed listing snapshot. There are now 62 supplier offers and 87 registered sources, with 31 cached artifacts. Manufacturer links, price, stock, billing quantities and UPN remain unapproved for these new offers. The seller-offer checker reproduces every persisted record. Remaining pages and detail/datasheet verification are outstanding.

PFC corroboration: `docs/structural-pfc-corroboration.md` adds official Macsteel and ArcelorMittal evidence. Macsteel's six rows agree in five nominal fields; ArcelorMittal has two agreements, three conflicts and one absent key. Shear-centre distance is kept separate from centroid distance. Source register83, cached artifacts27. Combined structural screening67distinct rows;66have at least one selected-source nominal candidate,738outside selected tables. Three corroboration findings now integrated; eleven source-only sizes retained as research facts, not articles. Earlier PFC tasks remain open. No article approval.

PFC expansion: `docs/structural-pfc-verification.md` screens six channel rows against British Steel: two nominal agreements, two conflicts and two absent serial candidates. Two findings with four row links remain integrated; queue267. Nominal agreements remain unapproved.

Independent follow-up: `docs/structural-british-corroboration.md` screens all49UB/UC rows against British Steel PDFs:48exact nominal candidates, one unmatched mass key and one inter-source width conflict among46cross-source comparisons. Root radii/clear depths retained. Four British UB/UC findings remain integrated. No article approval.

DS.0001 structural research: `docs/structural-heavy-verification.md` documents all49UB/UC rows screened:46unique nominal candidates with field differences and three unmatched exact keys. Manual transcription remains unreviewed. Combined with IPE/British evidence,61distinct structural rows screened;744remain outside selected-table screening. Five DS.0001 findings remain open alongside the British findings. No identity approval or UPN issuance.

Manufacturer equal-angle research: `docs/orangebook-equal-angle-screening.md` records 192 ArcelorMittal Orange Book S355 nominal rows screened against all 136 captured seller offers. There are 111 geometry candidates and 25 table-coverage gaps. Seven of ten earlier material-context gaps have geometry here, but none are closed: S355 does not verify seller S355JR+AR or the manufacturer of stock. No article approval.

Equal-angle mass audit: `docs/angle-mass-discrepancies.md` separates 40 distinct section/context comparisons across 104 offers from 32 uncomparable offers. Six displayed numeric values agree exactly; 30 pairs do not exclude a conditional nearest-rounding explanation; four pairs affecting nine offers are not explained by that hypothesis. No physical conflict or material-context equivalence is approved.

Structural identity foundation: `docs/equal-angle-identity-profile.md` documents a new draft profile with seventeen required fields, six exact cross-unit numeric rules and grade/shape/route specificity guards. Mass remains diagnostic. Ten synthetic regression tests cover missing evidence and differences; no seller offers or design-table rows were promoted to manufacturer articles.

Supplier research intake: `docs/supplier-research-findings.md` connects ten material-context gaps and four distinct publication mass discrepancies to checksum-bound, offer-linked P2 research tasks. The deterministic reviewer queue now has 417 tasks. These tasks do not authorize article approval and do not close merely when a maker link is assigned.

## What is here

- `schema.sql` — relational schema for sources, taxonomies, manufacturers, parts, observations, evidence, candidate matches, and reviewed equivalence decisions.
- `data/source-register.csv` — initial authoritative-source register with access and licensing constraints.
- `data/source-datasets.csv` — checksummed custody and allowed-use register for supplied bulk files; raw sensitive files stay Git-ignored.
- `data/dataset-findings.csv` and `data/dataset-finding-rows.csv` — 98 derived bulk-data findings with3,305links to2,253distinct dataset/row pairs, with checksummed report evidence and no implied corrections or identity approvals.
- `data/numeric-comparison-rules.csv` — versioned property-specific cross-unit representation tolerances for required numeric identity fields.
- `data/controlled-values.csv` and `data/specification-value-mappings.csv` — property-scoped canonical terms and reviewable mappings from raw source statements.
- `data/items-of-supply.csv`, `data/upn-allocations.csv`, `data/item-reviews.csv`, and `data/item-memberships.csv` — reproducible canonical-item ledger, permanent opaque-number allocation, independent approval, and reviewed part membership.
- `data/match-candidates.csv` and `data/equivalence-decisions.csv` — durable promotion path from algorithmic screening to human same-item decisions.
- `data/domain-seed.csv` — UPN's initial cross-industry domain vocabulary. These are navigation domains, not claims of equivalence.
- `data/supplier-offers.csv` and `data/supplier-offer-identifiers.csv` — commercial seller SKUs, package levels, quantities, and trade-item identifiers kept separate from physical-part identity.
- `data/external-identifiers.csv`, `data/manufacturer-part-external-references.csv`, and `data/external-identifier-evidence.csv` — governed crosswalks to systems such as NSN, with source assertions kept distinct from issuing-authority verification.
- `docs/data-model.md` — entity boundaries and why they matter.
- `docs/matching-policy.md` — conservative workflow for deciding whether two manufacturer part numbers describe the same item of supply.
- `docs/provenance-policy.md` — minimum evidence rules and trust tiers.
- `docs/normalization-policy.md` — controlled terminology, mapping provenance, and independent approval requirements.
- `docs/reviewer-workflow.md` — deterministic triage, dependency, and independent-review workflow.
- `docs/dataset-findings-workflow.md` — source-row triage and revision/promotion safeguards before exact-article ingestion.
- `docs/piping-source-verification.md` and `reports/piping-tenaris-comparison.json` — all 50 pipe rows compared with official nominal OD/wall data, preserving source ambiguity and the unresolved seamless/welded contradiction.
- `docs/user-reference-catalog-analysis.md` — structural and data-quality findings from the supplied plate, structural, gasket, and piping catalogues.
- `docs/klinger-dimension-verification.md` and `reports/klinger-maxiflex-comparison.json` — all 643 supplied Maxiflex rows compared against the official historical catalogue, with unresolved discrepancies retained by source locator.
- `docs/klinger-maxiprofile-verification.md` and `reports/klinger-maxiprofile-comparison.json` — all 239 MaxiProfile rows compared with pages 68–70; 238 agree and one differs, without assuming component meanings or exact article identity.
- `docs/klinger-softcut-verification.md` and `reports/klinger-softcut-comparison.json` — all remaining 11,280 gasket rows compared with historical soft-cut tables; drilling differences and unresolved class/field keys prevent OD/ID-only identity claims.
- `docs/research-plan.md` — staged path from source discovery to reviewed records.
- `docs/cable-ladder-straight-steel-profile.md` — first class-specific identity profile, evidence, hard stops, and unresolved fields.
- `docs/iso4017-hex-fastener-profile.md` — second identity profile and a documented exact-article comparison that remains short of equivalence.
- `docs/wire-mesh-basket-straight-steel-profile.md` — third identity profile and an exact Eaton SKU that deliberately remains incomplete where official evidence is silent.
- `docs/deep-groove-bearing-profile.md` — fourth identity profile, showing why matching 6205 boundary dimensions and double shields do not by themselves prove bearing identity.
- `docs/external-identifiers.md` — fail-closed policy for GTIN/EAN packaging scope, NSNs, and future external item-of-supply crosswalks.
- `scripts/validate_registry.py` — dependency-free validation for the seed data and SQLite schema.
- `scripts/build_registry.py` — creates a fresh local SQLite database from the reviewed seed files.
- `scripts/audit_completeness.py` — reports missing identity fields and prevents incomplete observations from being accepted.
- `scripts/audit_issuance.py` — validates UPN syntax, permanent allocation, independent item approval, and every active membership basis.
- `scripts/upn.py` — version-one opaque UPN formatting and check-digit validation.
- `scripts/screen_candidates.py` — reproducibly screens cross-manufacturer pairs and records hard conflicts before review.
- `scripts/verify_artifacts.py` — hashes locally retained evidence and rejects missing or mislabelled cache records.
- `scripts/build_review_queue.py` — derives the current evidence, mapping, artifact, and review backlog without making decisions.
- `scripts/test_quality_gates.py` — proves incomplete reviews, unverified artifacts, and unnumbered issued items fail closed.
- `reports/review-queue.csv` and `reports/review-queue-summary.md` — committed, reproducible reviewer work list and counts.

Run the full gate set from the repository root:

```powershell
python registry/scripts/validate_registry.py
python registry/scripts/build_dataset_findings.py --check
python registry/scripts/build_registry.py
python registry/scripts/audit_completeness.py
python registry/scripts/audit_issuance.py
python registry/scripts/screen_candidates.py --check registry/data/pair-screenings.csv
python registry/scripts/verify_artifacts.py
python registry/scripts/build_review_queue.py --check
python registry/scripts/test_quality_gates.py
python registry/scripts/test_dataset_findings.py
```

The generated database is written to `registry/build/registry.sqlite` and is intentionally excluded from Git; the schema and CSV inputs are the reproducible source of truth.

## Current status

Foundation and pilot data only. The schema, policies, ingestion checks, artifact verification, candidate screening, and fail-closed publication gates are operational. Source licensing must be resolved before bulk ingestion, and every manufacturer observation still requires independent review.

The pilot contains 38 branded or manufacturer parts across four identity profiles and thirteen catalogue organizations: twelve manufacturers plus Fabory Nederland B.V. as a distributor and stated catalogue controller. Thirty-two supplier offers explicitly separate seller SKUs, measured order quantities, package levels, and trade identifiers from the physical part records. Unknown EAN, UPC, or GTIN scope remains explicit rather than being assumed to identify one piece. The cable-ladder profile contains 30 parts: six Legrand Swifts, five Øglænd LOE55, ten Niedax KL, five OBO Bettermann LCIS 60, and four Atkore/Unistrut NEMA 3 20B. The Niedax profiles contain all 14 required fields, including an explicit statement that splice plates are ordered separately. The Legrand, Øglænd, and OBO profiles remain at 13 of 14 because splice inclusion is unstated. The Atkore profiles contain 10 of 14; rung profile, rung attachment, side perforation, and splice inclusion remain unknown.

The ISO 4017 profile contains exact Bossard, Würth, Fabory-branded, and Böllhoff M8 × 30 articles. It requires thread direction, bringing the class to 15 required identity properties. Böllhoff and Würth each have 14 of 15, Fabory has 13 of 15, and Bossard has 12 of 15. The wire-mesh profile separates nominal size from actual envelope and separates cross, top longitudinal, and other longitudinal wire diameters. Eaton `FT6X18X10 BLE` has nine of fifteen required properties. Official Eaton documents establish a five-millimetre minimum wire size, six-inch load depth, 107.3-square-inch inside area, span-specific load ratings, and four splices required for UL Classification. None proves the three exact wire diameters, the directional mesh spacings, or that splices are packaged with the section, so those six required fields remain unknown. Eaton's exact page also states 118.312 inches while its catalog calls the section three metres; the governed length rule surfaces that difference as an internal source conflict rather than silently rounding it away. Legrand `CF150/450BL` has fourteen of fifteen. Its technical guide contributes a 103.23-square-inch fill area and span-specific load table, while its installation guide requires four EDRN or four SWK connectors for the exact depth-width class. Neither source states that connectors are included, so splice inclusion remains unknown. Its exact page and official drawing still conflict on overall height: 6.53 inches converts to 165.862 mm while the drawing states 158 mm / 6.22 inches. Eaton and Legrand match on nominal 6-by-18-inch size and black powder-coat finish, yet the screen is a hard conflict on overall width, overall height, length, and wire-joint construction.

The bearing profile compares SKF `6205-2Z` with NSK `6205ZZ`. Both exact manufacturer pages state single-row deep-groove construction, double metal shields, CN clearance, and 25 × 52 × 15 mm boundary dimensions. SKF publishes tolerance group `Class 6 (p6)` while NSK publishes `P0`; NSK's captured source also leaves bore type, bearing material, and supplied lubricant unproven. The screen keeps the pair apart with one tolerance-class conflict and four evidence gaps. Twenty-two pairs now pass profile-specific coarse blocking: 18 are `hard_conflict` and four are `insufficient_evidence`. All records remain `unreviewed`, and no UPN has been issued.

The registry now builds 35 relational tables from 77 governed sources, four profiled reference datasets, and 61 observations. Twenty-one cached evidence artifacts and four local reference datasets pass SHA-256 verification; seventeen evidence records remain remote-only or blocked. GS1-labelled EAN, UPC, and GTIN values are rejected during validation unless their length and Mod-10 check digit are valid. Eaton and Legrand UPCs are attached to supplier offers with unknown packaging scope, not directly to physical-part identity. Twenty-one governed numeric rules convert evidence to common SI bases and apply property-specific representation tolerances. Nominal market-class tolerance is separate from tighter overall-geometry rules, and missing numeric governance fails closed. Eleven bearing controlled values and fifteen source-term mappings make normalization decisions explicit; all mappings remain proposed and cannot support an accepted manufacturer-part review until independently approved. Version-one UPNs are permanent opaque sequences with Luhn check digits; allocations, item approvals, equivalence decisions, and memberships are now reproducible seed data rather than schema-only placeholders. The issuance gate permits a unique anchor part through its latest accepted part review and permits additional parts only through `same_item` decisions. It rejects missing allocations, invalid check digits, non-independent approval, profile mismatch, or incomplete membership chains. No UPN has been allocated or issued. Fabory's NSN `5305-12-337-0503` remains an unreviewed supplier assertion with secondary corroboration, not an authority-verified manufacturer identifier; exact NMCRL verification remains outstanding. Cable-ladder screen 0.3, ISO 4017 screen 0.2, wire-mesh screen 0.2, and bearing screen 0.1 distinguish contradictions from compatible but unequal evidence specificity. Similarity scores are diagnostic only and never override an identity conflict.

## Non-negotiable rule

The source-dataset review layer contributes 66 gasket, 7 pipe, 8 plate, 3 IPE, 5 DS.0001, 4 British UB/UC, 2 British PFC and 3 PFC corroboration findings to the 267-task reviewer queue. It preserves 3,305 row links across 2,253 distinct dataset/row pairs. Stale report/input digests and identity promotion with unresolved findings are rejected. Earlier structural tasks cover all 805 article-evidence gaps and source-specific scope/field conflicts. British UB/UC findings add 50 overlapping links; British PFC adds four and corroboration adds four, without closing older issues. Eleven source-only Orange Book sizes have a separate coverage task without supplied-row links. Overlapping links represent multiple issues, not additional parts. No catalogue correction or article approval.

Independent pipe nominal-size corroboration is documented in `docs/pipe-independent-corroboration.md` and `reports/pipe-independent-observations.json`: six manually transcribed observations across four supplied records from a manufacturer and a supplier. `scripts/check_pipe_corroboration.py` checks internal row/key/geometry consistency, not live source fidelity. New remote-only source evidence requires capture/reuse review; original Tenaris findings remain open.

Plate family screening is documented in `docs/plate-source-screening.md` and `reports/plate-macsteel-screening.json`: all395 rows have source-page-linked, unreviewed interpretations; three mass discrepancies retained. `scripts/check_plate_macsteel.py` reproduces the report. It does not compare exact stock sizes or approve article identity, aliases or corrections. Plate findings are now integrated into the generic producer, retaining their research-only status.

Structural IPE comparison is documented in `docs/structural-ipe-verification.md`:12 selected rows compared with manually transcribed historical manufacturer nominal values. Six IPE rows agree; six IPE-AA rows retain Height/designation-versus-depth conflicts. Other793 structural rows remain outside this comparison. Source transcription remains unreviewed; no article verification or approved correction. Its report now lists all793 untested row locators. Three derived structural findings cover the entire805-row dataset without claiming those rows have been compared.

A similar description is not identity. UPN equivalence requires compatible identity-defining properties, traceable evidence, and a recorded human decision. Application suitability and substitution are separate decisions.
