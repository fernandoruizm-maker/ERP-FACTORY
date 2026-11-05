import unittest
from factory.mvp.github import GitHub
from factory.mvp.common import Blocked


class FakeTransport(GitHub):
    def __init__(self):
        self.repository = "o/r"
        self.calls = []
        self.branch = None
        self.pr = None
        self.protection = {"required_pull_request_reviews": {"required_approving_review_count": 1,
                             "dismiss_stale_reviews": True}, "enforce_admins": {"enabled": True},
                           "required_status_checks": {"strict": True,
                             "contexts": ["factory/quality", "factory/human-approval"]}}

    def get(self, path):
        if path.endswith("/protection"):
            return self.protection
        if path == "/git/commits/base":
            return {"tree": {"sha": "base-tree"}}
        if path == "/git/commits/head":
            return {"tree": {"sha": "candidate-tree"}, "parents": [{"sha": "base"}]}
        if path.startswith("/git/matching-refs/"):
            return [self.branch] if self.branch else []
        if path.startswith("/pulls?"):
            return [self.pr] if self.pr else []
        raise AssertionError(path)

    def post(self, path, data):
        self.calls.append((path, data))
        if path == "/git/trees":
            return {"sha": "candidate-tree"}
        if path == "/git/commits":
            return {"sha": "head"}
        if path == "/git/refs":
            self.branch = {"ref": data["ref"], "object": {"sha": data["sha"]}}
            return self.branch
        if path == "/pulls":
            self.pr = {"number": 1, "state": "open", "html_url": "https://github.com/o/r/pull/1",
                       "head": {"sha": "head"}}
            return self.pr
        raise AssertionError(path)


class GitHubAdapterTests(unittest.TestCase):
    def test_pr_is_draft_and_retry_does_not_duplicate(self):
        gh = FakeTransport()
        args = dict(base_sha="base", base_branch="main", branch="factory/task-1",
                    changes={"src/a.py": "x=1"}, title="change", body="evidence")
        first, second = gh.publish(**args), gh.publish(**args)
        self.assertEqual(first, second)
        creates = [d for p, d in gh.calls if p == "/pulls"]
        self.assertEqual(len(creates), 1)
        self.assertTrue(creates[0]["draft"])
        self.assertFalse(any("merge" in p for p, d in gh.calls))

    def test_closed_pr_is_not_reopened(self):
        gh = FakeTransport()
        args = dict(base_sha="base", base_branch="main", branch="factory/task-1",
                    changes={"src/a.py": "x=1"}, title="change", body="evidence")
        gh.publish(**args)
        gh.pr["state"] = "closed"
        with self.assertRaises(Blocked):
            gh.publish(**args)

    def test_governance_fails_closed(self):
        gh = FakeTransport()
        with self.assertRaises(Blocked):
            gh.governance("main")
        gh.protection["required_status_checks"]["contexts"].remove("factory/human-approval")
        with self.assertRaises(Blocked):
            gh.governance("main")
