# Pipe source comparison — 2026-09-30

All 50 supplied pipe rows were compared with nominal OD/wall values on page 13 of the [official Tenaris 2026 catalogue](https://www.tenaris.com/media/tjyk5gu5/pipes-for-civil-and-industrial-installations_2026.pdf). The complete page was rendered and visually inspected. Macsteel's [two-page seamless sheet](https://macsteel.co.za/wp-content/uploads/2022/12/seamless-pipe-2021.pdf) was also visually reviewed, but contains size/schedule availability rather than numeric wall values.

## Results

34 supplied records have a unique source key and OD/wall values compatible at their printed decimal precision. Twelve are outside the page's printed DN/schedule key scope. Four DN65 records have ambiguous source keys: the page prints both NPS2½ / OD73.02 and NPS3 / OD88.90 under DN65 for the same wall designations. Do not choose the convenient candidate or silently change the printed nominal diameter. No unique supported comparison produced a numeric conflict.

The 12 outside-scope rows are six DN6/8/10 records, four DN80 records and two DN90 records. This is a limit of this particular table, not proof that the supplied parts are invalid. NPS3/DN65 is recorded as a source anomaly requiring independent corroboration; corrected source metadata is not asserted here.

All 50 rows state `ASTM A106` and `Welded`, while both retained independent supplier/manufacturer documents place their A106 offerings under seamless pipe. The report retains this construction contradiction for every row. The supplied description also combines seamless A106 and `API 5LB WELDED`; product specification, grade, route and certification must be disentangled using exact article/certificate evidence. No raw record was corrected.

## Interpretation rules

Decimal comma and decimal point are parsed strictly, retaining raw strings. Unsupported representations such as ambiguous thousands separators are rejected. `(XXS)` maps to the table's wall identification XXS for lookup only; XXS remains a designation, not an invented numeric schedule.

Compatibility uses overlap of half-last-digit intervals from each printed value. For example 21.3 and 21.34 can represent compatible nominal values at different published precision. This is neither a manufacturing tolerance nor a match rule for certified material or application suitability. Mass, ID, length, grade, heat treatment, ends and actual article availability are not validated by this comparison.

The [ASME public listing](https://www.asme.org/codes-standards/find-codes-standards/welded-and-seamless-wrought-steel-pipe) identifies B36.10 as a dimensional standard covering both routes. The full standard was not acquired. ASTM's public listing exposed an AI-use restriction; its record is blocked bibliographic metadata only, and no standard text is ingested. Further standards use requires authorization/reuse review.

## Reproduce and next work

```powershell
python registry/scripts/check_piping_tenaris.py --catalogue registry/artifacts/tenaris/civil-industrial-pipes-2026.pdf --dataset "registry/artifacts/user-reference-csvs/Piping - Rev01 - 02 July 2026.csv" --report registry/reports/piping-tenaris-comparison.json
python registry/scripts/test_piping_tenaris.py
```

Report includes all 50 logical CSV lines, raw OD/wall values, source candidates, page and input checksums. Extraction requires 57 source rows and 50 supplied records. Exit1 is expected for source ambiguity, scope gaps and construction contradictions. No inference of interchangeability or UPN issuance.

The generic review layer now derives seven pipe findings with 66 links across all 50 supplied rows: construction conflicts, source ambiguity and coverage gaps. Dataset promotion is blocked while these findings remain unresolved. This is workflow integration, not independent corroboration or article approval.

Next: corroborate the source's nominal-diameter anomaly, extend smaller/other size coverage using independent official tables, and obtain exact grade/route/end/certification evidence. A dataset-correction approval and revision ledger is still required.

Independent follow-up is recorded in `pipe-independent-corroboration.md`: Tata Steel manufacturer evidence supports DN80/NPS3 OD88.9, and a separate supplier distinguishes65NB/80NB. Four supplied records have nominal OD/wall corroboration. Original source-specific findings remain open; no source correction or identity approval is asserted.
