"""Derive actionable supplier research findings, never approval decisions."""
import argparse
import hashlib
import json
import sqlite3
from collections import Counter
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUTS = {
    'macsteel-angle-coverage.json': 'B9BB5AA678DA1307680FEAB93294AF6C5203CD34B701311DC611F6C5A06003BA',
    'angle-mass-discrepancies.json': '9C944525325D93AFF3A8B9BAC91DDCEFE5A782E99ABB60A8B1E536A7A905A2A7',
}


def load_report(name):
    raw = (ROOT / 'reports' / name).read_bytes()
    if hashlib.sha256(raw).hexdigest().upper() != INPUTS[name]:
        raise ValueError('Supplier research input revision changed: ' + name)
    return json.loads(raw)


def finding_id(issue, subject):
    subject = dict(subject)
    if 'nominal_geometry_mm' in subject:
        subject['nominal_geometry_mm'] = [format(Decimal(v).normalize(), 'f') for v in subject['nominal_geometry_mm']]
    raw = json.dumps([issue, subject], separators=(',', ':'), sort_keys=True)
    return 'SRF-' + hashlib.sha256(raw.encode()).hexdigest()[:24].upper()


def derive(connection, coverage, mass):
    connection.row_factory = sqlite3.Row
    offers = {}
    for row in connection.execute('SELECT supplier_offer_id, source_id, seller_sku FROM supplier_offers WHERE supplier_id=?', ('ORG-MACSTEEL-SA',)):
        if row['seller_sku'] in offers:
            raise ValueError('Ambiguous supplier SKU')
        offers[row['seller_sku']] = dict(row)
    sources = {row[0] for row in connection.execute('SELECT source_id FROM sources')}
    findings = []

    def related(skus):
        if not skus or len(skus) != len(set(skus)) or any(s not in offers for s in skus):
            raise ValueError('Missing or duplicate finding-to-offer references')
        return [offers[s] for s in sorted(skus)]

    def append(issue, subject, skus, source_ids, name, pointer, summary, action):
        if any(s not in sources for s in source_ids):
            raise ValueError('Missing finding source')
        findings.append({'finding_id': finding_id(issue, subject), 'issue_type': issue,
            'priority': 'P2', 'review_state': 'open_research', 'subject_key': subject,
            'related_offers': related(skus), 'source_ids': sorted(set(source_ids)),
            'evidence_path': 'registry/reports/' + name, 'evidence_sha256': INPUTS[name],
            'evidence_pointer': pointer, 'summary': summary, 'next_action': action,
            'policy_version': 'supplier-research-0.1', 'identity_approved': False})

    seen = set()
    coverage_by_sku = {}
    for index, record in enumerate(coverage['records']):
        sku = record['seller_sku']
        if sku in seen or sku not in offers or offers[sku]['source_id'] != record['source_id']:
            raise ValueError('Coverage offer identity/source is missing or ambiguous')
        seen.add(sku)
        coverage_by_sku[sku] = record
        if record['outcome'] != 'source_context_gap':
            continue
        if record['same_context_candidates'] or record['identity_approved'] is not False:
            raise ValueError('Gap evidence is contradictory or promoted')
        append('material_context_gap', {'seller_sku': sku}, [sku], [record['source_id'], 'SRC-MACSTEEL-AE0061-PDF'],
            'macsteel-angle-coverage.json', f'/records/{index}',
            f'{sku}: no nominal row in the selected seller sheet under its declared material context.',
            'Obtain exact grade and delivery-condition evidence for seller stock; geometry in a CQ or generic S355 table does not close S355JR+AR. Do not infer global unavailability, approve substitution or issue a UPN.')
    for index, record in enumerate(mass['records']):
        c = record['comparison']
        if c['outcome'] != 'not_explained_by_displayed_nearest_rounding':
            continue
        if c['intervals_overlap'] or c['physical_conflict_verified'] is not False or c['identity_approved'] is not False:
            raise ValueError('Publication discrepancy was improperly adjudicated')
        subject = {'nominal_geometry_mm': record['nominal_geometry_mm'], 'seller_pdf_table': record['seller_pdf_table']}
        skus = record['affected_seller_skus']
        for sku in skus:
            source = coverage_by_sku.get(sku)
            if source is None or tuple(map(Decimal, source['nominal_geometry_mm'])) != tuple(map(Decimal, record['nominal_geometry_mm'])):
                raise ValueError('Mass finding detached from affected offer geometry')
            table = 1 if sku.startswith('AE_CQ_') else 2 if sku.startswith('AE_S355RA_') else None
            if table != record['seller_pdf_table']:
                raise ValueError('Mass finding detached from seller material context')
        append('published_mass_discrepancy', subject, skus,
            ['SRC-AM-ORANGEBOOK-EQUAL-ANGLES', 'SRC-MACSTEEL-AE0061-PDF'],
            'angle-mass-discrepancies.json', f'/records/{index}',
            f"{' x '.join(record['nominal_geometry_mm'])} mm: seller {c['seller_mass_kg_per_m']} versus manufacturer-table {c['manufacturer_mass_kg_per_m']} kg/m; {len(skus)} offers. Displayed nearest-rounding hypothesis does not explain the difference.",
            'Review source section drawings, radii, mass definitions, rounding policy and material contexts. Keep both values; do not classify a physical conflict, auto-correct data or approve identical-item equivalence from this diagnostic.')
    identifiers = [f['finding_id'] for f in findings]
    if len(set(identifiers)) != len(identifiers):
        raise ValueError('Duplicate supplier research finding')
    if len(seen) != 136 or len(findings) != 14:
        raise ValueError('Research finding scope changed; review inputs before replacing tasks')
    if Counter(f['issue_type'] for f in findings) != {'material_context_gap': 10, 'published_mass_discrepancy': 4}:
        raise ValueError('Research finding category scope changed')
    return sorted(findings, key=lambda f: f['finding_id'])


def build_report(connection):
    coverage, mass = (load_report(n) for n in INPUTS)
    findings = derive(connection, coverage, mass)
    return {'policy_version': 'supplier-research-0.1', 'input_report_hashes': INPUTS,
            'finding_count': len(findings), 'findings': findings,
            'limitations': ['Derived research tasks, not adjudicated article findings or equivalence decisions.',
                'Input hashes bind retained reports; this adapter does not independently validate extraction fidelity.',
                'Findings do not disappear merely because a manufacturer link is assigned.',
                'Input revision changes fail closed and require deliberate evidence and task reconciliation.'],
            'identity_approved': False}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--write-snapshot', action='store_true')
    args = p.parse_args()
    db = sqlite3.connect(ROOT / 'build/registry.sqlite')
    try:
        report = build_report(db)
    finally:
        db.close()
    path = ROOT / 'reports/supplier-research-findings.json'
    if args.write_snapshot:
        path.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    elif json.loads(path.read_text(encoding='utf-8')) != report:
        raise ValueError('Supplier research findings snapshot stale or altered')
    print('14 open supplier research findings: 10 material-context gaps and 4 published-mass discrepancies. No approval.')
