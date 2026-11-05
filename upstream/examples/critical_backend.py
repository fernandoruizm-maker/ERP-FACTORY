"""Simulated GitHub delivery + real Codex agents + real Docker TDD. No GitHub writes."""
import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import hmac
import json
from pathlib import Path
import secrets
import uuid

from factory.mvp.agents import CodexAgent
from factory.mvp.approval import resolve_approval
from factory.mvp.common import digest, load_config
from factory.mvp.pipeline import Pipeline
from factory.mvp.queue import Queue, worker_lock
from factory.mvp.runner import DockerRunner
from factory.mvp.service import accept_event

FILES = {
    "src/__init__.py": "",
    "src/api.py": 'def get_customer(customer_id):\n    return {"id": customer_id, "name": "Cliente"}\n',
    "tests/test_api.py": 'import unittest\nfrom src.api import get_customer\n\nclass Baseline(unittest.TestCase):\n    def test_existing_fields(self):\n        result = get_customer(7)\n        self.assertEqual(result["id"], 7)\n        self.assertEqual(result["name"], "Cliente")\n',
}
ISSUE = {"number": 900001, "title": "Añadir status al contrato del backend de clientes",
         "body": "En src/api.py, get_customer(customer_id) debe añadir el campo status con valor active. "
                 "Conservar id y name, la firma y el comportamiento existente. No hay persistencia ni se requiere BD. "
                 "Es una ampliación del contrato de respuesta del backend; debe exigir aprobación humana antes de integrar o desplegar. "
                 "Usar unittest; tests/ y src/ están disponibles. No hace falta UI ni pruebas visuales.",
         "state": "open", "updated_at": "2026-11-03T12:00:00Z", "labels": [{"name": "ai-factory"}]}


class SimulatedGitHub:
    """Fixture boundary. Does not inherit real HTTP transport and cannot publish remotely."""
    def __init__(self):
        self.statuses, self.publications, self.review_requests = [], [], []

    def can_write(self, _):
        return True

    def issue(self, _):
        return ISSUE

    def governance(self, _):
        return None

    def base(self, _):
        return "fixture-base-" + digest(FILES)[:12]

    def snapshot(self, *_):
        return dict(FILES)

    def publish(self, **payload):
        self.publications.append(payload)
        return {"number": 0, "url": None, "head_sha": "fixture-head-" + digest(payload["changes"])[:12]}

    def status(self, sha, context, state, description):
        self.statuses.append({"sha": sha, "context": context, "state": state, "description": description})

    def request_reviewers(self, number, reviewers):
        self.review_requests.append({"pr_number": number, "reviewers": reviewers})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", required=True)
    parser.add_argument("--wsl-distribution")
    parser.add_argument("--output", required=True)
    parser.add_argument("--state-dir", required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    config = load_config(root / "config.example.json")
    config["state_dir"] = str(Path(args.state_dir).resolve())
    config["runner_image"] = args.image
    config["wsl_distribution"] = args.wsl_distribution
    queue = Queue(Path(config["state_dir"]) / "simulation.sqlite3")
    secret = secrets.token_bytes(32)
    body = json.dumps({"action": "labeled", "repository": {"full_name": config["repository"]},
                       "issue": ISSUE, "label": {"name": "ai-factory"},
                       "sender": {"login": "fernandoruizm-maker", "type": "User"}}).encode()
    accepted = accept_event(config, queue, body, {
        "X-GitHub-Event": "issues", "X-GitHub-Delivery": str(uuid.uuid4()),
        "X-Hub-Signature-256": "sha256=" + hmac.new(secret, body, hashlib.sha256).hexdigest()}, secret)
    github = SimulatedGitHub()
    pipeline = Pipeline(config, github, CodexAgent(),
                        DockerRunner(args.image, wsl_distribution=args.wsl_distribution), queue)
    with worker_lock(Path(config["state_dir"]) / "worker.lock"):
        queue.recover()
        job = queue.claim()
        if not job:
            raise SystemExit("Simulation already ran; use a new state directory to rerun")
        result = pipeline.execute(job)
    saved = json.loads(queue.get(accepted["job_id"])["checkpoint"])
    assert result["state"] == "WAITING_APPROVAL"
    assert not result["deployment_attempted"]
    assert github.statuses[-1]["state"] == "pending"
    assert resolve_approval([], head=result["pr"]["head_sha"], author="factory-bot",
                            allowed=config["human_reviewers"], now=datetime.now(timezone.utc)) is None
    report = {"repository": config["repository"], "input": "SIMULATED_SIGNED_WEBHOOK",
              "backend": "LOCAL_FIXTURE_NOT_EXISTING_REPOSITORY_CODE",
              "agents": "REAL_CODEX", "tests": "REAL_DOCKER_NO_NETWORK",
              "github_publication": "SIMULATED_NO_REMOTE_WRITES",
              "state": result["state"], "deployment_attempted": False,
              "approval_required": True, "approval_status": github.statuses[-1],
              "review_requests": github.review_requests,
              "candidate": saved, "proposed_pr": github.publications[0]}
    destination = Path(args.output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"state": result["state"], "report": str(destination),
                      "real_models": True, "real_tests": True, "remote_writes": False}))


if __name__ == "__main__":
    main()
