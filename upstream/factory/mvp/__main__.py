import argparse
import json
from pathlib import Path
import time
import uuid
from .agents import CodexAgent, ResponsesAgent
from .approval import refresh
from .common import Blocked, load_config
from .github import GitHub
from .pipeline import Pipeline
from .queue import Queue, worker_lock
from .runner import DockerRunner
from .service import serve


def components(config):
    github = GitHub.from_config(config)
    provider = config.get("agent_provider", "codex")
    agent = (CodexAgent(config.get("model")) if provider == "codex"
             else ResponsesAgent(config["model"]) if provider == "responses" else None)
    if agent is None:
        raise Blocked("Unknown agent_provider")
    runner = DockerRunner(config["runner_image"], wsl_distribution=config.get("wsl_distribution"))
    return github, agent, runner


def work(config, queue, once=False):
    github, agent, runner = components(config)
    pipeline = Pipeline(config, github, agent, runner, queue)
    with worker_lock(Path(config["state_dir"]) / "worker.lock"):
        queue.recover()
        while True:
            job = queue.claim()
            if job:
                try:
                    print(json.dumps(pipeline.execute(job)), flush=True)
                except Exception as exc:
                    message = str(exc) if isinstance(exc, Blocked) else type(exc).__name__
                    # PUBLISHING survives uncertain external writes; recovery reconciles remote state.
                    current = queue.get(job["id"])
                    state = "PUBLISHING" if current["state"] == "PUBLISHING" and not isinstance(exc, Blocked) else "BLOCKED"
                    queue.set(job["id"], state, error=message)
                    print(json.dumps({"job": job["id"], "state": state, "error": message}), flush=True)
            for item in queue.list():
                if item["state"] in {"WAITING_APPROVAL", "APPROVED"}:
                    try:
                        refresh(config, github, queue, item["id"])
                    except Exception as exc:
                        print(json.dumps({"job": item["id"], "approval_refresh": type(exc).__name__}), flush=True)
            if once:
                return
            time.sleep(30)


def main():
    parser = argparse.ArgumentParser(description="Issue -> real agents -> verified TDD -> draft PR; never merge/deploy")
    parser.add_argument("--config", default="config.example.json")
    commands = parser.add_subparsers(dest="command", required=True)
    server = commands.add_parser("serve")
    server.add_argument("--port", type=int, default=8787)
    worker = commands.add_parser("worker")
    worker.add_argument("--once", action="store_true")
    enqueue = commands.add_parser("enqueue")
    enqueue.add_argument("--issue", type=int, required=True)
    enqueue.add_argument("--requester", required=True)
    commands.add_parser("jobs")
    refresh_parser = commands.add_parser("refresh-approval")
    refresh_parser.add_argument("job_id")
    retry = commands.add_parser("retry")
    retry.add_argument("job_id")
    commands.add_parser("doctor")
    pilot_parser = commands.add_parser('pilot')
    pilot_parser.add_argument('--once', action='store_true')
    commands.add_parser('pilot-pause')
    commands.add_parser('pilot-resume')
    args = parser.parse_args()
    config = load_config(args.config)
    queue = Queue(Path(config["state_dir"]) / "mvp.sqlite3")
    if args.command == 'pilot':
        from .polling import pilot
        return pilot(args.config, once=args.once)
    if args.command in {'pilot-pause', 'pilot-resume'}:
        flag = Path(config['state_dir']) / 'pilot.pause'
        if args.command == 'pilot-pause':
            flag.write_text('Pause requested by operator', encoding='utf-8')
        else:
            flag.unlink(missing_ok=True)
        print('Pilot paused after current work' if args.command == 'pilot-pause' else 'Pilot resumed')
        return
    if args.command == "serve":
        return serve(config, queue, port=args.port)
    if args.command == "jobs":
        print(json.dumps(queue.list(), indent=2))
        return
    if args.command == "retry":
        with worker_lock(Path(config["state_dir"]) / "worker.lock"):
            job = queue.get(args.job_id)
            if not job or job["state"] not in {"BLOCKED", "PUBLISHING"}:
                raise Blocked("Only stopped jobs can be retried")
            queue.set(args.job_id, "QUEUED")
        return
    if args.command == "worker":
        return work(config, queue, args.once)
    github = GitHub.from_config(config)
    if args.command == "enqueue":
        if args.requester not in config["allowed_requesters"] or not github.can_write(args.requester):
            raise Blocked("Requester must be an authorized repository writer")
        issue = github.issue(args.issue)
        job = queue.enqueue("manual-" + str(uuid.uuid4()), {
            "repository": config["repository"], "requester": args.requester,
            "issue_number": args.issue, "issue_updated_at": issue["updated_at"]})
        print(json.dumps({"job_id": job}))
    elif args.command == "refresh-approval":
        with worker_lock(Path(config["state_dir"]) / "worker.lock"):
            print(refresh(config, github, queue, args.job_id))
    elif args.command == "doctor":
        if github.auth:
            github.auth.verify_installation()
        github.governance(config["base_branch"])
        _, _, runner = components(config)
        runner.preflight()
        print("GitHub governance and Docker runner OK. Agent authentication checked on first call.")


if __name__ == "__main__":
    try:
        main()
    except Blocked as exc:
        raise SystemExit(str(exc))
