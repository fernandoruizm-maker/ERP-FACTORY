"""Persistent V2 checkpoints; the caller supplies events, never a live provider."""
import copy
import json
from pathlib import Path

from .contract import Blocked, canonical, digest, sha256
from .execution_budget import execution_limits, reserve, finish, amount
from .pipeline import request
from .runtime import (PRIVATE_REPOSITORY, UNVALIDATED_RETENTION_CODES, write_artifacts,
                      MAX_EXECUTION_BYTES, EARLY_FAILURE_CODES)
from .validation import (check_manifest, validate_review, validate_complete, cross_request,
                         successful_text, parse_result, safe_diagnostic, ReviewRejected)

MAX_STATE_BYTES = 8_000_000
STOP_CODES = {'CALL_LIMIT_REACHED', 'SPEND_LIMIT_REACHED', 'UNCERTAIN_OR_OVER_BUDGET',
              'CROSS_CONTEXT_TOO_LARGE', 'PARTIAL_PART', 'PARTS_EXCEED_FIXED_SLOTS'}


def _save(work, state, label):
    path = Path(work) / 'state' / (label + '.json')
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = canonical(state).encode('utf-8')
    if len(raw) > MAX_STATE_BYTES:
        raise Blocked('STATE_TOO_LARGE')
    with path.open('xb') as stream:
        stream.write(raw)
    return {'state_file': label + '.json', 'state_sha256': sha256(raw)}


def _load(work, receipt):
    import re
    if (not isinstance(receipt, dict) or set(receipt) != {'state_file', 'state_sha256'}
            or not re.fullmatch(r'(initial|slot-[0-9]+-(reserved|result|stop))\.json', receipt['state_file'])):
        raise Blocked('STATE_RECEIPT_INVALID')
    path = Path(work) / 'state' / receipt['state_file']
    if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_STATE_BYTES:
        raise Blocked('STATE_RECEIPT_INVALID')
    raw = path.read_bytes()
    if sha256(raw) != receipt['state_sha256']:
        raise Blocked('STATE_HASH_MISMATCH')
    state = json.loads(raw)
    check_manifest(state['manifest'])
    expected = state['manifest']['packets']
    if len(expected) != len(state['parts']) or any(
            item['artifact_digest'] != digest(part) for item, part in zip(expected, state['parts'])):
        raise Blocked('PACKET_DIGEST_MISMATCH')
    validate_complete(state['manifest'], state['bundle'])
    return state


def _snapshot(work, state, label, *, reason=None, blocked=False, response=None,
              unvalidated=None, diagnostic=None, response_hash=None):
    report = validate_complete(state['manifest'], state['bundle'])
    if blocked:
        report['status'] = 'BLOCKED'
    report.update(source_sha=state['manifest']['source_sha'], factory_digest=state['manifest']['factory_digest'],
                  provenance=state['provenance'])
    if reason:
        report['reason_code'] = reason
    if response_hash:
        report['response_sha256'] = response_hash
    if unvalidated is not None:
        report['unvalidated_response_saved'] = True
    target = Path(work) / 'checkpoints' / label
    write_artifacts(target, report, diagnostic or {'status': 'CHECKPOINT', 'provider_text_saved': False},
                    manifest=state['manifest'], response=response, unvalidated_response=unvalidated)
    folder = target / 'artifacts'
    budget = {'schema': 'private-budget-v1', 'source_sha': state['manifest']['source_sha'],
              'provenance': state['provenance'], 'limits': state['limits'],
              'attempts': state['budget'], 'billing_verified': False}
    (folder / 'budget.json').write_text(canonical(budget), encoding='utf-8')
    hashes = {p.name: sha256(p.read_bytes()) for p in folder.iterdir() if p.name != 'SHA256.json'}
    (folder / 'SHA256.json').write_text(canonical(hashes), encoding='utf-8')
    return report


def start(work, manifest, parts, policy, grant, provenance):
    limits = execution_limits(policy, grant, manifest['source_sha'])
    check_manifest(manifest)
    if len(parts) > 10:
        raise Blocked('PARTS_EXCEED_FIXED_SLOTS')
    if (provenance.get('repository') != PRIVATE_REPOSITORY
            or provenance.get('source_sha') != manifest['source_sha']):
        raise Blocked('PROVENANCE_INVALID')
    state = {'manifest': manifest, 'parts': parts, 'limits': limits, 'budget': [],
             'provenance': provenance, 'next_slot': 1, 'stopped': False,
             'bundle': {'protocol_version': 2, 'source_sha': manifest['source_sha'],
                        'factory_digest': manifest['factory_digest'], 'parts': [], 'cross': None}}
    # Validate packet binding before persisting any material as prepared.
    if len(parts) != len(manifest['packets']) or any(
            p['part_id'] != i or digest(p) != manifest['packets'][i-1]['artifact_digest']
            for i, p in enumerate(parts, 1)):
        raise Blocked('PACKET_DIGEST_MISMATCH')
    receipt = _save(work, state, 'initial')
    _snapshot(work, state, 'initial')
    return receipt


def select(work, receipt, slot):
    state = _load(work, receipt)
    if state['stopped'] or type(slot) is not int or slot != state['next_slot'] or not 1 <= slot <= 11:
        raise Blocked('ORDER_OR_NO_RETRY')
    label = 'slot-' + str(slot)
    try:
        if slot <= len(state['parts']):
            payload = state['parts'][slot-1]
        else:
            payload = cross_request(state['manifest'], state['bundle']['parts'])
        prepared = request(payload)  # Enforces user-message size before reservation/call.
        reserve(state['budget'], state['limits'], slot)
    except Blocked as error:
        reason = str(error) if str(error) in STOP_CODES else 'CROSS_NOT_READY'
        state['stopped'] = True
        report = _snapshot(work, state, label+'-stop', reason=reason)
        return {'ready': False, 'receipt': _save(work, state, label+'-stop'), 'report': report,
                'checkpoint': label+'-stop'}
    state['request'] = prepared
    state['payload'] = payload
    result = {'ready': True, 'receipt': _save(work, state, label+'-reserved'),
              'checkpoint': label+'-reserved', 'request': prepared,
              'max_budget_usd': amount(state['limits']['per_call_units'])}
    _snapshot(work, state, label+'-reserved', reason='CALL_RESERVED_RESULT_UNKNOWN')
    return result


def collect_events(work, receipt, slot, events, conclusion, *, early_reason=None):
    state = _load(work, receipt)
    if (state['stopped'] or slot != state['next_slot'] or not state['budget']
            or state['budget'][-1]['slot'] != slot or state['budget'][-1]['status'] != 'IN_FLIGHT'):
        raise Blocked('ORDER_OR_NO_RETRY')
    raw = safe_raw = unvalidated = reason = response_hash = None
    valid = False
    diagnostic = safe_diagnostic(events) if isinstance(events, list) else {'status': 'INVALID_EVENT_LIST'}
    try:
        if early_reason is not None:
            if early_reason not in EARLY_FAILURE_CODES:
                raise Blocked('UNRECOGNIZED_FAILURE_CODE')
            raise ReviewRejected(early_reason)
        if conclusion != 'success':
            raise ReviewRejected('ACTION_FAILED')
        raw = successful_text(events)
        response_hash = sha256(raw.encode('utf-8'))
        envelope = parse_result(raw)  # Scan original before parsing/retaining.
        part_id = state['payload'].get('part_id', 0)
        checked = validate_review(state['manifest'], envelope, part_id,
                                  cross_payload=state['payload'] if part_id == 0 else None)
        if part_id == 0:
            state['bundle']['cross'] = envelope
        else:
            state['bundle']['parts'].append(envelope)
        safe_raw = raw
        valid = True
        if not checked['complete']:
            reason = 'PARTIAL_PART'
    except (Blocked, ValueError, TypeError, KeyError) as error:
        reason = error.code if isinstance(error, ReviewRejected) else 'INVALID_OR_UNSAFE_RESPONSE'
        if isinstance(error, ReviewRejected) and error.code in UNVALIDATED_RETENTION_CODES and raw is not None:
            unvalidated = raw
    finish(state['budget'], valid, diagnostic)
    over_budget = state['budget'][-1]['status'] == 'OVER_BUDGET'
    if over_budget and unvalidated is None:
        # Retain accepted evidence but prohibit every subsequent call.
        reason = 'PROVIDER_REPORTED_OVER_BUDGET'
    state['stopped'] = reason is not None or state['payload']['phase'] == 'cross'
    state['next_slot'] = slot + 1
    label = 'slot-' + str(slot) + '-result'
    report = _snapshot(work, state, label, reason=reason, blocked=not valid or over_budget,
                       response=safe_raw, unvalidated=unvalidated, diagnostic=diagnostic,
                       response_hash=response_hash)
    return {'receipt': _save(work, state, label), 'checkpoint': label, 'report': report,
            'continue': not state['stopped']}


def collect_path(work, receipt, slot, path, conclusion):
    # Fixed trusted path prepared for this slot; never reuse prior action output.
    reason = None
    try:
        path = Path(path)
        if path.is_symlink() or (path.exists() and not path.is_file()):
            reason = 'EXECUTION_FILE_INVALID'
        elif not path.exists():
            reason = 'EXECUTION_FILE_MISSING'
        elif path.stat().st_size > MAX_EXECUTION_BYTES:
            reason = 'EXECUTION_FILE_INVALID'
        if reason:
            events = None
        else:
            with path.open('rb') as stream:
                raw = stream.read(MAX_EXECUTION_BYTES + 1)
            if len(raw) > MAX_EXECUTION_BYTES:
                reason, events = 'EXECUTION_FILE_INVALID', None
            else:
                events = json.loads(raw)
                if not isinstance(events, list):
                    reason, events = 'EXECUTION_FORMAT_INVALID', None
    except OSError:
        reason, events = 'EXECUTION_READ_FAILED', None
    except (ValueError, RecursionError):
        reason, events = 'EXECUTION_JSON_INVALID', None
    return collect_events(work, receipt, slot, events, conclusion, early_reason=reason)


def run_simulated(work, manifest, parts, policy, grant, provenance, responder, uploaded):
    """Explicit doubles only: upload callback is evidence of simulation, not GitHub."""
    receipt = start(work, manifest, parts, policy, grant, provenance)
    uploaded(Path(work) / 'checkpoints/initial/artifacts')
    for slot in range(1, len(parts)+2):
        chosen = select(work, receipt, slot)
        uploaded(Path(work) / 'checkpoints' / chosen['checkpoint'] / 'artifacts')
        if not chosen['ready']:
            return chosen['report']
        try:
            events, conclusion = responder(copy.deepcopy(chosen['request']))
        except Exception:
            events, conclusion = None, 'failure'
        result = collect_events(work, chosen['receipt'], slot, events, conclusion)
        uploaded(Path(work) / 'checkpoints' / result['checkpoint'] / 'artifacts')
        receipt = result['receipt']
        if not result['continue']:
            return result['report']
    raise Blocked('MISSING_FINAL_CHECKPOINT')
