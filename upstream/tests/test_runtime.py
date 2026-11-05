import asyncio
from dataclasses import replace
import hashlib
import hmac
import json
from pathlib import Path
import tempfile
import unittest

from factory.contracts import Review
from factory.ingress import receive_github, verify_github
from factory.memory import Brain, Store
from factory.policy import ROLES, route
from factory.reviews import parallel_reviews
from test_policy import fixture


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = Store(Path(self.tmp.name) / "state.db")

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def test_duplicate_is_idempotent(self):
        first, created = self.store.accept("github", "org/r", "event", b"body")
        second, duplicate = self.store.accept("github", "org/r", "event", b"body")
        self.assertTrue(created)
        self.assertFalse(duplicate)
        self.assertEqual(first, second)
        self.assertEqual(self.store.db.execute("SELECT count(*) FROM audit").fetchone()[0], 1)

    def test_event_collision_is_rejected(self):
        self.store.accept("github", "org/r", "event", b"body")
        with self.assertRaises(ValueError):
            self.store.accept("github", "org/r", "event", b"changed")

    def test_same_id_different_repo_is_separate(self):
        a, _ = self.store.accept("github", "org/a", "event", b"body")
        b, _ = self.store.accept("github", "org/b", "event", b"body")
        self.assertNotEqual(a, b)

    def test_restart_preserves_inbox(self):
        a, _ = self.store.accept("github", "org/r", "event", b"body")
        self.store.close()
        self.store = Store(Path(self.tmp.name) / "state.db")
        b, created = self.store.accept("github", "org/r", "event", b"body")
        self.assertEqual(a, b)
        self.assertFalse(created)

    def test_transition_checks_prior_state(self):
        task, _ = self.store.accept("github", "org/r", "event", b"body")
        self.store.transition(task, "RECEIVED", "REVIEWING", {})
        with self.assertRaises(ValueError):
            self.store.transition(task, "RECEIVED", "REVIEWING", {})
        with self.assertRaises(ValueError):
            self.store.transition(task, "REVIEWING", "DEPLOYED", {})

    def test_github_official_signature_vector(self):
        verify_github(b"Hello, World!",
                      "sha256=757107ea0eb2509fc211221cce984b8a37570b6d7586c22c46f4379c8b043e17",
                      b"It's a Secret to Everybody")

    def test_invalid_signature_rejected(self):
        for signature in ("", "sha256=wrong", "not-ascii-\u00f1"):
            with self.assertRaises(ValueError):
                verify_github(b"body", signature, b"secret")

    def test_signed_ingress_and_repo_allowlist(self):
        body = json.dumps({"action": "opened", "repository": {"full_name": "org/r"}}).encode()
        headers = {"X-GitHub-Event": "issues", "X-GitHub-Delivery": "1",
                   "X-Hub-Signature-256": "sha256=" + hmac.new(b"secret", body, hashlib.sha256).hexdigest()}
        _, created = receive_github(self.store, body, headers, b"secret", {"org/r"})
        self.assertTrue(created)
        with self.assertRaises(ValueError):
            receive_github(self.store, body, headers, b"secret", {"other/r"})
        with self.assertRaises(ValueError):
            receive_github(self.store, body + b" ", headers, b"secret", {"org/r"})

    def test_brain_hash_changes_and_missing_context_fails(self):
        root = Path(self.tmp.name) / "brain"
        (root / "decisions").mkdir(parents=True)
        for name in ("stack.md", "conventions.md", "decisions/0001-control-plane.md"):
            (root / name).write_text("original", encoding="utf-8")
        before = Brain.load(root)
        (root / "stack.md").write_text("changed", encoding="utf-8")
        self.assertNotEqual(before.fingerprint, Brain.load(root).fingerprint)
        (root / "stack.md").write_text("", encoding="utf-8")
        with self.assertRaises(ValueError):
            Brain.load(root)


class ReviewTests(unittest.IsolatedAsyncioTestCase):
    async def test_reviewers_actually_run_concurrently(self):
        c, e, _ = fixture()
        started = set()
        all_started = asyncio.Event()

        def adapter(role):
            async def run(candidate):
                started.add(role)
                if len(started) == 3:
                    all_started.set()
                await all_started.wait()  # Sequential invocation would time out.
                return Review(role, candidate.fingerprint, "PASS")
            return run

        results = await parallel_reviews(c, {r: adapter(r) for r in ROLES}, timeout=1)
        self.assertEqual(route(c, e, results), "READY_FAST_TRACK")

    async def test_reviewer_timeout_blocks(self):
        c, e, _ = fixture()
        async def stuck(candidate):
            await asyncio.Event().wait()
        results = await parallel_reviews(c, {r: stuck for r in ROLES}, timeout=0.01)
        self.assertEqual(route(c, e, results), "BLOCKED")

    async def test_stale_or_malformed_review_blocks(self):
        c, e, _ = fixture()
        async def bad(candidate):
            return {"verdict": "PASS"}
        results = await parallel_reviews(c, {r: bad for r in ROLES})
        self.assertEqual(route(c, e, results), "BLOCKED")

    async def test_missing_reviewer_rejected(self):
        with self.assertRaises(ValueError):
            await parallel_reviews(fixture()[0], {})
