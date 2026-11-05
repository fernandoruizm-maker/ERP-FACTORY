import unittest
from dataclasses import replace
from factory.contracts import Approval, Candidate, Evidence, Review
from factory.policy import CHECKS, ROLES, route


def fixture(**kwargs):
    c = Candidate("org/repo", "base", "head", "brain", "spec", "artifact", "policy",
                  ("web/content/home.txt",), "content", 4)
    c = replace(c, **kwargs)
    e = Evidence(c.fingerprint, tuple((k, "PASS") for k in sorted(CHECKS)),
                 "red-green-refactor")
    r = tuple(Review(role, c.fingerprint, "PASS") for role in sorted(ROLES))
    return c, e, r


class FirstPolicyTest(unittest.TestCase):
    def test_missing_evidence_blocks(self):
        self.assertEqual(route(None), "BLOCKED")

    def test_content_fast_track(self):
        self.assertEqual(route(*fixture()), "READY_FAST_TRACK")

    def test_presentation_fast_track(self):
        self.assertEqual(route(*fixture(changes=("web/presentation/card.css",),
                                       impact="presentation")), "READY_FAST_TRACK")

    def test_critical_and_unknown_paths_require_human(self):
        for path in ("db/migrations/1.sql", "src/core/a.py", "auth/login.ts",
                     ".github/workflows/ci.yml", "brain/stack.md", "package-lock.json",
                     "web/content/code.js", "README.md", "infra/main.tf"):
            with self.subTest(path=path):
                self.assertEqual(route(*fixture(changes=(path,))), "WAITING_APPROVAL")

    def test_large_change_requires_human(self):
        self.assertEqual(route(*fixture(lines_changed=81)), "WAITING_APPROVAL")

    def test_behavior_in_allowed_path_requires_human(self):
        self.assertEqual(route(*fixture(impact="behavior")), "WAITING_APPROVAL")

    def test_unknown_impact_requires_human(self):
        self.assertEqual(route(*fixture(impact="unknown")), "WAITING_APPROVAL")

    def test_traversal_and_empty_diff_block(self):
        for changes in ((), ("docs/user-guide/../../auth/a.md",), ("/root/a",),
                        ("C:\\test",), ("web/content//a.txt",)):
            self.assertEqual(route(*fixture(changes=changes)), "BLOCKED")

    def test_rename_uses_both_names(self):
        self.assertEqual(route(*fixture(changes=("auth/a.md", "docs/user-guide/a.md"))),
                         "WAITING_APPROVAL")

    def test_missing_check_blocks(self):
        c, e, r = fixture()
        self.assertEqual(route(c, replace(e, checks=e.checks[1:]), r), "BLOCKED")

    def test_failed_or_duplicate_check_blocks(self):
        c, e, r = fixture()
        for checks in (e.checks + (("extra", "FAIL"),), e.checks + (e.checks[0],)):
            self.assertEqual(route(c, replace(e, checks=checks), r), "BLOCKED")

    def test_all_reviews_required_without_majority_vote(self):
        c, e, r = fixture()
        self.assertEqual(route(c, e, r[:2]), "BLOCKED")
        self.assertEqual(route(c, e, (r[0], r[0], r[2])), "BLOCKED")
        self.assertEqual(route(c, e, (replace(r[0], verdict="BLOCK"), *r[1:])), "BLOCKED")

    def test_unresolved_finding_blocks(self):
        c, e, r = fixture()
        self.assertEqual(route(c, e, (replace(r[0], findings=("violation",)), *r[1:])), "BLOCKED")

    def test_changed_inputs_invalidate_evidence(self):
        c, e, r = fixture()
        for field in ("head_sha", "base_sha", "brain_sha", "spec_sha", "artifact_sha", "policy_sha"):
            self.assertEqual(route(replace(c, **{field: "new"}), e, r), "BLOCKED")

    def test_stale_review_blocks(self):
        c, e, r = fixture()
        self.assertEqual(route(c, e, (replace(r[0], candidate_id="old"), *r[1:])), "BLOCKED")

    def test_tdd_missing_blocks_behavior(self):
        c, e, r = fixture(impact="behavior")
        self.assertEqual(route(c, replace(e, tdd="missing"), r), "BLOCKED")

    def test_tdd_exemption_requires_static_change_and_reason(self):
        c, e, r = fixture()
        self.assertEqual(route(c, replace(e, tdd="not-applicable"), r), "BLOCKED")
        self.assertEqual(route(c, replace(e, tdd="not-applicable", tdd_reason="Copy only"), r),
                         "READY_FAST_TRACK")
        c, e, r = fixture(impact="behavior")
        self.assertEqual(route(c, replace(e, tdd="not-applicable", tdd_reason="Skip"), r), "BLOCKED")

    def test_valid_independent_human_approval(self):
        c, e, r = fixture(changes=("db/migrations/1.sql",), impact="behavior")
        a = Approval(c.fingerprint, "human-1", 200)
        self.assertEqual(route(c, e, r, a, authorized_humans=frozenset({"human-1"}), now=100),
                         "READY_APPROVED")

    def test_invalid_approval_cannot_release(self):
        c, e, r = fixture(changes=("src/core/a.py",), impact="behavior")
        a = Approval(c.fingerprint, "human-1", 200)
        for bad in (replace(a, candidate_id="old"), replace(a, expires_at=100),
                    replace(a, subject=c.author), replace(a, subject="stranger"),
                    replace(a, decision="REJECT")):
            self.assertEqual(route(c, e, r, bad,
                                  authorized_humans=frozenset({"human-1", c.author}), now=100),
                             "WAITING_APPROVAL")

    def test_approval_cannot_override_failed_quality(self):
        c, e, r = fixture(impact="behavior")
        self.assertEqual(route(c, replace(e, checks=()), r,
                               Approval(c.fingerprint, "human-1", 200),
                               authorized_humans=frozenset({"human-1"}), now=100), "BLOCKED")

    def test_no_unknown_environment(self):
        self.assertEqual(route(*fixture(environment="other")), "BLOCKED")


if __name__ == "__main__":
    unittest.main()
