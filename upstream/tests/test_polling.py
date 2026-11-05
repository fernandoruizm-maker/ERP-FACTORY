import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from urllib.error import HTTPError

from factory.mvp.common import Blocked, load_config
from factory.mvp.github import GitHub
from factory.mvp.queue import Queue
from factory.mvp.pipeline import Pipeline
from examples.critical_backend import SimulatedGitHub, ISSUE
from test_mvp import MockAgents, MockRunner


class PollGitHub(SimulatedGitHub):
    def __init__(self):
        super().__init__()
        self.item = copy.deepcopy(ISSUE)
        self.item.update({'state': 'open', 'updated_at': '2026-11-03T20:00:00Z'})
        self.events = [{'id': 44, 'event': 'labeled', 'label': {'name': 'ai-factory'},
                        'actor': {'login': 'fernandoruizm-maker', 'type': 'User'},
                        'created_at': self.item['updated_at']}]
        self.items = [self.item]
        self.block_governance = False

    def issue(self, number):
        return copy.deepcopy(self.item)

    def open_issues(self, label, cache):
        return copy.deepcopy(self.items)

    def issue_events(self, number):
        return copy.deepcopy(self.events)

    def governance(self, branch):
        if self.block_governance:
            raise Blocked('Missing required checks')


class PollingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.queue = Queue(self.root / 'jobs.sqlite3')
        self.config = load_config(Path(__file__).parents[1] / 'config.example.json')
        self.config['state_dir'] = str(self.root)
        self.gh = PollGitHub()

    def tearDown(self):
        self.tmp.cleanup()

    def poll(self):
        from factory.mvp.polling import poll_once
        return poll_once(self.config, self.gh, self.queue)

    def test_one_job_per_authorized_label_even_after_restart_and_comments(self):
        self.assertEqual(len(self.poll()['enqueued']), 1)
        self.queue = Queue(self.root / 'jobs.sqlite3')
        self.assertEqual(self.poll()['enqueued'], [])
        self.gh.item['updated_at'] = '2026-11-03T20:02:00Z'
        self.assertEqual(self.poll()['enqueued'], [])
        self.assertEqual(len(self.queue.list()), 1)

    def test_bot_unknown_actor_revoked_label_and_edited_issue_are_not_enqueued(self):
        for variant in ('bot', 'unknown', 'revoked', 'edited', 'no_event', 'no_label', 'pr'):
            with self.subTest(variant=variant):
                self.gh = PollGitHub()
                if variant == 'bot':
                    self.gh.events[0]['actor']['type'] = 'Bot'
                elif variant == 'unknown':
                    self.gh.events[0]['actor']['login'] = 'stranger'
                elif variant == 'revoked':
                    self.gh.events[0]['event'] = 'unlabeled'
                elif variant == 'edited':
                    self.gh.item['updated_at'] = '2026-11-03T20:01:00Z'
                elif variant == 'no_event':
                    self.gh.events = []
                elif variant == 'no_label':
                    self.gh.item['labels'] = []
                else:
                    self.gh.item['pull_request'] = {}
                self.assertEqual(self.poll()['enqueued'], [])
        self.assertEqual(self.queue.list(), [])

    def test_reapplying_label_creates_new_request(self):
        self.poll()
        self.gh.events.append({**self.gh.events[0], 'id': 45})
        self.assertEqual(len(self.poll()['enqueued']), 1)
        self.assertEqual(len(self.queue.list()), 2)

    def test_current_write_permission_is_required(self):
        self.gh.can_write = lambda login: False
        self.assertEqual(self.poll()['enqueued'], [])

    def test_pipeline_revalidates_label_and_stops_at_human_approval(self):
        job_id = self.poll()['enqueued'][0]
        job = self.queue.claim()
        pipeline = Pipeline(self.config, self.gh, MockAgents(), MockRunner(), self.queue)
        result = pipeline.execute(job)
        self.assertEqual(result['state'], 'WAITING_APPROVAL')
        self.assertFalse(result['deployment_attempted'])
        self.assertEqual(self.queue.get(job_id)['state'], 'WAITING_APPROVAL')
        checkpoint = json.loads(self.queue.get(job_id)['checkpoint'])
        self.gh.events.append({**self.gh.events[0], 'id': 45, 'event': 'unlabeled'})
        count = len(self.gh.publications)
        with self.assertRaises(Blocked):
            pipeline.publish(job_id, checkpoint)
        self.assertEqual(len(self.gh.publications), count)

    def test_missing_governance_never_claims_job_or_calls_agents(self):
        from factory.mvp.polling import cycle
        self.gh.block_governance = True
        agent = MockAgents()
        result = cycle(self.config, self.gh, agent, MockRunner(), self.queue)
        self.assertEqual(result['state'], 'BLOCKED')
        self.assertEqual(agent.roles, [])
        self.assertEqual(self.queue.list()[0]['state'], 'QUEUED')
        self.assertEqual(self.gh.publications, [])

    def test_api_backoff_survives_restart(self):
        from factory.mvp.polling import cycle
        from factory.mvp.common import RateLimited
        self.gh.open_issues = lambda *args: (_ for _ in ()).throw(RateLimited(123456))
        first = cycle(self.config, self.gh, MockAgents(), MockRunner(), self.queue, now=123000)
        self.assertEqual(first['state'], 'BACKOFF')
        self.queue = Queue(self.root / 'jobs.sqlite3')
        self.gh.open_issues = lambda *args: self.fail('API called before reset time')
        second = cycle(self.config, self.gh, MockAgents(), MockRunner(), self.queue, now=123001)
        self.assertEqual(second['state'], 'BACKOFF')

    def test_pause_requested_during_poll_prevents_starting_a_job(self):
        from factory.mvp.polling import cycle
        agent = MockAgents()
        result = cycle(self.config, self.gh, agent, MockRunner(), self.queue, should_pause=lambda: True)
        self.assertEqual(result['state'], 'PAUSED')
        self.assertEqual(self.queue.list()[0]['state'], 'QUEUED')
        self.assertEqual(agent.roles, [])

    def test_revoked_label_is_rejected_before_any_model_call(self):
        self.poll()
        self.gh.events.append({**self.gh.events[0], 'id': 45, 'event': 'unlabeled'})
        agent = MockAgents()
        with self.assertRaises(Blocked):
            Pipeline(self.config, self.gh, agent, MockRunner(), self.queue).execute(self.queue.claim())
        self.assertEqual(agent.roles, [])


class HttpResponse(io.BytesIO):
    def __init__(self, value, headers=None):
        super().__init__(json.dumps(value).encode())
        self.headers = headers or {}


class PollHTTPTests(unittest.TestCase):
    def test_conditional_request_reuses_persisted_cache_on_304(self):
        gh = GitHub('o/r', token='test')
        calls = []
        class Opener:
            def open(self, request, timeout):
                calls.append(dict((k.lower(), v) for k, v in request.header_items()))
                if len(calls) == 1:
                    return HttpResponse([{'number': 1}], {'ETag': 'revision-1'})
                raise HTTPError(request.full_url, 304, 'Not Modified', {}, None)
        gh.opener = Opener()
        with tempfile.TemporaryDirectory() as folder:
            cache = Queue(Path(folder) / 'cache.db')
            a = gh.conditional_get('/issues?state=open', cache)
            b = gh.conditional_get('/issues?state=open', Queue(Path(folder) / 'cache.db'))
            self.assertEqual(a, b)
            self.assertEqual(calls[1]['if-none-match'], 'revision-1')

    def test_rate_limit_retry_after_is_honored(self):
        import time
        from factory.mvp.common import RateLimited
        gh = GitHub('o/r', token='test')
        class Opener:
            def open(self, request, timeout):
                raise HTTPError(request.full_url, 429, 'Limited', {'Retry-After': '600'}, None)
        gh.opener = Opener()
        before = time.time()
        with self.assertRaises(RateLimited) as raised:
            gh.get('/issues')
        self.assertGreaterEqual(raised.exception.retry_at, before + 600)

    def test_app_token_rate_limit_also_delays_the_pilot(self):
        from factory.mvp.auth import InstallationToken
        from factory.mvp.common import RateLimited
        auth = InstallationToken('o/r', 123, 456, 'unused.pem', clock=lambda: 10000)
        auth.jwt = lambda: 'test-jwt'
        class Opener:
            def open(self, request, timeout):
                raise HTTPError(request.full_url, 429, 'Limited', {'Retry-After': '900'}, None)
        auth.opener = Opener()
        with self.assertRaises(RateLimited) as raised:
            auth.get_token()
        self.assertEqual(raised.exception.retry_at, 10900)

    def test_not_modified_response_can_extend_polling_interval(self):
        gh = GitHub('o/r', token='test')
        class Opener:
            def open(self, request, timeout):
                raise HTTPError(request.full_url, 304, 'Not Modified', {'X-Poll-Interval': '900'}, None)
        gh.opener = Opener()
        gh._response('GET', '/repos/o/r/issues', etag='revision-1')
        self.assertEqual(getattr(gh, 'poll_interval', 0), 900)

    def test_issue_pagination_excludes_pull_requests(self):
        gh = GitHub('o/r', token='test')
        pages = [[{'number': n, 'pull_request': {}} for n in range(100)],
                 [{'number': 101, 'state': 'open', 'labels': [{'name': 'ai-factory'}]}]]
        calls = []
        def read(path, cache):
            calls.append(path)
            return pages[len(calls)-1]
        gh.conditional_get = read
        self.assertEqual(gh.open_issues('ai-factory', None)[0]['number'], 101)
        self.assertEqual(len(calls), 2)


if __name__ == '__main__':
    unittest.main()
