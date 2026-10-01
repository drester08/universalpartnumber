# Explicit numeric conversion requirements

Numeric identity evidence now requires an explicit finite normalized number, a nonblank quantity kind, a positive finite conversion factor and a finite offset. Missing or blank metadata no longer defaults to factor one or offset zero. Unusable conversions return no numeric value rather than inventing a base-unit measurement. Decimal arithmetic failures fail closed.

Candidate screening excludes unusable numeric observations instead of falling back to their raw strings. Required-property coverage uses the same conversion check. For `numeric_exact` requirements, the unit's quantity kind must match the profile/property comparison rule. A length cannot satisfy a force requirement merely because its number is present. Explicit zero and negative numbers remain values; physical range validation is separate.

Numeric set comparison also validates every value against the rule even when the two sets contain the same single value. The previous pair-only loop could skip that validation. Non-finite values/tolerances, negative tolerances, relative tolerances above the existing two-percent policy limit and quantity-kind mismatches cannot establish a match.

Eleven synthetic tests cover missing/blank metadata, invalid/non-finite decimals, zero/negative factors, missing quantity kind, metric/inch conversion, affine offsets, explicit zero and negative values, invalid tolerance/value comparisons, SQLite coverage, screening without conversion metadata, equal singleton sets and rejection of a synthetically accepted article with a missing factor or wrong quantity kind. No synthetic review enters the real database.

This is numeric normalization and coverage enforcement, not proof that a registered unit definition or source measurement is correct. Source-defined tolerances, nominal versus measured values, rounding, physical ranges and independent source/review permission remain separate requirements. SQL still permits incomplete research rows; runtime publication/issuance audits enforce these checks. Conditional SQL predicates remain unresolved. No source facts, units, comparison policies, registrations, approvals or counts are edited.

Verification on 1 October 2026: all 453 tests passed in 82.167 seconds, including the eleven new conversion tests. Registry build/validation and the zero-allocation issuance audit passed. Existing rotated-text warnings remain unrelated. No source capture, CSV edits or PDF extraction occurred.
