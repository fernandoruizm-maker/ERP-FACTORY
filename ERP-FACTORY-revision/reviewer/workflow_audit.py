"""Closed-schema audit of JSON-subset YAML; no network or Actions execution."""
import json
from pathlib import Path

from .contract import Blocked
from .workflow_spec import blueprint, PRIVATE, CHECKOUT, CLAUDE, UPLOAD

PINS = {CHECKOUT, CLAUDE, UPLOAD}


def audit(workflow, policy=None):
    # An exact closed blueprint rejects extra commands, hidden env/defaults,
    # missing guards, changed pins, retry wrappers and parallel matrices alike.
    if workflow != blueprint():
        raise Blocked('MULTIPART_WORKFLOW_POLICY_MISMATCH')
    if policy is None:
        policy = json.loads((Path(__file__).resolve().parent.parent / 'policy.json').read_text(encoding='utf-8'))
    expected = {'repository': PRIVATE, 'execution_enabled': False,
                'automatic_review_status': 'PARKED',
                'reviewed_validator_sha': None, 'artifact_retention_days': 7,
                'budget_currency': 'USD', 'max_calls_per_execution': 11,
                'max_spend_per_execution': '12.00', 'max_budget_usd_per_call': '1.00',
                'max_spend_total': '13.00', 'cumulative_strategy': 'manual_authorization',
                'review_reference_status': 'PENDING_PRIVATE_REPOSITORY_AND_REVIEW'}
    if policy != expected:
        raise Blocked('DELIVERED_POLICY_OR_CAPS_CHANGED')
    return {'structural_checks': 'PASS', 'operational_readiness': 'BLOCKED',
            'pending': ['PENDING_REVIEWED_PRIVATE_COMMIT', 'EXECUTION_DISABLED',
                        'AUTOMATIC_REVIEW_PARKED', 'MANUAL_ALLOWANCE_ADAPTER_PENDING'],
            'publication_allowed': False}
