"""Regressions found during the pre-integration review of PR #1."""
import copy
from dataclasses import replace
from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock

from examples.critical_backend import SimulatedGitHub, ISSUE
from factory.memory import Brain
from factory.mvp.approval import refresh
from factory.mvp.common import Blocked, digest, load_config
from factory.mvp.pipeline import Pipeline
from factory.mvp.queue import Queue
from test_mvp import MockAgents, MockRunner
from test_github_adapter import FakeTransport


class ReviewGuards(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.addCleanup(self.temp.cleanup)
        self.config = load_config(Path(__file__).parents[1] / 'config.example.json')
        self.config['state_dir'] = str(self.root)
        self.queue = Queue(self.root / 'queue.db')

    def test_legacy_protection_cannot_start_autonomous_work(self):
        gh = FakeTransport()
        # Names of checks alone do not prove App provenance or absence of bypass.
        with self.assertRaises(Blocked):
            gh.governance('main')

    def approval_fixture(self):
        self.job = self.queue.enqueue('approval', {'issue_number': 3})
        saved = {'pr': {'number': 4, 'head_sha': 'head'}, 'base_sha': 'base',
                 'config_sha': digest(self.config),
                 'brain_sha': Brain.load(self.config['brain_dir']).fingerprint}
        self.queue.set(self.job, 'WAITING_APPROVAL', saved)
        pr = {'number': 4, 'state': 'open', 'merged': False,
              'user': {'login': 'factory[bot]'}, 'head': {'sha': 'head'},
              'base': {'sha': 'base', 'ref': 'main',
                       'repo': {'full_name': self.config['repository']}}}
        gh = Mock()
        gh.get.return_value = pr
        gh.base.return_value = 'base'
        gh.can_write.return_value = True
        gh.reviews.return_value = [{'id': 1, 'state': 'APPROVED', 'commit_id': 'head',
            'submitted_at': datetime.now(timezone.utc).isoformat(),
            'user': {'login': self.config['human_reviewers'][0], 'type': 'User'}}]
        return gh, pr

    def test_retargeted_open_pr_invalidates_approval(self):
        for field in ('branch', 'repository'):
            with self.subTest(field=field):
                gh, pr = self.approval_fixture()
                if field == 'branch':
                    pr['base']['ref'] = 'unprotected'
                else:
                    pr['base']['repo']['full_name'] = 'different/repo'
                self.assertEqual(refresh(self.config, gh, self.queue, self.job), 'BLOCKED')
                self.assertFalse(any(c.args[2] == 'success' for c in gh.status.call_args_list))

    def test_target_change_during_review_read_does_not_publish_success(self):
        gh, pr = self.approval_fixture()
        changed = copy.deepcopy(pr)
        changed['base']['ref'] = 'unprotected'
        gh.get.side_effect = [pr, changed]
        self.assertEqual(refresh(self.config, gh, self.queue, self.job), 'BLOCKED')
        self.assertFalse(any(c.args[2] == 'success' for c in gh.status.call_args_list))

    def test_valid_target_still_requires_and_accepts_real_human_review(self):
        gh, _ = self.approval_fixture()
        gh.reviews.return_value = []
        self.assertEqual(refresh(self.config, gh, self.queue, self.job), 'WAITING_APPROVAL')
        gh, _ = self.approval_fixture()
        self.assertEqual(refresh(self.config, gh, self.queue, self.job), 'APPROVED')

    def pipeline_with_skips(self, phase):
        class SkippingRunner(MockRunner):
            def run(inner, files, pattern='test*.py'):
                result = super().run(files, pattern)
                selected = pattern == 'test*.py' and (
                    ('tests/test_factory_status.py' in files) == (phase == 'regression'))
                return replace(result, skipped=1) if selected else result
        self.queue.enqueue('issue', {'requester': self.config['allowed_requesters'][0],
            'issue_number': ISSUE['number'], 'issue_updated_at': ISSUE['updated_at']})
        gh = SimulatedGitHub()
        with self.assertRaises(Blocked):
            Pipeline(self.config, gh, MockAgents(), SkippingRunner(), self.queue).execute(self.queue.claim())
        self.assertEqual(gh.publications, [])

    def test_skipped_baseline_does_not_establish_verified_starting_point(self):
        self.pipeline_with_skips('baseline')

    def test_skipped_existing_tests_block_candidate_publication(self):
        self.pipeline_with_skips('regression')

    def test_new_architecture_decisions_are_loaded_and_invalidate_old_context(self):
        brain_root = self.root / 'brain'
        for name in ('stack.md', 'conventions.md', 'decisions/0001-control-plane.md'):
            path = brain_root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('original', encoding='utf-8')
        original = Brain.load(brain_root)
        decision = brain_root / 'decisions/0002-data-contract.md'
        decision.write_text('New approved data contract', encoding='utf-8')
        updated = Brain.load(brain_root)
        self.assertIn('decisions/0002-data-contract.md', dict(updated.documents))
        self.assertNotEqual(original.fingerprint, updated.fingerprint)
        decision.write_text('Changed contract', encoding='utf-8')
        self.assertNotEqual(updated.fingerprint, Brain.load(brain_root).fingerprint)
        decision.unlink()
        self.assertEqual(original.fingerprint, Brain.load(brain_root).fingerprint)


if __name__ == '__main__':
    unittest.main()
