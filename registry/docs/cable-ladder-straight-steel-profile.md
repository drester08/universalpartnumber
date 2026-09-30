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

The three Legrand observations have 13 of 14 required profile properties. The cited product pages tell installers to use fastener sets but do not explicitly state whether splice plates and fasteners are included with each straight section. That field remains unknown, so all three observations remain `unreviewed` and no UPN is issued.

The two official catalogue PDFs were discoverable through research tooling, but direct retrieval into the local evidence cache was blocked or timed out on 2026-09-30. Their artifact records therefore contain no fabricated local path or checksum.

## Review needed before profile 1.0

1. Confirm the identity significance of package-included hardware with manufacturers and procurement users.
2. Define a structured load-rating tuple: load, support span, orientation, standard and edition, safety factor, temperature, and environmental conditions.
3. Decide whether certification differences always split identity or remain application constraints.
4. Obtain stable local evidence artifacts or manufacturer-signed data feeds.
5. Review terminology against licensed/open classification properties before promoting the profile from draft.
