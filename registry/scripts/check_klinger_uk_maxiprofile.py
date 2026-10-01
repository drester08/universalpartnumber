"""Reproduce bounded UK/SA family-context differences; never article approval."""
import hashlib
import json
import re
from pathlib import Path
import pdfplumber

ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / 'artifacts/klinger/Maxiprofile-UK-issue01-20190828-captured20261001.pdf'
PDF_SHA = 'D769825A67D89D12E3F3C929D506D31E15F51C175F38B440FA6B1F546A6418E5'
SA = ROOT / 'reports/klinger-maxiprofile-context.json'
SA_SHA = 'B6FD9F86173A4131B1C8FDF64B5A9EE2002DDA6C74D1B1D19CD03F479876F27D'
REPORT = ROOT / 'reports/klinger-uk-maxiprofile.json'
# Explicit research-label correspondences, not approved ontology mappings.
LABEL_PAIRS = [('Stainless Steel 316L', '316L Stainless Steel'),
               ('Stainless Steel 304', '304 Stainless Steel'),
               ('Stainless Steel 347', '347 Stainless Steel'),
               ('Stainless Steel 321', '321 Stainless Steel')]


def build_report(pdf=PDF, sa_path=SA):
    for path, expected in ((pdf, PDF_SHA), (sa_path, SA_SHA)):
        if hashlib.sha256(path.read_bytes()).hexdigest().upper() != expected:
            raise ValueError('Bound evidence revision changed')
    with pdfplumber.open(pdf) as document:
        if len(document.pages) != 3:
            raise ValueError('Expected three complete pages')
        texts = [p.extract_text() for p in document.pages]
        if not all('Issue: 01 - 28/08/19' in t for t in texts):
            raise ValueError('Printed issue/date missing')
        if 'with floating guide ring' not in texts[2] or 'without guide ring' not in texts[2]:
            raise ValueError('Style declarations missing')
        tables = document.pages[1].extract_tables()
    if len(tables) != 2:
        raise ValueError('Material table layout changed')
    rows = []
    for component, table in zip(('facing', 'core'), tables):
        for row in table[2:]:
            cells = [c.strip() for c in row if c and c.strip()]
            if len(cells) not in (2, 4):
                raise ValueError('Unexpected material row')
            for i in range(0, len(cells), 2):
                match = re.fullmatch(r'(\d+)˚C', cells[i + 1])
                if not match:
                    raise ValueError('Unexpected temperature cell')
                rows.append({'component': component, 'material_label_raw': cells[i],
                             'published_maximum_temperature_C_raw': match[1],
                             'physical_page': 2, 'temperature_is_article_rating': False})
    if len(rows) != 25 or len({(r['component'], r['material_label_raw']) for r in rows}) != 25:
        raise ValueError('Expected four facing and 21 core rows, without duplicates')
    sa_rows = json.loads(sa_path.read_text(encoding='utf-8'))['component_material_context']
    sa_index = {(r['component'], r['material_label_raw']): r for r in sa_rows}
    aliases = dict(LABEL_PAIRS)
    comparisons = []
    unmatched = []
    for row in rows:
        label = aliases.get(row['material_label_raw'], row['material_label_raw'])
        other = sa_index.get((row['component'], label))
        if other is None:
            unmatched.append(row['material_label_raw'])
            continue
        comparisons.append({'component': row['component'], 'uk_label_raw': row['material_label_raw'],
                            'sa_label_raw': other['material_label_raw'],
                            'uk_temperature_C_raw': row['published_maximum_temperature_C_raw'],
                            'sa_temperature_C_raw': other['published_maximum_temperature_C_raw'],
                            'values_agree': row['published_maximum_temperature_C_raw'] == other['published_maximum_temperature_C_raw'],
                            'label_mapping_approved': False, 'application_suitability_approved': False})
    return {'policy_version': 'klinger-uk-maxiprofile-context-0.1',
            'publisher': 'KLINGER United Kingdom',
            'source_url': 'https://www.klinger.co.uk/wp-content/uploads/2025/01/maxiprofile.pdf',
            'local_path': str(pdf.relative_to(ROOT.parent)).replace('\\', '/'),
            'source_sha256': PDF_SHA, 'printed_issue': '01', 'printed_issue_date': '2019-08-28',
            'retrieved_date': '2026-10-01', 'document_pages': 3,
            'visually_reviewed_physical_pages': [1, 2, 3],
            'source_registered': False, 'source_reuse_review': 'pending',
            'sa_research_sha256': SA_SHA, 'component_material_context': rows,
            'research_label_comparisons': comparisons, 'unmatched_uk_labels': unmatched,
            'temperature_disagreement_count': sum(not c['values_agree'] for c in comparisons),
            'style_context': {'LA1': 'guide ring present; fixed attachment not explicitly established',
                              'LA2': 'guide ring absent', 'LA3': 'floating guide ring',
                              'CA1_CA2_CA3': 'convex profiles in corresponding styles'},
            'dimensional_tuple_roles_resolved': False,
            'certificate_claims_independently_verified': False,
            'article_observations_added': 0, 'identity_approved': False,
            'application_suitability_approved': False, 'production_upn_allowed': False,
            'next_reviews': ['publisher clarification of divergent material temperature context',
                             'independent extraction and style applicability review',
                             'exact article drawing and component evidence', 'source registration and reuse review']}


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    result = build_report()
    if args.write:
        REPORT.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    else:
        if json.loads(REPORT.read_text(encoding='utf-8')) != result:
            raise ValueError('Report reproduction mismatch')
    print(f"UK family context: {len(result['component_material_context'])} rows; "
          f"{len(result['research_label_comparisons'])} research comparisons; "
          f"{result['temperature_disagreement_count']} disagreements; no article approvals")
