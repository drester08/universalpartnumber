# Equal-angle linked PDF verification

Milestone completed 2026-10-01; PDFs retrieved 2026-09-30. Research only.

Two seller-linked URLs, AE_S355RA_0061.pdf and AE_S355RA_0064.pdf, return identical
bytes with SHA-256 E3DCBF06039844BB99ADD88B77153F37543EC30EF617368C44383748D4AEB1A1.
Their single shared page was rendered and visually reviewed in full. It is a
generic equal-angle family datasheet, not two independent sources or exact
length-specific article certificates. Each URL retains a separate custody record.

The commercial-quality table has five size rows and 23 populated mass cells.
The SANS 50025/EN 10025 Grade S355JR table has eight size rows and 32 populated
mass cells. Sparse blanks are preserved as absence, not zero or out-of-stock.
All 55 observations retain table, row, column, printed thickness, grade context,
mass in kg/m and any availability star. Stars at 100x100x15 and 120x120x15 refer
to the instruction to confirm local branch availability.

All 30 previously captured listing offers have one nominal leg/thickness
candidate in the S355JR table. The 60x60x5 entry prints 4.568 kg/m for the section;
the PDF does not establish either the 6m or 13m saleable length. Those lengths
remain separately sourced seller assertions. The generic narrative refers to
roll-forming and bending; it cannot establish individual article manufacturing
route or resolve the listing's JR+AR condition. Do not expand S355JR to JR+AR
based on this sheet or infer a manufacturing mill.

The sheet lacks individual seller SKUs, mill identity, length tolerances,
dimensional tolerances and article-specific inspection certification. No maker
link, corrected user row, identity approval, equivalence or UPN was created.
All 30 missing-maker tasks remain open. Only the two completed artifact-retrieval
tasks are removed, reducing the queue from299to297. Licensing remains
review-required; original PDFs are private and Git-ignored.

Reproduce with `python registry/scripts/check_macsteel_angle_datasheet.py`.
It binds both PDFs and registered custody hashes, checks page/table/header/units,
preserves sparse cells and qualifications, correlates all listing rows and checks
the full persisted JSON. Seven tests cover qualifiers, duplicates, shifted
columns, units, zero mass, ambiguity and false independence/promotion.
Reproduction and visual review are not independent transcription approval.

Next: independently verify source fidelity, inspect the remaining offer details,
expand angle listings, obtain maker/route/tolerance evidence and compare the
supplied structural rows without automatic grade or route correction.
