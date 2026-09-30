# User-supplied catalogue structure analysis

## Scope and handling

Four operational CSV catalogues supplied on 2026-09-30 were profiled to test the registry model against real plate, structural steel, gasket, and piping data. Together they contain 13,412 rows. Their exact bytes are retained locally under `registry/artifacts/user-reference-csvs/`, which is Git-ignored. The committed `source-datasets.csv` records their hashes, shapes, sensitivity, and allowed use without publishing contact details or commercial rows.

These files are evidence of how operational catalogues are structured. They are not yet evidence that any described part exists exactly as stated. They have no manufacturer part-number column, no row-level source locator, and no independent provenance trail. Their current allowed use is therefore `structure_research`, not `identity_evidence`.

## What the structures teach us

Each row combines four different entities that UPN must keep separate:

| CSV fields | Registry meaning |
| --- | --- |
| Description, category, material/grade, form, dimensions, standard or schedule | Candidate physical-part identity and descriptive specifications |
| Supplier, unit cost, currency and order unit | Supplier offer |
| Quantity, reorder level, reorder quantity and warehouse location | Inventory balance and replenishment policy, not part identity |
| Contact name, phone and email | Organization contact data, not part identity or public registry content |

The files confirm that a universal identity record cannot be a flattened copy of a stock master. Price, quantity, warehouse, contact, and reorder settings can change without creating a new physical part. Conversely, a change to grade, construction, pressure class, dimensional standard, or defining dimensions can require a different identity.

## Dataset findings

### Steel plate — 395 rows, 20 columns

- The candidate identity key of grade/condition, plate type, length, width, and thickness is unique across all 395 rows.
- Calculated carbon-steel mass using 7,850 kg/m³ agrees within 0.5% for 392 rows.
- Three rows need review: 3,000 × 1,500 × 22 mm records 771.15 kg instead of 777.15 kg; 2,500 × 1,200 × 32 mm records 735.6 kg instead of 753.6 kg; and 4,000 × 2,000 × 30 mm records 3,768 kg instead of 1,884 kg.
- `MOC` combines standard, grade, delivery condition, commercial-quality wording, and product name. These must become separate properties.
- `S355 JO` is likely a character ambiguity for `S355 J0`, but UPN must not correct it without a cited source.
- Mass should be retained as a cross-check or descriptive value, not used as the sole identity field.

### Structural steel — 805 rows, 27 columns

- All 805 physical-field combinations are unique, spanning 21 descriptions and 17 section labels.
- One wide sparse table is being used for fundamentally different shapes. Diameter applies to round sections, width/depth/thickness to hollow or flat sections, and web/flange dimensions to beams and columns. These require class-specific profiles rather than one universal structural-steel fingerprint.
- `MOC` includes `S355JR`, `Mild Steel`, `GR55C`, and `450PMa`; the last value appears typographically suspect and is not a material specification that may be normalized without evidence.
- Text contains `Rectangluar` and a mojibake description (`IPE Sections �AA�`). Two near-identical Supalite descriptions differ only by `DIN.1026/1963` versus `DIN.1026/1964`; this may be meaningful or erroneous and requires source review.
- Supplier contact number and location each contain 122 unique values while the supplier and email remain fixed. Those sequences need operational-data review and must not influence identity.

### Klinger gaskets — 12,162 rows, 24 columns

- The file contains 26 product descriptions. Twenty-four descriptions repeat exactly 470 geometry/class combinations, which suggests a generated product-family matrix rather than 12,162 verified exact articles.
- One identity row is duplicated: Klinger Envelope Gasket, ASME B16.21, Class 300, 1/2 inch, 95 mm outer and 21 mm inner dimension.
- `MOC` is mostly `Sheet` or `Metallic`, which describes construction family rather than actual material. One Maxiflex row says `S316L`, creating inconsistent specificity.
- `Flange Type` contains overlapping labels such as `BS10 Flanges` and `BS 10 Standard Flanges`, plus rows where a pressure table appears in the flange-type field.
- `Nominal Size (NB) Inch` and `Nominal Size (PN)` are mutually exclusive across every row. The second heading appears to hold metric nominal bore/DN, not pressure nominal PN, and needs confirmation.
- Columns labelled outer/inner ring `Thk` contain values up to 3,060 mm and 3,030 mm. Every populated value is greater than 10 mm. They cannot safely be interpreted as thickness; they likely represent additional diameters or ring dimensions.
- A trustworthy gasket profile needs construction type, exact manufacturer product family/number, flange standard and style, pressure class/table, nominal size, gasket OD/ID, thickness, winding/filler/facing material, and inner/outer ring presence and material.

### Piping — 50 rows, 23 columns

- All 50 candidate dimensional keys are unique.
- Outside diameter, inside diameter, and wall thickness close mathematically for all rows within 0.01 mm. Published mass per metre agrees with a 7,850 kg/m³ steel calculation within 2% for all rows.
- Numeric formatting changes after the first records: decimal points and decimal commas are mixed in the same columns. Normalization must be locale-aware and must preserve the raw string.
- The description says `ASTM A106 - SEAMLESS PIPE / API 5LB WELDED`, while the separate type field says `Welded` and the material field says `ASTM A106`. Seamless/welded construction, product specification, grade, and API designation are conflated and contradictory.
- Schedule values mix numbers with `(XXS)`. Schedule and wall designation require controlled terminology rather than numeric coercion.
- A trustworthy pipe profile needs product specification and grade, manufacturing route, NPS/DN, dimensional standard, OD, wall thickness or governed schedule, length, end preparation, heat treatment and applicable product-specification level where relevant.

## Model consequences

1. Preserve every raw string and its locale before normalization.
2. Split standard, grade, delivery condition, material, construction, and product family into separate properties.
3. Use class-specific identity profiles for plate, each structural shape family, gasket construction families, and pipe products.
4. Keep supplier offers, prices, inventory balances, replenishment policies, warehouse locations, and contacts outside the physical identity fingerprint.
5. Require a manufacturer part number or a governed source-defined article key before treating a row as a manufacturer part.
6. Require row-level source locators and independent review before any of these records can support equivalence or UPN issuance.
7. Treat calculated mass and dimensional closure as validation checks. A passing calculation does not prove the source, grade, tolerance, or exact article.

## Next work

- Ninety-five Maxiflex tuples now match official historical catalogue page 52; see `klinger-dimension-verification.md`. Confirm the component meanings with a labelled drawing and verify the remaining rows.
- Obtain exact source catalogues or standards for the plate, structural, and pipe values and record row-level locators.
- Split each domain into narrow identity profiles before ingestion.
- Add inventory/location entities only after the operational ownership and update semantics are defined; these records must remain outside UPN identity.
- Resolve the listed contradictions and encoding defects without destructive cleanup of the preserved source files.
