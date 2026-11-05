"""Run untrusted project tests only inside a resource-limited, offline container."""
from dataclasses import asdict, dataclass
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import time
import uuid
from .common import Blocked, digest, safe_path


@dataclass
class TestResult:
    exit_code: int
    output: str
    files_digest: str
    tests_run: int
    failures: int
    errors: int
    skipped: int
    ids: tuple[str, ...]

    @property
    def green(self):
        return self.exit_code == 0 and self.tests_run > 0 and self.failures == 0 and self.errors == 0


def parse_result(code, output, files):
    count = re.search(r"Ran (\d+) tests? in", output)
    metric = lambda name: int((re.search(name + r"=(\d+)", output) or [None, "0"])[1])
    ids = tuple(re.findall(r"^(test\S+ \([^\r\n]+\)) \.\.\. ", output, re.M))
    return TestResult(code, output, digest(files), int(count[1]) if count else 0,
                      metric("failures"), metric("errors"), metric("skipped"), ids)


class DockerRunner:
    def __init__(self, image, timeout=120, wsl_distribution=None):
        # Pin an immutable image ID or digest; no implicit image pulls during a job.
        if not re.fullmatch(r"(?:[\w./:-]+@)?sha256:[a-f0-9]{64}", image):
            raise Blocked("Pin runner_image to a local sha256 image ID or repository@sha256 digest")
        self.image, self.timeout = image, timeout
        self.wsl = wsl_distribution
        self.command = (["wsl", "-d", wsl_distribution, "--exec", "docker"]
                        if wsl_distribution else ["docker"])

    def preflight(self):
        if not shutil.which(self.command[0]):
            raise Blocked("Docker is required; tests will not run on the host")
        result = subprocess.run([*self.command, "image", "inspect", self.image],
                                capture_output=True, timeout=20)
        if result.returncode:
            raise Blocked("Docker daemon or pinned test image is unavailable")

    def run(self, files, pattern="test*.py"):
        self.preflight()
        if not re.fullmatch(r"[a-zA-Z0-9_*.-]+\.py", pattern):
            raise Blocked("Invalid test pattern")
        name = "ai-factory-" + uuid.uuid4().hex
        with tempfile.TemporaryDirectory(prefix="factory-tests-") as temp:
            root = Path(temp) / "source"
            root.mkdir()
            for path, content in files.items():
                target = root / safe_path(path)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content, encoding="utf-8")
                target.chmod(0o644)
            for directory, _, _ in os.walk(root):
                Path(directory).chmod(0o755)
            log = Path(temp) / "test.log"
            mount_root = str(root)
            if self.wsl:
                mount_root = subprocess.check_output(
                    ["wsl", "-d", self.wsl, "--exec", "wslpath", "-u", str(root)],
                    text=True, encoding="utf-8", timeout=20).strip()
            command = [*self.command, "run", "--rm", "--pull=never", "--name", name,
                       "--network=none", "--read-only", "--cap-drop=ALL",
                       "--security-opt=no-new-privileges", "--pids-limit=64",
                       "--memory=512m", "--cpus=1", "--user=65534:65534",
                       "--tmpfs=/tmp:rw,noexec,nosuid,size=64m",
                       "--mount", f"type=bind,source={mount_root},target=/workspace,readonly",
                       "--workdir=/workspace", "--env=PYTHONDONTWRITEBYTECODE=1",
                       "--env=PYTHONPATH=/workspace", "--env=HOME=/tmp", self.image,
                       "python", "-m", "unittest", "discover", "-s", "tests", "-p", pattern, "-v"]
            try:
                with log.open("wb") as output:
                    process = subprocess.Popen(command, stdout=output, stderr=subprocess.STDOUT)
                    deadline = time.monotonic() + self.timeout
                    while process.poll() is None:
                        if time.monotonic() > deadline or log.stat().st_size > 1_000_000:
                            process.kill()
                            process.wait()
                            raise Blocked("Test timeout or output budget exceeded")
                        time.sleep(0.1)
                text = log.read_text(encoding="utf-8", errors="replace")
                return parse_result(process.returncode, text, files)
            finally:
                subprocess.run([*self.command, "rm", "-f", name], capture_output=True, timeout=15)
