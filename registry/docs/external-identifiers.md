# External identifier crosswalk policy

UPN must interoperate with established identifiers without mistaking them for automatic proof of identity.

## Identifier layers

- GTIN, EAN, and UPC normally identify trade items at a packaging level. They belong to a supplier offer until `each`, `pack`, `box`, `case`, or `pallet` scope is proven.
- Any identifier labelled EAN, UPC, or GTIN must have a valid scheme length and GS1 Mod-10 check digit. A manufacturer's documented prefix/suffix construction rule may be applied when both components are retained in evidence; an undocumented completion or guessed prefix is prohibited.
- A NATO Stock Number identifies an item of supply in the NATO Codification System. It is not a manufacturer part number and does not belong in `manufacturer_part_identifiers`.
- A UPN identifies a reviewed UPN item of supply. An external identifier can be linked to it only after the external record and the UPN membership evidence have both passed review.

## Verification states

1. `unverified`: one or more sources assert the identifier, but the issuing authority's exact current record has not been inspected.
2. `authority_verified`: the exact identifier record has been checked in an authoritative source and the evidence locator is retained.
3. `rejected`: review showed the asserted identifier or relationship was wrong or obsolete.

Supplier assertions, secondary corroboration, definitions, and authoritative exact records are stored as distinct evidence roles. A definition of the namespace is not verification of a particular identifier.

Niedax's current catalogue is an example of a documented construction rule: its six-digit table values are suffixes, and the legend instructs readers to prepend country prefix `40` and company prefix `13339`. UPN therefore records both raw suffix `904006` and complete, checksum-valid EAN `4013339904006` for `KL 100.203 F`, while leaving packaging scope unknown.

## Current NSN lead

Fabory article `01210.080.030` prints NSN `5305-12-337-0503`. A secondary record describes a hexagon-head cap screw and lists reference `ISO4017-M8X30-8.8-A2P`, which is directionally consistent with the Fabory product. The relationship remains `unreviewed` and the NSN remains `unverified` because the exact NMCRL record has not been accessed.

NATO identifies NMCRL as its current approved catalogue, but detailed access is subscription-controlled. UPN must not promote this lead to an accepted crosswalk until that record, or an equivalent issuing-authority record from the responsible National Codification Bureau, is obtained.
