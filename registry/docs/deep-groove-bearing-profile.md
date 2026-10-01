# Single-row double-shielded deep-groove bearing profile

Status: draft 0.1. No equivalence decision or UPN has been issued.

## Scope

This profile covers individual metric single-row deep-groove ball bearings with a cylindrical bore and a non-contact metal shield on both sides. It excludes open bearings, contact-sealed bearings, one-sided closures, snap-ring variants, flanged rings, special-temperature or coated variants, and complete bearing units.

The first comparison uses SKF `6205-2Z` and NSK `6205ZZ`. Both manufacturers state a 25 mm bore, 52 mm outside diameter, 15 mm width, single-row deep-groove geometry, and shields on both sides. Those shared fields are blocking evidence only. They do not prove that the two sellable bearings are the same item.

## Required identity fields

The draft requires bearing geometry, bore diameter, outside diameter, width, closure construction, bore type, radial internal-clearance class, tolerance class, cage construction, bearing material, supplied lubricant, and integral locating feature.

Load ratings, rolling-element count and diameter, limiting speed, and mass remain separately captured. Their interpretation needs the applicable calculation standard, rating basis, lubricant, load, temperature, and rounding context.

## Evidence result

SKF's exact page currently supplies all twelve required fields. NSK's exact page supplies nine. Bore type, bearing material, and supplied lubricant are not proven by the captured NSK evidence. A grease-lubrication speed does not establish which grease is supplied inside the bearing.

SKF publishes tolerance group `Class 6 (p6)` while NSK publishes `P0`. UPN preserves these as distinct unreviewed source claims. It does not assume that familiar `6205` and double-shield suffixes override that difference. SKF's generic `sheet metal` cage description and NSK's `pressed steel` description are treated as a compatible but unequal specificity gap, not a contradiction.

The bearing terminology is now represented by eleven property-scoped controlled values and fifteen explicit source-term mappings. The mappings record whether the source states a term directly or whether a manufacturer definition is being applied. All remain `proposed`; none is an approved semantic crosswalk.

The reproducible screen therefore records one hard conflict, four missing identity fields, seven matched fields, and no equivalence decision.

## Hard stops

- A shared ISO boundary size or base designation is not proof of item identity.
- `ZZ` and `2Z` terminology must be mapped from manufacturer evidence, not assumed globally.
- Clearance, precision, cage, grease, materials, coatings, heat treatment, noise class, electrical insulation, temperature stabilization, and locating features can all create distinct items.
- Load and speed ratings cannot be compared without their standard and operating context.
- Distributor cross-reference tables can generate research candidates but cannot approve equivalence.
- A proposed term mapping can generate a candidate but cannot support an accepted part review or UPN issuance.

## NTN source extension — 1 October 2026

NTN `6205ZZ` is now a separate manufacturer-namespaced research article. Its placement in this draft family is provisional: the captured page does not fully prove the profile's scope. A shared designation with NSK is not an identity link.

The private, checksum-bound HTML retains 26 named native rows (25 engineering rows plus one ordering-options row), including 25 × 52 × 15 mm boundary dimensions. Eleven selected specification rows were ingested with an unreviewed observation. No NTN terminology mapping was approved; “ISO Class 0” is not silently converted to NSK P0. “Round” does not prove cylindrical bore, “Double Shielded” does not explicitly establish non-contact metal closure, and grease limiting speed does not establish the supplied grease. Integral locating-feature absence remains unproven.

Two publication issues remain open research questions:

- The static-load row simultaneously displays 7,850 N and 11.60 kN (11,600 N). Neither is chosen as the corrected value or ingested as a trusted rating.
- The `da max` row contains two inch and two metric values, including 32 mm and 47 mm. Its interpretation is unresolved and no normalized mounting dimension was ingested.

The reproducible evidence is `registry/reports/ntn-6205zz-source.json`; run `registry/scripts/check_ntn_6205zz.py` to check its source hash, row extraction and specification custody. Extraction fidelity still needs independent review. Seek NTN clarification or a revised exact-article datasheet for the two publication issues, and manufacturer definitions/drawings for scope and missing identity fields. This extension creates no cross-brand equivalence decision.

Adding the second manufacturer's `6205ZZ` exposed a completeness-report grouping defect. Coverage and numeric-conflict aggregation now use the manufacturer-part ID, not bare part-number text. The report shows NTN and NSK separately, with nine of twelve required fields present for each; presence is not evidence approval. Ten regression tests cover source scope, contradictions, custody and namespace separation. The general reviewer queue grows from 417 to 421 items (one observation review and three required-field gaps); the two NTN publication issues are documented research questions, not yet dedicated queue items.

## Primary sources

### Catalogue corroboration — 1 October 2026

NTN CAT.No.3015-5/E now supplies additional manufacturer definitions. PDF page 3 (printed 3-4), Table 1, explicitly defines ZZ as non-contact shielding with a metal plate; the accompanying note establishes double shields. PDF page 7 (printed 11-12) lists 6205 with the ZZ option. A manufacturer-specific closure mapping is therefore proposed for the existing article observation. Its raw article-page text remains unchanged; the mapping is not approved. There are now sixteen proposed terminology mappings and zero approved mappings.

The 6205 catalogue table corroborates a static rating of 7.85 kN and separately labels `da max` 32 mm and `Da max` 47 mm. These are additional source claims, not a publisher correction to the malformed exact-article page. Both earlier publication questions remain unresolved. The catalogue's performance-test grease applies to 6305/6304 test specimens, not the supplied 6205ZZ lubricant. The table also covers multiple closure/snap-ring variants and approximate mass; availability of N/NR variants and the tabulated 0.128 kg do not establish exact article features or mass.

`check_ntn_shield_seal.py` reproduces the source hash, bounded ZZ table-column extraction, exact 6205 row and proposed-mapping custody. `ntn-shield-seal-corroboration.json` retains the evidence and scope limits. The main agent visually inspected both relevant spread pages; independent extraction review remains outstanding.

The closure proposal brings two NTN comparisons through coarse screening, both `insufficient_evidence`. Unmapped coded wording without a typed normalized value is now excluded from semantic comparison rather than automatically treated as a hard conflict: NTN “ISO Class 0” is not a proven contradiction with NSK “P0”, and raw “High Carbon Chrome Steel” is not automatically a contradiction with generic bearing steel. Other established comparisons are unchanged. The current screen contains 24 pairs; the reviewer queue contains 424 tasks, including two new candidate evidence follow-ups and one closure-mapping review. Missing bore type, supplied grease, locating features and precise tolerance/material semantics still prevent identity approval.

- NTN shield/seal catalogue: <https://www.ntnglobal.com/en/products/catalog/pdf/3015E.pdf>

- SKF exact product page: <https://www.emarketplace.in.skf.com/deep-groove-ball-bearing/6205-2z>
- NSK exact product page: <https://www.nsk.com/eu-en/engineering/products/bearings/ball-bearings/deep-groove-ball-bearings/single-row-deep-groove-ball-bearings/6205zz-apn.html>
- NTN exact product page: <https://bearingfinder.ntnamericas.com/item/deep-groove-ball-bearings/single-row-radial-ball-bearings/6205zz>
