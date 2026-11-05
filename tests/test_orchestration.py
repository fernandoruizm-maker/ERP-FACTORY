import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from factory2.codex_adapter import SafeCodexAgent, allowlisted_environment
from factory2.core import Blocked, file_digest
from factory2.orchestrator import run_simulated
from factory2.providers import BUILD_SCHEMA
from factory2.runner import test_command
from tests.operation_fixtures import coordinator


class OrchestrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.trusted = self.root / 'trusted'
        (self.trusted / 'tests').mkdir(parents=True)
        for name in ('test_example.py', 'example.test.mjs', 'example.test.ts', '__init__.py'):
            (self.trusted / 'tests' / name).write_text('PRUEBA FICTICIA NO EJECUTAR')
        self.hashes = {'tests/'+p.name: file_digest(p) for p in (self.trusted/'tests').iterdir()}
        self.profiles = {'python': ['tests/test_example.py'], 'javascript': ['tests/example.test.mjs'],
                         'typescript': ['tests/example.test.ts']}
        self.proposal = {'summary_es': 'Ficticio', 'edits': [{'path': 'src/demo.py', 'content': 'FICTICIO NO EJECUTAR'}]}
        self.seen = []
        self.coordinator = coordinator(self.root)

    def builder(self, brief):
        self.seen.append('build')
        return self.proposal

    def runner(self, candidate, profile, names, artifact_hash):
        self.seen.append(profile)
        self.assertEqual((candidate/'src/demo.py').read_text(), 'FICTICIO NO EJECUTAR')
        for name, expected in self.hashes.items():
            self.assertEqual(file_digest(candidate/name), expected)
        return {'status': 'PASS', 'test_count': 2, 'execution': 'SIMULATED',
                'profile': profile, 'artifact_digest': artifact_hash}

    def reviewer(self, evidence):
        self.seen.append('review')
        self.assertEqual(len(evidence['tests']), 3)
        return {'artifact_digest': evidence['artifact_digest'], 'verdict': 'PASS',
                'summary_es': 'Revision ficticia, no Claude', 'findings': []}

    def run_pipeline(self, **changes):
        args = {'trusted_test_root': self.trusted, 'trusted_hashes': self.hashes, 'profiles': self.profiles,
                'builder': self.builder, 'runner': self.runner, 'reviewer': self.reviewer, 'coordinator': self.coordinator}
        args.update(changes)
        return run_simulated(self.root, {'client': 'FICTICIO'}, **args)

    def test_build_mount_trusted_tests_test_then_review_with_doubles(self):
        result = self.run_pipeline()
        self.assertEqual(self.seen, ['build', 'python', 'javascript', 'typescript', 'review'])
        self.assertEqual(result['status'], 'SIMULATED_COMPLETE')
        self.assertFalse(result['publication_allowed'])
        self.assertEqual(result['human_approvals'], 0)
        self.assertIn('NOT_PROVIDER_OR_DOCKER', result['evidence_mode'])
        saved = json.loads((self.root/'candidates'/result['candidate_digest']/'pipeline.json').read_text())
        self.assertEqual(saved, result)

    def test_failed_tests_stop_review_without_retry_and_keep_earlier_tests(self):
        def runner(candidate, profile, names, artifact):
            if profile == 'javascript':
                self.seen.append('failed-js')
                return {'status': 'FAIL'}
            return self.runner(candidate, profile, names, artifact)
        result = self.run_pipeline(runner=runner)
        self.assertEqual(result['status'], 'BLOCKED')
        self.assertEqual(self.seen, ['build', 'python', 'failed-js'])
        self.assertEqual(len(result['tests']), 1)

    def test_wrong_artifact_or_no_tests_never_reaches_review(self):
        result = self.run_pipeline(runner=lambda *_: {'status': 'PASS', 'test_count': 0, 'execution': 'SIMULATED'})
        self.assertEqual(result['status'], 'BLOCKED')
        self.assertEqual(self.seen, ['build'])

    def test_review_failure_preserves_completed_test_evidence(self):
        def reviewer(_):
            self.seen.append('review-failure')
            raise TimeoutError('do not log this fictitious provider text')
        result = self.run_pipeline(reviewer=reviewer)
        self.assertEqual(result['status'], 'BLOCKED')
        self.assertEqual(len(result['tests']), 3)
        self.assertNotIn('do not log', json.dumps(result))

    def test_test_mutation_by_double_is_detected(self):
        def runner(candidate, profile, names, artifact):
            result = self.runner(candidate, profile, names, artifact)
            (candidate/names[0]).write_text('ALTERADO')
            return result
        result = self.run_pipeline(runner=runner)
        self.assertEqual(result['status'], 'BLOCKED')
        self.assertNotIn('review', self.seen)

    def test_untrusted_manifest_blocks_before_build(self):
        with self.assertRaises(Blocked):
            self.run_pipeline(trusted_hashes={**self.hashes, 'tests/test_example.py': 'bad'})
        self.assertEqual(self.seen, [])

    def test_builder_cannot_replace_trusted_tests(self):
        self.proposal['edits'][0]['path'] = 'tests/test_example.py'
        with self.assertRaises(Blocked):
            self.run_pipeline()

    def test_repeated_candidate_is_not_overwritten(self):
        self.run_pipeline()
        with self.assertRaises(Blocked):
            self.run_pipeline()

    def test_cwd_is_not_used_for_test_path_resolution(self):
        with patch('factory2.runner.Path.cwd', side_effect=AssertionError('Must use candidate')):
            command = test_command('python', ['tests/test_example.py'], directory=self.trusted)
        self.assertEqual(command, ['python', '-m', 'unittest', '-v', 'tests.test_example'])

    def test_tests_directory_shorthand_missing_file_and_duplicate_block(self):
        for files in (['tests'], ['tests/test_missing.py'], ['tests/test_example.py']*2):
            with self.subTest(files=files), self.assertRaises(Blocked):
                test_command('python', files, directory=self.trusted)


class CodexWrapperTests(unittest.TestCase):
    def test_whitelist_removes_secrets_proxies_and_language_injection(self):
        root = Path('isolated-fictitious')
        source = {'PATH': 'FICTICIO', 'SYSTEMROOT': 'FICTICIO', 'GITHUB_PAT': 'SYNTHETIC',
                  'TOKEN': 'SYNTHETIC', 'OPENAI_API_KEY': 'SYNTHETIC', 'PYTHONPATH': 'INJECTION',
                  'NODE_OPTIONS': 'INJECTION', 'HTTPS_PROXY': 'PROXY', 'CODEX_HOME': 'OLD', 'USERPROFILE': 'OLD'}
        result = allowlisted_environment(source, root)
        self.assertEqual(set(result), {'PATH', 'SYSTEMROOT', 'HOME', 'USERPROFILE', 'CODEX_HOME', 'PYTHONDONTWRITEBYTECODE'})
        self.assertEqual(result['CODEX_HOME'], str(root/'codex-home'))
        self.assertEqual(source['CODEX_HOME'], 'OLD')

    def test_mocked_launch_receives_whitelist_and_controls_without_real_process(self):
        proposal = {'summary_es': 'Ficticio', 'edits': [{'path': 'src/a.py', 'content': 'x=1'}]}
        def runner(command, **kwargs):
            self.assertNotIn('GITHUB_PAT', kwargs['env'])
            self.assertNotIn('PYTHONPATH', kwargs['env'])
            self.assertIn('--ignore-user-config', command)
            self.assertIn('--ephemeral', command)
            self.assertEqual(command[command.index('--sandbox')+1], 'read-only')
            self.assertIn('shell_tool', command)
            output = Path(command[command.index('--output-last-message')+1])
            output.write_text(json.dumps(proposal), encoding='utf-8')
            return SimpleNamespace(returncode=0, stdout='{"type":"completed"}\n')
        with patch.dict(os.environ, {'GITHUB_PAT': 'SYNTHETIC', 'PYTHONPATH': 'SYNTHETIC'}):
            result = SafeCodexAgent(runner=runner, executable='FICTICIO-NOT-EXECUTED').ask('builder', 'Ficticio', {}, BUILD_SCHEMA)
            self.assertEqual(os.environ['GITHUB_PAT'], 'SYNTHETIC')
        self.assertEqual(result, proposal)

    def test_live_runner_is_not_wired(self):
        with self.assertRaisesRegex(Blocked, 'NOT_CONNECTED'):
            SafeCodexAgent().ask('builder', 'Ficticio', {}, BUILD_SCHEMA)

    def test_tool_events_are_rejected_even_with_valid_proposal(self):
        def runner(command, **kwargs):
            Path(command[command.index('--output-last-message')+1]).write_text('{"summary_es":"Ficticio","edits":[]}')
            return SimpleNamespace(returncode=0, stdout='{"item":{"type":"command_execution"}}')
        with self.assertRaises(Blocked):
            SafeCodexAgent(runner=runner, executable='FICTICIO').ask('builder', 'Ficticio', {}, BUILD_SCHEMA)


if __name__ == '__main__':
    unittest.main()
