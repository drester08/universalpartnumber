"""Registered source-use state is a publication prerequisite, not legal advice."""


def part_holds(connection):
    holds = {}
    for row in connection.execute(
        "SELECT DISTINCT o.manufacturer_part_id,s.source_id,s.license_state,s.ingestion_status "
        "FROM observations o JOIN sources s ON s.source_id=o.source_id "
        "WHERE o.review_state NOT IN ('rejected','superseded') "
        "AND (s.ingestion_status!='license_verified' OR s.license_state NOT IN ('open','attribution')) "
        "ORDER BY o.manufacturer_part_id,s.source_id"
    ):
        holds.setdefault(row[0], []).append(dict(source_id=row[1], license_state=row[2], ingestion_status=row[3]))
    return holds
