# British Steel independent nominal comparison - 2026-09-30

## Sources and method

Primary manufacturer evidence: [British Steel UB datasheet](https://www.britishsteel.co.uk/wp-content/uploads/2026/02/british-steel-universal-beams-datasheet-190724.pdf) and [UC datasheet](https://www.britishsteel.co.uk/wp-content/uploads/2026/02/british-steel-universal-columns-datasheet-100723.pdf). The eight-page UB PDF's complete pages1/3 and four-page UC PDF's complete page1 were rendered and visually reviewed, including diagrams, headings and full tables. Other pages were not visually reviewed. File labels190724/100723 are retained, not asserted publication dates. Source reuse permission unresolved; private PDFs excluded from Git.

`check_structural_british.py` verifies both PDF hashes and original805-row CSV hash, requires expected row counts and column positions, and extracts nominal candidates only from those reviewed pages. Four unselected UB410x260 rows omit mass cells; they are explicitly excluded rather than shifted. Extraction fidelity still needs independent review. Existing South African comparison must reproduce from its retained inputs before cross-source comparison.

## Results

All49 supplied UB/UC rows screened:48have exact family/designation-size/published-mass candidates and nominal-field differences; one lacks an exact mass-key candidate. Depth differs in47, width46, web34 and flange3 compared rows. Counts overlap. These are nominal field checks, not measured-product defects or tolerances.

Two previously source-unmatched beams have exact mass candidates here:

| Logical CSV record | British Steel designation | Mass kg/m | Depth mm | Width mm | Web mm | Flange mm | Root radius mm |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 702 | 406 x 140 x 46 | 46.0 | 403.2 | 142.2 | 6.8 | 11.2 | 12.7 |
| 703 | 406 x 178 x 54 | 54.1 | 402.6 | 177.7 | 7.7 | 10.9 | 12.7 |

The source's designation mass label is not published mass. In logical748, supplied mass167 does not exactly match source167.1. A separate, explicitly labelled observation retains printed designation254x254x167, mass167.1, depth289.1, width265.2, web19.2, flange31.7 and root radius20.0. This is not a rounded mass-key match or approved row correction.

For46rows having unique candidates in both manufacturers' sources,45agree on the five compared nominal fields (mass/depth/width/web/flange). One source conflict remains: UB305x102 at32.8kg/m, British Steel width102.4 versus DS.0001 width102.0. British designation is305x102x33. No source is silently preferred. DS.0001 provides no selected root-radius values; five-field agreement does not prove complete geometric identity. Material, tolerance, certificates, radii, length/ends/finish and current availability are not approved.

Combined with IPE,61distinct structural rows remain screened; unique nominal candidates exist for60, with the UC167mass key still unmatched. No newly screened families or reduction of the744outside-selected-table count. Previous source-specific findings stay open. Manufacturer nominal corroboration does not close article-evidence gaps.

Four British-source findings now join the review workflow: two nominal-field conflict groups covering48rows, one unmatched-mass coverage group coveringlogical748 and one inter-source width-conflict group coveringone overlapping row. They contribute50links across49distinct supplied rows. Producer checks both PDF digests, prior-report digest and candidate equality, complete/disjoint row coverage, source IDs/pages, exact mass keys, label-only separation, reconstructed differences and totals, and rejects false identity approval. These consistency checks do not prove original PDF extraction fidelity. Current findings93groups/3297links/2253distinct dataset-row pairs; reviewer queue262.

## Verification and next work

Run `python registry/scripts/check_structural_british.py` and `python registry/scripts/test_structural_british.py`. Six tests verify full partition, two additional candidates, label-versus-mass separation, retained source conflict, extraction count guards and incomplete-cell handling. They do not certify complete extraction fidelity or same-item identity. The JSON snapshot retains original raw values, candidates, page/designation locators, root radii/clear depths, prior candidates and input/report hashes.

Next: independently review extraction and source width conflict, acquire exact grade/certificate/finish/tolerance evidence, expand other structural families and preserve governed correction history. No accepted equivalence, alias, corrected raw row or UPN issuance.
