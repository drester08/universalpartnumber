# Straight steel wire-mesh basket tray identity profile

Status: draft pilot profile 0.1. It defines identity fields; it does not declare two products equivalent and has no candidate-screening algorithm yet.

## Scope

Included: one-piece, straight, rigid, welded-steel wire-mesh basket tray sections.

Excluded: bends, tees, risers, reducers, supports, covers, splice kits, solid or perforated sheet tray, cable ladder, non-steel tray, field-formed assemblies, and complete installed systems.

## Why this is a separate profile

Wire-mesh tray is not a lighter-looking cable ladder. Its load-bearing geometry, joining construction, fittings, and usable envelope depend on wire diameter and grid dimensions rather than ladder side rails and rungs. Reusing the ladder profile would conceal the exact facts needed to distinguish two sellable sections.

## Identity-defining evidence

The required fields are product form, overall width, overall height, section length, base material, surface protection, primary wire diameter, longitudinal and transverse mesh spacing, wire-joint construction, and whether connection hardware is included. Material grade, contextual load rating, and certifications are conditional when declared. Mass, unambiguous usable area, and application guidance remain descriptive.

Numeric values retain the source unit. A later comparison must convert compatible units before equality testing; the current absence of a wire-mesh screening algorithm prevents accidental comparison on raw numbers alone.

## Eaton pilot record

The official Eaton exact-SKU page identifies `FT6X18X10 BLE`, UPC `662516721871`, as a black-powder-coated steel B-Line Flextray 6-inch-deep straight section. It states 118.312-inch length/depth, 6.38-inch height, 18-inch width, 25.06-pound weight, CE, CSA, and UL Classified certifications, and controlled-interior guidance. The official Flextray family page states a T-weld safety edge.

Those sources do not state the exact SKU's wire diameter, longitudinal grid spacing, transverse grid spacing, load context, or splice inclusion. The record therefore has seven of eleven required identity properties and remains `unreviewed`. Family claims are stored in their own observation and are not silently promoted to exact-SKU facts beyond the named family construction statement.

The exact page renders `107.3" actual area` without an unambiguous squared unit in the accessible text. The registry preserves no normalized usable-area value from that string.

The UPC is valid under GS1 Mod-10, but the official page does not establish whether it identifies one section or another packaging level. It is therefore attached to the supplier offer with `unknown` scope, never to the physical part record.

## Hard stops before comparison

- Add a second independently evidenced manufacturer part in the same profile.
- Resolve or explicitly retain the four missing required properties for each part.
- Define and test unit conversion before numeric matching across inch and metric sources.
- Version a profile-specific blocking and comparison algorithm.
- Obtain independent review of each observation before any equivalence decision.

Until those conditions are met, this profile can support capture and completeness auditing only. It cannot issue a UPN.
