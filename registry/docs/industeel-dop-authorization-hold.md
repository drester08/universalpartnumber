# Industeel plate declaration — private authorization hold

On 1 October 2026, the official [Industeel declaration](https://industeel.arcelormittal.com/fichier/dopil_s355jr_1-0045-en/) was captured privately and both pages visually reviewed. The English document identifies revision 6, S355JR / 1.0045 and the Châteauneuf production site in France. Its printed signature date is 4 November 2025; the publication date is unknown.

The performance-table thickness scope is strictly above 100 mm through 400 mm. This is not evidence for thinner stock, another mill, or any supplied CSV row. A grade-family name cannot establish actual-stock certification, application suitability or cross-manufacturer identity. The declaration's certification claims have not been independently authenticated.

The official [legal notice](https://industeel.arcelormittal.com/legal-mentions/), carrying a 15 April 2024 update date, restricts unauthorized reuse. A scope-specific permitted-use review is required before technical intake or publication. No performance table was extracted, no supplied rows were compared and no source or article was registered. No permission, equivalence or UPN was approved.

## Reproducible custody check

`scripts/check_industeel_dop_hold.py` verifies the two private capture checksums, PDF identity/page count and legal-notice cues against `reports/industeel-dop-authorization-hold.json`. It does not authenticate the manufacturer, certification or legal authority. Five tests cover changed bytes, wrong document identity and reproducible non-ingestion metadata. Raw captures remain excluded from Git.

Next: obtain permitted-use review, independently establish current declaration validity and exact stock provenance, then assess manufacturer/site and thickness applicability. Keep the earlier Macsteel family research separate; this document does not resolve its supplied-stock gaps.

Verification: all 463 tests passed in 80.808 seconds. Custody-report reproduction, registry build/validation, zero-allocation issuance audit and whitespace checks passed. Existing registry counts and approvals remain unchanged. Older PDF tests emitted rotated-text warnings; this is not evidence of complete extraction from those unrelated documents.
