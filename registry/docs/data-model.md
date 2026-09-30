# Data model

UPN separates what a manufacturer sells from the supply item the market needs to identify.

## Core boundaries

1. A **source** is a versioned authority, catalogue, datasheet, webpage, or database. A URL alone is not evidence: retrieval date, source locator, access terms, and—when locally retained—a checksum are recorded.
2. A **manufacturer part** is an item of production identified by a manufacturer part number. It remains distinct even when evidence later shows it belongs to the same item of supply as another manufacturer's part.
3. An **observation** is exactly what one source said at one location and time. Raw values are preserved; normalization creates separate structured values.
4. An **item of supply** is the canonical UPN concept. It can collect multiple manufacturer parts only after a reviewed equivalence decision.
5. **Application interchangeability** is separate from identity. Two different items may be substitutable in a defined application, while identical items may still require procurement or certification constraints.

## Identifier policy

Database IDs are opaque stable keys. A UPN is nullable until an item has passed review. Fingerprints are versioned and help detect candidates; they are never proof of identity.

## Change policy

Observations are append-only. Incorrect or stale observations are rejected or superseded rather than silently edited. Memberships carry validity dates so a later correction does not rewrite history.
