# Supplied piping: MPS nominal-dimension comparison

## Result — 1 October 2026

All 50 supplied piping rows have one MPS lookup candidate and compatible printed nominal outside diameter and wall thickness. All matched candidates are on physical/printed page 12 of the staged Mining Pressure Systems technical manual. This is supplier/fabricator dimensional context, not proof of the mill, certificate or actual supplied article.

| Earlier Tenaris result | Rows | New MPS result |
| --- | ---: | --- |
| Printed-precision compatible | 34 | Printed-precision compatible |
| Outside selected source key scope | 12 | Printed-precision compatible |
| Ambiguous selected source key | 4 | Printed-precision compatible |

The new source covers DN 6, 8, 10 and 90 and distinguishes DN 65 from DN 80. It does not correct the earlier Tenaris publication, resolve its source-specific findings, or alter any supplied CSV row.

## What remains open

All 50 supplied rows still say `Welded` and `ASTM A106`. The MPS product heading says `ASTM A106 – GRADE B SEAMLESS`. Nominal dimensions cannot resolve that contradiction. The separate API seamless/welded footnote is not transferred into A106 construction.

One matched row, DN 80 schedule 160, intersects the source's internal-diameter question. Two matched rows, DN 50 schedules 40 and 80, intersect its repeated approximate-mass question. These flags identify affected source rows without using internal diameter or mass as matching fields. The other two internal-diameter questions are outside the supplied size range. No published value is silently repaired.

XXS remains a wall designation with a nonnumeric source schedule. It is never converted to schedule 160. Printed-precision interval overlap accounts for decimal representation only, not manufacturing tolerance.

Independent extraction review, source reuse review, formal source registration and actual-stock manufacturer/certificate evidence remain outstanding. There is no identity, equivalence or UPN approval.

## Reproduction and custody

`scripts/check_piping_mps.py` verifies exact SHA-256 revisions of the private supplied CSV, private original MPS PDF, immutable MPS research JSON and immutable earlier Tenaris report. It joins by nominal bore and explicit numeric schedule or wall designation, rejects duplicate supplied keys, preserves ambiguous source keys and binds each supplied logical row to the earlier report. CSV logical row numbering starts at 2 and is not a claim about physical file lines with embedded newlines.

The new `reports/piping-mps-comparison.json` contains only selected technical fields and source locators. Business contacts, prices and commercial columns are excluded. Original CSV and PDF remain private and ignored by Git. The earlier reports are unchanged.

Run the bundled Python against `registry/scripts/check_piping_mps.py` to reproduce the persisted snapshot. Ten regression tests cover all 50 rows, historical outcomes, no identity approval, XXS separation, source defects, ambiguity, missing keys, real dimensional differences, revision/row binding and preservation of inputs.

This is staged research outside registered source/observation counts. The queue remains 460 tasks, all 26 mappings remain proposed and no actual review decision is recorded.
