"""Local fictitious arms/catalogs and simulated ports. No real state or provider."""
import copy
import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

from factory2.arming import validate_arm, FLAGS
from factory2.core import Blocked, canonical, digest
from factory2.dependencies import load_catalog, validate_dependencies, CATALOG
from factory2.orchestrator import clean_head, git_call
from tests.operation_fixtures import arm_fixture
from tests import test_pilot_trial as trials


class ArmingTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.cfg = {flag: False for flag in FLAGS}
        self.path = arm_fixture(self.root, self.cfg)
        self.arm = json.loads(self.path.read_text())

    def test_valid_local_arm_does_not_change_config(self):
        before = canonical(self.cfg)
        self.assertEqual(validate_arm(self.path, self.cfg, 'botellas', 1), self.arm)
        self.assertEqual(canonical(self.cfg), before)

    def test_absent_arm_is_off(self):
        with self.assertRaisesRegex(Blocked, '^PILOT_SWITCH_OFF$'):
            validate_arm(self.root/'missing.json', self.cfg, 'botellas', 1)

    def test_expired_future_too_long_and_invalid_times_block(self):
        now = time.time()
        for changes in ({'expires_at': now - 1}, {'issued_at': now + 1},
                        {'issued_at': now, 'expires_at': now + 86401},
                        {'expires_at': True}, {'issued_at': 'today'}, {'expires_at': float('inf')}):
            self.path.write_text(canonical({**self.arm, **changes}))
            with self.subTest(changes=changes), self.assertRaisesRegex(Blocked, '^PILOT_ARM_INVALID$'):
                validate_arm(self.path, self.cfg, 'botellas', 1, now=now)

    def test_maximum_lifetime_is_24_hours(self):
        now = time.time()
        self.path.write_text(canonical({**self.arm, 'issued_at': now, 'expires_at': now+86400}))
        validate_arm(self.path, self.cfg, 'botellas', 1, now=now)
        with self.assertRaisesRegex(Blocked, 'ARM_INVALID'):
            validate_arm(self.path, self.cfg, 'botellas', 1, now=now+86400)

    def test_job_attempt_digest_and_strict_schema(self):
        for changes in ({'encargo': 'caja-chica'}, {'attempt': 2}, {'attempt': True},
                        {'config_digest': 'a'*64}, {'extra': True}):
            self.path.write_text(canonical({**self.arm, **changes}))
            with self.subTest(changes=changes), self.assertRaisesRegex(Blocked, 'ARM_INVALID'):
                validate_arm(self.path, self.cfg, 'botellas', 1)
        self.path.write_text('{}')
        with self.assertRaisesRegex(Blocked, 'ARM_INVALID'):
            validate_arm(self.path, self.cfg, 'botellas', 1)

    def test_json_duplicate_invalid_size_and_links_block(self):
        for raw in ('not json', '{"attempt":1,"attempt":1}', ' '*4097):
            self.path.write_text(raw)
            with self.subTest(raw=raw[:20]), self.assertRaisesRegex(Blocked, 'ARM_INVALID'):
                validate_arm(self.path, self.cfg, 'botellas', 1)
        with patch('factory2.arming._plain_path', side_effect=Blocked('ENCARGO_PATH_UNSAFE')):
            with self.assertRaisesRegex(Blocked, 'ARM_INVALID'):
                validate_arm(self.path, self.cfg, 'botellas', 1)

    def test_all_git_switches_must_be_false(self):
        for flag in FLAGS:
            with self.subTest(flag=flag), self.assertRaisesRegex(Blocked, 'CONFIG_MUST_REMAIN_DISARMED'):
                validate_arm(self.path, {**self.cfg, flag: True}, 'botellas', 1)

    def test_arm_is_ignored_without_ignoring_unknown_state(self):
        repo = Path(__file__).resolve().parents[1]
        (self.root/'.gitignore').write_bytes((repo/'.gitignore').read_bytes())
        git_call(self.root, 'init', '-q')
        git_call(self.root, 'add', '.gitignore')
        git_call(self.root, 'commit', '-q', '-m', 'FICTICIO')
        head = clean_head(self.root)
        arm_fixture(self.root, self.cfg, attempt=2)
        self.assertEqual(clean_head(self.root), head)
        (self.root/'state/unexpected.txt').write_text('FICTICIO')
        with self.assertRaises(Blocked):
            clean_head(self.root)


def proposal(text, profile='javascript', extra=()):
    return {'summary_es': 'FICTICIO', 'edits': [
        {'path': 'src/main.mjs' if profile == 'javascript' else 'src/main.py', 'content': text}, *extra]}


class DependencyTests(unittest.TestCase):
    def setUp(self):
        self.catalog = load_catalog()

    def check(self, text, profile='javascript', catalog=None, extra=()):
        return validate_dependencies(proposal(text, profile, extra), profile, catalog or self.catalog)

    def test_repository_catalog_has_no_external_packages(self):
        self.assertEqual(self.catalog, {'schema_version': 1, 'packages': []})

    def test_node_standard_import_require_export_and_literal_dynamic(self):
        for source in ('import assert from "node:assert/strict";', 'require("fs/promises");',
                       'export {readFile} from "node:fs";', 'import("node:path");',
                       'import "node:test";', 'import * as x from "node:crypto";'):
            with self.subTest(source=source):
                self.assertEqual(self.check(source), [])

    def test_python_standard_library(self):
        self.assertEqual(self.check('import decimal, math\nfrom collections import defaultdict\n', 'python'), [])

    def test_unapproved_external_imports_block(self):
        for profile, source in (('javascript','import x from "unapproved";'),
                                ('javascript','const x = require("@scope/unapproved/sub");'),
                                ('javascript','export * from "unapproved";'),
                                ('python','import unapproved\n'),
                                ('python','from unapproved.sub import x\n')):
            with self.subTest(profile=profile, source=source), self.assertRaisesRegex(Blocked, 'DEPENDENCY_NOT_APPROVED'):
                self.check(source, profile)

    def test_strings_and_comments_are_not_imports(self):
        self.assertEqual(self.check('// require("bad")\nconst x = "import bad"; /* import "bad" */'), [])
        self.assertEqual(self.check('# import bad\nx = "import bad"\n', 'python'), [])

    def test_javascript_ambiguous_dynamic_loads_fail_closed(self):
        for source in ('require(name)', 'import(name)', 'const r = require; r("bad")',
                       'module.require("bad")', 'import.meta.require("bad")',
                       'createRequire(x)', 'eval("require(abc)")', 'new Function(x)',
                       'const x = `${require("bad")}`', 'requ\\u0069re("bad")',
                       'import "\\u0062ad";', '/* unfinished',
                       '''const re = /'/; import x from "bad"; const s='/';'''):
            with self.subTest(source=source), self.assertRaisesRegex(Blocked, 'DEPENDENCY_ANALYSIS_BLOCKED'):
                self.check(source)

    def test_python_dynamic_loaders_and_invalid_syntax_block(self):
        for source in ('__import__("bad")', 'eval("1")', 'exec("import bad")',
                       'x.import_module("bad")', 'getattr(x, "loader")', 'def broken('):
            with self.subTest(source=source), self.assertRaisesRegex(Blocked, 'DEPENDENCY_ANALYSIS_BLOCKED'):
                self.check(source, 'python')

    def test_known_local_modules_only(self):
        self.assertEqual(self.check('import "./helper.mjs";', extra=[
            {'path':'src/helper.mjs', 'content':'export const n = 1;'}]), [])
        self.assertEqual(self.check('from .helper import n', 'python', extra=[
            {'path':'src/helper.py', 'content':'n = 1'}]), [])
        for source in ('import "./missing.mjs";', 'import "../../outside.mjs";', 'import "https://ficticio.invalid/x";'):
            with self.subTest(source=source), self.assertRaises(Blocked):
                self.check(source)

    def test_product_approval_and_profile_are_required(self):
        row = {'package':'ficticio', 'version':'1.2.3', 'license':'MIT', 'use':'product', 'profile':'javascript'}
        catalog = {'schema_version':1, 'packages':[row]}
        self.assertEqual(self.check('require("ficticio/sub")', catalog=catalog), ['ficticio'])
        for change in ({'use':'internal'}, {'profile':'python'}):
            with self.subTest(change=change), self.assertRaisesRegex(Blocked, 'NOT_APPROVED'):
                self.check('require("ficticio")', catalog={'schema_version':1, 'packages':[{**row, **change}]})

    def test_catalog_schema_exact_versions_license_and_duplicates(self):
        row = {'package':'ficticio', 'version':'1.2.3', 'license':'MIT', 'use':'product', 'profile':'python'}
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'catalog.json'
            path.write_text(canonical({'schema_version':1, 'packages':[row]}))
            self.assertEqual(load_catalog(path)['packages'][0], row)
            for change in ({'version':'latest'}, {'version':'^1.2.3'}, {'license':''}, {'use':'all'}, {'extra':True}):
                path.write_text(canonical({'schema_version':1, 'packages':[{**row, **change}]}))
                with self.subTest(change=change), self.assertRaisesRegex(Blocked, 'CATALOG_INVALID'):
                    load_catalog(path)
            path.write_text(canonical({'schema_version':1, 'packages':[row, row]}))
            with self.assertRaisesRegex(Blocked, 'CATALOG_INVALID'):
                load_catalog(path)


class PipelineGuardTests(unittest.TestCase):
    setUp = trials.TrialTests.setUp
    review = trials.TrialTests.review
    change_config = trials.TrialTests.change_config

    def test_unapproved_dependency_stops_before_materializing_or_testing(self):
        self.generate = lambda _: {'summary_es':'FICTICIO', 'edits':[
            {'path':'src/bottles.mjs', 'content':'import x from "unapproved";'}]}
        result = self.trial.start(self.auth)
        self.assertEqual(result['status'], 'BLOCKED')
        self.assertEqual(result['reason_code'], 'DEPENDENCY_NOT_APPROVED')
        self.assertEqual(self.seen, ['provider'])
        self.assertEqual(self.store.budget.summary()['attempts'], 1)

    def test_arm_does_not_replace_authorization(self):
        with self.assertRaisesRegex(Blocked, 'PILOT_AUTHORIZATION_REQUIRED'):
            self.trial.start({**self.auth, 'authorized_by': None})
        self.assertEqual(self.seen, [])
        self.assertEqual(self.store.budget.summary()['attempts'], 0)

    def test_expiry_between_preflight_and_call_stops_provider(self):
        reserve = self.store.reserve_paid_call
        def expire(*args, **kwargs):
            reserve(*args, **kwargs)
            path = self.root/'state/armado.json'
            arm = json.loads(path.read_text())
            path.write_text(canonical({**arm, 'expires_at': 0}))
        with patch.object(self.store, 'reserve_paid_call', side_effect=expire):
            result = self.trial.start(self.auth)
        self.assertEqual(result['status'], 'BLOCKED')
        self.assertEqual(self.seen, [])

    def test_config_remains_disarmed_through_complete_simulation(self):
        before = self.store.config_path.read_bytes()
        result = self.trial.start(self.auth)
        self.assertEqual(result['status'], 'WAITING_FOR_MANUAL_REVIEW')
        self.assertEqual(self.store.config_path.read_bytes(), before)
        for flag in FLAGS:
            self.assertIs(self.store.config()[flag], False)
        self.assertFalse(result['publication_allowed'])
