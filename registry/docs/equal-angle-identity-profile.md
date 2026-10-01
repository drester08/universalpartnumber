# Equal-angle identity profile — draft 0.1

This adds the registry's first structural-section identity profile, not approved manufacturer articles or final standardisation rules. Profile: `PROFILE-ANGLE-EQUAL-HOT-ROLLED-STEEL-0.1`. It remains **draft** pending engineering, standards and independent policy review.

## Scope

Individual straight plain hot-rolled equal-leg structural steel angles with explicitly specified JR/J0/J2/K2 impact-quality designations. Other structural grade families require a separate reviewed scope or future profile version; the draft's grade-pattern guard is not a complete international steel-grade validator. Unequal legs, cold-formed angles, stainless alloys, built-up assemblies, holes and special end preparation are excluded. No existing seller offer or design-table row has been converted to a manufacturer article.

## Required evidence

Seventeen required properties keep the following facts separate:

- Section geometry: equal-leg nominal right-angle form, both leg dimensions, thickness, root radius and toe radius.
- Supplied form: exact nominal length and end condition.
- Material: section base material, full steel grade including impact quality, governing material standard/part/edition/options, production route and metallurgical delivery condition.
- Standards: nominal-dimension standard separately from dimensional/shape/length tolerance specification, including editions and deviations.
- Surface: coating or explicitly uncoated finish separately from surface quality specification/class/subclass.

Certificates establish evidence and may carry declared product approvals, but batch or heat certificate numbers do not create different physical-item UPNs by themselves. Supplier packaging remains separate. Seller SKU, EA unit and general grade narrative are not proof of a manufacturer article.

The [manufacturer product-range page](https://sections.arcelormittal.com/products_and_solutions/EN) publishes separate dimension, tolerance and material-standard columns for angles: EN 10056-1, EN 10056-2 and several material-standard families. This supports separating their roles; it does not supply purchased normative standard text or establish a seller article's compliance, edition or options. `SRC-AM-SECTION-STANDARD-CONTEXT` and its private artifact retain this context with SHA-256 `9CB49911F4B7892DF296E79F7A7F2336C8F7AA3CBE674BCEF6172EB5CB4DFAC2`.

## Matching behaviour

Candidate blocking uses both nominal legs and thickness. Every other required field must still be checked. Mass per length is descriptive/contextual: it cannot rescue a missing grade, radius, route, delivery condition or tolerance. Four previously identified mass publication discrepancies remain unresolved.

The six required numeric properties use exact Decimal values after unit conversion with zero representation allowance. A nominal 60 mm and 0.06 m can agree; a different nominal value cannot borrow an allowable manufacturing deviation. Source rounding disagreements remain review issues rather than automatic substitutions. This deliberately conservative draft policy can only be changed through a reviewed version.

The screening guard accepts this scope's canonical shape `equal_leg_angle_90_degree` and route `hot_rolled`. Other or unknown forms/routes cannot become positive candidates under this profile. The full grade canonical code must have the form `s355jr`, `s355j0`, `s355j2`, `s355k2` or a similarly specified three-digit grade with one of these quality suffixes. This syntax check does **not** prove that the grade exists or complies with a standard. Broad `s355`, commercial quality and unknown values remain missing evidence. `S355JR+AR` must be split through reviewed property-scoped mappings into grade and delivery condition, not accepted as a single full-grade value.

Four vocabulary records are added for right-angle equal-leg form, hot rolling, S355JR and S355J2. These are vocabulary, not mappings or approval evidence. No automatic seller-title mapping is added. Accepted article evidence and UPN issuance still require independent mapping, article and item reviews under existing governance.

## Verification and remaining work

Ten regression tests execute the real screening rules against synthetic values using the built registry's profile/rules. They cover all seventeen missing-field cases, geometry-only insufficiency, JR/J2 conflict, broad-grade rejection, out-of-scope route/shape, length/radius/condition/tolerance differences, mass not rescuing missing identity, exact conversion, quantity-kind mismatch and six zero-tolerance rules. Synthetic screening candidates are not issued UPNs and are not stored as manufacturer parts.

No real angle manufacturer parts are ingested. Existing 136 seller-maker tasks and ten material-context gaps remain open. Engineering review must assess the property set, treatment of standards editions and options, symmetry, radius representation, surface/end specifications and grade scope. Other angle/steel profiles and international grade families remain outstanding. Obtain primary exact-article evidence before any promotion. Current generic seller sheet and S355 design table are insufficient to populate the required properties.
