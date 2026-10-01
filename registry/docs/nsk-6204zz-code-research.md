# NSK 6204ZZ construction research — 1 October 2026

Historical staging milestone. The later [context registration](nsk-6204zz-code-registration.md) supersedes registration status and counts below; the staged JSON remains unchanged.

Status: staged primary-source PDFs and partial construction evidence. Neither new PDF is yet registered; no specification, canonical mapping, pair screen, correction, equivalence or UPN is added.

The [NSK Americas deep-groove brochure](https://info.nskamericas.com/hubfs/DGBB/NSK_APB_Deep_Groove_Ball_Bearings.pdf) defines ZZ as non-contact shielding on both sides in its single-row deep-groove designation table. Complete physical pages 5 and 10 were visually inspected, retaining family-range and code-row boundaries. Adjacent VV/DDU seal definitions are not assigned to ZZ. Private capture: `NSK-APB-DGBB-20261001.pdf`, SHA-256 `15E748AF493A8442A7CE3C82C243F2C82ACA5B0235F6B71B366F8CD03538CC61`.

The [NSK industrial-bearing catalogue Part C](https://www.nsk.com/content/dam/nsk/common/catalogs/ctrgPdf/bearings/e1103c_partc.pdf) supplies an exact 6204 row with a ZZ column. Complete physical pages 4 and 12 (printed C006–C007 and C022–C023) were visually inspected using the PDF skill. The 185-page source has overlapping duplicate text objects; extraction removes only same-position duplicates with `dedupe_chars`, never repeated character pairs in strings. Private capture: `E1103C-partC-20261001.pdf`, SHA-256 `3C1ACFDA536BB6A77487D1FCF6812618E31C62582FB20089659D20B7AF07A6E2`. The browser could not fetch this large PDF; direct official retrieval succeeded. No claim that all pages were reviewed.

The exact row retains 20 × 47 × 14 mm (bore from grouped label), dynamic/static ratings 14100/6600 N, grease speed 17000 min⁻¹, da minimum/maximum 25/26.5 mm, separate Da maximum 42 mm and approximate mass 0.107 kg. These align with the selected exact article's nominal context, not independently measured identity. The row also lists closure/locating variants. Approximate mass and shared speed columns remain scoped research context.

The reviewed pages do not explicitly establish shield metal. Pressed-steel cage statements refer to the cage, not the shield. No NTN material definition or miniature-bearing construction is transferred. The full `double_non_contact_metal_shield` mapping therefore remains absent for NSK 6204ZZ.

An industrial-catalogue footnote requires a grease designation when seals/shields are used on both sides. Its NS7 example is not the supplied grease for 6204ZZ. The exact article page still lacks supplied lubricant details. Blank designation explanations and N/NR availability do not independently settle exact locating construction. Additional exact-article clarification remains necessary.

`nsk-6204zz-code-research.json` retains bounded closure code rows, exact industrial row, grouped bore and grease footnote with source URLs, checksums and page scope. Seven regressions retain uncertainty, reject another row/revised bytes and preserve the earlier article snapshot. Registered baseline remains 127 sources, 72 cached records, 42 parts, 65 observations, 25 proposed mappings, 24 pairs and 452 queue tasks. Two private staged PDF captures are outside those counts.

Next: register both sources with reuse restrictions and explicit scoped research evidence; seek an NSK shield-material statement for this family before proposing full closure normalization. Independently review extraction/applicability, and resolve bore construction, material, supplied grease and locating evidence. A catalogue or dimension match does not approve interchangeability.
