# Soft-cut geometry comparison — 2026-09-30

All 11,280 supplied records outside Maxiflex and MaxiProfile were compared with the soft-cut tables on pages 102–113 of the [retained official 2014 catalogue](https://www.klinger.co.uk/wp-content/uploads/2025/01/klinger-catalogue-2014.pdf). This covers 24 descriptions with 470 rows each. It tests printed geometry, not whether every product family is manufactured or suitable in every listed combination.

## Result

10,360 records agree with full-face OD/ID pairs under supported flange/class/size keys. None of those supported records differs numerically, and none selects the IBC OD/ID pair. 920 records have unsupported keys within these tables. One duplicate key remains; it is counted as a supplied row, not silently removed.

The 470 source keys are fully extracted with per-page count guards. Report `reports/klinger-softcut-comparison.json` groups 723 distinct supplied key/value/outcome cases, preserving every CSV logical-line reference and its family, each applicable source page, IBC/full-face OD/ID, drilling information and the conditional PN10 hole-count footnote. Both input hashes are recorded. The source file is unchanged.

## Unresolved keys and coverage

- The export uses BS10 Table B in 24 families, while these catalogue tables contain A, D, E, F, H, J and K. 667 records carry the exact BS10/Table B combination; another 29 Table B records have the incorrect ASME flange label described below. Absence from this catalogue does not prove that a standard/class is invalid everywhere.
- All 194 BS10-style records in Top-sil-ML1 carry `ASME B16.21 Flanges`. Twenty-nine of those are also the Table B issue above.
- PSM-AS With Eyelet has 29 records with `BS10 Flanges` in both flange and class fields.
- Soft-Chem has 29 records with `Table E` in the flange field and `BS10 Flanges` in the class field.
- Sealex has one record with a long Table K description in both fields instead of separate class and flange values.
- Envelope logical lines 11714 and 11734 duplicate the ASME B16.21 / Class 300 / 1/2-inch key. Its source Class 600 / 1/2-inch key is consequently absent. Check intended assignment before any correction.

These categories overlap as stated and reconcile to 920 unsupported rows. Every family lacks the source's 29 Table D keys. Further missing keys follow from the malformed fields and Envelope duplicate; the report retains missing source coverage separately from unsupported supplied records. No label has been automatically rewritten.

## Diameter agreement is not full geometry

Pages 102 and 109–113 were rendered and visually inspected. Their headings explicitly distinguish IBC and full-face gaskets and label OD/ID. The manufacturer's full-face drilling columns have no equivalents in this dataset.

For nominal size 6 inches, Tables A, D and E share the 279 × 168 mm full-face pair and 235 mm bolt circle. Table A specifies four holes of 18 mm, D eight of 18 mm, and E eight of 22 mm. All three would collapse under an OD/ID-only fingerprint. These cells were visually checked on pages 109–111. A Table B record must not be mapped to one of these classes solely because its diameters agree.

The PN10 / size65 row's printed eight-hole value has a note allowing four holes for cast iron and copper alloy flanges. The report preserves this condition rather than turning eight into an unconditional defining value.

The first two CSV dimensions can be compared as full-face OD/ID under these specific source tables. This finding does not resolve the component meanings of Maxiflex or MaxiProfile tuples, and does not authorize renaming their fields.

## Next identity work

Full-face cut gaskets need verified material/product grade, thickness, flange standard and class, nominal size, OD/ID, hole count/diameter/bolt circle, and any eyelet or envelope construction. IBC gaskets need a separate form profile. Envelope, Sealex and other named constructions require their own applicability evidence rather than inheriting the common matrix as approved articles. Obtain exact drawing or order-defined article evidence, current source edition and independent review before ingestion as verified identity.

## Reproduce

```powershell
python registry/scripts/check_klinger_softcut_dimensions.py --catalogue registry/artifacts/klinger/klinger-catalogue-2014.pdf --dataset "registry/artifacts/user-reference-csvs/Klinger Gaskets - Rev02 - 13 July 2026.csv" --report registry/reports/klinger-softcut-comparison.json
python registry/scripts/test_klinger_softcut_dimensions.py
```

Comparison returns exit1 because unresolved keys, duplicate and missing source coverage remain. Seven regression tests cover original totals and row accounting, drilling and footnote preservation, missing row/family, changed dimensions, nonblank extra dimension, and duplicate detection without dropped records.

## Whole-file reconciliation

| Scope | Rows | Numeric agreements under supported keys | Numeric differences | Unsupported keys |
| --- | ---: | ---: | ---: | ---: |
| Maxiflex | 643 | 563 | 51 | 29 |
| MaxiProfile | 239 | 238 | 1 | 0 |
| Other 24 descriptions | 11,280 | 10,360 | 0 | 920 |
| Total | 12,162 | 11,161 | 52 | 949 |

The duplicate is an additional quality issue within those counts, not a thirteenth-thousandth record. The three comparisons cover every supplied gasket row, but only historical numeric agreement and source-key coverage. None establishes exact manufacturer article identity, current conformity, availability, suitability or interchangeability. The dataset remains structure research and no UPN is issued from it.
