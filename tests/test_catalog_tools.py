"""Fictitious replies and local static checks; never downloads or runs Docker."""
import copy
import hashlib
import json
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch

from factory2.core import Blocked
from factory2.dependencies import load_catalog, _js_imports, validate_dependencies
from factory2.js_analysis import javascript_imports, POLICY

ROOT = Path(__file__).resolve().parents[1]


class CatalogToolsTests(unittest.TestCase):
    def test_product_internal_and_cli_boundaries(self):
        catalog = load_catalog()
        def check(package, profile='javascript'):
            source = f'import "{package}";' if profile == 'javascript' else f'import {package}'
            return validate_dependencies({'summary_es': 'FICTICIO', 'edits': [{
                'path': 'src/main.mjs' if profile == 'javascript' else 'src/main.py',
                'content': source}]}, profile, catalog)
        for name in ('zod', 'drizzle-orm'):
            self.assertEqual(check(name), [name])
        for name, profile in [('acorn', 'javascript'), ('@playwright/test', 'javascript'),
                              ('pytest', 'python'), ('gitleaks', 'javascript'),
                              ('osv-scanner', 'javascript'), ('vitest', 'javascript')]:
            with self.subTest(name=name), self.assertRaisesRegex(Blocked, 'NOT_APPROVED'):
                check(name, profile)

    def test_tool_schema_sources_versions_types_and_duplicates(self):
        original = load_catalog()
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'catalog.json'
            for field, bad in [('name', 'other'), ('name', []), ('source', 'https://ficticio.invalid'),
                               ('source', 'https://github.com/gitleaks/gitleaks?token=ficticio'),
                               ('version', 'latest'), ('version', 'v8'), ('license', ''),
                               ('use', 'product'), ('extra', True)]:
                value = copy.deepcopy(original)
                value['herramientas'][0][field] = bad
                path.write_text(json.dumps(value))
                with self.subTest(field=field, bad=bad), self.assertRaisesRegex(Blocked, 'CATALOG_INVALID'):
                    load_catalog(path)
            for tools in (None, {}, original['herramientas'] * 2):
                path.write_text(json.dumps({**original, 'herramientas': tools}))
                with self.subTest(tools=tools), self.assertRaisesRegex(Blocked, 'CATALOG_INVALID'):
                    load_catalog(path)

    def test_old_or_unknown_top_level_schema_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'catalog.json'
            for value in ({'schema_version': 1, 'packages': []}, {**load_catalog(), 'extra': True}):
                path.write_text(json.dumps(value))
                with self.assertRaisesRegex(Blocked, 'CATALOG_INVALID'):
                    load_catalog(path)


class AcornAdapterTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.path = Path(temp.name)/'policy.json'
        self.policy = {'enabled': True, 'image': 'ficticio/parser@sha256:'+'a'*64, 'parser_version': '8.19.0'}
        self.source = 'import "node:path";'
        self.reply = {'parser_version': '8.19.0', 'source_sha256': hashlib.sha256(self.source.encode()).hexdigest(),
                      'imports': ['node:path']}
        self.calls = []

    def run_adapter(self, reply=None, code=0):
        self.path.write_text(json.dumps(self.policy))
        def process(command, **kwargs):
            self.calls.append(command)
            if command[1] == 'rm':
                return 0, ''
            return code, json.dumps(self.reply if reply is None else reply)
        with patch('factory2.js_analysis.bounded_process', side_effect=process):
            return javascript_imports(self.source, conservative=_js_imports, policy_path=self.path)

    def test_repository_disabled_conservative_and_no_process(self):
        self.assertEqual(json.loads(POLICY.read_text()), {'enabled': False, 'image': None, 'parser_version': '8.19.0'})
        with patch('factory2.js_analysis.bounded_process') as process:
            self.assertEqual(javascript_imports(self.source, conservative=_js_imports), ['node:path'])
            with self.assertRaises(Blocked):
                javascript_imports('const n = 10 / 2;', conservative=_js_imports)
            process.assert_not_called()

    def test_simulated_success_requires_isolation_and_exact_digest(self):
        self.assertEqual(self.run_adapter(), ['node:path'])
        command = self.calls[0]
        for flag in ('--network=none', '--pull=never', '--read-only', '--user=65534:65534',
                     '--cap-drop=ALL', '--security-opt=no-new-privileges', '--pids-limit=32'):
            self.assertIn(flag, command)
        self.assertIn(self.policy['image'], command)
        self.assertTrue(command[command.index('--mount')+1].endswith('target=/input,readonly'))
        self.assertFalse(any('socket' in arg or arg.startswith('--env') for arg in command))
        self.assertEqual(self.calls[1][:3], ['docker', 'rm', '-f'])
        self.assertEqual(self.calls[1][3], command[command.index('--name')+1])

    def test_bad_or_missing_image_never_runs_or_silently_falls_back(self):
        for image in (None, 'latest', 'ficticio/parser:8.19.0'):
            self.policy['image'] = image
            with self.subTest(image=image), self.assertRaises(Blocked):
                self.run_adapter()
            self.assertEqual(self.calls, [])
        self.policy['image'] = 'ficticio/parser@sha256:'+'a'*64
        with self.assertRaises(Blocked):
            self.run_adapter(code=125)

    def test_local_content_addressed_image_id_needs_no_registry(self):
        self.policy['image'] = 'sha256:'+'c'*64
        self.assertEqual(self.run_adapter(), ['node:path'])
        self.assertIn(self.policy['image'], self.calls[0])

    def test_invalid_parser_output_or_mismatched_source_blocks(self):
        for change in ({'source_sha256': 'b'*64}, {'parser_version': '9.0.0'},
                       {'imports': 'node:path'}, {'imports': [1]}, {'extra': 1}):
            with self.subTest(change=change), self.assertRaises(Blocked):
                self.run_adapter({**self.reply, **change})

    def test_invalid_json_timeout_and_unexpected_policy_block(self):
        self.path.write_text(json.dumps(self.policy))
        for result in ((0, 'not JSON'), (0, '{"imports":[],"imports":[]}')):
            with patch('factory2.js_analysis.bounded_process', return_value=result), self.assertRaises(Blocked):
                javascript_imports(self.source, conservative=_js_imports, policy_path=self.path)
        with patch('factory2.js_analysis.bounded_process', side_effect=Blocked('timeout')), self.assertRaises(Blocked):
            javascript_imports(self.source, conservative=_js_imports, policy_path=self.path)
        self.policy['enabled'] = 'false'
        with self.assertRaises(Blocked):
            self.run_adapter()


def audit_security_workflow(text):
    """Static assertions for this prepared YAML, not a general YAML validator."""
    required = ('on:\n  workflow_dispatch:\n', 'permissions:\n  contents: read\n',
                '    if: ${{ false }}\n', '    timeout-minutes: 15\n',
                '          persist-credentials: false\n', '          fetch-depth: 0\n',
                'scan source --offline --no-call-analysis=go --no-call-analysis=rust',
                '--redact=100', '--ignore-gitleaks-allow', '--config ', '--gitleaks-ignore-path ',
                '--proto-redir', 'sha256sum --check --status', ' > /dev/null 2>&1',
                'v8.30.1/gitleaks_8.30.1_linux_x64.tar.gz', 'v2.7.0/osv-scanner_linux_amd64',
                '551f6fc83ea457d62a0d98237cbad105af8d557003051f41f3e7ca7b3f2470eb',
                '160c6253e2922e9e0a6a9771c5c4c40a4b3c6090b34a3cdd5e80c96cc2e4218b')
    if not all(value in text for value in required):
        raise ValueError('WORKFLOW_POLICY')
    if re.findall(r'uses: (\S+)', text) != ['actions/checkout@11d5960a326750d5838078e36cf38b85af677262']:
        raise ValueError('WORKFLOW_ACTIONS')
    if any(word in text for word in ('secrets.', 'write-all', 'contents: write', 'pull_request:', 'push:',
                                      'schedule:', 'npm install', 'pip install', 'workflow_call:', '|| true')):
        raise ValueError('WORKFLOW_FORBIDDEN')


class PreparedWorkflowTests(unittest.TestCase):
    def test_offline_static_policy(self):
        audit_security_workflow((ROOT/'docs/propuestas/security-catalog.yml.txt').read_text())

    def test_mutations_block_activation_secrets_unpinned_downloads_and_actions(self):
        source = (ROOT/'docs/propuestas/security-catalog.yml.txt').read_text()
        mutations = [('if: ${{ false }}', 'if: ${{ true }}'), ('contents: read', 'contents: write'),
                     ('persist-credentials: false', 'persist-credentials: true'),
                     ('--offline', '--offline-vulnerabilities'), ('--redact=100', '--redact=0'),
                     ('v8.30.1/gitleaks_8.30.1', 'latest/gitleaks_latest'),
                     ('160c6253e2922e9e', '0000000000000000'),
                     ('actions/checkout@11d5960a326750d5838078e36cf38b85af677262', 'gitleaks/gitleaks-action@v2')]
        for before, after in mutations:
            with self.subTest(after=after), self.assertRaises(ValueError):
                audit_security_workflow(source.replace(before, after))
        for addition in ('\n  push:\n', '\n# secrets.EXAMPLE\n', '\n# npm install\n'):
            with self.subTest(addition=addition), self.assertRaises(ValueError):
                audit_security_workflow(source+addition)

    def test_acorn_build_has_pinned_base_hash_and_no_download_or_npm_hooks(self):
        dockerfile = (ROOT/'tools/acorn/Dockerfile').read_text()
        self.assertIn('FROM node@sha256:01d566e8d94d8c619591d78652babfccd3c6992a3dffa9ed5ab39e11cf6c70e9', dockerfile)
        self.assertIn("createHash('sha512')", dockerfile)
        self.assertIn('oJlA3XiRm7Cyk6qFD2Jn8ak9B7jSy0qy00ADO3+8dpT0LSjFihQYv4C02LFCSYJV3Q37xYwwRy5m+IpIiUzqWw==', dockerfile)
        self.assertNotIn('npm install', dockerfile)
        self.assertNotIn('curl ', dockerfile)
        self.assertIn('USER 65534:65534', dockerfile)
