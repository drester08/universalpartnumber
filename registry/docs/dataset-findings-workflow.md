# Source-dataset findings workflow

Source-dataset findings are reproducible research tasks, not manufacturer-part observations or approval decisions. This keeps errors in bulk catalogues visible before identity ingestion and supports later source revisions without altering originals.

## Evidence chain

Registered dataset checksum and source-artifact checksum identify the inputs. A checksummed comparison report identifies a result snapshot. JSON pointers identify the relevant cases within it. `dataset_findings` groups actionable issues; `dataset_finding_rows` links each group to logical CSV record numbers including the header as line 1. These are CSV logical records, not necessarily physical text lines when a quoted cell contains a newline.

Stable finding IDs derive from dataset ID, issue type and subject key. Report digests change when result bytes change, but IDs remain stable for an unchanged issue/subject. This is a current unresolved snapshot, not an append-only revision-history or resolved-review ledger. Preserve earlier snapshots in the project archive. Do not edit a derived finding to assert resolution.

## Current research backlog

The three gasket reports produce 66 groups: 41 P0 conflict/key/duplicate tasks and 25 P2 source-coverage tasks. Their 1,003 row references cover 52 dimension discrepancies, 949 unsupported-key records and the two Envelope duplicate rows. Coverage gaps have no fabricated supplied-row references. Every affected row is retained once per finding; no source record is removed or repaired by generation.

The pipe report adds seven groups: one P0 construction-conflict task covering all 50 rows, one P0 source-ambiguity task covering four DN65 rows, and five P2 coverage tasks covering twelve DN6/8/10/80/90 rows. These contribute 66 row links because 16 rows have more than one issue. The combined snapshot contains 73 groups, 1,069 links and 1,053 distinct dataset/row pairs. Row numbers must always be scoped by dataset; identical row numbers in different files are not duplicates.

The plate report adds eight groups: three P0 material-interpretation tasks (51rows), three P0 mass-discrepancy tasks (three rows), one P2 family-scope task (76rows) and one P0 exact-article evidence task covering all395rows. Its525links overlap because specific issues coexist with the shared article-evidence gap. Supported family wording does not remove the latter task.

The structural report adds three groups: one P0 exact-article evidence task covering all805 rows, one P2 selected-source coverage task covering793 untested rows, and one P0 dimension/field-meaning conflict task covering six IPE-AA rows. Its1604links overlap by design. A list of untested row locators proves accounting only, not manufacturer comparison. Report/source-transcription hashes bind the manual source snapshot; independent fidelity review remains outstanding.

The current combined snapshot contains84groups,3198links and2253distinct dataset/row pairs. The main reviewer queue contains253tasks, including these84. Existing11complete-part tasks retain their blocked dependencies. Each finding links to its report and source artifact rather than becoming a guessed part number. Other dataset issues, missing gasket construction/material/drilling evidence and external-source licensing remain separate outstanding work. These tasks are not an exhaustive catalogue of import prerequisites. Earlier232/233/240/242/250-task snapshots are historical, not current status.

## Resolve issues

1. Follow the finding's report pointers and raw CSV line references.
2. Obtain the exact drawing, specification or governed class evidence. Check source edition and applicability to the stated material/construction.
3. Keep proposed corrections or exclusions separate from original values. Unsupported keys are not automatically invalid, and equal diameters do not determine the intended class.
4. Record independent review and revision provenance before regenerating a comparison from a separately retained revised input. The current generator is scoped to the supplied revision; do not bypass its row-count guards to force a new file through.
5. Regenerate findings and review queue from current evidence. Only afterward consider article-level ingestion through the existing part-review and issuance workflow.

There is no implemented dataset-correction approval ledger yet. A correction note or completion of a queue task cannot make the dataset identity evidence. Independent correction governance, exact article provenance and unresolved construction fields remain required work.

## Checks

```powershell
python registry/scripts/build_dataset_findings.py --check
python registry/scripts/validate_registry.py
python registry/scripts/build_registry.py
python registry/scripts/build_review_queue.py --check
python registry/scripts/test_dataset_findings.py
python registry/scripts/test_quality_gates.py
```

To deliberately update snapshots after verified report changes, run the findings script with `--write-snapshot`, rebuild the database, then run the queue script with `--write-snapshot`. Review the diff. No raw input is changed by these commands.

Registry validation reproduces the findings and rejects modified snapshots, wrong report input digests and unsafe dataset promotion. Database constraints reject invalid priorities, noninteger/out-of-range CSV locators, finding/source digest mismatches, and dataset promotion or revision changes that invalidate active findings. Tests exercise both seed and database failure paths. These checks preserve evidence consistency; they do not independently prove every manufacturer statement.
