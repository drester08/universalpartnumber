"""Versioned research-capture predicates, never truth or approval decisions."""
import re

VERSION = 'research-applicability-0.1'
MISSING = object()
PATH = re.compile(r'[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*')


def present(value):
    if value is MISSING or value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (dict, list)):
        return bool(value)
    # Zero and false are actual values, not missing. Type/quantity validation
    # belongs to the capture schema, not this applicability evaluator.
    return True


def lookup(capture, path):
    value = capture
    for key in path.split('.'):
        if not isinstance(value, dict) or key not in value:
            return MISSING
        value = value[key]
    return value


def validate_contract(contract):
    if not isinstance(contract, dict) or set(contract) != {'policy_version', 'scope', 'rules'}:
        raise ValueError('Invalid applicability contract fields')
    if contract['policy_version'] != VERSION or contract['scope'] != 'research_capture_structure':
        raise ValueError('Unsupported applicability version or scope')
    rules = contract['rules']
    if not isinstance(rules, list) or not rules:
        raise ValueError('Nonempty applicability rules required')
    ids, selectors, targets = set(), set(), set()
    for rule in rules:
        if not isinstance(rule, dict) or set(rule) != {'rule_id', 'selector', 'states', 'branches'}:
            raise ValueError('Invalid applicability rule fields')
        identifier, selector, states, branches = (rule[k] for k in ('rule_id', 'selector', 'states', 'branches'))
        if not isinstance(identifier, str) or not identifier.strip() or identifier in ids:
            raise ValueError('Duplicate or missing rule ID')
        ids.add(identifier)
        if not isinstance(selector, str) or not PATH.fullmatch(selector) or selector in selectors:
            raise ValueError('Invalid or duplicate selector path')
        selectors.add(selector)
        if (not isinstance(states, list) or not states or
            any(not isinstance(s, str) or not s.strip() or s != s.strip() for s in states) or
            len(states) != len(set(states))):
            raise ValueError('Unique explicit selector states required')
        if not isinstance(branches, dict) or set(branches) != set(states):
            raise ValueError('Every declared state must have exactly one branch')
        local_targets = set()
        for branch in branches.values():
            if not isinstance(branch, dict) or set(branch) != {'required', 'forbidden'}:
                raise ValueError('Invalid branch fields')
            for key in ('required', 'forbidden'):
                paths = branch[key]
                if (not isinstance(paths, list) or any(not isinstance(p, str) or not PATH.fullmatch(p) for p in paths)
                    or len(paths) != len(set(paths))):
                    raise ValueError('Unique field paths required')
                local_targets.update(paths)
            if set(branch['required']) & set(branch['forbidden']):
                raise ValueError('A branch cannot require and forbid the same field')
        if targets & local_targets:
            raise ValueError('Multiple selectors cannot control the same field in this version')
        targets.update(local_targets)
    for target in targets:
        if any(target == selector or target.startswith(selector + '.') or selector.startswith(target + '.')
               for selector in selectors):
            raise ValueError('Selector dependencies/cycles are unsupported')
        if any(other != target and (other.startswith(target + '.') or target.startswith(other + '.'))
               for other in targets):
            raise ValueError('Overlapping target paths are unsupported')


def evaluate(capture, contract):
    validate_contract(contract)
    results, issues = [], []
    for rule in contract['rules']:
        selector = lookup(capture, rule['selector'])
        state = selector if isinstance(selector, str) and selector in rule['states'] else None
        local_issues = []
        if state is None:
            local_issues.append(rule['selector'] + ': explicit ' + '/'.join(rule['states']) +
                                ' required (unresolved applicability)')
            status = 'unresolved_applicability'
            required, forbidden = [], []
        else:
            branch = rule['branches'][state]
            required, forbidden = list(branch['required']), list(branch['forbidden'])
            local_issues.extend(path + ': missing' for path in required if not present(lookup(capture, path)))
            local_issues.extend(path + ': contradicts ' + state + ' state'
                                for path in forbidden if present(lookup(capture, path)))
            status = 'incomplete_branch_structure' if local_issues else 'resolved_research_structure'
        issues.extend(local_issues)
        results.append(dict(rule_id=rule['rule_id'], selector_path=rule['selector'], selected_state=state,
                            status=status, required_fields=required, forbidden_fields=forbidden,
                            issues=local_issues))
    return dict(policy_version=VERSION, scope=contract['scope'], rules=results,
                status='incomplete_research_structure' if issues else 'resolved_research_structure',
                issues=sorted(set(issues)), source_truth_verified=False, identity_approved=False,
                application_suitability_approved=False, production_upn_allowed=False)


def kamprofile_contract(design):
    """Adapt the already source-bound draft without altering its semantics."""
    rules = []
    for component in ('guide_ring', 'partitions'):
        definition = design[component]
        if definition['states'] != ['present', 'absent']:
            raise ValueError('Draft component state contract changed')
        prefix = component + '.'
        rules.append(dict(rule_id='kamprofile-' + component, selector=prefix + 'state',
                          states=list(definition['states']), branches={
                              'present': {'required': [prefix + p for p in definition['required_when_present']], 'forbidden': []},
                              'absent': {'required': [], 'forbidden': [prefix + p for p in definition['forbidden_when_absent']]}}))
    connection = design['connection']
    rules.append(dict(rule_id='kamprofile-connection', selector='connection.kind', states=list(connection['kinds']),
                      branches={kind: {'required': ['connection.' + p for p in connection[kind + '_required']],
                                      'forbidden': []} for kind in connection['kinds']}))
    contract = dict(policy_version=VERSION, scope='research_capture_structure', rules=rules)
    validate_contract(contract)
    return contract
