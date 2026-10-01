"""Synthetic structure tests are not real gasket evidence or approvals."""
import copy
import unittest
from unittest.mock import patch
import check_kamprofile_design as c
import check_klinger_maxiprofile_registration as registration


def fixture():
    # Deliberately synthetic references; nothing is persisted as a real article.
    material=lambda name: dict(designation=name,definition_reference='synthetic material definition')
    dim=lambda value: dict(value=value,unit='mm')
    return dict(construction='serrated_metal_core_with_two_facings',profile_form='parallel',
                core_material=material('TEST-CORE-GRADE'),upper_facing_material=material('TEST-UPPER-GRADE'),
                lower_facing_material=material('TEST-LOWER-GRADE'),core_thickness=dim('3.0'),
                upper_facing_thickness=dim('0.5'),lower_facing_thickness=dim('0.5'),overall_thickness=dim('4.0'),
                geometry=dict(shape='circular',labelled_definition='synthetic labelled geometry',
                              tolerance_definition='synthetic tolerance definition',
                              dimension_roles=dict(seal_element_outer_diameter=dim('100'),seal_element_inner_diameter=dim('60'))),
                serration_definition='synthetic serration definition',guide_ring=dict(state='absent'),
                partitions=dict(state='absent'),connection=dict(kind='drawing_defined',interface_definition='synthetic interface'),
                article_evidence=dict(manufacturer_article_reference='synthetic article',drawing_reference='synthetic drawing',
                                      revision='TEST-1',source_locator='synthetic locator',artifact_sha256='A'*64))


class KamprofileDesignTests(unittest.TestCase):
    def test_structural_readiness_never_approval(self):
        report=c.assess_capture(fixture())
        self.assertEqual(report['status'],'structure_ready_for_independent_review')
        for key in ('source_truth_verified','identity_approved','application_suitability_approved','production_upn_allowed'):
            self.assertFalse(report[key])

    def test_blank_is_not_explicit_absence(self):
        value=fixture()
        value['guide_ring']={}
        self.assertTrue(any('guide_ring.state' in x for x in c.capture_issues(value)))
        value['partitions']={'state':'unknown'}
        self.assertTrue(any('partitions.state' in x for x in c.capture_issues(value)))

    def test_present_ring_requires_all_details(self):
        value=fixture()
        value['guide_ring']={'state':'present'}
        issues=c.capture_issues(value)
        self.assertTrue(all(any('guide_ring.'+key in x for x in issues) for key in ('material','attachment','geometry_definition','thickness')))

    def test_absent_ring_cannot_keep_material(self):
        value=fixture()
        value['guide_ring']['material']=value['core_material']
        self.assertTrue(any('contradicts absent' in x for x in c.capture_issues(value)))

    def test_present_partitions_need_geometry_joint_and_material(self):
        value=fixture()
        value['partitions']={'state':'present','profile_form':'parallel'}
        issues=c.capture_issues(value)
        self.assertTrue(any('layout_definition' in x for x in issues))
        self.assertTrue(any('joint_method' in x for x in issues))
        self.assertTrue(any('partitions.material' in x for x in issues))

    def test_generic_material_not_complete(self):
        value=fixture()
        value['core_material']['designation']='Metallic'
        value['upper_facing_material']['designation']='Graphite'
        self.assertEqual(sum('exact grade' in x for x in c.capture_issues(value)),2)

    def test_each_side_and_thickness_separate(self):
        value=fixture()
        del value['lower_facing_thickness']
        self.assertIn('lower_facing_thickness: missing',c.capture_issues(value))
        value['overall_thickness']={'value':'0','unit':'mm'}
        self.assertTrue(any('positive decimal' in x for x in c.capture_issues(value)))

    def test_geometry_roles_and_units_required(self):
        value=fixture()
        roles=value['geometry']['dimension_roles']
        del roles['seal_element_inner_diameter']
        roles['seal_element_outer_diameter']['unit']=''
        issues=c.capture_issues(value)
        self.assertTrue(any('inner_diameter' in x for x in issues))
        self.assertTrue(any('unit' in x for x in issues))
        value=fixture()
        value['geometry']['dimension_roles']['seal_element_inner_diameter']={'value':'4','unit':'in'}
        self.assertTrue(any('outer diameter must exceed' in x for x in c.capture_issues(value)))

    def test_drawing_defined_non_circular_not_forced_to_diameters(self):
        value=fixture()
        value['geometry']['shape']='drawing_defined'
        value['geometry']['dimension_roles']={'drawing_width':{'value':'10.5','unit':'in'}}
        self.assertEqual(c.capture_issues(value),[])

    def test_standard_connection_needs_edition(self):
        value=fixture()
        value['connection']={'kind':'standard_flange','standard':'TEST','class':'TEST','nominal_size':'TEST'}
        self.assertIn('connection.edition: missing',c.capture_issues(value))

    def test_no_synthetic_source_truth_or_input_mutation(self):
        value=fixture()
        before=copy.deepcopy(value)
        value['article_evidence']['artifact_sha256']='bad'
        self.assertTrue(any('SHA-256' in x for x in c.capture_issues(value)))
        value['article_evidence']['artifact_sha256']=before['article_evidence']['artifact_sha256']
        c.assess_capture(value)
        self.assertEqual(value,before)

    def test_live_custody_failure_rejected(self):
        with patch.object(registration,'verify',side_effect=ValueError('custody changed')):
            with self.assertRaisesRegex(ValueError,'custody changed'):
                c.load_design()


if __name__=='__main__':
    unittest.main()
