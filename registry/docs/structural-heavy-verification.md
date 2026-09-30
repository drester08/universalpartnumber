# Universal beam and column nominal screening - 2026-09-30

## Source and scope

The [manufacturer's heavy structural datasheet](https://www.arcelormittalsa.com/Portals/0/H1.1%20Heavy%20structural%20steels.pdf), linked from its heavy-structural product page, is three pages. All pages were rendered and visually inspected. The URL is H1.1, but the document labels itself DS.0001; no publication date or current revision was verified. Its UB and UC tables cite EN10034. These headings do not certify the material grade of any supplied article.

Image tables cannot be recovered from ordinary PDF text extraction. The 30 UB entries on page1 and 19 UC entries on page2 were manually transcribed into `reports/arcelormittal-heavy-observations.json`. Independent transcription review remains pending. Narrow nominal facts and enquiry-only markers are retained; the raw PDF is private and excluded from Git. Reuse permission remains unresolved.

## Results

All49 supplied UB/UC rows were screened against the complete selected source tables. Exact candidate keys use family, designation height/width and published mass, ignoring decimal representation differences. This is an unreviewed interpretation of supplied Height/Width, not a certified article key. No mass rounding or nearest-key matching is used.

| Result | Supplied rows |
| --- | ---: |
| Unique designation/mass candidate; nominal fields differ | 46 |
| No exact designation/mass candidate in these tables | 3 |
| Other structural families, outside this comparison | 756 |

Across the 46 uniquely compared rows, depth differs in45, width in43, web thickness in32 and flange thickness in3. Counts overlap and are not additional parts. Thirteen matched candidates carry the source's enquiry-only marker. No enquiry marker does not establish current availability.

For UB203x133 at25.1kg/m, the CSV gives Height203, Width133 and Web5.8; the source gives depth203.2, width133.2 and web5.7. Flange7.8 agrees. Designation-versus-dimension differences do not prove a manufactured beam is defective. Web differences cannot be dismissed without independent evidence.

Unmatched exact keys are logical CSV records702 (UB406x140 /46kg/m),703 (UB406x178 /54.1kg/m), and748 (UC254x254 /167kg/m). Same-serial source candidates are retained but not selected. The source publishes167.1 for the latter family;167 is not silently rounded to that key. Three source entries lack a supplied exact key: UB533x210 /138, UC305x305 /240 and UC254x254 /167.1. These are source-scope gaps, not claims that supplied parts do not exist.

## Reproduction and limitations

`scripts/check_structural_heavy.py` verifies dataset/PDF digests, source table shape, unique candidate keys, expected family counts and page locators. It reproduces `reports/structural-heavy-comparison.json`, retaining all805 row locators as49 screened plus756 outside-family records, transcription digest, source candidates and differences. Five tests check full partition, designation/web differences, no mass rounding, enquiry markers and ambiguity. Tests establish internal consistency, not source-transcription fidelity or engineering suitability.

Run `python registry/scripts/check_structural_heavy.py` and `python registry/scripts/test_structural_heavy.py`. Use `--write-snapshot` only when intentionally regenerating from preserved inputs.

Combined with the earlier12-row IPE comparison,61 distinct supplied structural rows have source-table screening, leaving744 without selected-table screening. Only58 have a unique nominal candidate; three UB/UC exact keys remain unmatched. The earlier793-row IPE source-scope finding stays open because it means outside that particular source/family comparison. This report is not yet integrated into the generic finding/reviewer queue; queue coverage must not be claimed for it.

Next: independently review transcription, resolve Height/Width interpretation and thickness discrepancies, corroborate missing candidates with another manufacturer, integrate source-specific findings, and acquire grade/certificate, radii, length/end/finish and current article evidence. No raw correction, accepted alias, approved equivalence or UPN issuance.
