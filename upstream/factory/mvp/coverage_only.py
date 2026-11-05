"""Explicit operator grant for adding coverage to an unchanged working endpoint."""
from .common import Blocked, digest

TEST = 'tests/test_factory_ping_http.py'
DOC = 'src/PING.md'

def enabled(config, issue_number, base, files):
    grant = config.get('ping_coverage_grant')
    if not grant or issue_number != 13:
        return False
    if (config['repository'] != 'fernandoruizm-maker/rdc' or grant.get('issue') != 13
            or grant.get('base_sha') != base or grant.get('snapshot_sha') != digest(files)
            or TEST in files or DOC in files):
        raise Blocked('Coverage authorization does not match issue, base or original files')
    return True

def validate_tests(tests):
    if set(tests) != {TEST}:
        raise Blocked('Coverage task may only add its designated test file')

def validate_docs(edits):
    if set(edits) != {DOC}:
        raise Blocked('Coverage task may only add src/PING.md; product code is frozen')

def require_passing(result):
    if not result.green or result.skipped or not result.ids:
        raise Blocked('Coverage of existing behavior must pass without errors or skips; do not change the endpoint')
