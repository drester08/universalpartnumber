# Terminology normalization policy

Status: draft 0.1. No controlled-value mapping is approved.

## Principle

Normalization is an evidence claim. A raw manufacturer term and a canonical UPN value are stored separately. The registry never rewrites the source wording or assumes that similar abbreviations used by different manufacturers have identical meaning.

## Controlled values

Each controlled value belongs to one property and has a stable identifier, canonical code, preferred label, definition, and lifecycle state. A code cannot be reused across properties by implication. Deprecated values remain addressable so historical observations do not change meaning.

## Mapping record

Every mapping identifies the exact specification value, its property, the proposed controlled value, the basis, rationale, proposer, date, policy version, review state, and—when approved—an independent reviewer and review date.

Allowed bases are:

- `source_exact` when the exact product source states the mapped term directly.
- `manufacturer_definition` when the manufacturer defines a designation or suffix elsewhere in the same governed source context.
- `standard_crosswalk` when an inspected authoritative standard explicitly establishes the relationship.
- `expert_interpretation` when qualified judgment is required and the reasoning is recorded.

## Review boundary

Proposed mappings may support candidate discovery and expose likely matches or conflicts. They are not publication authority. Before a manufacturer-part review can be accepted, every required code-valued specification contributing to that part must have exactly one active mapping and that mapping must be `approved`. The reviewer must differ from the proposer. Competing non-rejected mappings remain an unresolved ambiguity and fail the publication gate.

Rejected mappings remain in the ledger but are ignored by candidate screening. Corrections add or review mapping records; they do not erase the raw observation.

## Bearing pilot

The initial bearing vocabulary covers geometry, closure, bore form, internal clearance, tolerance designation, cage construction, bearing material, lubricant, and locating feature. SKF `2Z` and NSK `ZZ` currently map to the same double non-contact metal-shield concept based on their manufacturer descriptions. This is a proposed normalization, not an approved declaration of product equivalence.
