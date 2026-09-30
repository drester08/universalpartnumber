# Parallel-flange channel screening - 2026-09-30

## Source and method

The [British Steel PFC datasheet](https://www.britishsteel.co.uk/wp-content/uploads/2026/02/british-steel-parallel-flange-channels-datasheet.pdf) is two pages; both were rendered and visually reviewed. Page 1 contains twelve dimension rows, a labelled drawing and units. Page 2 contains section properties, a BS EN10365:2017 dimension/property reference, copyright 2023 and disclaimer. Copyright is not asserted as publication date; current availability and reuse permission remain unresolved. Raw PDF stays private and excluded from Git.

`check_structural_pfc.py` verifies original dataset and PDF digests, two pages, twelve dimension rows and expected column counts. It binds candidates by serial height/width because each published serial size is unique in this particular table. Mass is independently compared, not rounded to the designation mass label. Ambiguity is retained, not first-matched. Candidate binding and extraction remain unreviewed; no article-level identity assertion.

## Results

All six supplied Parallel Flange rows screened against this table:

| Supplied serial size mm | Result |
| --- | --- |
| 100 x 50 | No source serial-size candidate |
| 180 x 70 | No source serial-size candidate |
| 200 x 75 | Web, flange and mass differ |
| 230 x 90 | Five nominal fields agree |
| 260 x 90 | Five nominal fields agree |
| 300 x 100 | Mass differs |

For 200x75, supplied web7.5/flange11.4/mass24.3 differs from source web6.0/flange12.5/mass23.4. Depth200 and width75 agree. For 300x100, source mass45.5 differs from supplied45.4; depth300/width100/web9/flange16.5 agree. These are nominal comparisons, not manufacturing tolerances or approved corrections. Absent keys limit this table; they do not prove the supplied sections invalid or authorize reclassification as tapered channels.

Source root radius and depth between fillets are retained for four candidates; supplied CSV lacks those properties. Centroid distance is explicitly cm, not mm or radius. Example source300x100: centroid3.05cm, root radius15mm, clear depth237mm. Matching five fields cannot fill missing certified material/tolerance/end/finish/availability evidence.

The report partitions all805 supplied records into6screened and799outside this PFC comparison. Combined distinct screening across IPE, UB/UC and PFC is67rows, leaving738outside selected tables. Sixty-four have unique nominal candidates across sources; three currently lack selected-table candidates (UC exact mass key and two PFC serial keys). No full geometric/article approval is implied.

## Verification and next work

Run `python registry/scripts/check_structural_pfc.py` and `python registry/scripts/test_structural_pfc.py`. Five tests check full partition, the200x75differences, no rounding-away of mass discrepancy, separate units and ambiguity handling. They establish consistency, not extraction fidelity or engineering suitability. The JSON retains source/page/designation locators, raw values, nominal differences, row locators, hashes and missing evidence.

Two PFC-specific findings are integrated into the generic review queue: one P0 nominal-field conflict with two row links, and one P2 selected-table coverage gap with two row links. The two nominal agreements do not become approved articles; the existing article-evidence gap still covers them. Earlier source-specific findings remain open.

The producer checks the complete 805-row partition, PDF/dataset digests, twelve retained source observations, unique source keys, source/page locators, units and candidate/difference reconstruction. Mutation tests reject stale digests, false approval, altered differences, missing or duplicate source observations, invalid values/pages and overlapping row locators. These checks establish internal consistency and revision binding, not independent transcription fidelity.

Next: independently review extraction and field meaning, corroborate absent serial sizes using other manufacturers, and obtain exact article/grade/certificate/tolerance/finish evidence. No original edit, accepted alias/equivalence or UPN issuance.
