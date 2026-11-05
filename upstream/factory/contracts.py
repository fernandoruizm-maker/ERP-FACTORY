"""Trusted internal contracts. Never deserialize agent JSON into approvals."""
from dataclasses import asdict, dataclass
import hashlib
import json


@dataclass(frozen=True)
class Candidate:
    repo: str
    base_sha: str
    head_sha: str
    brain_sha: str
    spec_sha: str
    artifact_sha: str
    policy_sha: str
    changes: tuple[str, ...]  # Include old and new paths for renames.
    impact: str  # Trusted analysis: content, presentation, behavior, unknown.
    lines_changed: int
    author: str = "builder-bot"
    environment: str = "production"

    @property
    def fingerprint(self):
        data = json.dumps(asdict(self), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(data.encode()).hexdigest()


@dataclass(frozen=True)
class Evidence:
    candidate_id: str
    checks: tuple[tuple[str, str], ...]
    tdd: str  # red-green-refactor, not-applicable, missing
    tdd_reason: str = ""


@dataclass(frozen=True)
class Review:
    role: str
    candidate_id: str
    verdict: str
    findings: tuple[str, ...] = ()


@dataclass(frozen=True)
class Approval:
    candidate_id: str
    subject: str  # Human ID from authenticated SSO/GitHub adapter.
    expires_at: float
    decision: str = "APPROVE"
