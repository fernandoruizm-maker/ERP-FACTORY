"""Standalone validator derived from local block 1 b0da873; no target imports.
This copy still requires review before a private immutable reference is selected.
"""
import json
import re
from .contract import Blocked, canonical, SECRET_PATTERN

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


def coverage_diagnostic(manifest, result):
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
    if cross is not True:
        codes.append('CROSS_REVIEW_FALSE')
    return {'codes': codes, 'expected_count': len(expected),
            'reviewed_count': len(reviewed) if isinstance(reviewed, list) else None,
            'missing_count': len(missing) if missing is not None else None,
            'extra_count': extra, 'duplicate_count': duplicates, 'missing_files': missing,
            # Invalid provider values are not allowed into diagnostics.
            'coverage': coverage if coverage in ('complete', 'incomplete') else 'INVALID',
            'cross_component_review': cross if type(cross) is bool else 'INVALID'}


def validate_result(manifest, result):
    if not isinstance(result, dict) or set(result) != set(schema()['required']):
        raise ReviewRejected('REPORT_STRUCTURE')
    if len(canonical(result).encode('utf-8')) > MAX_RESULT_BYTES or SECRET_PATTERN.search(canonical(result)):
        raise ReviewRejected('OUTPUT_SAFETY_OR_SIZE')
    if result['source_sha'] != manifest['source_sha'] or result['factory_digest'] != manifest['factory_digest']:
        raise ReviewRejected('VERSION_MISMATCH')
    coverage = coverage_diagnostic(manifest, result)
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


def text_result(events):
    results = [e for e in events if isinstance(e, dict) and e.get('type') == 'result']
    if len(results) != 1:
        raise ReviewRejected('RESULT_EVENT_COUNT')
    event = results[0]
    if (event.get('subtype') != 'success' or event.get('is_error') is not False
            or type(event.get('num_turns')) is not int or not 1 <= event['num_turns'] <= 2
            or event.get('permission_denials') != []):
        raise ReviewRejected('RESULT_EXECUTION_INVALID')
    raw = event.get('result')
    if not isinstance(raw, str) or len(raw.encode('utf-8')) > MAX_RESULT_BYTES:
        raise ReviewRejected('RESULT_MISSING_OR_TOO_LARGE')
    return json.loads(raw)


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
