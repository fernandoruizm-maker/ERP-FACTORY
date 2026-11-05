"""Ejecutor de propuestas: exclusivamente contenedores sin red, imagen ya instalada."""
import os
from pathlib import Path
import re
import subprocess
import tempfile
import time
import uuid

from .core import Blocked, contained, digest


def test_command(profile, files, *, directory):
    root = Path(directory)
    if not root.is_dir():
        raise Blocked('CANDIDATE_DIRECTORY_REQUIRED')
    for part in (root, *root.parents):
        if part.is_symlink() or (hasattr(part, 'is_junction') and part.is_junction()):
            raise Blocked('CANDIDATE_LINK_FORBIDDEN')
    if not isinstance(files, list) or not files or not all(isinstance(name, str) for name in files):
        raise Blocked("No hay pruebas seleccionadas.")
    if len({name.casefold() for name in files}) != len(files):
        raise Blocked('DUPLICATE_TEST_PATH')
    for name in files:
        p = contained(root, name)
        if not name.startswith("tests/") or not p.is_file():
            raise Blocked("Las pruebas deben estar en tests/.")
    if profile == "python":
        # Explicit modules only. The former ["tests"] -> "te" branch is removed.
        if any(not re.fullmatch(r"tests/test_[A-Za-z0-9_]+\.py", x) for x in files):
            raise Blocked("Prueba Python no admitida.")
        return ["python", "-m", "unittest", "-v", *[x[:-3].replace("/", ".") for x in files]]
    if profile in ("javascript", "typescript"):
        suffix = ".test.mjs" if profile == "javascript" else ".test.ts"
        if any(not x.endswith(suffix) for x in files):
            raise Blocked("Extensión de prueba incorrecta.")
        return ["node", *(["--experimental-strip-types"] if profile == "typescript" else []), "--test", "--test-reporter=tap", *files]
    raise Blocked("Perfil desconocido.")


def assess(profile, code, output):
    if profile == "python":
        count = re.search(r"Ran (\d+) tests? in", output)
        skipped = re.search(r"skipped[= ]\d+", output)
        valid = count and int(count[1]) > 0 and re.search(r"^OK\s*$", output, re.M) and not skipped
    else:
        count = re.search(r"# tests (\d+)", output)
        valid = count and int(count[1]) > 0 and "# fail 0" in output and "# skipped 0" in output and "# cancelled 0" in output
    return {"status": "PASS" if code == 0 and valid else "FAIL", "exit_code": code,
            "test_count": int(count[1]) if count else 0,
            "type_check": "NOT_RUN" if profile == "typescript" else "NOT_APPLICABLE"}


def bounded_process(command, *, cwd=None, timeout=60, output_limit=1000000):
    # No shell, no inherited provider secrets. Output is bounded on disk and in memory.
    allow = {"PATH", "SYSTEMROOT", "WINDIR", "TEMP", "TMP", "PATHEXT", "COMSPEC"}
    env = {k: v for k, v in os.environ.items() if k.upper() in allow}
    env.update(PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8")
    with tempfile.TemporaryFile() as out:
        process = subprocess.Popen(command, cwd=cwd, stdout=out, stderr=out, env=env)
        start = time.monotonic()
        while process.poll() is None:
            if time.monotonic() - start > timeout or os.fstat(out.fileno()).st_size > output_limit:
                process.kill()
                process.wait(timeout=5)
                raise Blocked("Prueba detenida por tiempo o volumen de salida.")
            time.sleep(0.05)
        if os.fstat(out.fileno()).st_size > output_limit:
            raise Blocked("Salida de prueba demasiado grande.")
        out.seek(0)
        return process.returncode, out.read(output_limit).decode("utf-8", errors="replace")


class DockerRunner:
    def command(self, directory, image, profile, tests, name):
        path = Path(directory).resolve()
        if not path.is_dir() or "," in str(path):
            raise Blocked("Directorio de ensayo inválido.")
        if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9./:_-]*@sha256:[a-f0-9]{64}", image):
            raise Blocked("Falta una imagen aprobada fijada por SHA-256.")
        return ["docker", "run", "--rm", "--pull=never", "--name", name,
                "--network=none", "--read-only", "--cap-drop=ALL", "--security-opt=no-new-privileges",
                "--user=65534:65534", "--pids-limit=64", "--memory=512m", "--cpus=1",
                "--tmpfs=/tmp:rw,noexec,nosuid,size=64m", "--env=PYTHONDONTWRITEBYTECODE=1",
                "--mount", f"type=bind,source={path},target=/workspace,readonly",
                "--workdir=/workspace", image, *test_command(profile, tests, directory=directory)]

    def run(self, directory, image, profile, tests, artifact_digest):
        name = "rdc2-test-" + uuid.uuid4().hex
        command = self.command(directory, image, profile, tests, name)
        try:
            code, output = bounded_process(command)
            return {**assess(profile, code, output), "artifact_digest": artifact_digest,
                    "output_digest": digest(output), "profile": profile}
        finally:
            # Only our uniquely named test container; no broad cleanup or service stop.
            try:
                bounded_process(["docker", "rm", "-f", name], timeout=10)
            except (Blocked, OSError):
                pass
