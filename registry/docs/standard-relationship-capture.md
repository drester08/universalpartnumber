# Standard relationship research capture

`scripts/standard_relationships.py` adds a reusable, research-only capture validator for standards and article relationships. It makes the distinction identified in [fastener transition research](fastener-standard-transition-research.md) executable without inventing an approved standard alias. No real publisher assertion is ingested by this milestone.

## Separate relationship types

- `declared_conformance`: a manufacturer part or product family is asserted to conform to a standard. Family evidence remains family evidence; it is not inherited by individual articles.
- `supplier_cross_reference`: a source links two references of the same entity kind. This is not proof of identity or compliance.
- `successor_standard`: the subject is the predecessor standard and the target is its successor. The direction is preserved, not reversed or made transitive.
- `application_interchangeability`: a source makes a context-bound interchangeability claim between references of the same kind. This does not establish same-item identity or verified suitability.

Every entity preserves its kind, namespace, exact identifier and standard edition. An unstated edition is explicitly `null`; it is neither filled from the current standard nor silently merged with another edition. Every assertion needs explicit context, a qualifier list, retained source URL, local artifact path, SHA-256 and locator. Empty qualifiers do not mean that the source was proven unconditional; semantic review remains outstanding.

## Validation and limits

The top-level contract contains `policy_version` (`standard-relationship-research-0.1`), `scope` (`research_only`) and a nonempty `assertions` list. Each assertion has exactly `assertion_id`, `subject`, `target`, `relation`, `context`, `qualifiers`, `evidence` and `review_state`. Entity keys are `kind`, `namespace`, `identifier`, `edition`; evidence keys are `source_url`, `artifact_path`, `sha256`, `locator`. Only the `unreviewed` review state is supported.

The CLI accepts a saved JSON capture: `python registry/scripts/standard_relationships.py PATH_TO_CAPTURE.json`. It emits a report to standard output and writes no database or file. The source artifact must exist under the workspace's private `registry/artifacts/` directory and match the declared bytes. Paths that escape custody, credential-bearing source URLs, duplicate IDs/qualifiers, blank context, unknown fields, invalid endpoint kinds and attempted identity/approval relations are rejected.

A matching hash verifies retained bytes, not source authenticity, URL-to-file origin, locator interpretation, legal rights or assertion truth. The validator does not read technical source content, authenticate reviewers, infer links, compare article properties, screen pairs or issue UPNs. Every approval, suitability, permission and production flag remains false. It does not replace the SQL identity/mapping policies or the existing publication/issuance gates.

Thirteen synthetic tests cover the four distinct relations, direction, namespaces/editions, family scope, no approvals/inference, changed/missing/escaping sources, invalid entities and input non-mutation. Synthetic evidence is created only in temporary test directories and is not registered as real research. Obtain permitted-use review and independent semantic evidence before introducing real assertions or integrating an approved policy into ingestion and screening.

Verification: all 476 tests passed in 78.567 seconds. CLI help, registry build/validation, zero-allocation issuance audit and whitespace checks passed. Older PDF tests emitted rotated-text warnings; these do not prove complete extraction of unrelated sources. Registered source, article, mapping, screen and queue counts remain unchanged.
