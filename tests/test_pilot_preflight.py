"""Offline regressions: temporary Git/SQLite, fake Docker and fake environment only."""
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from factory2.core import Blocked
from factory2.operations import worker_lock
from factory2.orchestrator import clean_head, git_call
from factory2.pilot_preflight import REASON_CODES, reason_code, docker_query

ROOT = Path(__file__).resolve().parents[1]


class PreflightRegressionTests(unittest.TestCase):
    def test_worker_lock_does_not_dirty_git_but_other_state_files_do(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root/'.gitignore').write_bytes((ROOT/'.gitignore').read_bytes())
            git_call(root, 'init', '-q')
            git_call(root, 'add', '.gitignore')
            git_call(root, 'commit', '-q', '-m', 'FICTICIO local')
            expected = clean_head(root)
            (root/'state').mkdir()
            with worker_lock(root/'state/worker.lock'):
                self.assertEqual(clean_head(root), expected)
            (root/'state/unexpected.txt').write_text('FICTICIO')
            with self.assertRaisesRegex(Blocked, '^SOURCE_OR_CANDIDATE_NOT_CLEAN$'):
                clean_head(root)

    def test_closed_codes_and_unknown_exceptions_never_reveal_text(self):
        for code in REASON_CODES:
            with self.subTest(code=code):
                self.assertEqual(reason_code(Blocked(code)), code)
        for error, expected in (
            (Blocked('FICTICIO_PRIVATE'), 'PILOT_PREFLIGHT_UNEXPECTED_NO_RETRY'),
            (RuntimeError('FICTICIO_PRIVATE'), 'PILOT_PREFLIGHT_UNEXPECTED_NO_RETRY'),
            (sqlite3.OperationalError('FICTICIO_PRIVATE'), 'PILOT_PREFLIGHT_LEDGER_ERROR'),
            (OSError('FICTICIO_PRIVATE'), 'PILOT_PREFLIGHT_IO_ERROR'),
            (subprocess.TimeoutExpired('FICTICIO_PRIVATE', 1), 'PILOT_PREFLIGHT_PROCESS_TIMEOUT')):
            self.assertEqual(reason_code(error), expected)
            self.assertNotIn('FICTICIO_PRIVATE', reason_code(error))

    def test_docker_query_errors_are_fixed_codes(self):
        for error, code in ((OSError('FICTICIO_PRIVATE'), 'PILOT_DOCKER_QUERY_FAILED'),
                            (Blocked('FICTICIO_PRIVATE'), 'PILOT_DOCKER_QUERY_FAILED'),
                            (subprocess.TimeoutExpired('FICTICIO', 1), 'PILOT_DOCKER_QUERY_TIMEOUT')):
            with self.subTest(code=code), patch('factory2.pilot_preflight.bounded_process', side_effect=error):
                with self.assertRaisesRegex(Blocked, '^'+code+'$'):
                    docker_query(['docker','context','inspect'])

    def test_check_and_run_process_info_have_identical_reduced_environment(self):
        # Parse/load ONLY the trusted constructor function. Never invoke the launcher,
        # Process.Start, a credential prompt, run/check mode, Docker or a provider.
        env = {k:v for k,v in os.environ.items() if k.upper() in
               {'PATH','SYSTEMROOT','WINDIR','TEMP','TMP','PATHEXT','COMSPEC'}}
        env.update(OPENAI_API_KEY='FICTICIO', GITHUB_TOKEN='FICTICIO', USERPROFILE='FICTICIO',
                   APPDATA='FICTICIO', DOCKER_HOST='tcp://ficticio.invalid', PYTHONPATH='FICTICIO')
        with tempfile.TemporaryDirectory() as folder:
            # PowerShell may create its own cache despite -NoProfile. Keep even
            # those fictitious profile files outside the real checkout/profile.
            env.update(USERPROFILE=folder, APPDATA=folder, LOCALAPPDATA=folder)
            result = subprocess.run(['pwsh','-NoProfile','-NonInteractive','-File',
                                     str(ROOT/'tests/inspect_trial_launcher.ps1'),
                                     str(ROOT/'scripts/ensayo-intento-1.ps1')],
                                    env=env, cwd=folder, capture_output=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr.decode(errors='replace'))
        check, run = json.loads(result.stdout)
        expected = sorted([k for k in env if k.upper() in
                    {'PATH','SYSTEMROOT','WINDIR','TEMP','TMP','PATHEXT','COMSPEC'}]
                    +['PYTHONDONTWRITEBYTECODE','PYTHONIOENCODING'])
        self.assertEqual(sorted(check['environment']), expected)
        self.assertEqual(check['environment'], run['environment'])
        self.assertEqual(check['action'], 'check')
        self.assertEqual(run['action'], 'run')
        self.assertFalse(check['shell'])
        self.assertFalse(run['shell'])

