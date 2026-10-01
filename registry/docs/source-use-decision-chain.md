# Evidence-bound source-use decisions - 1 October 2026

`data/source-use-decisions.json` is a versioned decision/revocation ledger. It contains zero real decisions and zero revocations. No permission or independent review is invented. The source-use publication gate now requires more than `license_verified` metadata: a single current, independently attested decision must cover the exact source ID, URL, observed captured artifact checksum and `upn_derived_fact_publication` purpose.

Each decision binds private permission evidence bytes and a clause locator, proposer, independent reviewer, proposal/review dates and explicit validity interval. The source revision must also be a retrieved registered artifact with matching local bytes. Missing observation hashes, uncaptured/changed source artifacts, invalid permission evidence, self-review, future review/start dates, expiry, effective revocation, rejected decisions and ambiguous overlapping grants remain holds. Invalid ledger structure fails closed. The registry builder validates the ledger before replacing SQLite; an invalid ledger preserves the previous output.

Path resolution stays within private `registry/artifacts/` evidence storage; absolute and escaping paths are rejected. No raw HTML publication purpose is accepted. Zero end dates, perpetual/default validity or permission inherited from another article are not assumed. Attribution licenses and listed obligations remain held until executable fulfillment is implemented. An empty obligations list cannot evade an attribution-state hold.

The same source-use gate runs through completeness and the existing issuance audit. Unreviewed research is still permitted. All actual source states, artifact registrations, observations, reviewer decisions and counts remain unchanged. Synthetic test grants only exist in disposable files/in-memory databases and never enter the real ledger.

Sixteen new tests cover full synthetic chains, empty ledger, validity boundaries, future review, effective revocation, source/URL/revision/purpose scope, independent attestation, evidence tampering, path escape, duplicate grants, attribution, invalid dates/fields, rejection, no mutation and failed-build preservation. Existing source-use tests continue to cover publication and issuance propagation.

## Limits and next work

These checks validate a recorded evidence chain, not legal authenticity, signer authority or whether the permission document actually grants the stated rights. Those require genuine independent human review before a real decision is recorded. Decision JSON is an auditable local ledger, not an authenticated approval service. Its entries cannot be treated as trusted merely because they parse or name two different people.

Next implement authenticated review/decision ingestion, immutable history and source/artifact bindings, attribution fulfillment and revocation/expiry monitoring. Keep the SKF marketplace authorization hold intact pending actual permission or a rights-compatible source. Continue reviewed conditional SQL bindings and exact-article primary-source research without relaxing these gates. No part, equivalence or UPN is approved here.
