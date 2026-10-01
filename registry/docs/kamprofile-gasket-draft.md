# Draft kamprofile gasket capture profile

## Result — 1 October 2026

`profiles/kamprofile-gasket-draft-0.1.json` defines an executable research-capture design for two-faced serrated-metal-core gaskets. It covers parallel/convex profiles, explicit guide-ring and partition declarations, and circular or drawing-defined geometry. Spiral wound, soft-cut and ring-type-joint products remain separate classes.

This design is not a sixth SQL identity profile. The registered database still has five draft profiles. Candidate screening, equivalence and issuance do not consume this design yet. Its conditional rules must be integrated and independently reviewed before article ingestion or activation. No supplied data or historical findings are changed.

## Why conditional data needs explicit structure

The current SQL profile table supports the label `conditional` but does not encode predicates such as “ring material is required when the ring is present.” A blank cannot establish that a ring is absent. This design requires a `present` or `absent` declaration for both guide rings and partitions.

| Component state | Required research structure |
| --- | --- |
| Ring present | Material definition, attachment, geometry definition and thickness |
| Ring absent | Explicit absence; populated ring details are contradictory |
| Partitions present | Layout, material definition, joint method, profile and thickness |
| Partitions absent | Explicit absence; populated partition details are contradictory |

Core and both facing materials remain separate, as do core, each facing and overall thickness. Generic material labels are incomplete. Circular seal geometry requires labelled inner/outer diameter roles. Drawing-defined geometry is not coerced into diameters. Measurements carry units; no rounding tolerance, numeric equivalence or manufacturing tolerance is inferred. Serration and dimensional-tolerance definitions remain required references.

Standard flange connections require standard, edition, class and nominal size. Drawing-defined interfaces use an explicit definition instead of an invented flange class. Article evidence requires an article reference, drawing revision, locator and artifact checksum.

## Source and verification boundaries

The design binds the immutable [KLINGER family registration](klinger-maxiprofile-registration.md) and [construction research](klinger-maxiprofile-context.md). It also verifies current source/artifact custody against the built database. The source motivates component distinctions; this drafted schema is a UPN engineering proposal, not a manufacturer's approved identity standard.

`scripts/check_kamprofile_design.py` validates capture structure. It does not verify the truth of supplied references or grades, locate a certificate, approve a drawing, compare real articles or allocate a UPN. Synthetic tests deliberately use fabricated TEST references and never persist them as actual parts. All outputs keep source-truth, identity, application suitability and UPN permission false.

Twelve tests cover conditional requirements, contradictory absence, generic materials, individual thicknesses, dimension roles/units, non-circular geometry, flange editions, checksums, input preservation and live custody failure. `--capture <path>` can assess a privately prepared JSON research capture; the command without that option verifies the source-bound design only.

An official-site search for labelled Maxiprofile dimensions found family/specification leads, including `https://www.klinger.co.uk/wp-content/uploads/2025/01/maxiprofile.pdf`. This URL is an unacquired lead here, not proof of an exact article drawing or current standard conformity. The earlier tuple-role gap remains open.

Next implement conditional enforcement in database ingestion, candidate screening and issuance; add governed material/construction mappings and geometry/tolerance comparison rules. Obtain exact manufacturer article drawings and independent review. Family pressure/temperature maxima, colours and maintenance claims never fill missing identity fields or establish application suitability.
