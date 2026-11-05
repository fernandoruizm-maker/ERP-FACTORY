import json
import hashlib
import io
import os
import subprocess
import zipfile
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from factory2.actions_review import build_request, collect, coverage_diagnostic, prepare, safe_diagnostic, text_result, validate_result
from factory2.core import Blocked, canonical
from factory2.review_packet import packet
from factory2.state import Store


class ActionsReviewTests(unittest.TestCase):
    def test_successful_review_text_is_not_classified_as_provider_failure(self):
        result = safe_diagnostic([{'type': 'result', 'subtype': 'success', 'is_error': False,
                                  'result': 'Review mentions rate limit, json schema and budget limit.'}])
        self.assertEqual(result['categories'], [])

    def test_diagnostic_classifies_without_revealing_provider_text(self):
        result = safe_diagnostic([{'type': 'result', 'is_error': True,
                                  'result': 'Invalid OAuth token: SECRET-DO-NOT-PUBLISH',
                                  'num_turns': 1, 'total_cost_usd': 0}])
        self.assertEqual(result['categories'], ['AUTHENTICATION'])
        self.assertNotIn('SECRET-DO-NOT-PUBLISH', canonical(result))
        self.assertFalse(result['provider_text_saved'])
        self.assertEqual(result['total_cost_usd'], 0)

    def test_diagnostic_unknown_error_is_not_a_guessed_cause(self):
        result = safe_diagnostic([{'type': 'result', 'is_error': True,
                                  'result': 'Private unknown details', 'num_turns': 'secret'}])
        self.assertEqual(result['categories'], ['UNCLASSIFIED'])
        self.assertNotIn('Private', canonical(result))
        self.assertNotIn('num_turns', result)
        self.assertEqual(safe_diagnostic([])['status'], 'NO_RESULT_EVENT')

    def test_turn_and_permission_diagnostics_do_not_publish_tool_inputs(self):
        result = safe_diagnostic([{'type': 'result', 'subtype': 'error_max_turns',
            'permission_denials': [{'tool_name': 'StructuredOutput', 'tool_input': 'PRIVATE'},
                                  {'tool_name': 'PRIVATE-NAME'}]}])
        self.assertIn('TURN_LIMIT', result['categories'])
        self.assertIn('TOOL_PERMISSION_DENIED', result['categories'])
        self.assertTrue(result['structured_output_denied'])
        self.assertEqual(result['permission_denials_count'], 2)
        self.assertNotIn('PRIVATE', canonical(result))

    def setUp(self):
        self.manifest = {'source_sha': 'a' * 40, 'factory_digest': 'digest-a',
                         'files': {'factory2/a.py': 'hash-a'}, 'file_lines': {'factory2/a.py': 3}}
        self.result = {'source_sha': 'a' * 40, 'factory_digest': 'digest-a',
                       'reviewed_files': ['factory2/a.py'], 'coverage': 'complete',
                       'cross_component_review': True, 'verdict': 'PASS',
                       'summary_es': 'Resultado simulado para comprobar el validador.',
                       'findings': [], 'limitations_es': ['No se ejecutaron pruebas ni llamadas reales.']}
        self.env = {'GITHUB_REPOSITORY': 'fernandoruizm-maker/ERP-FACTORY',
                    'GITHUB_SHA': 'a' * 40, 'GITHUB_RUN_ID': '123', 'GITHUB_RUN_ATTEMPT': '1',
                    'GITHUB_ACTOR': 'fernandoruizm-maker', 'CLAUDE_CONCLUSION': 'success'}
        self.event = {'type': 'result', 'subtype': 'success', 'is_error': False,
                      'num_turns': 1, 'permission_denials': [], 'result': canonical(self.result)}

    def write_execution(self, dest, raw=None):
        event = {**self.event, 'result': raw if raw is not None else canonical(self.result)}
        (dest / 'claude-execution-output.json').write_text(canonical([event]), encoding='utf-8')

    def test_plain_json_result_rejects_errors_denials_turn_overruns_and_ambiguous_output(self):
        self.assertEqual(text_result([self.event]), self.result)
        for change in ({'subtype': 'error_max_turns'}, {'is_error': True}, {'num_turns': 3},
                       {'num_turns': True}, {'permission_denials': [{}]},
                       {'permission_denials': None}, {'result': '```json\n{}\n```'},
                       {'result': 'x' * 100001}):
            with self.subTest(change=change), self.assertRaises((Blocked, ValueError)):
                text_result([{**self.event, **change}])
        for events in ([], [self.event, self.event]):
            with self.assertRaises(Blocked):
                text_result(events)

    def test_collection_without_execution_file_stays_blocked(self):
        with tempfile.TemporaryDirectory() as temp:
            dest = Path(temp)
            (dest / 'manifest.json').write_text(canonical(self.manifest), encoding='utf-8')
            self.assertEqual(collect(dest, {**self.env, 'RUNNER_TEMP': temp}), 1)
            report = json.loads((dest / 'report.json').read_text(encoding='utf-8'))
            self.assertEqual(report['failure_stage'], 'EXECUTION_FILE')

    def test_rejection_diagnostic_distinguishes_json_version_and_coverage_without_raw_text(self):
        cases = [('SECRET-RAW', 'RESULT_JSON', 'INVALID_JSON'),
                 (canonical({**self.result, 'source_sha': 'b' * 40}), 'REPORT_VALIDATION', 'VERSION_MISMATCH')]
        for raw, stage, reason in cases:
            with self.subTest(reason=reason), tempfile.TemporaryDirectory() as temp:
                dest = Path(temp)
                (dest / 'manifest.json').write_text(canonical(self.manifest), encoding='utf-8')
                self.write_execution(dest, raw)
                self.assertEqual(collect(dest, {**self.env, 'RUNNER_TEMP': temp}), 1)
                report = json.loads((dest / 'report.json').read_text(encoding='utf-8'))
                self.assertEqual(report['failure_stage'], stage)
                self.assertEqual(report['reason_code'], reason)
                self.assertNotIn('SECRET-RAW', canonical(report))

    def test_complete_review_never_grants_approval(self):
        result = validate_result(self.manifest, self.result)
        self.assertEqual(result['status'], 'NEEDS_HUMAN_REVIEW')
        self.assertEqual(result['human_approvals'], 0)
        self.assertFalse(result['publication_allowed'])

    def test_stale_partial_duplicate_and_missing_cross_review_block(self):
        for changes in ({'source_sha': 'b' * 40}, {'factory_digest': 'old'}):
            with self.subTest(changes=changes), self.assertRaises(Blocked):
                validate_result(self.manifest, {**self.result, **changes})

    def test_reviewed_not_list(self):
        data = {**self.result, 'reviewed_files': 'PRIVATE'}
        self.assertEqual(coverage_diagnostic(self.manifest, data)['codes'], ['REVIEWED_NOT_LIST'])
        with self.assertRaises(Blocked): validate_result(self.manifest, data)

    def test_reviewed_not_strings(self):
        data = {**self.result, 'reviewed_files': ['factory2/a.py', {'secret': 'PRIVATE'}]}
        self.assertEqual(coverage_diagnostic(self.manifest, data)['codes'], ['REVIEWED_NOT_STRINGS'])
        with self.assertRaises(Blocked): validate_result(self.manifest, data)

    def assert_partial(self, changes, code):
        value = validate_result(self.manifest, {**self.result, **changes})
        self.assertEqual(value['status'], 'PARTIAL')
        self.assertEqual(value['coverage_diagnostic']['codes'], [code])
        return value['coverage_diagnostic']

    def test_reviewed_duplicates(self):
        d = self.assert_partial({'reviewed_files': ['factory2/a.py'] * 2}, 'REVIEWED_DUPLICATES')
        self.assertEqual(d['duplicate_count'], 1)

    def test_reviewed_missing(self):
        d = self.assert_partial({'reviewed_files': []}, 'REVIEWED_MISSING')
        self.assertEqual(d['missing_count'], 1)
        self.assertEqual(d['missing_files'], ['factory2/a.py'])

    def test_reviewed_extra(self):
        d = self.assert_partial({'reviewed_files': ['factory2/a.py', 'PRIVATE-EXTRA']}, 'REVIEWED_EXTRA')
        self.assertEqual(d['extra_count'], 1)
        self.assertNotIn('PRIVATE', canonical(d))

    def test_coverage_declared_incomplete(self):
        d = self.assert_partial({'coverage': 'incomplete'}, 'COVERAGE_DECLARED_INCOMPLETE')
        self.assertEqual(d['coverage'], 'incomplete')

    def test_cross_review_false(self):
        d = self.assert_partial({'cross_component_review': False}, 'CROSS_REVIEW_FALSE')
        self.assertIs(d['cross_component_review'], False)

    def test_all_applicable_causes_and_safe_values(self):
        data = {**self.result, 'reviewed_files': ['PRIVATE', 'PRIVATE', None],
                'coverage': 'PRIVATE-COVERAGE', 'cross_component_review': 'PRIVATE-CROSS'}
        d = coverage_diagnostic(self.manifest, data)
        self.assertEqual(d['codes'], ['REVIEWED_NOT_STRINGS', 'REVIEWED_DUPLICATES',
            'REVIEWED_MISSING', 'REVIEWED_EXTRA', 'COVERAGE_DECLARED_INCOMPLETE', 'CROSS_REVIEW_FALSE'])
        self.assertEqual((d['reviewed_count'], d['missing_count'], d['extra_count'], d['duplicate_count']), (3, 1, 1, 1))
        self.assertEqual(d['coverage'], 'INVALID')
        self.assertEqual(d['cross_component_review'], 'INVALID')
        self.assertNotIn('PRIVATE', canonical(d))

    def test_partial_validates_findings_and_never_satisfies_gate(self):
        finding = {'severity': 'medium', 'file': 'factory2/a.py', 'line': 2,
                   'evidence_es': 'FICTICIO', 'impact_es': 'FICTICIO', 'recommendation_es': 'FICTICIO'}
        partial = validate_result(self.manifest, {**self.result, 'coverage': 'incomplete', 'findings': [finding]})
        self.assertFalse(partial['publication_allowed'])
        self.assertEqual(partial['human_approvals'], 0)
        self.assertEqual(partial['review']['findings'], [finding])
        for change in ({'line': 4}, {'file': '../outside'}, {'severity': 'invalid'}):
            with self.assertRaises(Blocked):
                validate_result(self.manifest, {**self.result, 'coverage': 'incomplete', 'findings': [{**finding, **change}]})
        with tempfile.TemporaryDirectory() as temp:
            store = Store(Path(temp) / 'state.sqlite3')
            version = store.put_task('FICTICIO', {'artifact_digest': 'artifact'})
            store.accept('FICTICIO', version, 'persona-a', 'business')
            store.accept('FICTICIO', version, 'persona-b', 'technical')
            product = {'artifact_digest': 'artifact', 'verdict': 'PASS', 'summary_es': 'Ficticio', 'findings': []}
            tests = [{'status': 'PASS', 'test_count': 1, 'artifact_digest': 'artifact'}]
            for review in (partial, partial['review']):
                outcome = store.gate('FICTICIO', version, 'artifact', product, tests,
                                     factory_digest='digest-a', factory_review=review)
                self.assertEqual(outcome['status'], 'BLOCKED')
                self.assertFalse(outcome['publication_allowed'])

    def test_real_base_packet_91_files_and_missing_empty_test_file(self):
        root = Path(__file__).resolve().parent.parent
        env = {k: v for k, v in os.environ.items() if k.upper() in ('PATH', 'SYSTEMROOT', 'TEMP', 'TMP')}
        env.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_COUNT='0')
        # Local Git object database only; no checkout, hooks, fetch or provider.
        archive = subprocess.run(['git', 'archive', '--format=zip',
            '0cb1882548fc141f4b764e82ff2e5154cfae2762'], cwd=root, env=env,
            check=True, capture_output=True).stdout
        with tempfile.TemporaryDirectory() as temp, zipfile.ZipFile(io.BytesIO(archive)) as files:
            base = Path(temp)
            for info in files.infolist():
                if info.is_dir(): continue
                target = base / info.filename
                self.assertTrue(target.resolve().is_relative_to(base.resolve()))
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(files.read(info))
            manifest, parts = packet(base)
            self.assertEqual(len(manifest['files']), 91)
            manifest['source_sha'] = '0cb1882548fc141f4b764e82ff2e5154cfae2762'
            manifest['file_lines'] = {name: max(1, len(body.splitlines())) for part in parts for name, body in part['files'].items()}
            response = {**self.result, 'source_sha': manifest['source_sha'], 'factory_digest': manifest['factory_digest'],
                        'reviewed_files': list(manifest['files'])}
            self.assertEqual(validate_result(manifest, response)['status'], 'NEEDS_HUMAN_REVIEW')
            response['reviewed_files'].remove('tests/__init__.py')
            result = validate_result(manifest, response)
            self.assertEqual(result['status'], 'PARTIAL')
            self.assertEqual(result['coverage_diagnostic']['missing_files'], ['tests/__init__.py'])
            self.assertEqual(result['coverage_diagnostic']['missing_count'], 1)

    def test_bad_evidence_and_contradictory_pass_block(self):
        finding = {'severity': 'high', 'file': 'factory2/a.py', 'line': 2,
                   'evidence_es': 'Evidencia ficticia.', 'impact_es': 'Impacto ficticio.',
                   'recommendation_es': 'Correccion ficticia.'}
        for changes in ({}, {'severity': 'invalid'}, {'file': '../secreto'}, {'line': True}, {'line': 4}):
            with self.subTest(changes=changes), self.assertRaises(Blocked):
                validate_result(self.manifest, {**self.result, 'findings': [{**finding, **changes}]})
        self.assertEqual(validate_result(self.manifest, {**self.result, 'verdict': 'BLOCK',
                                                        'findings': [finding]})['status'], 'BLOCKED')

    def test_invalid_types_missing_limits_and_secret_like_output_block(self):
        for changes in ({'findings': None}, {'reviewed_files': [{}]}, {'limitations_es': []},
                        {'summary_es': 'sk-' + 'x' * 40}, {'unexpected': 'value'}):
            with self.subTest(changes=changes), self.assertRaises(Blocked):
                validate_result(self.manifest, {**self.result, **changes})

    def test_collection_failure_leaves_blocked_report_without_raw_content(self):
        for changes in ({'raw_fixture': 'not-json-sensitive-fixture'},
                        {'CLAUDE_CONCLUSION': 'failure'}, {'GITHUB_RUN_ATTEMPT': '2'},
                        {'GITHUB_SHA': 'b' * 40}, {'GITHUB_ACTOR': 'someone-else'}):
            with self.subTest(changes=changes), tempfile.TemporaryDirectory() as temp:
                dest = Path(temp)
                (dest / 'manifest.json').write_text(canonical(self.manifest), encoding='utf-8')
                self.write_execution(dest, changes.get('raw_fixture'))
                self.assertEqual(collect(dest, {**self.env, **changes, 'RUNNER_TEMP': temp}), 1)
                report = (dest / 'report.json').read_text(encoding='utf-8')
                self.assertNotIn('not-json-sensitive-fixture', report)
                self.assertEqual(json.loads(report)['status'], 'BLOCKED')

    def test_valid_collection_preserves_provenance_not_approval(self):
        with tempfile.TemporaryDirectory() as temp:
            dest = Path(temp)
            (dest / 'manifest.json').write_text(canonical(self.manifest), encoding='utf-8')
            self.write_execution(dest)
            self.assertEqual(collect(dest, {**self.env, 'RUNNER_TEMP': temp}), 0)
            report = json.loads((dest / 'report.json').read_text(encoding='utf-8'))
            self.assertEqual(report['provenance']['GITHUB_RUN_ID'], '123')
            self.assertFalse(report['publication_allowed'])
            self.assertTrue((dest / 'INFORME.txt').is_file())

    def test_pending_partial_retains_findings_without_public_free_text(self):
        with tempfile.TemporaryDirectory() as temp:
            dest = Path(temp)
            (dest / 'manifest.json').write_text(canonical(self.manifest), encoding='utf-8')
            raw = json.dumps({**self.result, 'coverage': 'incomplete', 'summary_es': 'PRIVATE-REVIEW'}, indent=2)
            self.write_execution(dest, raw)
            self.assertEqual(collect(dest, {**self.env, 'RUNNER_TEMP': temp}), 1)
            report = json.loads((dest / 'report.json').read_text(encoding='utf-8'))
            self.assertEqual(report['status'], 'PARTIAL')
            self.assertEqual(report['response_sha256'], hashlib.sha256(raw.encode()).hexdigest())
            self.assertNotIn('PRIVATE-REVIEW', canonical(report))
            self.assertNotIn('PRIVATE-REVIEW', (dest / 'INFORME.txt').read_text(encoding='utf-8'))
            pending = json.loads((dest / 'review.pending.json').read_text(encoding='utf-8'))
            self.assertEqual(pending['review']['summary_es'], 'PRIVATE-REVIEW')
            workflow = (Path(__file__).resolve().parent.parent / '.github/workflows/claude-factory-review.yml').read_text(encoding='utf-8')
            self.assertNotIn('review.pending.json', workflow)
            with self.assertRaises(Blocked): collect(dest, {**self.env, 'RUNNER_TEMP': temp})

    def test_request_includes_workflow_but_excludes_state_and_credentials(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'config.json').write_text(canonical({k: False for k in
                ('enabled', 'external_calls_enabled', 'erp_access_enabled', 'publication_enabled')}))
            (root / '.github/workflows').mkdir(parents=True)
            (root / '.github/workflows/claude-factory-review.yml').write_text('name: fixture')
            (root / '.env').write_text('DO-NOT-INCLUDE')
            (root / 'state').mkdir()
            (root / 'state/old.json').write_text('OLD-TASK-DO-NOT-INCLUDE')
            manifest, request = build_request(root, 'a' * 40)
            self.assertIn('.github/workflows/claude-factory-review.yml', manifest['files'])
            self.assertNotIn('DO-NOT-INCLUDE', request)
            self.assertEqual(manifest['review_status'], 'NOT_RUN')
            with patch.dict('os.environ', {'GITHUB_OUTPUT': str(root / 'job-output.txt')}):
                prepare(root, root / 'outputs/claude-review', 'a' * 40)
            args = (root / 'job-output.txt').read_text(encoding='utf-8')
            # OAuth credentials are ignored in bare mode (Anthropic auth docs).
            self.assertNotIn('--bare', args)
            self.assertIn('--safe-mode', args)
            self.assertIn('--disallowedTools "*"', args)
            self.assertNotIn('--tools ""', args)
            self.assertIn('--append-system-prompt-file', args)
            self.assertNotIn('--json-schema', args)
            self.assertIn('ESQUEMA DEL INFORME:', request)
            with patch('factory2.actions_review.MAX_REQUEST_BYTES', 10), self.assertRaises(Blocked):
                build_request(root, 'a' * 40)


if __name__ == '__main__':
    unittest.main()
