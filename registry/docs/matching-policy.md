# Matching and equivalence policy

Version: 0.2-draft

## Decision rule

Two manufacturer part numbers may share one UPN only when the evidence supports that they represent the same item of supply. Text similarity, dimensional resemblance, or a distributor's substitution claim is insufficient by itself.

## Workflow

1. Normalize part numbers, units, terminology, and enumerated values without discarding the raw source values.
2. Block candidates by domain and the minimum identity-defining properties for that class.
3. Compare every identity-defining property. Missing or less-specific values reduce certainty; only contradictory values block equivalence. A generic family value such as `steel` or `hot-dip galvanized` does not contradict a compatible, more-specific value, but it also does not prove exact equality.
4. Check material grade, governing standard and edition, dimensions and tolerances, performance/rating, connection or interface, finish/coating, certification, and supply form when applicable.
5. Require primary-source evidence for both manufacturer parts. Secondary sources may identify a lead but cannot close the decision.
6. Record one of `same_item`, `different_item`, or `insufficient_evidence`, with a reviewer, policy version, rationale, and source locators.
7. Issue or attach a UPN only after the `same_item` decision passes review.

## Hard stops

- Conflicting safety, pressure, temperature, electrical, load, dimensional, material, or certification properties.
- An unknown manufacturer or ambiguous part-number revision.
- A source that cannot be traced to a stable locator.
- A match based only on a reseller title, search snippet, image, or AI-generated text.

## Fingerprints

Fingerprints are deterministic serializations of class-specific identity properties. The algorithm and property set must be versioned. A collision creates a review candidate, not an automatic merge.
