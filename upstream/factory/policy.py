"""Fail-closed policy over trusted evidence. Does not deploy anything."""
import re
import time
from .contracts import Approval, Candidate, Evidence, Review

ROLES = frozenset({"security", "architecture", "ux"})
CHECKS = frozenset({"tests", "lint", "security", "build", "acceptance"})


def safe_path(path):
    return bool(path) and not (
        path.startswith("/") or "\\" in path or ":" in path
        or any(p in {"", ".", ".."} for p in path.split("/"))
        or any(ord(c) < 32 for c in path))


def fast_track(candidate):
    if not 0 < candidate.lines_changed <= 80 or len(candidate.changes) > 5:
        return False
    if candidate.impact == "content":
        return all(
            re.fullmatch(r"docs/user-guide/[a-zA-Z0-9_/-]+\.md", p)
            or re.fullmatch(r"web/content/[a-zA-Z0-9_/-]+\.txt", p)
            for p in candidate.changes)
    if candidate.impact == "presentation":
        return all(re.fullmatch(r"web/presentation/[a-zA-Z0-9_-]+\.css", p)
                   for p in candidate.changes)
    return False


def route(candidate: Candidate | None, evidence: Evidence | None = None,
          reviews: tuple[Review, ...] = (), approval: Approval | None = None,
          *, authorized_humans: frozenset[str] = frozenset(), now=None):
    """Caller must verify identity and attestations before constructing these inputs.

    presentation requires a semantic CSS checker, not an LLM label.
    Approval subject comes from authenticated SSO, never a request field.
    READY_* means eligible for a protected controller, never already deployed.
    """
    if not isinstance(candidate, Candidate) or not isinstance(evidence, Evidence):
        return "BLOCKED"
    if not candidate.changes or not all(safe_path(p) for p in candidate.changes):
        return "BLOCKED"
    if not all((candidate.repo, candidate.base_sha, candidate.head_sha,
                candidate.brain_sha, candidate.spec_sha, candidate.artifact_sha,
                candidate.policy_sha, candidate.environment)):
        return "BLOCKED"
    identity = candidate.fingerprint
    checks = dict(evidence.checks)
    if (evidence.candidate_id != identity or len(checks) != len(evidence.checks)
            or not CHECKS.issubset(checks)
            or any(checks[k] != "PASS" for k in checks)):
        return "BLOCKED"
    if evidence.tdd != "red-green-refactor":
        if not (evidence.tdd == "not-applicable" and evidence.tdd_reason.strip()
                and candidate.impact in {"content", "presentation"}):
            return "BLOCKED"
    if len(reviews) != len(ROLES) or {r.role for r in reviews} != ROLES:
        return "BLOCKED"
    if any(r.candidate_id != identity or r.verdict != "PASS" or r.findings
           for r in reviews):
        return "BLOCKED"
    if candidate.environment != "production":
        return "BLOCKED"
    if fast_track(candidate):
        return "READY_FAST_TRACK"
    now = time.time() if now is None else now
    if approval is None:
        return "WAITING_APPROVAL"
    if (approval.candidate_id != identity or approval.decision != "APPROVE"
            or approval.subject not in authorized_humans
            or approval.subject == candidate.author
            or approval.expires_at <= now):
        return "WAITING_APPROVAL"
    return "READY_APPROVED"
