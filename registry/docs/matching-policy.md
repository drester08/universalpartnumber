# Matching and equivalence policy

Version: 0.3-draft

## Decision rule

Two manufacturer part numbers may share one UPN only when the evidence supports that they represent the same item of supply. Text similarity, dimensional resemblance, or a distributor's substitution claim is insufficient by itself.

## Workflow

1. Normalize part numbers, units, terminology, and enumerated values without discarding the raw source values.
2. Block candidates by domain and the minimum identity-defining properties for that class.
3. Compare every identity-defining property. Missing or less-specific values reduce certainty; only contradictory values block equivalence. A generic family value such as `steel` or `hot-dip galvanized` does not contradict a compatible, more-specific value, but it also does not prove exact equality.
4. Check material grade, governing standard and edition, dimensions and tolerances, performance/rating, connection or interface, finish/coating, certification, and supply form when applicable.
5. Compare physical identity independently from supplier packaging. A matching GTIN or seller SKU may identify a box or pack and cannot close a physical-part decision unless its package level and contained part are proven.
6. Require primary-source evidence for both manufacturer parts. Secondary sources may identify a lead but cannot close the decision.
7. Record one of `same_item`, `different_item`, or `insufficient_evidence`, with a reviewer, policy version, rationale, and source locators.
8. Issue or attach a UPN only after the `same_item` decision passes review.

## Numeric comparison

Required `numeric_exact` properties are compared only through a versioned rule in `data/numeric-comparison-rules.csv`. Values are converted to a common SI base with the governed unit table before comparison. A rule uses the greater of its absolute and relative representation tolerances.

These limits reconcile source rounding; they are not manufacturing tolerances and never expand a declared product tolerance. Nominal market classes deliberately have broader rules because, for example, 450 mm and 18 inches can name the same fitting class. Overall dimensions remain independently defining under much tighter rules. A required numeric property without a rule, a missing unit, or a quantity-kind mismatch yields insufficient evidence rather than a match.

When one part has multiple authoritative values, every value must be mutually compatible under the same property rule. Otherwise the part has an internal source conflict and cannot advance to positive equivalence review. Candidate-screen algorithm versions change whenever these rules or their interpretation change.

## Hard stops

- Conflicting safety, pressure, temperature, electrical, load, dimensional, material, or certification properties.
- An unknown manufacturer or ambiguous part-number revision.
- A source that cannot be traced to a stable locator.
- A match based only on a reseller title, search snippet, image, or AI-generated text.

## Fingerprints

Fingerprints are deterministic serializations of class-specific identity properties. The algorithm and property set must be versioned. A collision creates a review candidate, not an automatic merge.
