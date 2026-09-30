# Straight steel wire-mesh basket tray identity profile

Status: draft pilot profile 0.1. It defines identity fields and has a conservative candidate-screening algorithm; it does not declare two products equivalent.

## Scope

Included: one-piece, straight, rigid, welded-steel wire-mesh basket tray sections.

Excluded: bends, tees, risers, reducers, supports, covers, splice kits, solid or perforated sheet tray, cable ladder, non-steel tray, field-formed assemblies, and complete installed systems.

## Why this is a separate profile

Wire-mesh tray is not a lighter-looking cable ladder. Its load-bearing geometry, joining construction, fittings, and usable envelope depend on distinct cross, top-edge, and other longitudinal wire diameters plus grid dimensions rather than ladder side rails and rungs. Reusing the ladder profile—or flattening all wire sizes into one number—would conceal the exact facts needed to distinguish two sellable sections.

## Identity-defining evidence

The fifteen required fields are product form, nominal width, overall width, nominal height, overall height, section length, base material, surface protection, cross-wire diameter, top longitudinal wire diameter, other longitudinal wire diameter, longitudinal and transverse mesh spacing, wire-joint construction, and whether connection hardware is included. Nominal size preserves the market and fitting class; overall size preserves the real installed envelope. Material grade, contextual load rating, and certifications are conditional when declared. Mass, unambiguous usable area, and application guidance remain descriptive.

Numeric values retain the source unit. Completeness auditing converts values to each unit's common base and surfaces cross-source differences greater than 0.1 percent. Screening 0.1 blocks only on compatible form and coarse steel material, then reports all remaining required-property differences. It deliberately cannot approve equivalence; candidate-grade numeric comparison still requires a versioned precision and unit-conversion policy.

## Eaton pilot record

The official Eaton exact-SKU page identifies `FT6X18X10 BLE`, UPC `662516721871`, as a black-powder-coated steel B-Line Flextray 6-inch-deep straight section. Its name and catalogue number establish the nominal 6-by-18-inch class; it states 118.312-inch length/depth, 6.38-inch overall height, 18-inch overall width, 25.06-pound weight, CE, CSA, and UL Classified certifications, and controlled-interior guidance. The official Flextray family page states a T-weld safety edge.

Those sources do not state the exact SKU's three wire diameters, longitudinal grid spacing, transverse grid spacing, load context, or splice inclusion. The record therefore has nine of fifteen required identity properties and remains `unreviewed`. Family claims are stored in their own observation and are not silently promoted to exact-SKU facts beyond the named family construction statement.

The exact page renders `107.3" actual area` without an unambiguous squared unit in the accessible text. The registry preserves no normalized usable-area value from that string.

The UPC is valid under GS1 Mod-10, but the official page does not establish whether it identifies one section or another packaging level. It is therefore attached to the supplier offer with `unknown` scope, never to the physical part record.

## Legrand pilot record

The official Legrand North America page identifies `CF150/450BL`, UPC `800388009257`, as a black painted carbon-steel straight Cablofil section. The title, selectors, and tray-height field establish its nominal 6-by-18-inch class; the page separately states 17.71-inch overall width, 6.53-inch product height, 118.2-inch length, 27.101-pound mass, a two-inch-wide by four-inch-long mesh, UL Classified status, and commercial/industrial application. Manufacturer technical support on the same page states 5.9 mm for the cross and top longitudinal wires, 3.9 mm for the other longitudinal wires, and that factory-painted mesh tray is powder coated over plain steel.

The retained one-page CF150 drawing independently states 450 mm width, 158 mm height, 3000 mm length, 27.10-pound mass, black painted finish, and a top-wave safety edge. Its 158 mm height conflicts materially with the exact page's 6.53 inches (165.862 mm). UPN stores both statements, surfaces `Overall height` as a source conflict, and does not choose one silently. Splice inclusion remains unknown, leaving the record at fourteen of fifteen required fields.

The two articles match on nominal width, nominal height, and black powder-coat finish. The exact Eaton/Legrand pair is nevertheless a `hard_conflict`: the accessible evidence differs on overall width, overall height, length, and safety-edge construction, while Eaton still lacks its wire and mesh geometry. Matching nominal labels such as “6 × 18 × 10” therefore do not prove identity.

## Hard stops before equivalence review

- Resolve Eaton's six missing required properties and Legrand's missing splice-inclusion evidence.
- Resolve Legrand's conflicting official height statements or obtain an authoritative revision decision.
- Define and test candidate-grade numeric precision and unit conversion before any positive match.
- Obtain independent review of each observation before any equivalence decision.

Until those conditions are met, this profile can support capture, completeness auditing, and negative screening only. It cannot issue a UPN.
