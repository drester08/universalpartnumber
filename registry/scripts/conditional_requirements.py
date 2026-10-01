"""Fail closed on conditional profile fields without governed predicates.

The current SQL schema stores the label 'conditional', but not an applicability
predicate or its review decision. Populated values and blank values therefore
cannot establish applicability. This guard is not a predicate implementation.
"""
from collections import defaultdict


def unresolved_profiles(connection):
    result = defaultdict(list)
    for row in connection.execute(
        "SELECT ipp.profile_id, ipp.property_id, p.preferred_label "
        "FROM identity_profile_properties ipp JOIN properties p "
        "ON p.property_id=ipp.property_id WHERE ipp.requirement='conditional' "
        "ORDER BY ipp.profile_id, ipp.sequence_number, ipp.property_id"
    ):
        result[row[0]].append((row[1], row[2]))
    return dict(result)


def unresolved_parts(connection):
    profiles = unresolved_profiles(connection)
    return {row[0]: profiles[row[1]] for row in connection.execute(
        'SELECT manufacturer_part_id, profile_id FROM manufacturer_parts ORDER BY manufacturer_part_id'
    ) if row[1] in profiles}
