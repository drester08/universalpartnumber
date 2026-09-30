# Regional PFC corroboration - 2026-09-30

## Evidence and results

The official [Macsteel datasheet](https://shop.macsteel.co.za/SpecSheets/CHP_S355RA_0048.pdf) contains six PFC rows under SANS50025/EN10025 S355JR. Its complete single page was rendered and visually reviewed. Five nominal fields agree with all six supplied CSV rows: depth, width, web, flange and mass. This supports the previously absent100x50 and180x70 serial sizes in this source, without closing British-table coverage gaps or approving articles. The filename's S355RA text is not used to override the printed S355JR header or infer publication date. No exact article, certified grade, root radius or current availability is established.

The official [ArcelorMittal Orange Book table](https://orangebook.arcelormittal.com/node/259) has sixteen PFC rows under S355. Of six supplied keys, two agree in the five compared fields, three conflict and one is absent. Its100x50x10 mass10.2/flange8.5 differs from supplied10.1/8.4. The180x70 key is absent. Its200x75x23 differs in web/flange/mass;300x100x46 differs in mass45.5 versus45.4. These agree with earlier British conflicts where both sources have candidates, but do not prove independent upstream lineage.

## Field boundaries

ArcelorMittal's e0 is distance from the web centre to the shear centre, in cm. British Steel's retained field is centroid distance in cm. They must not be compared as the same property merely because units match. For300x100 the values are3.67 and3.05 respectively. ArcelorMittal radius15mm and depth between fillets237mm are retained separately; Macsteel does not provide these fields. S355 is not silently expanded to S355JR. Serial names and similar five-field geometry are not proof of identical cross-publisher parts.

## Reproduction and remaining work

`check_structural_pfc_corroboration.py` binds original805-row CSV, both new source hashes and the reproducible earlier British report. Macsteel extraction requires the ordered headings, six rows and positive unique keys. HTML extraction preserves empty cells and checks one table, five header rows, sixteen30-cell data rows, column meanings/units and numeric uniqueness. The output partitions6selected/799outside and retains22source observations and source locators. Extraction fidelity still requires independent review.

Eight tests cover scope/no promotion, newly corroborated keys, retained three-source conflicts, distinct distance/grade meanings, duplicate ambiguity, altered HTML units/schema/values, input revision mismatch and rejection of unsupported source types before database construction. Run the checker with `--write-snapshot` to regenerate; without it to check reproduction.

This report is not yet integrated into generic findings. Existing PFC tasks remain open; no CSV corrections, manufacturer article creation, accepted equivalence or UPN issuance. Next: queue the new inter-source disagreements, independently review geometry/lineage and obtain exact article, material, tolerance, length/end/finish and certificate evidence. Combined distinct structural screening remains67rows; now66have at least one unique nominal candidate across selected sources, not approved identity.738rows remain outside selected structural tables.
