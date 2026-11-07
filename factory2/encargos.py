"""Offline, closed contracts for fictional jobs and their operator-controlled tests."""
import json
from pathlib import Path
import re

from .core import Blocked, canonical, discover
from .manual_review import SECRET_PATTERN

ROOT = Path(__file__).resolve().parents[1] / 'encargos'
RESERVED = {'con', 'prn', 'aux', 'nul', *(f'com{i}' for i in range(10)), *(f'lpt{i}' for i in range(10))}


def job_name(name):
    if (not isinstance(name, str) or not re.fullmatch(r'[a-z][a-z0-9]*(?:-[a-z0-9]+)*', name)
            or len(name) > 50 or name in RESERVED or name == 'bottles'):
        raise Blocked('ENCARGO_NAME_INVALID')
    return name


def attempt_ids(name, attempt):
    job_name(name)
    if type(attempt) is not int or not 1 <= attempt <= 1000000:
        raise Blocked('PILOT_ATTEMPT_INVALID')
    current = f'{name}-{attempt}'
    return (current, f'bottles-{attempt}') if name == 'botellas' else (current,)


def assert_new_attempt(db, name, attempt):
    """Shared by read-only preflight and locked start, including legacy aliases."""
    ids = attempt_ids(name, attempt)
    tables = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    for table in sorted(tables):
        quoted = '"' + table.replace('"', '""') + '"'
        columns = {row[1] for row in db.execute(f'PRAGMA table_info({quoted})')}
        for column in sorted(columns & {'id', 'task', 'execution'}):
            for ident in ids:
                if db.execute(f'SELECT 1 FROM {quoted} WHERE "{column}"=?', (ident,)).fetchone():
                    raise Blocked('PILOT_ALREADY_RECORDED_NO_RETRY')
    prior = {}
    prefixes = ('botellas', 'bottles') if name == 'botellas' else (name,)
    if 'pilot_trials' in tables:
        for ident, raw in db.execute('SELECT id,data FROM pilot_trials'):
            prefix, _, number = ident.rpartition('-')
            if prefix not in prefixes or not number.isdigit():
                continue
            n = int(number)
            if n in prior:
                raise Blocked('PILOT_LEGACY_ID_CONFLICT')
            prior[n] = json.loads(raw)['status']
            if prior[n] != 'BLOCKED':
                raise Blocked('PILOT_PREVIOUS_ATTEMPT_UNFINISHED')
    if any(prior.get(n) != 'BLOCKED' for n in range(1, attempt)):
        raise Blocked('PILOT_PREVIOUS_ATTEMPT_UNFINISHED')


def _plain_path(path):
    for part in (path, *path.parents):
        if part.is_symlink() or (hasattr(part, 'is_junction') and part.is_junction()):
            raise Blocked('ENCARGO_PATH_UNSAFE')


def _text(value):
    return isinstance(value, str) and bool(value.strip()) and len(value) <= 10000 and '\0' not in value


def _json(path):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError
            result[key] = value
        return result
    def invalid(_):
        raise ValueError
    try:
        if path.stat().st_size > 100000:
            raise ValueError
        return json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=pairs, parse_constant=invalid)
    except (ValueError, OSError, RecursionError):
        raise Blocked('ENCARGO_JSON_INVALID') from None


def load_encargo(name, root=ROOT):
    job_name(name)
    folder = Path(root).absolute() / name
    _plain_path(folder)
    if not folder.is_dir():
        raise Blocked('ENCARGO_MISSING')
    if {p.name for p in folder.iterdir()} != {'requisitos.json', 'salida.json', 'tests'}:
        raise Blocked('ENCARGO_SCOPE_INVALID')
    for path in folder.iterdir():
        _plain_path(path)
    req = _json(folder / 'requisitos.json')
    output = _json(folder / 'salida.json')
    if (not isinstance(req, dict) or set(req) != {'schema_version', 'synthetic', 'brief'}
            or type(req['schema_version']) is not int or req['schema_version'] != 1
            or req['synthetic'] is not True):
        raise Blocked('ENCARGO_REQUIREMENTS_INVALID')
    brief = req['brief']
    if (not isinstance(brief, dict) or set(brief) != {'client', 'objective', 'users', 'areas',
                                                   'requirements', 'exclusions', 'assumptions'}
            or not all(_text(brief[k]) for k in ('client', 'objective'))):
        raise Blocked('ENCARGO_REQUIREMENTS_INVALID')
    for key in ('users', 'areas', 'exclusions', 'assumptions'):
        value = brief[key]
        if (not isinstance(value, list) or not 1 <= len(value) <= 100
                or not all(_text(v) for v in value) or len(set(value)) != len(value)):
            raise Blocked('ENCARGO_REQUIREMENTS_INVALID')
    rows = brief['requirements']
    if (not isinstance(rows, list) or not 1 <= len(rows) <= 100
            or any(not isinstance(r, dict) or set(r) != {'id', 'goal', 'acceptance', 'document'}
                   or not all(_text(v) for v in r.values()) for r in rows)
            or len({r['id'] for r in rows}) != len(rows)
            or discover(brief)['status'] != 'READY_FOR_SCOPE_REVIEW'):
        raise Blocked('ENCARGO_REQUIREMENTS_INVALID')
    if (not isinstance(output, dict) or set(output) != {'schema_version', 'files', 'profile', 'expected_tests', 'interface'}
            or type(output['schema_version']) is not int or output['schema_version'] != 1
            or output['profile'] not in ('javascript', 'python')
            or type(output['expected_tests']) is not int or not 1 <= output['expected_tests'] <= 1000
            or not _text(output['interface'])):
        raise Blocked('ENCARGO_OUTPUT_INVALID')
    files = output['files']
    suffix = r'(?:mjs|js)' if output['profile'] == 'javascript' else 'py'
    if (not isinstance(files, list) or not 1 <= len(files) <= 10
            or any(not isinstance(f, str) or not re.fullmatch(r'src/(?:[A-Za-z0-9_-]+/)*[A-Za-z0-9_-]+\.'+suffix, f)
                   or any(p.split('.')[0].casefold() in RESERVED for p in f.split('/')) for f in files)
            or len({f.casefold() for f in files}) != len(files)):
        raise Blocked('ENCARGO_OUTPUT_INVALID')
    tests_dir = folder / 'tests'
    if not tests_dir.is_dir():
        raise Blocked('ENCARGO_TESTS_INVALID')
    paths = sorted(tests_dir.iterdir())
    if not 1 <= len(paths) <= 30:
        raise Blocked('ENCARGO_TESTS_INVALID')
    tests = {}
    for path in paths:
        _plain_path(path)
        pattern = r'[A-Za-z0-9_-]+\.test\.mjs' if output['profile'] == 'javascript' else r'test_[A-Za-z0-9_]+\.py'
        if (not path.is_file() or not re.fullmatch(pattern, path.name)
                or path.stat().st_size > 100000):
            raise Blocked('ENCARGO_TESTS_INVALID')
        try:
            raw = path.read_text(encoding='utf-8')
        except (OSError, UnicodeError):
            raise Blocked('ENCARGO_TESTS_INVALID') from None
        if not raw.strip() or '\0' in raw:
            raise Blocked('ENCARGO_TESTS_INVALID')
        tests['tests/' + path.name] = raw
    if len({k.casefold() for k in tests}) != len(tests):
        raise Blocked('ENCARGO_TESTS_INVALID')
    context = {'encargo': name, 'brief': brief, 'synthetic': True,
               'required_output': files, 'profile': output['profile'], 'expected_tests': output['expected_tests'],
               'interface': output['interface'], 'trusted_tests': tests}
    raw = canonical(context)
    if len(raw.encode('utf-8')) > 100000 or SECRET_PATTERN.search(raw):
        raise Blocked('ENCARGO_CONTENT_REJECTED')
    return context
