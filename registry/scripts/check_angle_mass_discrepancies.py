"""Audit displayed mass disagreements, preserving grain and conditional rounding."""
import argparse
import hashlib
import json
import re
from collections import Counter
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from check_orangebook_equal_angles import build_report as reproduce_parent
from check_macsteel_angle_datasheet import extract_pdf, SHA as SELLER_PDF_SHA

ROOT = Path(__file__).resolve().parents[2]
PARENT = ROOT / 'registry/reports/orangebook-equal-angle-screening.json'
PARENT_SHA = 'A0060C4F4B1FCFA406EBEC4A2601FF1F8ED8EC58B81B63B31CA9C1F204764801'


def rounding_audit(seller, manufacturer):
    if not all(re.fullmatch(r'\d+(?:\.\d+)?', v) for v in (seller, manufacturer)):
        raise ValueError('Mass must retain a positive plain-decimal displayed value')
    a, b = Decimal(seller), Decimal(manufacturer)
    if a <= 0 or b <= 0:
        raise ValueError('Mass must be positive')
    seller_step = Decimal(1).scaleb(a.as_tuple().exponent)
    manufacturer_step = Decimal(1).scaleb(b.as_tuple().exponent)
    a_low, a_high = a - seller_step / 2, a + seller_step / 2
    b_low, b_high = b - manufacturer_step / 2, b + manufacturer_step / 2
    # Closed intervals conservatively retain boundary-touching hypotheses.
    overlap = max(a_low, b_low) <= min(a_high, b_high)
    status = ('exact_displayed_agreement' if a == b else
              'nearest_rounding_hypothesis_not_excluded' if overlap else
              'not_explained_by_displayed_nearest_rounding')
    return {'seller_mass_kg_per_m': seller, 'manufacturer_mass_kg_per_m': manufacturer,
            'signed_manufacturer_minus_seller_kg_per_m': str(b - a),
            'absolute_difference_kg_per_m': str(abs(b - a)),
            'seller_nearest_rounding_interval_kg_per_m': [str(a_low), str(a_high)],
            'manufacturer_nearest_rounding_interval_kg_per_m': [str(b_low), str(b_high)],
            'intervals_overlap': overlap,
            'seller_value_rounds_to_manufacturer_display': a.quantize(manufacturer_step, rounding=ROUND_HALF_UP) == b,
            'outcome': status, 'rounding_convention_source_verified': False,
            'physical_conflict_verified': False, 'identity_approved': False}


def audit(parent):
    groups, missing = {}, []
    seen = set()
    for index, record in enumerate(parent['records']):
        sku = record['seller_sku']
        if sku in seen:
            raise ValueError('Duplicate seller offer; do not inflate counts')
        seen.add(sku)
        candidates = record['manufacturer_catalogue_candidates']
        comparisons = record['seller_table_mass_comparisons']
        if len(candidates) > 1 or len(comparisons) > 1:
            raise ValueError('Ambiguous comparison grain')
        if not comparisons:
            missing.append({'seller_sku': sku, 'parent_record_locator': f'/records/{index}',
                            'reason': 'no_manufacturer_geometry_candidate' if not candidates else
                                      'no_same_context_seller_pdf_mass'})
            continue
        comparison = comparisons[0]
        if len(candidates) != 1 or comparison['seller_pdf_table'] not in (1, 2):
            raise ValueError('Missing candidate or unknown material context')
        candidate = candidates[0]
        if comparison['manufacturer_mass_kg_per_m'] != candidate['mass_kg_per_m']:
            raise ValueError('Comparison mass detached from source candidate')
        k = tuple(Decimal(v) for v in record['nominal_geometry_mm']) + (comparison['seller_pdf_table'],)
        result = rounding_audit(comparison['seller_mass_kg_per_m'], comparison['manufacturer_mass_kg_per_m'])
        group = {'nominal_geometry_mm': [format(v.normalize(), 'f') for v in k[:3]],
                 'seller_pdf_table': k[3],
                 'seller_material_context': 'Mild steel (commercial quality)' if k[3] == 1 else 'S355JR',
                 'manufacturer_material_context': candidate['source_grade_context'],
                 'material_context_equivalence_verified': False,
                 'manufacturer_source_locator': {'html_table': candidate['html_table'],
                     'html_data_row': candidate['html_data_row'], 'mass_column': 4},
                 'comparison': result, 'affected_seller_skus': [], 'parent_record_locators': []}
        if k in groups and any(groups[k][field] != group[field] for field in group
                               if field not in ('affected_seller_skus', 'parent_record_locators')):
            raise ValueError('Inconsistent values for a distinct section/context pair')
        groups.setdefault(k, group)
        groups[k]['affected_seller_skus'].append(sku)
        groups[k]['parent_record_locators'].append(f'/records/{index}')
    records = [groups[k] for k in sorted(groups)]
    counts = dict(Counter(r['comparison']['outcome'] for r in records))
    weighted = Counter()
    for r in records:
        weighted[r['comparison']['outcome']] += len(r['affected_seller_skus'])
    return {'report_date': '2026-10-01', 'supplier_offer_count': len(seen),
            'distinct_section_context_comparisons': len(records),
            'compared_offer_count': sum(weighted.values()), 'uncompared_offer_count': len(missing),
            'section_context_outcomes': counts, 'offer_outcomes': dict(weighted),
            'records': records, 'uncompared_offers': missing,
            'assumption': 'Conditional diagnostic: both publishers round to nearest at their displayed decimal precision. This convention is not source-confirmed.',
            'limitations': ['Closed intervals conservatively include boundary ties; this is not a manufacturing tolerance.',
                'Same geometry is not exact article identity or material-context equivalence.',
                'Two publisher values may derive from different section geometry, tabulation methods or upstream sources.',
                'The seller sheet does not publish root/toe radii; differing radii cannot be checked against the manufacturer table.',
                'No source value is replaced and no discrepancy is physically adjudicated.',
                'Parent extraction fidelity remains independently unreviewed.'],
            'identity_approved': False}


def build_report():
    raw = PARENT.read_bytes()
    if hashlib.sha256(raw).hexdigest().upper() != PARENT_SHA:
        raise ValueError('Parent mass-comparison revision changed')
    parent = json.loads(raw)
    if reproduce_parent() != parent:
        raise ValueError('Parent screening does not reproduce source custody')
    pdf = ROOT / 'registry/artifacts/macsteel/AE_S355RA_0061.pdf'
    if hashlib.sha256(pdf.read_bytes()).hexdigest().upper() != SELLER_PDF_SHA:
        raise ValueError('Seller PDF revision changed')
    retained = json.loads((ROOT / 'registry/reports/macsteel-angle-datasheet.json').read_text(encoding='utf-8'))
    facts = extract_pdf(pdf)
    if facts != retained['table_facts']:
        raise ValueError('Seller PDF facts do not reproduce')
    result = audit(parent)
    result['parent_report_sha256'] = PARENT_SHA
    result['seller_pdf_sha256'] = SELLER_PDF_SHA
    result['seller_pdf_facts_reproduced'] = len(facts)
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--write-snapshot', action='store_true')
    args = p.parse_args()
    report = build_report()
    path = ROOT / 'registry/reports/angle-mass-discrepancies.json'
    if args.write_snapshot:
        path.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    elif json.loads(path.read_text(encoding='utf-8')) != report:
        raise ValueError('Mass audit report stale or altered')
    print(f"{report['distinct_section_context_comparisons']} distinct comparisons across {report['compared_offer_count']} offers: {report['section_context_outcomes']}. No physical conflict or identity approved.")
