import copy
import json
from pathlib import Path
import tempfile
import unittest

from factory.mvp.approval import refresh
from factory.mvp.queue import Queue


class MergedApprovalTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.queue = Queue(Path(self.folder.name) / 'queue.db')
        self.job_id = self.queue.enqueue('request', {'issue_number': 3})
        self.saved = {'pr': {'number': 4, 'head_sha': 'reviewed-head'}, 'base_sha': 'old-base'}
        self.queue.set(self.job_id, 'APPROVED', self.saved)
        self.config = {'base_branch': 'main', 'repository': 'owner/repo'}
        self.pr = {'number': 4, 'state': 'closed', 'merged': True,
                   'head': {'sha': 'reviewed-head'},
                   'base': {'ref': 'main', 'sha': 'new-base', 'repo': {'full_name': 'owner/repo'}},
                   'merge_commit_sha': 'merge-sha', 'merged_at': '2026-11-04T01:52:15Z',
                   'merged_by': {'login': 'human'}}
        self.statuses = []
        owner = self
        class GitHub:
            def get(self, path):
                owner.assertEqual(path, '/pulls/4')
                return copy.deepcopy(owner.pr)
            def status(self, *args):
                owner.statuses.append(args)
        self.github = GitHub()

    def tearDown(self):
        self.folder.cleanup()

    def test_completed_merge_is_recorded_without_rewriting_historical_checks(self):
        self.assertEqual(refresh(self.config, self.github, self.queue, self.job_id), 'MERGED')
        saved = self.queue.get(self.job_id)
        self.assertEqual(saved['state'], 'MERGED')
        self.assertEqual(json.loads(saved['checkpoint'])['integration']['merge_commit_sha'], 'merge-sha')
        self.assertEqual(self.statuses, [])

    def test_a_different_merged_candidate_or_target_is_not_accepted_as_ours(self):
        original = copy.deepcopy(self.pr)
        for variant in ('head', 'branch', 'repository', 'missing_merge_sha', 'open'):
            with self.subTest(variant=variant):
                self.pr = copy.deepcopy(original)
                self.queue.set(self.job_id, 'APPROVED', self.saved)
                if variant == 'head':
                    self.pr['head']['sha'] = 'unreviewed-head'
                elif variant == 'branch':
                    self.pr['base']['ref'] = 'other'
                elif variant == 'repository':
                    self.pr['base']['repo']['full_name'] = 'other/repo'
                elif variant == 'missing_merge_sha':
                    self.pr['merge_commit_sha'] = None
                else:
                    self.pr['state'] = 'open'
                self.assertEqual(refresh(self.config, self.github, self.queue, self.job_id), 'BLOCKED')
                self.assertEqual(self.queue.get(self.job_id)['state'], 'BLOCKED')
                self.assertEqual(self.statuses, [])

    def test_closed_without_merge_does_not_become_merged(self):
        self.pr['merged'] = False
        self.assertEqual(refresh(self.config, self.github, self.queue, self.job_id), 'BLOCKED')
        self.assertEqual(self.queue.get(self.job_id)['state'], 'BLOCKED')
        self.assertEqual([s[2] for s in self.statuses], ['failure', 'pending'])


if __name__ == '__main__':
    unittest.main()
