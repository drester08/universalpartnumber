"""Report unusable active numeric evidence without filling values or units."""
import argparse
import json
import sqlite3
from pathlib import Path
import numeric_rules

ROOT = Path(__file__).resolve().parents[1]
VERSION = 'numeric-evidence-gaps-0.1'


def build_report(connection):
    connection.row_factory = sqlite3.Row
    records = connection.execute('''
        SELECT sv.specification_id, sv.property_id, sv.raw_value,
               sv.normalized_number, sv.unit_id, sv.qualifier,
               o.observation_id, o.manufacturer_part_id, o.source_id,
               o.source_locator, o.raw_payload_sha256,
               u.quantity_kind, u.conversion_factor, u.conversion_offset
        FROM specification_values sv
        JOIN observations o ON o.observation_id=sv.observation_id
        LEFT JOIN units u ON u.unit_id=sv.unit_id
        WHERE o.review_state NOT IN ('rejected','superseded')
          AND sv.normalized_number IS NOT NULL
        ORDER BY sv.specification_id
    ''').fetchall()
    issues = []
    for row in records:
        if numeric_rules.to_base_value(row) is not None:
            continue
        missing = [key for key in ('unit_id','quantity_kind','conversion_factor','conversion_offset')
                   if row[key] is None or not str(row[key]).strip()]
        artifact_states = sorted({r[0] for r in connection.execute(
            'SELECT retrieval_state FROM source_artifacts WHERE source_id=?', (row['source_id'],))})
        issue = dict(row)
        issue.update(issue_id='NUMERIC-GAP-' + row['specification_id'],
                     missing_metadata=missing,
                     issue_type='missing_conversion_metadata' if missing else 'invalid_conversion_metadata',
                     registered_source_artifact_states=artifact_states,
                     observation_declares_source_hash=bool(row['raw_payload_sha256']),
                     status='needs_source_and_normalization_review',
                     next_action='Verify source revision, counted object/quantity scope and explicit unit/conversion metadata. Preserve raw values and qualifiers; do not infer package inclusion or fill a default unit.',
                     identity_approved=False, reuse_permission=False)
        issues.append(issue)
    return dict(policy_version=VERSION, scope='active_numeric_evidence_diagnostics',
                active_normalized_numeric_records=len(records),
                usable_explicit_conversion_records=len(records)-len(issues),
                issue_count=len(issues), issues=issues, database_mutated=False,
                source_truth_verified=False, identity_approved=False,
                application_suitability_approved=False, production_upn_allowed=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', type=Path, default=ROOT/'build/registry.sqlite')
    parser.add_argument('--write-snapshot', action='store_true')
    args = parser.parse_args()
    with sqlite3.connect(args.database.resolve().as_uri()+'?mode=ro', uri=True) as connection:
        report = build_report(connection)
    path = ROOT/'reports/numeric-evidence-gaps.json'
    if args.write_snapshot:
        path.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    elif json.loads(path.read_text(encoding='utf-8')) != report:
        raise ValueError('Numeric evidence gap snapshot is stale or altered')
    print(f"Numeric evidence gaps: {report['issue_count']}; no values, source bindings or approvals changed.")


if __name__ == '__main__':
    main()
