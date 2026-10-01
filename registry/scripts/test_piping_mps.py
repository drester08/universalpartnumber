"""Nominal agreement never resolves stock identity or historical findings."""
import copy
import csv
import json
import unittest
from unittest.mock import patch
import check_piping_mps as c


class PipingMPSTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=json.loads(c.MPS.read_text(encoding='utf-8'))
        cls.prior=json.loads(c.OLD.read_text(encoding='utf-8'))
        with c.DATASET.open(encoding='utf-8-sig',newline='') as handle:
            cls.supplied=list(csv.DictReader(handle))
        cls.report=c.build_report()

    def test_all_fifty_unique_nominal_matches(self):
        self.assertEqual(self.report['outcomes'],{'printed_precision_compatible':50})
        self.assertTrue(all(len(r['source_candidates'])==1 for r in self.report['records']))
        self.assertEqual({r['source_candidates'][0]['physical_page'] for r in self.report['records']},{12})

    def test_old_coverage_findings_retained(self):
        self.assertEqual(self.report['prior_to_current_counts'],{
            'outside_source_key_scope -> printed_precision_compatible':12,
            'printed_precision_compatible -> printed_precision_compatible':34,
            'ambiguous_source_key -> printed_precision_compatible':4})
        self.assertFalse(self.report['prior_findings_resolved'])

    def test_no_identity_or_route_approval(self):
        self.assertEqual(self.report['construction_conflicts'],50)
        for flag in ('identity_approved','source_registered','dataset_corrected'):
            self.assertFalse(self.report[flag])

    def test_xxs_stays_distinct_from_160(self):
        rows=[r for r in self.report['records'] if r['key'][0]=='80']
        self.assertEqual({r['key'][1] for r in rows},{'40','80','160','XXS'})
        xxs=next(r for r in rows if r['key'][1]=='XXS')['source_candidates'][0]
        self.assertEqual((xxs['schedule_raw'],xxs['wall_mm_raw']),('–','15,24'))
        self.assertEqual(c.source_key({'nominal_bore':'300','schedule_raw':'–','wall_designation_raw':'STD'}),('300','STD'))

    def test_source_defects_not_silently_corrected_or_promoted(self):
        self.assertEqual(self.report['rows_with_source_id_question'],1)
        self.assertEqual(self.report['rows_with_source_mass_question'],2)
        flagged=[r for r in self.report['records'] if r['source_internal_diameter_question']]
        self.assertEqual(flagged[0]['key'],['80','160'])
        self.assertNotIn('id_mm_raw',flagged[0]['source_candidates'][0])
        self.assertNotIn('mass_approx_kg_m_raw',flagged[0]['source_candidates'][0])

    def test_ambiguous_key_not_first_match(self):
        source=copy.deepcopy(self.source)
        source['records'].append(copy.deepcopy(source['records'][0]))
        rows=c.compare(source,self.supplied,self.prior)
        self.assertEqual(rows[0]['outcome'],'ambiguous_source_key')

    def test_missing_key_not_zero_or_match(self):
        source=copy.deepcopy(self.source)
        source['records']=source['records'][1:]
        self.assertEqual(c.compare(source,self.supplied,self.prior)[0]['outcome'],'outside_source_key_scope')

    def test_real_dimension_difference_detected(self):
        source=copy.deepcopy(self.source)
        source['records'][0]['wall_mm_raw']='9,999'
        self.assertEqual(c.compare(source,self.supplied,self.prior)[0]['outcome'],'dimension_conflict')

    def test_revisions_and_row_binding_fail_closed(self):
        with patch.object(c,'MPS_SHA','0'*64):
            with self.assertRaisesRegex(ValueError,'revision changed'):
                c.build_report()
        supplied=copy.deepcopy(self.supplied)
        supplied[0]['Outside Diameter (mm)']='99'
        with self.assertRaisesRegex(ValueError,'same supplied row'):
            c.compare(self.source,supplied,self.prior)

    def test_no_sensitive_columns_or_input_mutations(self):
        inputs=copy.deepcopy((self.source,self.supplied,self.prior))
        rows=c.compare(self.source,self.supplied,self.prior)
        self.assertEqual((self.source,self.supplied,self.prior),inputs)
        allowed={'od_mm','wall_mm'}
        self.assertTrue(all(set(r['actual'])==allowed for r in rows))
        self.assertNotIn('Email',json.dumps(self.report))


if __name__=='__main__':
    unittest.main()
