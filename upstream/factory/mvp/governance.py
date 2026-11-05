"""Trusted operator audits for read-only Apps; never generated from agent output.

GitHub hides bypass_actors from callers without ruleset write access. An operator
can enroll a complete admin-visible response. The App then requires the exact
same timestamp and public policy on every governance check, plus its own 'never'
bypass result. Any settings edit requires a new admin audit, including edits to
hidden bypass actors. This relies on GitHub updating updated_at for ruleset edits.
"""
from datetime import datetime, timezone
from .common import Blocked, digest


def policy_fingerprint(detail):
    fields = ('id', 'target', 'source_type', 'source', 'enforcement', 'conditions', 'rules')
    return digest({k: detail.get(k) for k in fields})


def revision(detail):
    try:
        value = datetime.fromisoformat(detail['updated_at'].replace('Z', '+00:00'))
        if value.tzinfo is None:
            raise ValueError('Timezone required')
        return value.astimezone(timezone.utc).isoformat()
    except (KeyError, ValueError, TypeError, AttributeError):
        raise Blocked('Ruleset revision unavailable') from None


def attest_ruleset(detail):
    """Call only on a response obtained by an authorized ruleset administrator."""
    if (detail.get('bypass_actors') != [] or detail.get('enforcement') != 'active'
            or detail.get('target') != 'branch' or detail.get('source_type') != 'Repository'):
        raise Blocked('Admin audit requires an active ruleset with visible, empty bypass actors')
    return {'updated_at': revision(detail), 'policy_sha': policy_fingerprint(detail),
            'bypass_actors': []}


def no_bypass_verified(detail, attestations):
    if 'bypass_actors' in detail:
        return detail['bypass_actors'] == []
    saved = attestations.get(str(detail.get('id')), {})
    return (detail.get('current_user_can_bypass') == 'never'
            and saved.get('bypass_actors') == []
            and saved.get('policy_sha') == policy_fingerprint(detail)
            and saved.get('updated_at') == revision(detail))
