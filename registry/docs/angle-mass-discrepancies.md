# Equal-angle displayed mass audit

Status: research ready within the checked scope, with material caveats. Snapshot 1 October 2026; no physical conflict, substitute or same-item equivalence has been approved.

## Scope and results

The preceding Orange Book screen has 136 seller offers. Of these, 104 have both a manufacturer geometry candidate and a same-context mass in the generic seller PDF. These represent **40 distinct geometry/material-context comparisons**, not 104 independent measurements. The other 32 offers have no comparison: 25 lack a manufacturer-table geometry candidate and seven lack a same-context seller-PDF mass.

| Displayed mass result | Distinct section/context pairs | Seller offers |
| --- | ---: | ---: |
| Exact numeric agreement | 6 | 19 |
| Nearest-rounding hypothesis not excluded | 30 | 76 |
| Not explained by displayed nearest-rounding | 4 | 9 |

The four discrepancies are:

| Nominal section (mm) | Seller table context | Seller mass (kg/m) | Orange Book mass (kg/m) | Offers |
| --- | --- | ---: | ---: | ---: |
| 25 × 25 × 3 | Commercial quality | 1.114 | 1.12 | 2 |
| 45 × 45 × 3 | Commercial quality | 2.131 | 2.09 | 2 |
| 70 × 70 × 8 | S355JR | 8.358 | 8.37 | 4 |
| 200 × 200 × 18 | S355JR | 54.200 | 54.3 | 1 |

Orange Book's context is S355 throughout. These contexts have **not** been equated. In particular, the two commercial-quality comparisons are geometry comparisons across unresolved material contexts, not proof of mass conflict for identical steel articles.

## Method and checks

For each displayed decimal mass `x` with decimal step `q`, the conditional nearest-rounding interval is `[x - q/2, x + q/2]`. Intersect the two intervals; conservatively retain touching boundaries. This convention is an explicit hypothesis, not source-confirmed rounding policy or manufacturing tolerance. The script additionally records direct ROUND_HALF_UP conversion of seller mass to the manufacturer's displayed precision. Neither diagnostic closes a part-identity gate.

Example: 2.131 has the conditional interval [2.1305, 2.1315], whereas 2.09 has [2.085, 2.095]. Those intervals do not overlap. Even so, differing actual section geometry, tabulation conventions or source errors remain possible; the root cause is unknown. No value is silently corrected.

The complete one-page seller PDF was rendered and visually reviewed this turn. The four displayed masses above agree with the visible table cells; all 55 sparse seller facts were automatically re-extracted and reproduced. The sheet provides no root/toe-radius table, so radius differences cannot be tested against the manufacturer's retained radii. General roll-formed narrative does not certify the route of any seller SKU. A second independent extraction-fidelity reviewer remains outstanding.

Eight regression tests cover distinct grain, all-offer accounting, the four discrepancies, interval arithmetic, conservative boundaries, malformed/missing inputs, duplicate offers and detached comparison values. Parent reports and source bytes are checksum-bound and reproduced before the audit runs.

## Evidence and next action

- `registry/scripts/check_angle_mass_discrepancies.py` and `registry/scripts/test_angle_mass_discrepancies.py`.
- `registry/reports/angle-mass-discrepancies.json`: source locators via its parent-record references, affected seller SKUs, exact inputs, intervals and all exclusions.
- Parent: `registry/reports/orangebook-equal-angle-screening.json`, SHA-256 `A0060C4F4B1FCFA406EBEC4A2601FF1F8ED8EC58B81B63B31CA9C1F204764801`.
- [Manufacturer table](https://orangebook.arcelormittal.com/node/220).
- Seller source: retained `registry/artifacts/macsteel/AE_S355RA_0061.pdf`, SHA-256 `E3DCBF06039844BB99ADD88B77153F37543EC30EF617368C44383748D4AEB1A1`.

Treat the four publication discrepancies as medium-priority research concerns, with high confidence in the arithmetic but unresolved physical interpretation. Obtain attributable section drawings, mass/rounding definitions, exact grade and certificates for seller stock. All 136 missing-maker tasks and ten earlier material-context gaps remain open. The four discrepancies now have dedicated derived research tasks through `docs/supplier-research-findings.md`; no governed article observation or physical adjudication has been created.
