# Equal-angle category capture — 2026-10-01

Five sequential category requests captured all five pages observed in the pager:
30/30/30/30/16 rows, 136 unique seller SKUs. This is dated supplier-category
coverage, not an atomic stock snapshot or complete global/manufacturer catalogue.
44offers state commercial quality;92state S355JR+AR. Seven descriptions use
an alternate decimal-dimension format. Exact names, raw grade statements, seller
codes, detail links and row locators remain distinct from derived numeric fields.

106new offers were appended without replacing the earlier30records. Their original
source bindings remain intact, and new dated page observations are retained in
the report. Manufacturer links, brand, order quantity/unit, package level and
lifecycle remain blank/unknown. Total supplier offers168; missing-maker tasks136.

One pair shares the same nominal description key: commercial-quality50x50x5,
length6m, codes AE_CQ_0096000006000 and AE_CQ_0096000007200. Both are retained.
The latter code suffix is not decoded as a7.2m length; its visible description
says6m. Inspect both detail pages before interpreting the apparent inconsistency.
No duplicate merge or interchangeability conclusion is permitted from these fields.

Follow-up: `macsteel-cq-pair.md` records both detail pages explicitly saying6.000m.
Suffix-based7.2m interpretation remains unsupported; separate article identity is
still unresolved. Neither offer is merged or corrected.

The earlier generic datasheet correlation still covers only the original30offers.
It is not silently expanded to all136. Remaining source-table coverage, article
details, manufacturer provenance, grade/route/length/tolerance meaning and licence
review remain outstanding. Commercial quality is not a verified material grade.

Run `python registry/scripts/check_macsteel_angle_catalogue.py` to reproduce the
snapshot and seeded offers. It validates all five custody hashes, page markers,
pager horizon, row shape/counts, dimensions, grade/code family alignment and
publisher detail URLs. Duplicate SKUs across pages or changed original offer
records fail before append. Same-nominal keys are retained as unapproved groups.
Six tests exercise pagination, grade, geometry, price and coverage invariants.
All raw HTML remains private and Git-ignored; no user CSV correction or UPN.

Page4 reuses its existing source identity and retains a second dated artifact.
Artifact uniqueness now includes SHA-256, preserving differing bytes at the same
URL without creating a duplicate source. A partial unique index still rejects
multiple unhashed captures at one source/URL. Four schema tests cover distinct
revisions, duplicate identical content, digest-case differences and duplicate
unknown captures.
