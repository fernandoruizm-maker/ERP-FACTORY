"""Standalone validator derived from local block 1 b0da873; no target imports.
This copy still requires review before a private immutable reference is selected.
"""
import json
import re
from .contract import Blocked, canonical, digest, SECRET_PATTERN

MAX_RESULT_BYTES = 100_000

def schema():
    string = {'type': 'string'}
    finding = {'type': 'object', 'additionalProperties': False, 'properties': {
        'severity': {'enum': ['critical', 'high', 'medium', 'low']},
        'file': string, 'line': {'type': 'integer', 'minimum': 1},
        'evidence_es': string, 'impact_es': string, 'recommendation_es': string},
        'required': ['severity', 'file', 'line', 'evidence_es', 'impact_es', 'recommendation_es']}
    props = {'source_sha': string, 'factory_digest': string,
             'reviewed_files': {'type': 'array', 'items': string},
             'coverage': {'enum': ['complete', 'incomplete']},
             'cross_component_review': {'type': 'boolean'},
             'verdict': {'enum': ['PASS', 'BLOCK']}, 'summary_es': string,
             'findings': {'type': 'array', 'items': finding},
             'limitations_es': {'type': 'array', 'items': string}}
    return {'type': 'object', 'additionalProperties': False, 'properties': props,
            'required': list(props)}


def nonempty(value, maximum=10000):
    return isinstance(value, str) and bool(value.strip()) and len(value) <= maximum


class ReviewRejected(Blocked):
    """Fixed machine code, independent of human-readable exception messages."""
    def __init__(self, code, coverage=None):
        super().__init__(code)
        self.code = code
        self.coverage = coverage


def coverage_diagnostic(manifest, result, require_cross=True):
    reviewed = result.get('reviewed_files')
    expected = set(manifest['files'])
    codes = []
    names = None
    if not isinstance(reviewed, list):
        codes.append('REVIEWED_NOT_LIST')
    else:
        names = [name for name in reviewed if isinstance(name, str)]
        if len(names) != len(reviewed):
            codes.append('REVIEWED_NOT_STRINGS')
    duplicates = len(names) - len(set(names)) if names is not None else None
    missing = sorted(expected - set(names)) if names is not None else None
    extra = len(set(names) - expected) if names is not None else None
    if duplicates:
        codes.append('REVIEWED_DUPLICATES')
    if missing:
        codes.append('REVIEWED_MISSING')
    if extra:
        codes.append('REVIEWED_EXTRA')
    coverage = result.get('coverage')
    cross = result.get('cross_component_review')
    if coverage != 'complete':
        codes.append('COVERAGE_DECLARED_INCOMPLETE')
    if require_cross and cross is not True:
        codes.append('CROSS_REVIEW_FALSE')
    return {'codes': codes, 'expected_count': len(expected),
            'reviewed_count': len(reviewed) if isinstance(reviewed, list) else None,
            'missing_count': len(missing) if missing is not None else None,
            'extra_count': extra, 'duplicate_count': duplicates, 'missing_files': missing,
            # Invalid provider values are not allowed into diagnostics.
            'coverage': coverage if coverage in ('complete', 'incomplete') else 'INVALID',
            'cross_component_review': cross if type(cross) is bool else 'INVALID'}


def _validate_report(manifest, result, require_cross=True):
    if not isinstance(result, dict) or set(result) != set(schema()['required']):
        raise ReviewRejected('REPORT_STRUCTURE')
    if len(canonical(result).encode('utf-8')) > MAX_RESULT_BYTES or SECRET_PATTERN.search(canonical(result)):
        raise ReviewRejected('OUTPUT_SAFETY_OR_SIZE')
    if result['source_sha'] != manifest['source_sha'] or result['factory_digest'] != manifest['factory_digest']:
        raise ReviewRejected('VERSION_MISMATCH')
    coverage = coverage_diagnostic(manifest, result, require_cross)
    if (any(code in coverage['codes'] for code in ('REVIEWED_NOT_LIST', 'REVIEWED_NOT_STRINGS'))
            or coverage['coverage'] == 'INVALID' or coverage['cross_component_review'] == 'INVALID'):
        raise ReviewRejected('COVERAGE_STRUCTURE', coverage)
    if result['verdict'] not in ('PASS', 'BLOCK') or not nonempty(result['summary_es']):
        raise ReviewRejected('INVALID_VERDICT', coverage)
    limitations = result['limitations_es']
    if not isinstance(limitations, list) or not limitations or not all(nonempty(x) for x in limitations):
        raise ReviewRejected('MISSING_LIMITATIONS', coverage)
    findings = result['findings']
    if not isinstance(findings, list) or len(findings) > 100:
        raise ReviewRejected('INVALID_FINDINGS', coverage)
    for finding in findings:
        fields = schema()['properties']['findings']['items']['required']
        if not isinstance(finding, dict) or set(finding) != set(fields):
            raise ReviewRejected('FINDING_STRUCTURE', coverage)
        if (finding['severity'] not in ('critical', 'high', 'medium', 'low')
                or not isinstance(finding['file'], str) or finding['file'] not in manifest['files']
                or type(finding['line']) is not int
                or not 1 <= finding['line'] <= manifest['file_lines'][finding['file']]
                or not all(nonempty(finding[k]) for k in ('evidence_es', 'impact_es', 'recommendation_es'))):
            raise ReviewRejected('INVALID_FINDING_EVIDENCE', coverage)
    if result['verdict'] == 'PASS' and any(f['severity'] in ('critical', 'high') for f in findings):
        raise ReviewRejected('CONTRADICTORY_PASS', coverage)
    status = 'PARTIAL' if coverage['codes'] else ('NEEDS_HUMAN_REVIEW' if result['verdict'] == 'PASS' else 'BLOCKED')
    return {'status': status, 'coverage_diagnostic': coverage,
            'publication_allowed': False, 'human_approvals': 0, 'review': result}


def envelope_schema():
    properties = {'protocol_version': {'const': 2}, 'phase': {'enum': ['part', 'cross']},
                  'part_id': {'type': 'integer', 'minimum': 0},
                  'artifact_digest': {'type': 'string'}, 'report': schema()}
    return {'type': 'object', 'additionalProperties': False, 'properties': properties,
            'required': list(properties)}


def check_manifest(manifest):
    """Validate coverage intervals from the trusted packet builder, never a model."""
    try:
        if manifest['protocol_version'] != 2 or not manifest['packets']:
            raise ReviewRejected('MANIFEST_INVALID')
        if set(manifest['files']) != set(manifest['file_lines']):
            raise ReviewRejected('MANIFEST_INVALID')
        intervals = {name: [] for name in manifest['files']}
        seen = set()
        for index, part in enumerate(manifest['packets'], 1):
            if (type(part['part_id']) is not int or part['part_id'] != index
                    or not re.fullmatch('[0-9a-f]{64}', part['artifact_digest'])
                    or part['artifact_digest'] in seen or not part['ranges']):
                raise ReviewRejected('MANIFEST_INVALID')
            seen.add(part['artifact_digest'])
            for name, span in part['ranges'].items():
                if name not in intervals or not isinstance(span, list) or len(span) != 2 or not all(type(n) is int for n in span):
                    raise ReviewRejected('MANIFEST_INVALID')
                intervals[name].append(span)
        for name, spans in intervals.items():
            count = manifest['file_lines'][name]
            if type(count) is not int or count < 0:
                raise ReviewRejected('MANIFEST_INVALID')
            if count == 0:
                if spans != [[0, 0]]:
                    raise ReviewRejected('MANIFEST_INVALID')
                continue
            cursor = 1
            for start, end in sorted(spans):
                if start != cursor or end < start or end > count:
                    raise ReviewRejected('MANIFEST_INVALID')
                cursor = end + 1
            if cursor != count + 1:
                raise ReviewRejected('MANIFEST_INVALID')
    except (KeyError, TypeError, AttributeError):
        raise ReviewRejected('MANIFEST_INVALID') from None


def validate_review(manifest, envelope, part_id, *, cross_payload=None):
    """The one envelope contract for a part or the final cross-component pass."""
    check_manifest(manifest)
    if (not isinstance(envelope, dict) or set(envelope) != set(envelope_schema()['required'])
            or type(envelope['protocol_version']) is not int or envelope['protocol_version'] != 2
            or type(envelope['part_id']) is not int):
        raise ReviewRejected('REPORT_STRUCTURE')
    if part_id == 0:
        if cross_payload is None:
            raise ReviewRejected('COVERAGE_STRUCTURE')
        expected_digest = digest(cross_payload)
        ranges = {name: [1, count] for name, count in manifest['file_lines'].items()}
        phase = 'cross'
    else:
        matches = [p for p in manifest['packets'] if p['part_id'] == part_id]
        if len(matches) != 1:
            raise ReviewRejected('VERSION_MISMATCH')
        expected_digest, ranges = matches[0]['artifact_digest'], matches[0]['ranges']
        phase = 'part'
    if (envelope['phase'] != phase or envelope['part_id'] != part_id
            or envelope['artifact_digest'] != expected_digest):
        raise ReviewRejected('VERSION_MISMATCH')
    context = {**manifest, 'files': {name: manifest['files'][name] for name in ranges}}
    checked = _validate_report(context, envelope['report'], require_cross=(part_id == 0))
    for finding in envelope['report']['findings']:
        start, end = ranges[finding['file']]
        if not start <= finding['line'] <= end or start == 0:
            raise ReviewRejected('INVALID_FINDING_EVIDENCE', checked['coverage_diagnostic'])
    return {'complete': not checked['coverage_diagnostic']['codes'],
            'coverage_diagnostic': checked['coverage_diagnostic'], 'envelope': envelope,
            'publication_allowed': False, 'human_approvals': 0}


def _parts(manifest, reviews):
    if not isinstance(reviews, list):
        raise ReviewRejected('REPORT_STRUCTURE')
    checked = {}
    for envelope in reviews:
        if not isinstance(envelope, dict) or type(envelope.get('part_id')) is not int or envelope['part_id'] <= 0:
            raise ReviewRejected('REPORT_STRUCTURE')
        identifier = envelope['part_id']
        if identifier in checked:
            raise ReviewRejected('COVERAGE_STRUCTURE')
        checked[identifier] = validate_review(manifest, envelope, identifier)
    return checked


def cross_request(manifest, reviews):
    """Bind final review to every exact, validated part result, including findings."""
    check_manifest(manifest)
    checked = _parts(manifest, reviews)
    if (set(checked) != {p['part_id'] for p in manifest['packets']}
            or not all(item['complete'] for item in checked.values())):
        raise ReviewRejected('COVERAGE_STRUCTURE')
    return {'protocol_version': 2, 'phase': 'cross', 'source_sha': manifest['source_sha'],
            'factory_digest': manifest['factory_digest'], 'scope_digest': manifest['scope_digest'],
            'files': manifest['files'], 'file_lines': manifest['file_lines'],
            'part_results': [{'part_id': i, 'result_digest': digest(checked[i]['envelope']),
                              'result': checked[i]['envelope']} for i in sorted(checked)],
            'task': 'Revisar interacciones entre TODAS las partes. No ejecutar ni aprobar.'}


def validate_complete(manifest, bundle):
    check_manifest(manifest)
    if (not isinstance(bundle, dict) or set(bundle) != {'protocol_version', 'source_sha', 'factory_digest', 'parts', 'cross'}
            or type(bundle['protocol_version']) is not int or bundle['protocol_version'] != 2):
        raise ReviewRejected('REPORT_STRUCTURE')
    if bundle['source_sha'] != manifest['source_sha'] or bundle['factory_digest'] != manifest['factory_digest']:
        raise ReviewRejected('VERSION_MISMATCH')
    # The aggregate is local; each individual response has its own 100 KB limit.
    if SECRET_PATTERN.search(canonical(bundle)):
        raise ReviewRejected('OUTPUT_SAFETY_OR_SIZE')
    checked = _parts(manifest, bundle['parts'])
    expected = {p['part_id'] for p in manifest['packets']}
    complete = {i for i, item in checked.items() if item['complete']}
    cross_complete = False
    if bundle['cross'] is not None:
        payload = cross_request(manifest, bundle['parts'])
        cross_complete = validate_review(manifest, bundle['cross'], 0, cross_payload=payload)['complete']
    all_complete = complete == expected and cross_complete
    reports = [item['envelope']['report'] for item in checked.values()]
    if bundle['cross'] is not None:
        reports.append(bundle['cross']['report'])
    blocked = any(report['verdict'] == 'BLOCK' for report in reports)
    status = 'PARTIAL' if not all_complete else ('BLOCKED' if blocked else 'NEEDS_HUMAN_REVIEW')
    file_parts = {name: {p['part_id'] for p in manifest['packets'] if name in p['ranges']}
                  for name in manifest['files']}
    covered = sorted(name for name, ids in file_parts.items() if ids <= complete)
    return {'status': status, 'publication_allowed': False, 'human_approvals': 0,
            'coverage': {'expected_parts': len(expected), 'validated_parts': len(checked),
                         'complete_parts': len(complete), 'missing_parts': sorted(expected - set(checked)),
                         'covered_files': covered, 'missing_files': sorted(set(file_parts) - set(covered)),
                         'cross_component_review_validated': cross_complete},
            'findings': [finding for report in reports for finding in report['findings']],
            'review': bundle}


def validate_result(manifest, result):
    return validate_complete(manifest, result)


def successful_text(events):
    """Return original text only after the successful-execution and size checks."""
    if not isinstance(events, list):
        raise ReviewRejected('EXECUTION_FORMAT')
    results = [e for e in events if isinstance(e, dict) and e.get('type') == 'result']
    if len(results) != 1:
        raise ReviewRejected('RESULT_EVENT_COUNT')
    event = results[0]
    provider_error = any(isinstance(item, dict) and (
        item.get('type') == 'error' or item.get('is_error') is True
        or (isinstance(item.get('subtype'), str) and item['subtype'].startswith('error'))
        or bool(item.get('error')) or bool(item.get('errors'))) for item in events)
    if (event.get('subtype') != 'success' or event.get('is_error') is not False
            or type(event.get('num_turns')) is not int or not 1 <= event['num_turns'] <= 2
            or event.get('permission_denials') != [] or provider_error):
        raise ReviewRejected('RESULT_EXECUTION_INVALID')
    raw = event.get('result')
    if not isinstance(raw, str):
        raise ReviewRejected('RESULT_MISSING_OR_TOO_LARGE')
    try:
        if len(raw.encode('utf-8')) > MAX_RESULT_BYTES:
            raise ReviewRejected('RESULT_MISSING_OR_TOO_LARGE')
    except UnicodeError:
        raise ReviewRejected('RESULT_MISSING_OR_TOO_LARGE') from None
    return raw


def parse_result(raw):
    # Scan ORIGINAL text before parsing or retaining it, including Markdown/invalid JSON.
    if SECRET_PATTERN.search(raw):
        raise ReviewRejected('POSSIBLE_SECRET')
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, RecursionError):
        raise ReviewRejected('INVALID_JSON') from None


def text_result(events):
    return parse_result(successful_text(events))


def safe_diagnostic(events):
    """Return only fixed labels and numeric metadata, never provider text."""
    if not isinstance(events, list):
        raise Blocked('Formato de diagnostico desconocido.')
    results = [e for e in events if isinstance(e, dict) and e.get('type') == 'result']
    if not results:
        return {'status': 'NO_RESULT_EVENT', 'provider_text_saved': False}
    event = results[-1]
    successful = event.get('subtype') == 'success' and event.get('is_error') is False
    # Successful review prose can mention errors without being a provider error.
    error_material = '' if successful else canonical({k: event.get(k) for k in ('result', 'errors', 'error')}).lower()
    patterns = {
        'AUTHENTICATION': r'authentication_error|invalid (?:api key|oauth|token)|not logged in|token.{0,30}expired',
        'SUBSCRIPTION_OR_CREDITS': r'credit balance|subscription|billing|insufficient.{0,20}credit',
        'RATE_LIMIT': r'rate_limit|rate limit|too many requests',
        'CONTEXT_LIMIT': r'prompt is too long|context.{0,20}(?:limit|window)|too many tokens',
        'SCHEMA_OR_FORMAT': r'structuredoutput|json.schema|invalid schema|structured.output',
        'MODEL_ACCESS': r'model.{0,40}(?:not found|not available|not supported|access)',
        'BUDGET': r'budget.{0,30}(?:exceed|limit)',
        'TRANSPORT': r'econnreset|econnrefused|timed? ?out|connection error',
    }
    categories = [label for label, pattern in patterns.items() if re.search(pattern, error_material)]
    if event.get('subtype') == 'error_max_turns':
        categories.append('TURN_LIMIT')
    denials = event.get('permission_denials')
    if isinstance(denials, list) and denials:
        categories.append('TOOL_PERMISSION_DENIED')
    report = {'status': 'DIAGNOSTIC_ONLY', 'provider_text_saved': False,
              'categories': categories if successful else categories or ['UNCLASSIFIED'],
              'is_error': event.get('is_error') is True}
    if isinstance(denials, list):
        report['permission_denials_count'] = len(denials)
        report['structured_output_denied'] = any(
            isinstance(d, dict) and d.get('tool_name') == 'StructuredOutput' for d in denials)
    for key in ('duration_ms', 'num_turns', 'total_cost_usd'):
        value = event.get(key)
        if type(value) in (int, float) and 0 <= value < 10**10:
            report[key] = value
    return report
