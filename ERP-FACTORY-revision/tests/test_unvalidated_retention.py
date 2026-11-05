"""Synthetic responses only. No provider, credentials or network integration."""
import io
import json
from pathlib import Path
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

import test_private_review as fixtures
from reviewer.contract import canonical, sha256
from reviewer.material import archive_material
from reviewer.runtime import (UNVALIDATED_NOTICE, collect, collect_file, preflight, prepare,
                              validate_result)
from protocol_fixtures import protocol_bundle
prepare = fixtures.prepare

MARKER = 'FICTICIO_PRIVADO_NO_PUBLICAR_241'


class UnvalidatedRetentionTests(unittest.TestCase):
    def setUp(self):
        self.context = {'TRUSTED_REVIEWER_SHA': fixtures.TRUSTED, 'INPUT_SOURCE_SHA': fixtures.SOURCE,
            'GITHUB_REPOSITORY': 'fernandoruizm-maker/ERP-FACTORY-revision',
            'REPOSITORY_PRIVATE': 'true', 'GITHUB_REF': 'refs/heads/main',
            'GITHUB_ACTOR_ID': '342326625', 'GITHUB_ACTOR': 'fernandoruizm-maker',
            'TRIGGERING_ACTOR': 'fernandoruizm-maker', 'GITHUB_RUN_ATTEMPT': '1',
            'AUTHORIZE_ANTHROPIC': 'true', 'GITHUB_RUN_ID': '123', 'WORKFLOW_SHA': fixtures.WORKFLOW}
        self.policy = {'repository': self.context['GITHUB_REPOSITORY'], 'execution_enabled': True}
        self.provenance = preflight(self.policy, self.context, fixtures.TRUSTED)
        material = archive_material(fixtures.archive(), fixtures.SOURCE)
        self.material = material
        self.result = {'source_sha': fixtures.SOURCE, 'factory_digest': material['factory_digest'],
            'reviewed_files': list(material['files']), 'coverage': 'complete', 'cross_component_review': True,
            'verdict': 'PASS', 'summary_es': MARKER, 'findings': [], 'limitations_es': ['Ficticio.']}
        self.finding = {'severity': 'medium', 'file': 'src/ficticio.py', 'line': 1,
                        'evidence_es': MARKER, 'impact_es': MARKER, 'recommendation_es': MARKER}

    def encode(self, changes):
        return canonical(protocol_bundle(self.material, {**self.result, **changes}))

    def run_case(self, raw, reason, *, retain=True, event_changes=None, conclusion='success',
                 extra_event=None, provenance=None, bad_material=False):
        with tempfile.TemporaryDirectory() as temp:
            work = Path(temp)
            receipt, _ = prepare(work, fixtures.archive(), fixtures.SOURCE)
            event = {'type': 'result', 'subtype': 'success', 'is_error': False,
                     'num_turns': 1, 'permission_denials': [], 'result': raw}
            event.update(event_changes or {})
            events = ([extra_event] if extra_event is not None else []) + [event]
            with redirect_stdout(io.StringIO()) as console, \
                 patch('reviewer.runtime.validate_result', wraps=validate_result) as validate:
                report = collect(work, 'd' * 64 if bad_material else receipt, fixtures.SOURCE,
                                 events, conclusion, provenance if provenance is not None else self.provenance)
            self.assertLessEqual(validate.call_count, 1)  # Never retry or revalidate.
            self.assertEqual(report['status'], 'BLOCKED')
            self.assertEqual(report['reason_code'], reason)
            self.assertFalse(report['publication_allowed'])
            self.assertEqual(report['human_approvals'], 0)
            dest = work / 'artifacts'
            self.assertFalse((dest / 'response.txt').exists())
            path = dest / 'response.unvalidated.txt'
            self.assertEqual(path.exists(), retain)
            hashes = json.loads((dest / 'SHA256.json').read_text(encoding='utf-8'))
            if retain:
                self.assertTrue(report['unvalidated_response_saved'])
                self.assertEqual(path.read_bytes(), raw.encode('utf-8'))
                self.assertEqual(report['response_sha256'], sha256(path.read_bytes()))
                self.assertEqual(hashes['response.unvalidated.txt'], report['response_sha256'])
                self.assertIn(UNVALIDATED_NOTICE, (dest / 'INFORME.txt').read_text(encoding='utf-8'))
            else:
                self.assertIsNot(report.get('unvalidated_response_saved'), True)
                self.assertNotIn('response.unvalidated.txt', hashes)
            for name in ('report.json', 'INFORME.txt', 'diagnostic.json'):
                self.assertNotIn(MARKER, (dest / name).read_text(encoding='utf-8'))
            self.assertNotIn(MARKER, console.getvalue())
            self.assertNotIn('review', report)

    def test_retain_invalid_json(self):
        self.run_case(MARKER + ' {invalid', 'INVALID_JSON')

    def test_retain_report_structure(self):
        self.run_case(self.encode({'unexpected': MARKER}), 'REPORT_STRUCTURE')

    def test_retain_version_mismatch(self):
        self.run_case(self.encode({'source_sha': fixtures.TRUSTED}), 'VERSION_MISMATCH')

    def test_retain_coverage_structure(self):
        self.run_case(self.encode({'reviewed_files': MARKER}), 'COVERAGE_STRUCTURE')

    def test_retain_invalid_verdict(self):
        self.run_case(self.encode({'verdict': 'MAYBE'}), 'INVALID_VERDICT')

    def test_retain_missing_limitations(self):
        self.run_case(self.encode({'limitations_es': []}), 'MISSING_LIMITATIONS')

    def test_retain_invalid_findings(self):
        self.run_case(self.encode({'findings': MARKER}), 'INVALID_FINDINGS')

    def test_retain_finding_structure(self):
        self.run_case(self.encode({'findings': [{'detail_es': MARKER}]}), 'FINDING_STRUCTURE')

    def test_retain_invalid_finding_evidence(self):
        self.run_case(self.encode({'findings': [{**self.finding, 'line': 99}]}),
                      'INVALID_FINDING_EVIDENCE')

    def test_retain_contradictory_pass(self):
        self.run_case(self.encode({'findings': [{**self.finding, 'severity': 'high'}]}),
                      'CONTRADICTORY_PASS')

    def test_markdown_unicode_and_crlf_are_preserved_exactly(self):
        raw = '```json\r\n' + json.dumps({**self.result, 'summary_es': MARKER + ' ñ'},
                                        ensure_ascii=False, indent=2) + '\r\n```\r\n'
        self.run_case(raw, 'INVALID_JSON', event_changes={'num_turns': 2})

    def test_exact_100000_byte_boundary_is_retained(self):
        raw = self.encode({'unexpected': MARKER})
        self.run_case(raw + ' ' * (100000 - len(raw.encode('utf-8'))), 'REPORT_STRUCTURE')

    def test_exclude_possible_secret(self):
        raw = self.encode({'summary_es': MARKER + ' github_pat_' + 'x' * 40})
        self.run_case(raw, 'POSSIBLE_SECRET', retain=False)

    def test_exclude_output_safety_or_size(self):
        # The decoded token matches; the original JSON text deliberately does not.
        raw = self.encode({'summary_es': MARKER + ' github_pat_' + 'x' * 40})
        raw = raw.replace('github_pat_', '\\u0067ithub_pat_')
        self.run_case(raw, 'OUTPUT_SAFETY_OR_SIZE', retain=False)

    def test_exclude_result_missing_or_too_large(self):
        self.run_case(None, 'RESULT_MISSING_OR_TOO_LARGE', retain=False)

    def test_exclude_result_execution_invalid(self):
        self.run_case(MARKER, 'RESULT_EXECUTION_INVALID', retain=False, event_changes={'num_turns': 3})

    def test_exclude_action_failed(self):
        self.run_case(MARKER, 'ACTION_FAILED', retain=False, conclusion='failure')

    def test_exclude_provider_error_final_event(self):
        self.run_case(MARKER, 'RESULT_EXECUTION_INVALID', retain=False,
                      event_changes={'is_error': True, 'subtype': 'error_during_execution'})

    def test_exclude_any_provider_error_even_with_successful_final_event(self):
        for event in ({'type': 'error', 'message': MARKER}, {'type': 'system', 'error': MARKER},
                      {'type': 'system', 'subtype': 'error_notice', 'message': MARKER}):
            with self.subTest(event=event):
                self.run_case(MARKER, 'RESULT_EXECUTION_INVALID', retain=False, extra_event=event)

    def test_exclude_denials_or_invalid_turns(self):
        for change in ({'permission_denials': [{}]}, {'permission_denials': None},
                       {'num_turns': 0}, {'num_turns': True}, {'is_error': 0}):
            with self.subTest(change=change):
                self.run_case(MARKER, 'RESULT_EXECUTION_INVALID', retain=False, event_changes=change)

    def test_exclude_multiple_result_events(self):
        self.run_case(MARKER, 'RESULT_EVENT_COUNT', retain=False, extra_event={'type': 'result'})

    def test_invalid_json_with_credential_pattern_is_never_retained(self):
        self.run_case(MARKER + ' {bad github_pat_' + 'x' * 40, 'POSSIBLE_SECRET', retain=False)

    def test_over_100000_bytes_is_never_retained(self):
        self.run_case(MARKER + 'x' * 100001, 'RESULT_MISSING_OR_TOO_LARGE', retain=False)
        self.run_case(MARKER + 'ñ' * 50001, 'RESULT_MISSING_OR_TOO_LARGE', retain=False)

    def test_exclude_material_verification_failure(self):
        self.run_case(MARKER, 'MATERIAL_VERIFICATION_FAILED', retain=False, bad_material=True)

    def test_exclude_provenance_failure(self):
        self.run_case(MARKER, 'PROVENANCE_INVALID', retain=False,
                      provenance={**self.provenance, 'source_sha': fixtures.TRUSTED})

    def test_cli_keeps_unvalidated_text_out_of_console_and_other_reports(self):
        from reviewer.cli import main
        with tempfile.TemporaryDirectory() as temp:
            work = Path(temp)
            receipt, _ = prepare(work, fixtures.archive(), fixtures.SOURCE)
            event = {'type': 'result', 'subtype': 'success', 'is_error': False,
                     'num_turns': 1, 'permission_denials': [], 'result': MARKER}
            (work / 'claude-execution-output.json').write_text(canonical([event]), encoding='utf-8')
            context = {**self.context, 'REVIEW_WORKDIR': str(work), 'RUNNER_TEMP': str(work),
                       'MATERIAL_SHA256': receipt, 'CLAUDE_CONCLUSION': 'success'}
            real_read = Path.read_text
            def read_policy_only(path, *args, **kwargs):
                return canonical(self.policy) if path.name == 'policy.json' else real_read(path, *args, **kwargs)
            with patch('sys.argv', ['entrypoint.py', 'collect']), \
                 patch.dict('os.environ', context, clear=True), patch.object(Path, 'read_text', read_policy_only), \
                 patch('reviewer.cli.subprocess.run') as git, \
                 patch('reviewer.material.download_archive') as download, redirect_stdout(io.StringIO()) as console:
                git.return_value.stdout = fixtures.TRUSTED + '\n'
                self.assertEqual(main(), 1)
            download.assert_not_called()
            self.assertEqual(console.getvalue(), 'PRIVATE_REVIEW_BLOCKED\n')
            self.assertEqual((work / 'artifacts/response.unvalidated.txt').read_bytes(), MARKER.encode('utf-8'))
            for name in ('report.json', 'INFORME.txt', 'diagnostic.json'):
                self.assertNotIn(MARKER, (work / 'artifacts' / name).read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
