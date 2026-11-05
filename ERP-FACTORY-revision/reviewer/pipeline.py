"""Offline protocol exercise with an explicitly supplied test double; no provider."""
from .contract import Blocked, canonical, digest
from .packets import MAX_PART_BYTES, SYSTEM_INSTRUCTIONS, user_message
from .validation import cross_request, envelope_schema, validate_complete, validate_review


def request(payload):
    user = user_message(payload)
    if len(user.encode('utf-8')) > MAX_PART_BYTES:
        raise Blocked('CROSS_CONTEXT_TOO_LARGE')
    return {'system': SYSTEM_INSTRUCTIONS + canonical(envelope_schema()), 'user': user,
            'artifact_digest': digest(payload), 'phase': payload['phase'],
            'part_id': payload.get('part_id', 0)}


def run_simulated(manifest, parts, responder):
    """No production transport/default. The result explicitly identifies simulation.

    Every callback is one fictitious review, not evidence that Claude read source.
    Invalid responses stop immediately. Partial reports are kept without retries;
    the cross pass is only possible when every part validates with full coverage.
    """
    expected = {part['part_id']: part['artifact_digest'] for part in manifest['packets']}
    if (len(parts) != len(expected) or len({p['part_id'] for p in parts}) != len(parts)
            or any(expected.get(p['part_id']) != digest(p) for p in parts)):
        raise Blocked('PACKET_DIGEST_MISMATCH')
    bundle = {'protocol_version': 2, 'source_sha': manifest['source_sha'],
              'factory_digest': manifest['factory_digest'], 'parts': [], 'cross': None}
    calls = 0
    for part in sorted(parts, key=lambda item: item['part_id']):
        response = responder(request(part))
        calls += 1
        validate_review(manifest, response, part['part_id'])
        bundle['parts'].append(response)
    partial = validate_complete(manifest, bundle)
    if partial['coverage']['complete_parts'] == partial['coverage']['expected_parts']:
        payload = cross_request(manifest, bundle['parts'])
        response = responder(request(payload))
        calls += 1
        validate_review(manifest, response, 0, cross_payload=payload)
        bundle['cross'] = response
    result = validate_complete(manifest, bundle)
    result.update(evidence_mode='SIMULATED_NOT_PROVIDER_INTEGRATION', simulated_calls=calls)
    return result
