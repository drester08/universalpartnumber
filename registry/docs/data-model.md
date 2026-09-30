# Data model

UPN separates a physical branded part, a supplier's commercial offer, and the supply item the market needs to identify.

## Core boundaries

1. A **source** is a versioned authority, catalogue, datasheet, webpage, or database. A URL alone is not evidence: retrieval date, source locator, access terms, and—when locally retained—a checksum are recorded.
2. A **manufacturer or branded part** is a physical item identified by the responsible brand's part number. It remains distinct even when evidence later shows it belongs to the same item of supply as another organization's part. When the actual legal manufacturer is unknown, that uncertainty is retained rather than assigning the seller as manufacturer by assumption.
3. A **supplier offer** is a seller SKU for a commercial unit such as one piece, a measured length, a pack, a box, or an unknown package level. It may point to a known branded part. Order quantity, order unit, package level, and trade-item identifiers belong here, not in the physical identity profile. A three-metre sales unit and a 200-piece box are therefore represented differently rather than forced into one integer pack field.
4. An **observation** is exactly what one source said at one location and time. Raw values are preserved; normalization creates separate structured values.
5. A **source dataset** records the custody, checksum, shape, sensitivity, verification state, and permitted use of a supplied bulk file. Profiling a file does not make its rows identity evidence.
6. An **item of supply** is the canonical UPN concept. It may begin with one independently accepted anchor manufacturer part; further parts join only through reviewed `same_item` decisions. This lets a genuinely unique part receive a UPN without inventing a duplicate comparison.
7. **Application interchangeability** is separate from identity. Two different items may be substitutable in a defined application, while identical items may still require procurement or certification constraints.
8. An **external identifier** such as an NSN is its own governed record. A manufacturer or supplier assertion creates an unreviewed cross-reference; it becomes authority-verified only after the exact issuing-authority record is inspected.
9. A **numeric comparison rule** belongs to one profile-property pair. It defines only how differently rounded source representations are compared after unit conversion. It is versioned, cannot stand in for a manufacturer's dimensional tolerance, and is mandatory for every required `numeric_exact` field.
10. A **controlled value** belongs to exactly one property. A separate specification-value mapping connects a raw observation to that canonical term, records the mapping basis and proposer, and requires an independent reviewer before approval. Raw text is never overwritten by the mapping.

## Identifier policy

Database IDs are opaque stable keys. A UPN is nullable until an item has passed review. Version-one UPNs use a non-semantic twelve-digit allocation and check digit; they never encode product class or manufacturer. Allocations are permanent and cannot be reused. Fingerprints are versioned and help detect candidates; they are never proof of identity. A GTIN, EAN, or UPC is attached to the observed commercial offer with an explicit scope (`each`, `pack`, `box`, `case`, `pallet`, or `unknown`) and is never assumed to identify one physical piece.

## Change policy

Observations are append-only. Incorrect or stale observations are rejected or superseded rather than silently edited. Memberships carry validity dates so a later correction does not rewrite history.
