# Macsteel equal-angle seller evidence

Research milestone, 2026-09-30. Not approved identity or UPN issuance.

Thirty public seller offers were extracted from one privately retained page at
https://shop.macsteel.co.za/angle_equal?pagenumber=4. The retained bytes, not
search-engine pagination, define this snapshot. Each observation retains the
seller SKU, exact whitespace-normalized name, detail URL and product-row locator.
Four source/artifact register entries bind the listing, two detail pages and the
shop legal-entity statement to SHA-256 hashes. Raw HTML remains Git-ignored.

Macsteel Service Centres SA (Pty) Limited is registered as the seller/distributor,
not the manufacturing mill. Manufacturer-part links and brand are blank.
Order unit, package level and lifecycle remain unknown in the offer seeds.
Dimensions parsed from listing names are source assertions in the research JSON,
not independently approved canonical properties.

The 60x60x5 section has distinct 6m and 13m offers, AE_S355RA_0061 and
AE_S355RA_0064. Both retained detail pages show EA, size 60.00 X 60.00,
thickness 5.00mm and S355 JR+AR EN 10025-2 AS ROLLED. Their technical lengths
must not be silently used as billing quantities. The page's Material label is
the seller SKU, not the material specification.

Hidden JSON-LD repeats the seller code as mpn with an empty brand, zero price
and InStock. The visible page requires login for price. These fields do not
establish a manufacturer, free goods or confirmed current availability.

Reproduce with `python registry/scripts/check_macsteel_angle_offers.py`.
The checker rejects changed hashes, unexpected row layout, duplicate SKUs,
unequal-leg descriptions, invalid dimensions and changed visible price text.
It checks the exact persisted offer seeds and research output against the cache.
This is reproducibility, not independent source-fidelity review.

Outstanding: inspect every offer detail and datasheet, expand remaining pages,
establish manufacturing provenance, review dimensional tolerances and commercial
unit semantics, and compare with the supplied angle rows without merging on
dimensions alone. Rights remain review-required. No user CSV was corrected.
