# Current UPN reviewer queue

This report is generated deterministically from the governed registry seed data.
It is a work list, not a set of reviewer decisions. Regenerate it whenever source data changes.

- Total work items: 299
- Ready: 288
- Blocked by explicit dependencies: 11
- No queue item authorizes UPN issuance.

## Priority counts

| Priority | Count |
| --- | ---: |
| P0 | 76 |
| P1 | 42 |
| P2 | 170 |
| P3 | 11 |

## Queue counts

| Queue | Count |
| --- | ---: |
| artifact_retrieval | 19 |
| candidate_evidence_followup | 4 |
| complete_part_review | 11 |
| dataset_finding_review | 98 |
| external_identifier_verification | 1 |
| observation_review | 61 |
| reference_dataset_validation | 4 |
| required_evidence_gap | 49 |
| source_conflict_resolution | 2 |
| source_governance | 5 |
| supplier_manufacturer_identity | 30 |
| terminology_mapping_review | 15 |

## Priority meaning

- P0 — blocks trustworthy normalization or contains contradictory identity evidence.
- P1 — direct review or evidence work for a complete profile or plausible candidate pair.
- P2 — required evidence, observation, artifact, or authority-verification work.
- P3 — supporting source-access and licensing work.
