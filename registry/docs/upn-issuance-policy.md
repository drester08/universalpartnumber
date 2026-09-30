# UPN allocation and issuance policy

Status: draft 1.0. No UPN has been issued.

## Identifier format

Version-one identifiers use `UPN1-NNNNNNNNNNNN-C`:

- `UPN1` is the syntax version, not a product classification.
- `NNNNNNNNNNNN` is a centrally allocated, opaque twelve-digit sequence. Zero is reserved and sequences are never reused.
- `C` is a Luhn check digit calculated over version digit `1` followed by the twelve-digit sequence.

The number contains no manufacturer, geography, class, date, or mutable business meaning. Product meaning lives in the governed registry, not inside the identifier.

## Allocation versus issuance

A candidate or under-review item may reserve a number. Its allocation remains `reserved` and must not be represented publicly as issued. An issued item requires an `active` allocation. Deprecated or withdrawn numbers become `retired` and are never returned to the pool.

## Review chain

An item can begin with one accepted manufacturer part. That anchor membership cites the latest accepted manufacturer-part review. Additional manufacturer parts may join only through a reviewed `same_item` equivalence decision whose two parts are both active members of the item.

Before issuance:

1. Every member part must pass completeness, conflict, provenance, and observation-review gates.
2. The item must have at least one active manufacturer-part membership and a matching identity profile.
3. The latest item decision must be `approved` by a reviewer who attests independence from evidence capture.
4. The UPN must match its permanent allocation sequence and check digit.
5. The item lifecycle, allocation state, and review date must agree.

The automated gate proves these records are structurally consistent. It does not replace engineering judgment or the independent reviewer.
