# Mining Pressure Systems pipe-table research — 1 October 2026

The supplier/fabricator's own [technical manual](https://www.miningpressure.co.za/uploads/1/2/4/2/124291661/mps_technical_manual_full.pdf) supplies an independent pipe-size table spanning the nominal sizes absent from the selected Tenaris page. Mining Pressure Systems describes itself as a supplier and fabricator on its [own website](https://www.miningpressure.co.za/). This is primary evidence of a supplier publication, not proof of the mill or certification of the user's stock.

Private original: `registry/artifacts/mining-pressure-systems/technical-manual-20261001.pdf`, SHA-256 `FE5731D47330DAD79637F05CC44E969100B62651852E23F64DBAE147794DED4B`. The browser rejected its approximately 35 MB body; direct official retrieval succeeded. The document has 167 pages. Complete physical/printed pages 12, 13 and 14 were rendered and visually inspected using the PDF skill. No full-manual visual review or verified publication date is claimed.

Those pages contain 144 table rows: 50 on page 12, 46 on page 13, 48 on page 14. The product heading is A106 Grade B seamless. The broader section heading says seamless or welded, and a footnote lists API5LX grades with both routes. The footnote is not permission to relabel the A106 table as welded pipe.

The table explicitly includes nominal bore 6/8/10 with OD 10.3/13.7/17.1 mm and schedules 40/80. It separates nominal bore 65 at OD 73.0 from 80 at OD 88.9, and includes nominal bore 90 at OD 101.6. These are source-table facts, not yet a row-by-row comparison or correction of the supplied dataset. Wall designations and numeric schedules remain separate, including XXS with a dash rather than an invented schedule number.

## Source discrepancies retained

| Nominal bore / schedule | Printed internal diameter (mm) | OD minus twice wall (mm) | Difference (mm) |
| --- | ---: | ---: | ---: |
| 80 / 160 | 6.64 | 66.64 | 60.00 |
| 400 / 10 | 392.70 | 393.70 | 1.00 |
| 600 / 160 | 490.52 | 490.92 | 0.40 |

These differences exceed the combined half-last-digit representation bounds of the three printed inputs. That is an internal arithmetic diagnostic, not a manufacturing tolerance or an approved correction. Original ID cells stay unchanged.

Nominal bore 50 schedules 40 and 80 both print approximate mass 5.43 kg/m despite different walls. This is a publication question, not an independently established mass error. No density assumption or substitute mass is inserted.

The deterministic checker retains every selected source row, inherited bore/OD group, raw decimal-comma values, page/text-line locators, wall designation, schedule and original checksum. It enforces page headings, footnotes, page numbers, unique full keys and row counts. Eight tests cover smaller sizes, the 65/80 distinction, raw-ID preservation, all three arithmetic questions, the mass question, XXS scope, changed bytes and no mutation/approval.

This capture is staged outside registered counts. Current registry remains 130 sources, 75 cached records, 42 parts, 68 observations, 26 proposed mappings, 25 screened pairs and 460 tasks. Existing Tenaris/source-specific findings and all 50 supplied construction conflicts remain open. No dataset value, source value, article approval, equivalence or UPN was changed.

Next: compare all 50 supplied nominal OD/wall keys against this separately identified source, preserving the old report. Register appropriate supplier authority and reuse restrictions. Independently review extraction, publication discrepancies and exact grade/route/end/certificate evidence. Do not fill supplied internal diameter or mass from this unreviewed table.
