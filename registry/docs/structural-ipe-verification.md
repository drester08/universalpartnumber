# Structural IPE nominal comparison — 2026-09-30

Official ArcelorMittal South Africa E1.2 PDF pages4/5 were rendered and visually inspected. Tables distinguish IPE (DIN1025:1965) from IPE-AA (SPE230); designation labels do not always equal nominal depth. Their historical footer dates and E1.2-cover/E1.1-footer inconsistency are retained. Source grade lists are not equivalence approvals.

All12 supplied IPE/IPE-AA records compared: six IPE nominal depth/width/web/flange/mass values agree; six IPE-AA rows differ only in the Height field. For example, designation100x55 has nominal depth97.6, while supplied Height is100. This is an unresolved dimension-versus-designation interpretation, not proof of an incorrectly manufactured beam. Other793 records not compared here.

`reports/arcelormittal-ipe-observations.json` records12 manually transcribed source rows with page/family/designation locators. `reports/structural-ipe-comparison.json` retains exact CSV logical records754–765 and hashes. `scripts/check_structural_ipe.py` reproduces the comparison; three tests check selected coverage, representation and family-specific depth distinction. Tests cannot prove transcription fidelity. Raw source stays private; reuse and independent transcription review remain pending.

Next: corroborate exact section designation/Height meaning, capture grade certificates, root radii, lengths/ends/coatings and current manufacturer articles; expand other structural families and integrate unresolved issues into review. No raw correction, accepted equivalence or UPN issuance.
