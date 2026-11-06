"""Opt-in real Docker check. Never pulled by unittest discovery; never pulls images."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import shutil
import tempfile
import time
from unittest.mock import patch

from factory2.core import digest
from factory2 import runner


ROOT = Path(__file__).resolve().parents[1]
SANDBOX_TEST = '''import errno
import os
from pathlib import Path
import socket
import unittest

class SandboxTests(unittest.TestCase):
    def test_nonprivileged(self):
        self.assertEqual((os.getuid(), os.getgid()), (65534, 65534))
        status = dict(line.split(':', 1) for line in Path('/proc/self/status').read_text().splitlines() if ':' in line)
        self.assertEqual(int(status['CapEff'].strip(), 16), 0)
        self.assertEqual(status['NoNewPrivs'].strip(), '1')

    def test_workspace_and_root_cannot_be_written(self):
        for name in ('/workspace/FICTICIO_NO_ESCRIBIR.txt', '/FICTICIO_NO_ESCRIBIR.txt'):
            with self.subTest(path=name), self.assertRaises(OSError) as caught:
                Path(name).write_text('FICTICIO')
            self.assertIn(caught.exception.errno, (errno.EROFS, errno.EACCES))
        self.assertEqual(Path('/workspace/sentinel.txt').read_text(), 'FICTICIO')
        with self.assertRaises(OSError):
            Path('/workspace/sentinel.txt').write_text('ALTERADO')

    def test_no_network_route_to_fictitious_destination(self):
        # TEST-NET-1, not a real service. Assert loopback-only before the attempt.
        self.assertEqual({p.name for p in Path('/sys/class/net').iterdir()}, {'lo'})
        with socket.socket() as connection:
            connection.settimeout(2)
            with self.assertRaises(OSError) as caught:
                connection.connect(('192.0.2.1', 9))
        self.assertEqual(caught.exception.errno, errno.ENETUNREACH)
'''


def snapshot(folder):
    return {p.relative_to(folder).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(folder.rglob('*')) if p.is_file()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--python-image', required=True)
    parser.add_argument('--node-image', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    real_process = runner.bounded_process
    calls = []

    def local(command, **options):
        code, output = real_process(command, **options)
        calls.append({'command': command, 'exit_code': code, 'output': output})
        return code, output

    results = []
    evidence = {'status': 'BLOCKED', 'real_docker': True, 'providers_used': False, 'publication_allowed': False}
    start = math.floor(time.time())
    try:
        code, host = local(['docker', 'context', 'inspect', '--format', '{{.Endpoints.docker.Host}}'])
        if code or host.strip() not in ('npipe:////./pipe/dockerDesktopLinuxEngine',
                                       'npipe:////./pipe/docker_engine'):
            raise RuntimeError('LOCAL_DOCKER_ENDPOINT_REQUIRED')
        evidence['endpoint'] = host.strip()
        code, default_id = local(['docker', 'info', '--format', '{{.ID}}'])
        explicit_code, desktop_id = local(['docker', '--host', 'npipe:////./pipe/dockerDesktopLinuxEngine',
                                          'info', '--format', '{{.ID}}'])
        if code or explicit_code or not default_id.strip() or default_id != desktop_id:
            raise RuntimeError('DOCKER_ENGINE_MISMATCH')
        code, version = local(['docker', 'version', '--format', '{{.Server.Version}} {{.Server.Os}}/{{.Server.Arch}}'])
        if code or 'linux/amd64' not in version:
            raise RuntimeError('LOCAL_LINUX_ENGINE_REQUIRED')
        evidence['engine'] = version.strip()
        for image in (args.python_image, args.node_image):
            code, output = local(['docker', 'image', 'inspect', image, '--format', '{{.Id}} {{.Os}}/{{.Architecture}}'])
            if code or 'linux/amd64' not in output:
                raise RuntimeError('PINNED_LOCAL_IMAGE_REQUIRED')
        with tempfile.TemporaryDirectory(prefix='factory-docker-fiction-') as temporary:
            base = Path(temporary)
            python = base / 'python'
            javascript = base / 'javascript'
            sandbox = base / 'sandbox'
            for name in ('factory2/__init__.py', 'factory2/core.py', 'factory2/pilot.py',
                         'tests/__init__.py', 'tests/test_pilot.py'):
                destination = python / name
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / name, destination)
            for name in ('src/bottles.mjs', 'tests/bottles.test.mjs'):
                destination = javascript / name
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / 'pilot-js' / name, destination)
            (sandbox / 'tests').mkdir(parents=True)
            (sandbox / 'tests/__init__.py').write_text('')
            (sandbox / 'tests/test_sandbox.py').write_text(SANDBOX_TEST, encoding='utf-8')
            (sandbox / 'sentinel.txt').write_text('FICTICIO', encoding='utf-8')
            before = snapshot(base)
            plan = [(python, args.python_image, 'python', ['tests/test_pilot.py']),
                    (javascript, args.node_image, 'javascript', ['tests/bottles.test.mjs']),
                    (sandbox, args.python_image, 'python', ['tests/test_sandbox.py'])]
            with patch.object(runner, 'bounded_process', side_effect=local):
                for directory, image, profile, tests in plan:
                    result = runner.DockerRunner().run(directory, image, profile, tests, digest(snapshot(directory)))
                    results.append({'case': directory.name, 'image': image, **result})
                    if result['status'] != 'PASS':
                        raise RuntimeError('DOCKER_CHECK_FAILED')
            evidence['host_files_unchanged'] = before == snapshot(base)
            if not evidence['host_files_unchanged']:
                raise RuntimeError('HOST_FIXTURE_CHANGED')
        code, pulls = local(['docker', 'events', '--since', str(start), '--until', f'{time.time():.9f}',
                             '--filter', 'type=image', '--filter', 'event=pull', '--format', 'PULL_EVENT'], timeout=10)
        evidence['pull_events_during_checks'] = len(pulls.strip().splitlines()) if code == 0 else None
        if code or pulls.strip():
            raise RuntimeError('NO_PULL_EVIDENCE_FAILED')
        for entry in calls:
            command = entry['command']
            if command[:2] == ['docker', 'run']:
                for required in ('--pull=never', '--network=none', '--read-only', '--user=65534:65534',
                                 '--cap-drop=ALL', '--security-opt=no-new-privileges'):
                    if required not in command:
                        raise RuntimeError('RUNNER_RESTRICTION_MISSING')
        evidence['status'] = 'PASS'
    finally:
        evidence['results'] = results
        (args.output / 'evidence.json').write_text(json.dumps(evidence, indent=2) + '\n', encoding='utf-8')
        (args.output / 'commands-and-output.json').write_text(json.dumps(calls, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(evidence, indent=2))


if __name__ == '__main__':
    main()
