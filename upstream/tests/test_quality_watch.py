import copy
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from factory.mvp.quality_watch import watch
from factory.mvp.common import Blocked


class QualityWatchTests(unittest.TestCase):
    def setUp(self):
        self.config = {'repository': 'owner/demo', 'base_branch': 'main',
                       'context_prefixes': ['src/', 'tests/'], 'quality_watch_prs': [18]}
        self.pr = {'state': 'open', 'merged': False,
                   'head': {'sha': 'a'*40, 'repo': {'full_name': 'owner/demo'}},
                   'base': {'ref': 'main', 'repo': {'full_name': 'owner/demo'}}}
        self.github = Mock()
        self.comparison = {'files': [{'filename': 'tests/test_failure.py'}]}
        self.github.get.side_effect = lambda path: self.comparison if path.startswith('/compare/') else self.pr
        self.github.base.return_value = 'b'*40
        self.github.changed_paths.return_value = ['tests/test_failure.py']
        self.github.snapshot.return_value = {'tests/test_failure.py': 'test'}
        self.queue = Mock()
        self.queue.list.return_value = []
        self.queue.meta_get.return_value = None
        self.runner = Mock()
        self.runner.run.return_value = SimpleNamespace(green=False, skipped=0, exit_code=1,
            tests_run=36, failures=1, errors=0)

    def states(self, context):
        return [c.args[2] for c in self.github.status.call_args_list if c.args[1] == context]

    def test_failed_tests_publish_failure_and_never_approve(self):
        watch(self.config, self.github, self.runner, self.queue)
        self.assertEqual(self.states('factory/quality'), ['pending', 'failure'])
        self.assertEqual(self.states('factory/human-approval'), ['pending'])
        self.github.snapshot.assert_called_once_with('a'*40, ['src/', 'tests/'])

    def test_green_tests_do_not_replace_full_review(self):
        self.runner.run.return_value.green = True
        self.runner.run.return_value.exit_code = 0
        self.runner.run.return_value.failures = 0
        watch(self.config, self.github, self.runner, self.queue)
        self.assertEqual(self.states('factory/quality'), ['pending', 'pending'])
        self.assertEqual(self.states('factory/human-approval'), ['pending'])

    def test_no_opt_in_does_not_read_or_execute(self):
        self.config.pop('quality_watch_prs')
        watch(self.config, self.github, self.runner, self.queue)
        self.github.get.assert_not_called()
        self.runner.run.assert_not_called()

    def test_closed_or_foreign_pr_never_executes(self):
        for variant in ('closed', 'foreign', 'base'):
            with self.subTest(variant=variant):
                pr = copy.deepcopy(self.pr)
                if variant == 'closed': pr['state'] = 'closed'
                if variant == 'foreign': pr['head']['repo']['full_name'] = 'stranger/demo'
                if variant == 'base': pr['base']['ref'] = 'other'
                self.github.get.side_effect = lambda path: pr
                watch(self.config, self.github, self.runner, self.queue)
                self.runner.run.assert_not_called()

    def test_runner_error_is_red_not_success(self):
        self.runner.run.side_effect = Blocked('untrusted text')
        watch(self.config, self.github, self.runner, self.queue)
        self.assertEqual(self.states('factory/quality'), ['pending', 'error'])
        self.assertNotIn('untrusted text', str(self.github.status.call_args_list))

    def test_changed_head_discards_result(self):
        changed = copy.deepcopy(self.pr)
        changed['head']['sha'] = 'c'*40
        self.github.get.side_effect = [self.pr, self.comparison, changed]
        watch(self.config, self.github, self.runner, self.queue)
        self.assertEqual(self.states('factory/quality'), ['pending'])
        self.queue.meta_set.assert_not_called()

    def test_outside_scope_does_not_execute(self):
        self.comparison['files'] = [{'filename':'erp/private.py'}]
        watch(self.config, self.github, self.runner, self.queue)
        self.runner.run.assert_not_called()
        self.assertEqual(self.states('factory/quality'), ['pending', 'error'])

    def test_invalid_allowlist_is_rejected(self):
        self.config['quality_watch_prs'] = [True]
        with self.assertRaises(Blocked):
            watch(self.config, self.github, self.runner, self.queue)

    def test_registered_job_is_not_overwritten(self):
        self.queue.list.return_value = [{'id': 'job'}]
        self.queue.get.return_value = {'checkpoint': '{"pr":{"number":18}}'}
        watch(self.config, self.github, self.runner, self.queue)
        self.github.status.assert_not_called()

    def test_previous_result_never_replaces_fresh_execution(self):
        self.queue.meta_get.return_value = {'state': 'failure'}
        watch(self.config, self.github, self.runner, self.queue)
        self.pr['head']['sha'] = 'c'*40
        watch(self.config, self.github, self.runner, self.queue)
        self.assertEqual(self.runner.run.call_count,2)
        self.queue.meta_get.assert_not_called()
        keys = [c.args[0] for c in self.queue.meta_set.call_args_list]
        self.assertNotEqual(keys[0], keys[1])

    def test_pause_never_runs_tests(self):
        watch(self.config, self.github, self.runner, self.queue, should_pause=lambda: True)
        self.runner.run.assert_not_called()

    def test_other_pr_sharing_tracked_commit_is_not_overwritten(self):
        self.queue.list.return_value = [{'id': 'job'}]
        self.queue.get.return_value = {'checkpoint': '{"pr":{"number":99,"head_sha":"'+'a'*40+'"}}'}
        watch(self.config, self.github, self.runner, self.queue)
        self.github.status.assert_not_called()
        self.runner.run.assert_not_called()

    def test_missing_pr_does_not_prevent_following_pr(self):
        self.config['quality_watch_prs'] = [17,18]
        self.github.get.side_effect = [Blocked('404'),self.pr,self.comparison,self.pr]
        results = watch(self.config, self.github, self.runner, self.queue)
        self.assertEqual([r['state'] for r in results], ['error','failure'])

    def test_pause_during_monitor_prevents_claim(self):
        from factory.mvp.polling import cycle
        self.queue.meta_get.return_value = 0
        with patch('factory.mvp.polling.poll_once',return_value={}), patch('factory.mvp.quality_watch.watch'):
            result=cycle(self.config,self.github,Mock(),self.runner,self.queue,
                         should_pause=Mock(side_effect=[False,True]))
        self.assertEqual(result['state'],'PAUSED')
        self.queue.claim.assert_not_called()

    def test_monitor_error_does_not_starve_queue(self):
        from factory.mvp.polling import cycle
        self.queue.meta_get.return_value = 0
        self.queue.claim.return_value = None
        with patch('factory.mvp.polling.poll_once',return_value={}), patch('factory.mvp.quality_watch.watch',side_effect=Blocked('404')):
            result=cycle(self.config,self.github,Mock(),self.runner,self.queue)
        self.queue.claim.assert_called_once()
        self.assertEqual(result['quality_watch'][0]['state'],'error')

    def test_scope_uses_immutable_commits_before_execution(self):
        watch(self.config,self.github,self.runner,self.queue)
        self.github.get.assert_any_call('/compare/'+'b'*40+'...'+'a'*40)
        self.github.changed_paths.assert_not_called()

    def test_truncated_comparison_blocks_execution(self):
        self.comparison['files'] = [{'filename':'tests/test_failure.py'}]*300
        watch(self.config,self.github,self.runner,self.queue)
        self.runner.run.assert_not_called()
        self.assertEqual(self.states('factory/quality'),['pending','error'])

    def test_new_head_of_registered_pr_is_protected(self):
        self.queue.list.return_value = [{'id':'job'}]
        self.queue.get.return_value = {'checkpoint':'{"pr":{"number":99,"head_sha":"'+'d'*40+'"}}'}
        watch(self.config,self.github,self.runner,self.queue)
        self.github.status.assert_not_called()
        self.runner.run.assert_not_called()

    def test_changed_execution_config_changes_cache_key(self):
        watch(self.config,self.github,self.runner,self.queue)
        first=self.queue.meta_set.call_args.args[0]
        self.config['runner_image']='different-pinned-image'
        watch(self.config,self.github,self.runner,self.queue)
        second=self.queue.meta_set.call_args.args[0]
        self.assertNotEqual(first,second)

    def test_registered_pr_adopting_head_during_tests_is_protected(self):
        self.queue.list.return_value=[{'id':'job'}]
        self.queue.get.return_value={'checkpoint':'{"pr":{"number":99,"head_sha":"'+'d'*40+'"}}'}
        other=copy.deepcopy(self.pr);other['head']['sha']='d'*40
        def get(path):
            if path=='/pulls/99': return other
            return self.comparison if path.startswith('/compare/') else self.pr
        self.github.get.side_effect=get
        result=self.runner.run.return_value
        def run(files):
            other['head']['sha']='a'*40
            return result
        self.runner.run.side_effect=run
        watch(self.config,self.github,self.runner,self.queue)
        self.assertEqual(self.states('factory/quality'),['pending'])
        self.queue.meta_set.assert_not_called()

    def test_docker_start_failure_is_error_not_test_failure(self):
        self.runner.run.return_value.exit_code=125
        self.runner.run.return_value.tests_run=0
        self.runner.run.return_value.failures=0
        watch(self.config,self.github,self.runner,self.queue)
        self.assertEqual(self.states('factory/quality'),['pending','error'])
