"""Minimal webhook ingress; bind loopback behind a TLS reverse proxy for remote delivery."""
import json
import os
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from .common import Blocked
from ..ingress import verify_github


def accept_event(config, queue, body, headers, secret):
    headers = {k.lower(): v for k, v in headers.items()}
    if len(body) > 1_000_000:
        raise Blocked("Payload too large")
    verify_github(body, headers.get("x-hub-signature-256", ""), secret)
    payload = json.loads(body)
    if headers.get("x-github-event") == "ping":
        return {"accepted": False, "reason": "ping"}
    if headers.get("x-github-event") != "issues":
        return {"accepted": False, "reason": "unsupported_event"}
    if payload["repository"]["full_name"] != config["repository"]:
        raise Blocked("Repository not authorized")
    if payload.get("action") not in {"opened", "labeled", "reopened"}:
        return {"accepted": False, "reason": "unsupported_action"}
    issue = payload["issue"]
    requester = payload["sender"]["login"]
    if payload["sender"].get("type") != "User" or requester not in config["allowed_requesters"]:
        raise Blocked("Requester not authorized")
    if config["trigger_label"] not in [item["name"] for item in issue["labels"]]:
        return {"accepted": False, "reason": "missing_opt_in_label"}
    if payload["action"] == "labeled" and payload["label"]["name"] != config["trigger_label"]:
        return {"accepted": False, "reason": "unrelated_label"}
    delivery = headers.get("x-github-delivery", "")
    if not delivery or len(delivery) > 200 or type(issue["number"]) is not int:
        raise Blocked("Invalid event identity")
    job = queue.enqueue(delivery, {"repository": config["repository"], "requester": requester,
                                  "issue_number": issue["number"],
                                  "issue_updated_at": issue["updated_at"]})
    return {"accepted": True, "job_id": job}


def serve(config, queue, host="127.0.0.1", port=8787):
    secret = (Path(config['webhook_secret_file']).read_bytes().strip()
              if config.get('webhook_secret_file') else os.environ.get("GITHUB_WEBHOOK_SECRET", "").encode())
    if len(secret) < 32:
        raise Blocked("Set GITHUB_WEBHOOK_SECRET to at least 32 random characters")

    class Handler(BaseHTTPRequestHandler):
        def setup(self):
            super().setup()
            self.connection.settimeout(10)

        def log_message(self, *_):
            pass  # Avoid request content and arbitrary user-controlled log lines.

        def reply(self, code, value):
            body = json.dumps(value).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            self.reply(200 if self.path == "/health" else 404, {"service": "ai-factory"})

        def do_POST(self):
            if self.path != "/webhooks/github":
                return self.reply(404, {"error": "not_found"})
            try:
                if self.headers.get("Transfer-Encoding"):
                    raise Blocked("Chunked bodies not supported")
                size = int(self.headers.get("Content-Length", "0"))
                if not 0 < size <= 1_000_000:
                    return self.reply(413, {"error": "invalid_body_size"})
                body = self.rfile.read(size)
                if len(body) != size:
                    raise Blocked("Incomplete request")
                result = accept_event(config, queue, body, dict(self.headers), secret)
                self.reply(202, result)
            except (Blocked, ValueError, KeyError, TypeError):
                self.reply(400, {"error": "invalid_or_unauthorized_event"})
            except TimeoutError:
                self.reply(408, {"error": "request_timeout"})

    ThreadingHTTPServer((host, port), Handler).serve_forever()
