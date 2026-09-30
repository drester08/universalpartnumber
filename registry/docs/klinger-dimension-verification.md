# Klinger dimension verification — 2026-09-30

## Result

All 95 Maxiflex CSV rows within the Class 150/300/600/900/1500 ASME B16.5 scope match the four-number dimension tuples on page 52 of the [official 2014 catalogue](https://www.klinger.co.uk/wp-content/uploads/2025/01/klinger-catalogue-2014.pdf). CSV logical lines 2–96 were compared by pressure class and nominal size. No conflicting or missing catalogue key was found. The 14 Class 2500 rows are outside this comparison.

The table headings supply a dimension tuple, not four component definitions. The CSV's thickness-labelled columns therefore remain unmapped. A labelled drawing is required before assigning their physical meaning. The historical catalogue also does not establish present-day dimensional conformity.

## Exact scope and reproducibility

- Dataset: `DATASET-USER-KLINGER-GASKETS-20260713`, unchanged SHA-256 `207581e2b2c523fdfb7720131da2dd58f9795bc2745cfef84ee596139001ce86`.
- Catalogue: `SRC-KLINGER-CATALOGUE-2014`, PDF page 52, 95 class/size keys extracted; page 52 visually reviewed.
- Comparator: `scripts/check_klinger_asme_dimensions.py`, requires pypdf. It fails on missing or duplicate keys, tuple conflicts, or an unexpected extraction count.
- This check covers numeric tuples for one construction family and one flange-standard scope. It does not verify the remaining gasket rows, exact material variants, thickness, style, availability, or interchangeability.

```powershell
python registry/scripts/check_klinger_asme_dimensions.py --catalogue registry/artifacts/klinger/klinger-catalogue-2014.pdf --dataset "registry/artifacts/user-reference-csvs/Klinger Gaskets - Rev02 - 13 July 2026.csv"
```

## Construction evidence

The [manufacturer's 2024 specification](https://www.klinger.co.uk/wp-content/uploads/2025/01/maxiflex-2024.pdf), Issue 03, distinguishes filler from winding material and specifies ring configurations. A catalogue family name and one material cell cannot uniquely select those combinations. Each candidate needs explicit style, component materials and thickness evidence before identity review.

## Next evidence needed

Obtain a labelled dimensional drawing, confirm the catalogue edition underlying the user export, and verify each remaining size/class combination. Record gasket style, component materials and thickness per exact article. Keep the supplied dataset at `profiled/structure_research` until these questions are resolved.

## Extended comparison — pages 52–59

The comparator now covers all 643 supplied Maxiflex rows. It extracts 674 catalogue keys across pages 52–59, retaining three-value tuples for Tables S and T and separate ASME Series A/B keys. Unicode inch marks and mixed-fraction punctuation are normalized only for key comparison.

| Outcome | Supplied rows |
| --- | ---: |
| Exact tuple agreement | 563 |
| Tuple differs from historical source | 51 |
| Class key absent from these source tables | 29 |

The 51 discrepancies comprise PN16 (16), PN40 (18), PN100 (14), Table K (1), and Table R (2). The Table R records transpose the tuples for 1¼ and 1½ inch sizes. The 29 unsupported records use PN20; the catalogue contains PN25 instead. This suggests a class-label problem but does not authorize relabelling them. Sixty catalogue keys are absent from the export: 29 PN25 records and 31 Table H records. Missing coverage is recorded separately from conflicting supplied values.

All 241 supplied ASME tuples agree. DIN has 104 agreements, 48 differences and 29 unsupported keys. BS10 has 218 agreements and three differences. These counts reconcile to 643 records. The DIN and BS10 discrepancy pages 55, 56 and 58 were visually inspected. The supplied CSV remains unchanged.

`reports/klinger-maxiflex-comparison.json` records each discrepancy with its CSV line, class/size key, actual tuple, catalogue tuple and source page, plus input checksums. This report is final for the historical comparison; corrected source data and current product conformity remain unresolved.

```powershell
python registry/scripts/check_klinger_asme_dimensions.py --catalogue registry/artifacts/klinger/klinger-catalogue-2014.pdf --dataset "registry/artifacts/user-reference-csvs/Klinger Gaskets - Rev02 - 13 July 2026.csv" --all-tables --report registry/reports/klinger-maxiflex-comparison.json
```

Exit status 1 is expected for this dataset because discrepancies and unsupported keys exist. Extraction errors and duplicate keys raise an exception rather than producing a passing result. The original page-52 comparison still passes independently.
