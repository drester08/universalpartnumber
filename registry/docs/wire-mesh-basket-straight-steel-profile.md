# Straight steel wire-mesh basket tray identity profile

Status: draft pilot profile 0.1. It defines identity fields and has a conservative candidate-screening algorithm; it does not declare two products equivalent.

## Scope

Included: one-piece, straight, rigid, welded-steel wire-mesh basket tray sections.

Excluded: bends, tees, risers, reducers, supports, covers, splice kits, solid or perforated sheet tray, cable ladder, non-steel tray, field-formed assemblies, and complete installed systems.

## Why this is a separate profile

Wire-mesh tray is not a lighter-looking cable ladder. Its load-bearing geometry, joining construction, fittings, and usable envelope depend on distinct cross, top-edge, and other longitudinal wire diameters plus grid dimensions rather than ladder side rails and rungs. Reusing the ladder profile—or flattening all wire sizes into one number—would conceal the exact facts needed to distinguish two sellable sections.

## Identity-defining evidence

The fifteen required fields are product form, nominal width, overall width, nominal height, overall height, section length, base material, surface protection, cross-wire diameter, top longitudinal wire diameter, other longitudinal wire diameter, longitudinal and transverse mesh spacing, wire-joint construction, and whether connection hardware is included. Nominal size preserves the market and fitting class; overall size preserves the real installed envelope. Material grade, contextual load rating, and certifications are conditional when declared. Mass, unambiguous usable area, and application guidance remain descriptive.

Numeric values retain the source unit. Completeness auditing and screening convert them through governed unit factors and property-specific rules. Nominal market classes allow metric-inch naming differences up to two percent, while actual envelope, length, wire, and mesh geometry use much tighter representation limits. These are comparison rules, not manufacturing tolerances. Screening 0.2 blocks only on compatible form and coarse steel material, then reports all remaining required-property differences. It deliberately cannot approve equivalence.

## Eaton pilot record

The official Eaton exact-SKU page identifies `FT6X18X10 BLE`, UPC `662516721871`, as a black-powder-coated steel B-Line Flextray 6-inch-deep straight section. Its name and catalogue number establish the nominal 6-by-18-inch class; it states 118.312-inch length/depth, 6.38-inch overall height, 18-inch overall width, 25.06-pound weight, CE, CSA, and UL Classified certifications, and controlled-interior guidance. The official Flextray family page states a T-weld safety edge. Additional official catalog, specification, performance-paper, load-fill, and drawing evidence is stored as separate observations.

The catalog and Section 16135 specification state a minimum wire diameter of 0.196 inches (5 mm). That lower bound does not establish the exact cross, top-longitudinal, or other-longitudinal wire diameter, so it is stored as a descriptive property and cannot satisfy any of those three required fields. The drawing states a standard 2-inch by 4-inch welded mesh, but the accessible evidence does not safely assign the two numbers to UPN's along-length and across-width fields. Both directional spacing fields therefore remain unknown.

The exact page's accessible text renders `107.3" actual area` ambiguously. A separate official Eaton load-fill table resolves the same FT6X18 value as 107.3 square inches, so the normalized area is sourced to that table rather than inferred from the page. Official performance material also records six-inch load depth and span-specific ratings. It states that four splices are required for UL Classification, but that installation requirement is not evidence that four splices are included with the sold section. `Splice hardware included` remains unknown.

The exact page states a 118.312-inch section while the official catalog states three metres. Those values differ by 5.1248 mm, beyond the governed three-millimetre representation allowance, so `Length` is an explicit internal source conflict. The record therefore still has nine of fifteen required identity properties and remains `unreviewed`. The extra evidence improves engineering context without manufacturing false completeness. Family claims remain in their own observations and are not silently promoted to exact-SKU facts.

The UPC is valid under GS1 Mod-10, but the official page does not establish whether it identifies one section or another packaging level. It is therefore attached to the supplier offer with `unknown` scope, never to the physical part record.

## Legrand pilot record

The official Legrand North America page identifies `CF150/450BL`, UPC `800388009257`, as a black painted carbon-steel straight Cablofil section. The title, selectors, and tray-height field establish its nominal 6-by-18-inch class; the page separately states 17.71-inch overall width, 6.53-inch product height, 118.2-inch length, 27.101-pound mass, a two-inch-wide by four-inch-long mesh, UL Classified status, and commercial/industrial application. Manufacturer technical support on the same page states 5.9 mm for the cross and top longitudinal wires, 3.9 mm for the other longitudinal wires, and that factory-painted mesh tray is powder coated over plain steel. The official technical guide adds a 103.23-square-inch fill area and load ratings of 175.9, 155.0, 113.9, and 98.3 pounds per foot at five-, six-, seven-, and eight-foot spans.

The retained one-page CF150 drawing independently states 450 mm width, 158 mm / 6.22-inch height, 3000 mm length, 27.10-pound mass, black painted finish, and a top-wave safety edge. Its height conflicts materially with the exact page's 6.53 inches (165.862 mm). UPN stores both statements, surfaces `Overall height` as a source conflict, and does not choose one silently. The installation guide calls for four EDRN splices or four SWK sets for a 450 mm CF150 joint, but required installation quantity is not proof that those accessories ship with the section. Splice inclusion therefore remains unknown, leaving the record at fourteen of fifteen required fields.

The two articles match on nominal width, nominal height, and black powder-coat finish. The exact Eaton/Legrand pair is nevertheless a `hard_conflict`: the accessible evidence differs on overall width, overall height, length, and safety-edge construction, while Eaton still lacks its wire and mesh geometry. Matching nominal labels such as “6 × 18 × 10” therefore do not prove identity.

## Hard stops before equivalence review

- Resolve Eaton's three exact wire diameters, two directional mesh spacings, and splice-inclusion evidence; also resolve Legrand's missing splice-inclusion evidence.
- Resolve Legrand's conflicting official height statements or obtain an authoritative revision decision.
- Obtain independent engineering review of the versioned numeric comparison rules before any positive match.
- Obtain independent review of each observation before any equivalence decision.

Until those conditions are met, this profile can support capture, completeness auditing, and negative screening only. It cannot issue a UPN.
