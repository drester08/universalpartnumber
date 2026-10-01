# JTEKT / Koyo 6205 ZZ exact-article intake

Status: unreviewed primary-source research. No physical identity, equivalence or UPN approved.

The official [6205 ZZ product page](https://koyo.jtekt.co.jp/en/products/detail/?pno=6205+ZZ) was retrieved on 1 October 2026 as real HTML, not a search excerpt or application shell. Its private snapshot is `registry/artifacts/jtekt/6205-ZZ-20261001.html`, SHA-256 `900D5F9E0ECA6275769BA774B7C2326353052BD8E032C0916A865306546A5230`. Register IDs: `SRC-JTEKT-6205-ZZ`, `ART-JTEKT-6205-ZZ`, `ORG-JTEKT`, `MP-JTEKT-6205-ZZ`, `OBS-JTEKT-6205-ZZ-20261001`.

The manufacturer designation retains its space: `6205 ZZ`. Normalized text `6205ZZ` also appears under NSK and NTN, but each remains in its own manufacturer namespace. No seller SKU or cross-reference was used to establish this article.

## Retained facts and limits

The exact heading and construction text identify single-row deep-groove geometry and raw `Shielded ZZ` closure. Fourteen native `dl/dt/dd` fields are retained with case-sensitive names, HTML line numbers and field ordinals. Nine facts enter the unreviewed observation: geometry, three boundary dimensions, raw closure, two basic load ratings, grease limiting speed and reference mass. kN ratings are normalized to N while original units remain in raw values. Reference mounting dimensions, chamfer, fatigue limit and calculation factor remain report-only.

The source separately gives lowercase `da(max.)` and uppercase `Da(max.)`; the extraction preserves both. Mounting values and mass sit in the reference section. They are not measured stock dimensions or proof of interchangeability. The page does not state the calculation standards/basis for load ratings.

The shared descriptive mass property's definition now covers an article as well as a supplied section; it no longer assumes every article is a straight section. Existing values and identities are unchanged. Source/reference/approximate qualifiers remain necessary.

Seven required identity fields remain absent: bore type, cage construction, radial internal clearance, tolerance class, material, supplied lubricant and locating feature. `Shielded ZZ` alone does not establish canonical non-contact metal sidedness. The article's profile assignment is a research hypothesis pending that closure evidence, not proof of full profile membership. Grease limiting speed does not identify supplied grease. No suffix-absence inference or generic CAD illustration was used.

The current candidate blocker requires canonical closure agreement, so this article is not yet compared to NSK, NTN or SKF. The existing 24-pair screen remains unchanged; this is a specific known blocking-coverage limit, not a conclusion of physical difference. An official manufacturer closure definition is a next research step. The published JTEKT rating must never be used as an NTN publisher correction or to close NTN's two source-publication findings.

## Reproduction and verification

`scripts/check_jtekt_6205_zz.py` rejects changed bytes, a changed exact heading/context, changed native field names/order/values and ambiguous numeric units. It binds the permitted nine CSV facts to the original source values, manufacturer namespace, observation and artifact custody. The generated `reports/jtekt-6205-ZZ-source.json` is research evidence, not an editable approval record. Independent transcription review and publisher reuse terms remain outstanding; raw HTML is not committed to Git.

Eight regression tests exercise case-sensitive fields, article/variant changes, malformed or altered values/units, hash revision, CSV binding, preserved reference-mass qualifier, separate namespaces, missing-field persistence and absence of premature candidate/UPN creation. Registry totals become 123 sources, 68 cached evidence records, 40 manufacturer parts and 63 observations. Reviewer work grows by seven evidence gaps and one observation task: 434 total, 423 ready and 11 blocked. No mappings or resolutions are approved.

The spreadsheet skill's source-preservation checks informed CSV inspection: identifiers remain text, original units/values are retained, missing fields remain absent rather than zero, and changes preserve the established registry schema. No workbook was created, modified or exported.
