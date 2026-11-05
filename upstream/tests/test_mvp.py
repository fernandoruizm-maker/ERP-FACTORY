from datetime import datetime, timezone, timedelta
import hashlib
import hmac
import json
from pathlib import Path
import tempfile
import unittest

from examples.critical_backend import SimulatedGitHub, ISSUE, FILES
from factory.mvp.approval import resolve_approval
from factory.mvp.common import Blocked, checked_edits, digest, load_config
from factory.mvp.pipeline import Pipeline
from factory.mvp.queue import Queue, worker_lock
from factory.mvp.runner import DockerRunner, parse_result
from factory.mvp.service import accept_event


class MockAgents:
    def __init__(self, verdict="PASS"):
        self.roles, self.verdict = [], verdict

    def ask(self, role, instruction, context, schema):
        self.roles.append(role)
        if role == "spec_writer":
            assert "NEW tests/test_factory_" in context["execution_constraints"]["tests"]
            return {"title": "Add status", "problem": "Missing status", "acceptance": ["status active"],
                    "design": "Extend return dict", "test_plan": "Assert new field", "open_questions": []}
        if role == "test_writer":
            return {"explanation": "test", "edits": [{"path": "tests/test_factory_status.py", "content": "# frozen"}]}
        if role == "builder":
            return {"explanation": "fix", "edits": [{"path": "src/api.py", "content": 'def get_customer(i): return {"id":i,"name":"Cliente","status":"active"}\n'}]}
        return {"verdict": self.verdict, "findings": [] if self.verdict == "PASS" else ["defect"], "rationale": "checked"}


class MockRunner:
    def __init__(self):
        self.calls = []
    def preflight(self):
        pass
    def run(self, files, pattern="test*.py"):
        self.calls.append((dict(files), pattern))
        focused = pattern != "test*.py"
        red = focused and '"status"' not in files["src/api.py"]
        ids = "test_new (regression.Case) ... " if focused else "test_old (baseline.Case) ... ok\n"
        if not focused and "tests/test_factory_status.py" in files:
            ids += "test_new (regression.Case) ... ok\n"
        output = ids + ("FAIL\nAssertionError: missing\nRan 1 test in 0.01s\nFAILED (failures=1)\n" if red
                        else "ok\nRan 2 tests in 0.01s\nOK\n")
        return parse_result(1 if red else 0, output, files)


class MVPTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.queue = Queue(self.root / "db.sqlite3")
        self.config = load_config(Path(__file__).parents[1] / "config.example.json")
        self.config["state_dir"] = str(self.root)

    def tearDown(self):
        self.temp.cleanup()

    def event(self):
        body = json.dumps({"action": "labeled", "repository": {"full_name": self.config["repository"]},
            "issue": ISSUE, "label": {"name": "ai-factory"},
            "sender": {"login": "fernandoruizm-maker", "type": "User"}}).encode()
        headers = {"X-GitHub-Event": "issues", "X-GitHub-Delivery": "delivery",
                   "X-Hub-Signature-256": "sha256=" + hmac.new(b"secret", body, hashlib.sha256).hexdigest()}
        return body, headers

    def test_webhook_receives_once(self):
        body, headers = self.event()
        a = accept_event(self.config, self.queue, body, headers, b"secret")
        b = accept_event(self.config, self.queue, body, headers, b"secret")
        self.assertEqual(a, b)
        self.assertEqual(len(self.queue.list()), 1)

    def test_bad_signature_does_not_enqueue(self):
        body, headers = self.event()
        with self.assertRaises(ValueError):
            accept_event(self.config, self.queue, body + b" ", headers, b"secret")
        self.assertEqual(self.queue.list(), [])

    def test_unauthorized_sender_rejected(self):
        body, headers = self.event()
        self.config["allowed_requesters"] = ["someone-else"]
        with self.assertRaises(Blocked):
            accept_event(self.config, self.queue, body, headers, b"secret")

    def test_delivery_collision(self):
        self.queue.enqueue("a", {"data": 1})
        with self.assertRaises(Blocked):
            self.queue.enqueue("a", {"data": 2})

    def test_claim_and_restart_recovery(self):
        ident = self.queue.enqueue("a", {"data": 1})
        self.assertEqual(self.queue.claim()["id"], ident)
        self.assertIsNone(self.queue.claim())
        self.queue.recover()
        self.assertEqual(self.queue.claim()["id"], ident)

    def test_second_worker_is_denied(self):
        path = self.root / "lock"
        with worker_lock(path):
            with self.assertRaises(Blocked):
                with worker_lock(path):
                    pass

    def test_builder_cannot_touch_tests_or_policies_or_escape(self):
        for path in ("tests/test_a.py", "brain/a.md", ".github/a.py", "src/../auth.py", "src/.codex/a.py", "src/NUL.py"):
            with self.subTest(path=path), self.assertRaises(Blocked):
                checked_edits([{"path": path, "content": "x"}], {}, phase="build", allowed_prefixes=["src/"])

    def test_test_writer_cannot_overwrite_test_or_product(self):
        for path in ("src/api.py", "tests/test_api.py", "tests/test_factory_a.py"):
            with self.assertRaises(Blocked):
                checked_edits([{"path": path, "content": "x"}], {path: "exists"}, phase="test", allowed_prefixes=[])

    def test_unpinned_image_fails(self):
        with self.assertRaises(Blocked):
            DockerRunner("python:latest")

    def test_case_colliding_edit_is_rejected(self):
        with self.assertRaises(Blocked):
            checked_edits([{"path": "src/API.py", "content": "x=1"}], {"src/api.py": "x=0"},
                          phase="build", allowed_prefixes=["src/"])

    def test_import_error_is_not_green_or_assertion_red(self):
        result = parse_result(1, "Ran 1 test in 0.1s\nFAILED (errors=1)", {})
        self.assertEqual(result.errors, 1)
        self.assertFalse(result.green)

    def test_issue_to_pr_stops_for_human(self):
        body, headers = self.event()
        ident = accept_event(self.config, self.queue, body, headers, b"secret")["job_id"]
        github, agent, runner = SimulatedGitHub(), MockAgents(), MockRunner()
        result = Pipeline(self.config, github, agent, runner, self.queue).execute(self.queue.claim())
        self.assertEqual(result["state"], "WAITING_APPROVAL")
        self.assertFalse(result["deployment_attempted"])
        self.assertEqual(self.queue.get(ident)["state"], "WAITING_APPROVAL")
        self.assertEqual(set(agent.roles), {"spec_writer", "test_writer", "builder", "security", "architecture", "ux"})
        self.assertEqual(len(runner.calls), 4)
        # Baseline -> RED with old product -> GREEN with unchanged new test.
        self.assertEqual(runner.calls[1][0]["src/api.py"], FILES["src/api.py"])
        self.assertEqual(runner.calls[1][0]["tests/test_factory_status.py"], runner.calls[2][0]["tests/test_factory_status.py"])
        self.assertEqual(github.statuses[-1]["state"], "pending")
        self.assertEqual(github.review_requests[0]["reviewers"], self.config["human_reviewers"])

    def test_failed_reviewer_never_publishes(self):
        body, headers = self.event()
        accept_event(self.config, self.queue, body, headers, b"secret")
        github = SimulatedGitHub()
        with self.assertRaises(Blocked):
            Pipeline(self.config, github, MockAgents("BLOCK"), MockRunner(), self.queue).execute(self.queue.claim())
        self.assertEqual(github.publications, [])


class ApprovalTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime.now(timezone.utc)
        self.review = {"id": 1, "state": "APPROVED", "user": {"login": "human", "type": "User"},
                       "commit_id": "head", "submitted_at": self.now.isoformat()}

    def resolve(self, reviews, **kwargs):
        return resolve_approval(reviews, head="head", author="bot", allowed=["human"], now=self.now, **kwargs)

    def test_missing_approval_blocks(self):
        self.assertIsNone(self.resolve([]))

    def test_exact_head_human_approval(self):
        self.assertEqual(self.resolve([self.review]), "human")

    def test_stale_commit_or_expired_approval_blocks(self):
        self.assertIsNone(self.resolve([{**self.review, "commit_id": "old"}]))
        self.assertIsNone(self.resolve([{**self.review, "submitted_at": (self.now-timedelta(days=2)).isoformat()}]))

    def test_bots_and_unlisted_users_cannot_approve(self):
        for user in ({"login": "human", "type": "Bot"}, {"login": "other", "type": "User"}):
            self.assertIsNone(self.resolve([{**self.review, "user": user}]))

    def test_author_cannot_approve_self(self):
        self.assertIsNone(resolve_approval([self.review], head="head", author="human", allowed=["human"], now=self.now))

    def test_dismissal_or_change_request_revokes(self):
        for state in ("DISMISSED", "CHANGES_REQUESTED"):
            self.assertIsNone(self.resolve([self.review, {**self.review, "id": 2, "state": state}]))
