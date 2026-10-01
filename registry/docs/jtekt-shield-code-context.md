# JTEKT shield-code context

Status: retained manufacturer terminology research, not a complete canonical closure mapping. No new exact-article facts, review approvals or UPNs.

JTEKT's official [bearing-number guide, Table 6-2](https://koyo.jtekt.co.jp/en/support/bearing-knowledge/6-3000.html) defines `ZZ` as fixed shielding on both sides. The retained HTML table places it in the Shield category, distinct from the adjacent Non-contact seal category. The table does not explicitly establish shield material or shield contact form. Do not transfer an adjacent category label to `ZZ`.

Private original: `registry/artifacts/jtekt/bearing-number-20261001.html`. SHA-256: `ED41FF7A2565FF8B1DA23FED6B34379D1E9B73F7C6D1238F13B390020C5E6A9F`. Registered as `SRC-JTEKT-BEARING-NUMBER` and `ART-JTEKT-BEARING-NUMBER`. The nested subtable begins at HTML line 1181; the `ZZ` row starts at line 1193, with category and row locators retained by extraction rather than inferred from a flattened page.

`scripts/check_jtekt_shield_codes.py` extracts all sixteen shield/seal codes with their native category boundaries and sidedness descriptions. It verifies source bytes, exact row order/values, unique target subtable, source/artifact custody and the unchanged related JTEKT exact-article observation. `reports/jtekt-shield-code-context.json` retains the table and partial interpretation. Six tests cover categories, sidedness, changed/duplicate tables, hash revision, custody and rejected material/contact-form promotion.

The related `6205 ZZ` raw closure remains `Shielded ZZ`; no canonical mapping is added. This source improves sidedness/fixing evidence but does not complete the double non-contact metal-shield definition. The existing twenty-four-pair screen and 434-task queue remain unchanged. An official deep-groove shield construction statement is still needed. Do not infer material, tolerance, clearance, cage, grease, bore or locating properties from absent supplementary codes. Any future manufacturer-default interpretation needs explicit applicability and independent review.

This milestone adds one registered source and one cached artifact: 124 sources and 69 cached evidence records. The forty manufacturer parts, sixty-three observations, seventeen proposed mappings and zero manufacturer resolution events are unchanged. Independent extraction/interpretation review and reuse permissions remain outstanding. Raw HTML stays private.
