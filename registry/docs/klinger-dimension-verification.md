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
