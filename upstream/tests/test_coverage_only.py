import unittest
from factory.mvp.coverage_only import enabled,validate_tests,validate_docs,require_passing,TEST,DOC
from factory.mvp.common import Blocked,digest
from factory.mvp.runner import parse_result

class CoverageOnlyTests(unittest.TestCase):
    def setUp(self):
        self.files={'src/api.py':'existing endpoint','tests/test_old.py':'original assertions'}
        self.config={'repository':'fernandoruizm-maker/rdc','ping_coverage_grant':{
            'issue':13,'base_sha':'base','snapshot_sha':digest(self.files)}}
    def test_explicit_exact_grant_required(self):
        self.assertTrue(enabled(self.config,13,'base',self.files))
        self.assertFalse(enabled({},13,'base',self.files))
        self.assertFalse(enabled(self.config,12,'base',self.files))
        with self.assertRaises(Blocked): enabled(self.config,13,'changed',self.files)
        with self.assertRaises(Blocked): enabled(self.config,13,'base',{**self.files,'other':'x'})
    def test_cannot_overwrite_even_with_matching_hash(self):
        for p in [TEST,DOC]:
            files={**self.files,p:'existing'}
            self.config['ping_coverage_grant']['snapshot_sha']=digest(files)
            with self.assertRaises(Blocked): enabled(self.config,13,'base',files)
    def test_no_product_or_existing_test_changes(self):
        validate_tests({TEST:'new'}); validate_docs({DOC:'guide'})
        for edits in [{DOC:'guide','src/api.py':'changed'},{'src/api.py':'changed'},{}]:
            with self.assertRaises(Blocked): validate_docs(edits)
        with self.assertRaises(Blocked): validate_tests({'tests/test_old.py':'changed'})
    def test_failing_skipped_or_empty_tests_block(self):
        good='test_http (test_ping.Case.test_http) ... ok\nRan 1 test in 0.1s\nOK\n'
        require_passing(parse_result(0,good,{}))
        for code,out in [(1,good+'FAILED (failures=1)'),(0,good+'OK (skipped=1)'),(0,'Ran 0 tests in 0s\nOK')]:
            with self.assertRaises(Blocked): require_passing(parse_result(code,out,{}))
