"""Source-use state plus evidence-bound authorization, not legal advice."""
from datetime import date
import source_use_decisions as decisions


def part_holds(connection, ledger=None, as_of=None):
    ledger = decisions.load() if ledger is None else ledger
    decisions.validate(ledger)
    as_of = as_of or date.today().isoformat()
    decisions.day(as_of)
    holds = {}
    for row in connection.execute(
        "SELECT DISTINCT o.manufacturer_part_id,s.source_id,s.license_state,s.ingestion_status,s.source_url,o.raw_payload_sha256 "
        "FROM observations o JOIN sources s ON s.source_id=o.source_id "
        "WHERE o.review_state NOT IN ('rejected','superseded') "
        "ORDER BY o.manufacturer_part_id,s.source_id"
    ):
        if row[3] != 'license_verified' or row[2] not in ('open', 'attribution'):
            reason = 'registered reuse metadata is unresolved'
        elif row[2] == 'attribution':
            reason = 'attribution license fulfillment is not implemented'
        else:
            reason = decisions.hold_reason(connection, row[1], row[4], row[5], ledger, as_of)
        if reason:
            entry = dict(source_id=row[1], license_state=row[2], ingestion_status=row[3], reason=reason)
            if entry not in holds.setdefault(row[0], []):
                holds[row[0]].append(entry)
    return holds
