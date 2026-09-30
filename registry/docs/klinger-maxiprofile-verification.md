# MaxiProfile source comparison — 2026-09-30

All 239 supplied MaxiProfile records were compared by flange type, pressure class and nominal size with pages 68–70 of the [official historical catalogue](https://www.klinger.co.uk/wp-content/uploads/2025/01/klinger-catalogue-2014.pdf). All three pages were rendered and visually inspected, including the discrepant cell.

## Result

238 dimension tuples agree. One differs: CSV logical line 789, DIN / PN16 / nominal size 400, contains `495 × 450 × 42`, whereas page 69 shows `495 × 450 × 426`. This is a likely omitted digit, retained as a discrepancy rather than automatically corrected. All 239 source keys are represented in the supplied family; none is unsupported or absent.

Page extraction counts are 95, 90 and 54. The detailed report includes each agreement's source page and CSV line, the discrepancy, and both input hashes. It compares the first three dimension cells with the printed tuple and requires the fourth cell to remain blank. It does not assign physical component meanings to these cells: the table heading is only “Dimensions (mm)”.

## Identity consequences

Catalogue pages 62–65 distinguish core material, facing material, core/facing thickness, parallel/convex profile and fixed/absent/floating guide rings. Those choices cannot be recovered from the dataset's generic `Metallic` material value. A family and size tuple is insufficient to select an exact article.

The current manufacturer download page was checked on 2026-09-30. Search results exposed an older Maxiprofile specification URL, but direct retrieval returned an access error. That uncached document is not used as verified evidence here; construction findings above come from the retained catalogue.

Do not adopt listed family temperature or pressure maxima as the rating of every variant. They depend on the selected construction and application. Matching historical numbers does not establish current standard conformity, suitability, or interchangeability.

The dataset remains `profiled/structure_research`. Required follow-up: exact style, component materials, core/facing thickness, drawing with dimension labels, source edition, and independently reviewed article evidence. No raw CSV values were changed and no UPN was allocated.

## Reproduce

```powershell
python registry/scripts/check_klinger_maxiprofile_dimensions.py --catalogue registry/artifacts/klinger/klinger-catalogue-2014.pdf --dataset "registry/artifacts/user-reference-csvs/Klinger Gaskets - Rev02 - 13 July 2026.csv" --report registry/reports/klinger-maxiprofile-comparison.json
python registry/scripts/test_klinger_maxiprofile_dimensions.py
```

Comparator exit 1 is expected because the discrepancy remains. Five regression checks cover original findings, truncation, duplicate keys, unsupported keys, and a nonblank fourth dimension. Extraction-count and 239-row guards reject incomplete scope before report export.
