# NTN 6204ZZ - quarantined primary-source research

Status: captured and reproducibly extracted, not yet registered or ingested as a manufacturer-part observation. No mapping, pair-screen, correction or UPN approval.

The [official NTN Bearing Finder exact article](https://bearingfinder.ntnamericas.com/item/deep-groove-ball-bearings/single-row-radial-ball-bearings/6204zz) identifies `6204ZZ`, not the AC/EC expansion-compensating or clearance variants. The original privately retained HTML has SHA-256 `3F2253DB6EEA5B032A410C39E2C939FBB786C7014CD0E4F8FE96E83A24F25003`. Its twenty-six native property rows include one ordering row. The blank illustration is excluded only when the exact `6204ZZ` image attribute is present; images are not engineering evidence.

Two publication issues require quarantine:

- Static load row, HTML line 804: `1500 lbf`, `6650 N`, `9.75 kN`. The metric values convert to 6,650 and 9,750 N, a 3,100 N conflict. No preferred or corrected rating is selected.
- `da max`, HTML line 966: 28.000 and 42.000 mm under the same source label. Uppercase `Da max`, line 979, is a distinct 42.000 mm row. Do not collapse case-sensitive mounting symbols or silently relocate cells.

The exact native dimensions are 20.000 x 47.000 x 14.000 mm. The retained NSK 6204ZZ page reports 20 x 47 x 14 mm, so these three nominal values agree. `reports/ntn-6204zz-pre-ingestion.json` binds both sources and their HTML row locators for this limited comparison. It is not the canonical identity screen, and size agreement is not same-item evidence. Native NTN static values are not compared as trustworthy ratings against NSK. Differences in published performance may reflect design, calculation basis or source error; do not choose a cause without evidence.

NTN also supplies CN, pressed/steel cage wording, High Carbon Chrome Steel, ISO Class 0, Double Shielded, 16,000 RPM grease speed and 0.103 kg mass. These remain native research rows. No mapping is inherited from NTN 6205ZZ or NSK. Round bore does not prove cylindrical bore; grease speed does not identify supplied grease. Precise closure, locating construction, standards applicability and article review remain outstanding. The existing NTN catalogue may provide future scoped corroboration, but was not re-read or applied to this article in this turn.

`scripts/check_ntn_6204zz_research.py` checks exact h1/sku/construction, all ordered row names and measure-labelled values, one article-specific illustration exclusion, source bytes and existing NSK custody. Six tests cover snapshot, bounded dimension comparison, retained conflicts, variants, rejected silent correction, hash revision and unchanged earlier 6205 report. The original NTN parser now accepts an explicit illustration article, defaulting to 6205ZZ; earlier output remains byte-semantically unchanged.

The similar errors now occur on two examined NTN article pages. This supports a broader publication-quality investigation, not a claim that every NTN page is wrong or that a publisher correction was obtained. Existing 6205 findings and empty resolution ledger stay open and unchanged. New 6204 issues are not yet in the registered review queue.

Next: perform governed source/part intake, preserve all unambiguous fields, register these two publication questions with exact article bindings, and obtain applicable closure/tolerance evidence. Independent extraction review and reuse permission remain outstanding. Registry baseline remains 126 registered sources, 71 registered cached evidence records, 41 parts, 64 observations, 21 proposed mappings, 24 pair screens and 442 tasks. This extra private HTML is staging material outside those totals. No user commercial/contact data is published.
