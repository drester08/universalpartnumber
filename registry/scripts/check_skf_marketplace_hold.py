"""Preserve authorization evidence; do not extract the quarantined product table."""
import hashlib
import json
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRODUCT = ROOT/'artifacts/skf/6204-2z-20261001.html'
TERMS = ROOT/'artifacts/skf/marketplace-terms-20261001.html'
PRODUCT_SHA = '931D8C2F75E3781F538FE4B8F554B82F0D58CA9B4500FFEB7D5E0B82A267588F'
TERMS_SHA = '462E78AB7BA3870578052C2947F3B70F6956796ED51F6C40E5A7112CBD6D38D7'
REPORT = ROOT/'reports/skf-marketplace-authorization-hold.json'


class TermsText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.skip = 0
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style'):
            self.skip += 1

    def handle_endtag(self, tag):
        if tag in ('script', 'style') and self.skip:
            self.skip -= 1

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)


def build_report(product=PRODUCT, terms=TERMS):
    for path, expected in ((product, PRODUCT_SHA), (terms, TERMS_SHA)):
        if hashlib.sha256(path.read_bytes()).hexdigest().upper() != expected:
            raise ValueError('Authorization evidence revision changed')
    parser = TermsText()
    parser.feed(terms.read_text(encoding='utf-8'))
    text = ' '.join(' '.join(parser.parts).split())
    if ('systematic extraction of data or data fields' not in text or
        'extract and/or re-utilize parts of the contents' not in text):
        raise ValueError('Captured restriction clauses missing')
    return dict(policy_version='skf-marketplace-authorization-hold-0.1',
                product_url='https://www.emarketplace.in.skf.com/deep-groove-ball-bearing/6204-2z',
                product_capture_path='registry/artifacts/skf/6204-2z-20261001.html', product_sha256=PRODUCT_SHA,
                terms_url='https://www.emarketplace.in.skf.com/terms-and-conditions',
                terms_capture_path='registry/artifacts/skf/marketplace-terms-20261001.html', terms_sha256=TERMS_SHA,
                captured_date='2026-10-01', terms_publication_date=None,
                restriction_locators=['6.1(k)-(l)', '7.3(vi)'],
                issue='Marketplace terms restrict content aggregation, systematic extraction and reutilization.',
                status='authorization_hold_pending_permission_or_alternative_source',
                source_registered=False, article_ingested=False, structured_product_table_generated=False,
                reuse_permission=False, identity_approved=False, application_suitability_approved=False,
                production_upn_allowed=False,
                related_existing_source='SRC-SKF-6205-2Z', existing_research_changed=False,
                next_action='Obtain written scope-specific permission or a source with acceptable reuse rights. Independently review publisher/content provenance; do not infer clearance/tolerance or equivalence from the designation.')


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write-snapshot', action='store_true')
    args = parser.parse_args()
    report = build_report()
    if args.write_snapshot:
        REPORT.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    elif json.loads(REPORT.read_text(encoding='utf-8')) != report:
        raise ValueError('Authorization-hold report stale')
    print('SKF marketplace authorization hold verified; no 6204 product-table intake or approval.')
