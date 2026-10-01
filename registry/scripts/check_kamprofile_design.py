"""Validate draft capture structure, not truth, equivalence or suitability."""
import argparse
import hashlib
import json
import re
import sqlite3
from decimal import Decimal
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DESIGN=ROOT/'profiles/kamprofile-gasket-draft-0.1.json'


def load_design():
    design=json.loads(DESIGN.read_text(encoding='utf-8'))
    for key in ('source_registration','source_research'):
        binding=design[key]
        data=(ROOT.parent/binding['path']).read_bytes()
        if hashlib.sha256(data).hexdigest().upper()!=binding['sha256']:
            raise ValueError('Kamprofile design source revision changed')
    if design['status']!='draft_design_not_database_profile' or any(design[key] for key in ('identity_approved','application_suitability_approved','production_upn_allowed')):
        raise ValueError('Draft design approval scope changed')
    import check_klinger_maxiprofile_registration
    with sqlite3.connect(ROOT/'build/registry.sqlite') as db:
        check_klinger_maxiprofile_registration.verify(db)
    return design


def capture_issues(capture, design=None):
    design=design or load_design()
    issues=[]
    def present(value):
        if isinstance(value,str):
            return bool(value.strip())
        return value is not None and value!='' and value!={} and value!=[]
    def text_fields(obj,keys,prefix):
        if isinstance(obj,dict):
            for key in keys:
                value=obj.get(key)
                if not isinstance(value,str) or not value.strip():
                    issues.append(prefix+key+': expected nonblank text')
    def required(obj, keys, prefix=''):
        if not isinstance(obj,dict):
            issues.append(prefix.rstrip('.')+': expected object')
            return False
        for key in keys:
            if not present(obj.get(key)):
                issues.append(prefix+key+': missing')
        return True
    def material(value, path):
        if required(value,design['material_requirements'],path+'.'):
            text_fields(value,design['material_requirements'],path+'.')
            label=value.get('designation')
            if not isinstance(label,str) or label.strip().casefold() in design['generic_material_labels_not_complete'] or not label.strip():
                issues.append(path+'.designation: exact grade/product definition missing')
    def dimension(value,path):
        if not required(value,('value','unit'),path+'.'):
            return
        raw=value.get('value')
        if not isinstance(raw,str) or not re.fullmatch(r'\d+(?:\.\d+)?',raw) or Decimal(raw)<=0:
            issues.append(path+'.value: expected positive decimal string')
        if value.get('unit') not in design['numeric_units']:
            issues.append(path+'.unit: unsupported or missing unit')
        # No arithmetic equality or manufacturing tolerance is inferred here.
    if not required(capture,design['required_fields']):
        return issues
    if capture.get('construction')!=design['allowed_construction']:
        issues.append('construction: outside draft scope')
    if capture.get('profile_form') not in design['allowed_profile_forms']:
        issues.append('profile_form: missing or unsupported')
    text_fields(capture,('serration_definition',),'')
    for field in design['component_material_fields']:
        material(capture.get(field),field)
    for field in design['thickness_fields']:
        dimension(capture.get(field),field)
    geometry=capture.get('geometry')
    if required(geometry,design['geometry_requirements'],'geometry.'):
        text_fields(geometry,('labelled_definition','tolerance_definition'),'geometry.')
        if geometry.get('shape') not in ('circular','drawing_defined'):
            issues.append('geometry.shape: unsupported')
        roles=geometry.get('dimension_roles')
        if not isinstance(roles,dict):
            issues.append('geometry.dimension_roles: expected role-keyed object')
        else:
            if geometry.get('shape')=='circular':
                required(roles,('seal_element_outer_diameter','seal_element_inner_diameter'),'geometry.dimension_roles.')
            if not roles:
                issues.append('geometry.dimension_roles: no labelled dimensions')
            for role,value in roles.items():
                dimension(value,'geometry.dimension_roles.'+role)
            if geometry.get('shape')=='circular':
                values=[]
                for role in ('seal_element_outer_diameter','seal_element_inner_diameter'):
                    value=roles.get(role)
                    if isinstance(value,dict) and isinstance(value.get('value'),str) and re.fullmatch(r'\d+(?:\.\d+)?',value['value']) and value.get('unit') in design['numeric_units']:
                        values.append(Decimal(value['value'])*(Decimal('25.4') if value['unit']=='in' else Decimal(1)))
                if len(values)==2 and values[0]<=values[1]:
                    issues.append('geometry.dimension_roles: outer diameter must exceed inner diameter')
    for field in ('guide_ring','partitions'):
        value=capture.get(field)
        if not required(value,('state',),field+'.'):
            continue
        state=value.get('state')
        rules=design[field]
        if state not in rules['states']:
            issues.append(field+'.state: explicit present/absent required')
        elif state=='absent':
            for key in rules['forbidden_when_absent']:
                if present(value.get(key)):
                    issues.append(field+'.'+key+': contradicts absent state')
        else:
            required(value,rules['required_when_present'],field+'.')
            text_fields(value,('attachment','geometry_definition') if field=='guide_ring' else ('layout_definition','joint_method'),field+'.')
            material(value.get('material'),field+'.material')
            dimension(value.get('thickness'),field+'.thickness')
            if field=='partitions' and value.get('profile_form') not in design['allowed_profile_forms']:
                issues.append('partitions.profile_form: missing or unsupported')
    connection=capture.get('connection')
    if required(connection,('kind',),'connection.'):
        kind=connection.get('kind')
        if kind not in design['connection']['kinds']:
            issues.append('connection.kind: explicit standard or drawing-defined interface required')
        else:
            required(connection,design['connection'][kind+'_required'],'connection.')
            text_fields(connection,design['connection'][kind+'_required'],'connection.')
    evidence=capture.get('article_evidence')
    if required(evidence,design['article_evidence_requirements'],'article_evidence.'):
        text_fields(evidence,design['article_evidence_requirements'],'article_evidence.')
        if not re.fullmatch(r'[A-Fa-f0-9]{64}',str(evidence.get('artifact_sha256',''))):
            issues.append('article_evidence.artifact_sha256: invalid SHA-256')
    return sorted(set(issues))


def assess_capture(capture):
    issues=capture_issues(capture)
    return dict(status='incomplete_research_structure' if issues else 'structure_ready_for_independent_review',
                issues=issues,source_truth_verified=False,identity_approved=False,
                application_suitability_approved=False,production_upn_allowed=False)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capture',type=Path)
    args=parser.parse_args()
    design=load_design()
    if args.capture:
        report=assess_capture(json.loads(args.capture.read_text(encoding='utf-8')))
        print(json.dumps(report,indent=2))
        raise SystemExit(bool(report['issues']))
    print('Source-bound kamprofile draft design verified; conditional capture checks only, no database or identity activation.')
