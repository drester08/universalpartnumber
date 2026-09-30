# Straight steel cable-ladder identity profile

Profile: `PROFILE-CABLE-LADDER-STRAIGHT-STEEL-0.1`  
Status: draft  
Date: 2026-09-30

## Scope

One rigid, straight steel cable-ladder section. The profile excludes bends, tees, risers, reducers, supports, covers, accessories, non-steel ladders, and complete installed systems.

## Primary evidence used

- Legrand's official pages for [ZL450G](https://www.legrand.co.uk/en/catalog/products/swifts-medium-duty-hot-dip-galvanised-steel-cable-ladder-450mm-x-100mm-x-3m-length-zl450g), [ZL600G](https://www.legrand.co.uk/en/catalog/products/swifts-medium-duty-hot-dip-galvanised-steel-cable-ladder-600mm-x-100mm-x-3m-length-zl600g), and [ZL750G](https://www.legrand.co.uk/en/catalog/products/swifts-medium-duty-hot-dip-galvanised-steel-cable-ladder-750mm-x-100mm-x-3m-length-zl750g).
- Legrand's official [Swifts cable ladder catalogue](https://www.legrand.co.uk/sites/g/files/ocwmcr866/files/2023-05/swifts-cable-ladder.pdf), especially the product-selection and straight-length technical sections.
- Eaton's official [B-Line metric cable-ladder catalogue](https://www.eaton.com/content/dam/eaton/products/support-systems/cable-management/metric-cable-ladder-system/metric-cable-ladder/cable-ladder-support-system-me-catalog-css-19.pdf), page 42 in the printed pagination, for the straight-section ordering grammar and dimension diagram.
- Øglænd's official [LOE system page](https://www.oglaend-system.com/products/cableladders/loe/?offset2504=0) and product pages for HDG LOE55 item numbers [1371512](https://www.oglaend-system.com/product-variants/cable-ladder-loe55-cl-300-3000-hdg-article49562-52088.html?pid=40300), [1371513](https://www.oglaend-system.com/product-variants/cable-ladder-loe55-cl-400-3000-hdg-article49593-52088.html?pid=40300), [1371514](https://www.oglaend-system.com/product-variants/cable-ladder-loe55-cl-500-3000-hdg-article49623-52088.html), and [1371515](https://www.oglaend-system.com/product-variants/cable-ladder-loe55-cl-600-3000-hdg-article49656-52088.html?pid=40300).

## Important findings

Nominal width and overall width are different properties. Legrand's product names use nominal widths of 450, 600, and 750 mm, while their technical tables give overall widths of 490, 640, and 790 mm. Eaton's straight-section diagram likewise distinguishes inside width from overall width. A matcher that keeps only one `width` field would create false candidates and potentially unsafe substitutions.

The manufacturer sources also distinguish material and finish, side-rail height/profile, rung spacing/profile/orientation/attachment, duty or load series, section length, certifications, and splice supply. These are not descriptive decoration; they can change structural performance, interfaces, installation envelope, or the contents purchased.

## Hard-stop conflicts

Any conflict in the following fields prevents a `same_item` decision under profile 0.1:

- product form;
- nominal or overall width;
- side-rail height;
- section length;
- base material or declared material grade;
- surface protection;
- rung spacing, profile, or attachment;
- side-rail profile or perforation;
- declared load series/rating in its full test context;
- safety/certification set where the application requires it; or
- whether splice hardware is included.

## Current evidence gaps

All seven manufacturer parts have 13 of 14 required profile properties. The cited pages show splice connectors or fastener sets as related items but do not explicitly state the straight-section package contents. That field remains unknown, so every observation remains `unreviewed` and no UPN is issued.

The Legrand and Eaton catalogue PDFs were discoverable through research tooling, but direct retrieval into the local evidence cache was blocked or timed out on 2026-09-30. Their artifact records therefore contain no fabricated local path or checksum. Øglænd's official LOE55 wall chart was retrieved successfully and recorded with its SHA-256 checksum; the cached PDF remains outside Git.

## First cross-manufacturer screening

The coarse blocking keys are form, nominal width, length, base material, surface protection, and rung spacing. Only Legrand `ZL600G` and Øglænd `1371515` share all six.

They are **not the same item** under profile 0.1. The reproducible screening records conflicts in overall width (640 vs 600 mm), side-rail height (100 vs 55 mm), rung profile, rung attachment, side-rail profile, side perforation, and duty series. Splice inclusion is also missing for both. The pair receives a similarity score of 0.461538 solely as a diagnostic; the `hard_conflict` result controls and no equivalence decision or UPN is created.

## Review needed before profile 1.0

1. Confirm the identity significance of package-included hardware with manufacturers and procurement users.
2. Define a structured load-rating tuple: load, support span, orientation, standard and edition, safety factor, temperature, and environmental conditions.
3. Decide whether certification differences always split identity or remain application constraints.
4. Obtain stable local evidence artifacts or manufacturer-signed data feeds.
5. Review terminology against licensed/open classification properties before promoting the profile from draft.
