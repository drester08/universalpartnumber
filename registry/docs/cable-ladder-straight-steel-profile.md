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
- Øglænd's official [LOE system page](https://www.oglaend-system.com/products/cableladders/loe/?offset2504=0) and product pages for HDG LOE55 item numbers [1371511](https://www.oglaend-system.com/product-variants/cable-ladder-loe55-cl-200-3000-hdg-article49493-52088.html?pid=40300), [1371512](https://www.oglaend-system.com/product-variants/cable-ladder-loe55-cl-300-3000-hdg-article49562-52088.html?pid=40300), [1371513](https://www.oglaend-system.com/product-variants/cable-ladder-loe55-cl-400-3000-hdg-article49593-52088.html?pid=40300), [1371514](https://www.oglaend-system.com/product-variants/cable-ladder-loe55-cl-500-3000-hdg-article49623-52088.html), and [1371515](https://www.oglaend-system.com/product-variants/cable-ladder-loe55-cl-600-3000-hdg-article49656-52088.html?pid=40300).
- Legrand's official 6 m product pages for [ZL300G6M](https://www.legrand.co.uk/en/catalog/products/swifts-medium-duty-hot-dip-galvanised-steel-cable-ladder-300mm-x-100mm-x-6m-length-zl300g6m), [ZL450G6M](https://www.legrand.co.uk/en/catalog/products/swifts-medium-duty-hot-dip-galvanised-steel-cable-ladder-450mm-x-100mm-x-6m-length-zl450g6m), and [ZL600G6M](https://www.legrand.co.uk/en/catalog/products/swifts-medium-duty-hot-dip-galvanised-steel-cable-ladder-600mm-x-100mm-x-6m-length-zl600g6m).
- Niedax's retained official [current German catalogue](https://www.niedax.com/fileadmin/user_upload/Downloads/Global/KAT_NX_KR_DE_ab24_komplett_web_01.pdf), retained [international cable-ladder catalogue](https://www.niedax.com/fileadmin/user_upload/Downloads/Global/NX_KAT_INT_USA_Cable_Ladder_System.pdf), and [piece-galvanizing specification](https://www.niedax.com/de-en/pillarpages/galvanizing/piece-galvanizing/) for pre-galvanized `KL 100.203` and hot-dip-galvanized `KL 100.203 F`, `KL 100.303 F`, `KL 100.403 F`, `KL 100.503 F`, and `KL 100.603 F`.
- OBO Bettermann's official LCIS 60 product pages and retained technical datasheets for item numbers [6209721](https://www.obo-bettermann.com/en-xi/products/cable-ladder-lcis-60-3-m-c30-ft-3000-200-1-5-no-6209721.html), [6209723](https://www.obo-bettermann.com/en-xi/products/cable-ladder-lcis-60-3-m-c30-ft-3000-300-1-5-no-6209723.html), [6209725](https://www.obo-bettermann.com/en-xi/products/cable-ladder-lcis-60-3-m-c30-ft-3000-400-no-1-5-6209725.html), [6209727](https://www.obo-bettermann.com/en-xi/products/cable-ladder-lcis-60-3-m-c30-ft-3000-500-1-5-no-6209727.html), and [6209729](https://www.obo-bettermann.com/en-xi/products/cable-ladder-lcis-60-3-m-c30-ft-3000-600-1-5-no-6209729.html).
- Atkore/Unistrut's official Australian product pages for [LEK101RHG](https://www.atkore.com/en-au/product/lek101rhg), [LEK103RHG](https://www.atkore.com/en-au/product/lek103rhg), [LEK104RHG](https://www.atkore.com/en-au/product/lek104rhg), and [LEK106RHG](https://www.atkore.com/en-au/product/lek106rhg), plus their shared NEMA 3 20B steel cable-ladder datasheet and individual dimension drawings.

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

## Current evidence state

The six Legrand, five Øglænd, and five OBO parts have 13 of 14 required profile properties. Their cited pages show splice connectors or fastener sets as related items but do not explicitly state the straight-section package contents. That field remains unknown.

The six Niedax parts have all 14 fields populated. The retained current catalogue states that `KSV 100` splice plates must be ordered separately, so splice inclusion is recorded as `false` rather than inferred. It distinguishes `S` steel strip galvanizing to DIN EN 10346 from `F` hot-dip galvanizing to DIN EN ISO 1461. It also distinguishes the `F` construction as omitting the 5.4 mm floor perforation between rungs while retaining continuous side perforation and additional 8.5 mm floor holes. These differences prevent the near-identical `KL 100.203` and `KL 100.203 F` names from being collapsed. Completeness is not approval: every observation remains `unreviewed`, no equivalence decision has been accepted, and no UPN is issued.

The four Atkore parts have 10 of 14 required properties. Official structured product records and drawings establish overall width, overall height, length, rung spacing, rail-in geometry, and item mass; the shared datasheet establishes mild steel, hot-dip galvanizing standards, and NEMA 3 20B load data. Rung profile, rung attachment, side perforation, and splice inclusion are not explicitly stated and remain unknown.

The Legrand and Eaton catalogue PDFs were discoverable through research tooling, but direct retrieval into the local evidence cache was blocked or timed out on 2026-09-30. Their artifact records therefore contain no fabricated local path or checksum. Thirteen Øglænd, Niedax, OBO, and Atkore evidence artifacts were retrieved successfully and recorded with SHA-256 checksums. Cached source files remain outside Git.

## Cross-manufacturer screening

The coarse blocking keys are form, nominal width, length, base-material family, surface-protection family, and rung spacing. Fourteen pairs share all six:

- Legrand `ZL300G6M` versus Niedax `KL 100.303 F`: conflicts in overall width, rung profile, rung attachment, side-rail profile, side perforation, and duty series; Legrand splice inclusion is missing.
- Legrand `ZL600G` versus Øglænd `1371515`: conflicts in overall width, side-rail height, rung profile, rung attachment, side-rail profile, side perforation, and duty series; surface-protection specificity and splice inclusion remain unresolved.
- Legrand `ZL600G6M` versus Niedax `KL 100.603 F`: conflicts in overall width, rung profile, rung attachment, side-rail profile, side perforation, and duty series; Legrand splice inclusion is missing.
- Legrand `ZL600G` versus OBO `6209729`: conflicts in overall width, side-rail height, rung profile, side-rail profile, side perforation, and duty series; splice inclusion is missing.
- Each same-width OBO/Øglænd pair at 200, 300, 400, 500, and 600 mm: conflicts in side-rail height, rung profile, rung attachment, side-rail profile, side perforation, and duty series; surface-protection specificity and splice inclusion remain unresolved.
- Five Atkore pairs at matching 300, 450, or 600 mm widths and 6 m lengths: all conflict in side-rail height, side-rail profile, and duty series; three also conflict in overall width. Mild-steel specificity and four unreported construction/package fields remain unresolved rather than being treated as contradictions.

All fourteen are `hard_conflict` and are **not the same item** under profile 0.1. Their similarity scores are diagnostic only; a score cannot override any hard-stop conflict. No equivalence decision or UPN is created.

## Review needed before profile 1.0

1. Confirm the identity significance of package-included hardware with manufacturers and procurement users.
2. Define a structured load-rating tuple: load, support span, orientation, standard and edition, safety factor, temperature, and environmental conditions.
3. Decide whether certification differences always split identity or remain application constraints.
4. Obtain stable local evidence artifacts or manufacturer-signed data feeds.
5. Review terminology against licensed/open classification properties before promoting the profile from draft.
