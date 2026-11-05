import hashlib
import hmac
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from urllib.request import Request, urlopen
from urllib.error import URLError
from examples.critical_backend import ISSUE
from factory.mvp.queue import Queue


class HTTPIntegrationTests(unittest.TestCase):
    def test_real_http_signed_delivery_is_persisted(self):
        self.signed_delivery(use_secret_file=False)

    def test_private_secret_file_is_loaded_and_delivery_is_persisted(self):
        self.signed_delivery(use_secret_file=True)

    def signed_delivery(self, *, use_secret_file):
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            config = json.loads((root / "config.example.json").read_text())
            config["brain_dir"] = str(root / "brain")
            config["state_dir"] = str(Path(tmp) / "state")
            filename = Path(tmp) / "config.json"
            filename.write_text(json.dumps(config))
            with socket.socket() as s:
                s.bind(("127.0.0.1", 0))
                port = s.getsockname()[1]
            secret = secrets.token_hex(32)
            env = {**os.environ, "GITHUB_WEBHOOK_SECRET": secret}
            if use_secret_file:
                (Path(tmp) / 'webhook.secret').write_text(secret, encoding='ascii')
                config['webhook_secret_file'] = 'webhook.secret'
                filename.write_text(json.dumps(config))
                env.pop('GITHUB_WEBHOOK_SECRET')
            process = subprocess.Popen([sys.executable, "-m", "factory.mvp", "--config", str(filename),
                                        "serve", "--port", str(port)], cwd=root, env=env,
                                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            base = f"http://127.0.0.1:{port}"
            try:
                for attempt in range(100):
                    try:
                        with urlopen(base + "/health", timeout=1) as response:
                            self.assertEqual(response.status, 200)
                        break
                    except URLError:
                        if process.poll() is not None:
                            self.fail("Server exited")
                        time.sleep(0.1)
                else:
                    self.fail("Server did not start")
                body = json.dumps({"action": "opened", "repository": {"full_name": config["repository"]},
                                   "issue": ISSUE, "sender": {"login": "fernandoruizm-maker", "type": "User"}}).encode()
                request = Request(base + "/webhooks/github", data=body, headers={
                    "X-GitHub-Event": "issues", "X-GitHub-Delivery": "http-test",
                    "X-Hub-Signature-256": "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()})
                with urlopen(request, timeout=5) as response:
                    self.assertEqual(response.status, 202)
                    job = json.load(response)["job_id"]
                self.assertEqual(Queue(Path(config["state_dir"]) / "mvp.sqlite3").get(job)["state"], "QUEUED")
            finally:
                process.terminate()
                process.wait(timeout=10)
