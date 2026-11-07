"""Conservative static dependency gate. Does not install or execute candidate code.

This is an import inventory, not a JavaScript/Python security sandbox. Unsupported
dynamic loaders fail closed; Docker and human review remain mandatory.
"""
import ast
from pathlib import Path, PurePosixPath
import re

from .core import Blocked, validate_edits
from .encargos import _json, _plain_path

CATALOG = Path(__file__).resolve().parents[1] / 'catalogo-aprobado.json'
# Deliberately explicit portable subset, not all modules installed on this PC.
PY_STDLIB = frozenset('abc argparse array ast base64 bisect calendar cmath collections '
    'contextlib copy csv dataclasses datetime decimal enum fractions functools hashlib '
    'heapq hmac html http io itertools json logging math numbers operator os pathlib '
    'queue random re secrets shutil socket sqlite3 statistics string struct subprocess '
    'sys tempfile textwrap threading time timeit traceback types typing unicodedata '
    'unittest urllib uuid warnings weakref xml zipfile zoneinfo'.split())
NODE_STDLIB = frozenset('assert assert/strict async_hooks buffer child_process cluster '
    'console constants crypto dgram diagnostics_channel dns dns/promises domain events '
    'fs fs/promises http http2 https inspector net os path path/posix path/win32 '
    'perf_hooks process punycode querystring readline readline/promises repl stream '
    'stream/consumers stream/promises stream/web string_decoder test test/reporters '
    'timers timers/promises tls trace_events tty url util util/types v8 vm wasi '
    'worker_threads zlib'.split())


def load_catalog(path=CATALOG):
    try:
        _plain_path(Path(path).absolute())
        value = _json(Path(path))
        if (not isinstance(value, dict) or set(value) != {'schema_version', 'packages', 'herramientas'}
                or type(value['schema_version']) is not int or value['schema_version'] != 2
                or not isinstance(value['packages'], list) or len(value['packages']) > 1000
                or not isinstance(value['herramientas'], list) or len(value['herramientas']) > 100):
            raise ValueError
        seen = set()
        for row in value['packages']:
            if (not isinstance(row, dict) or set(row) != {'package', 'version', 'license', 'use', 'profile'}
                    or row['profile'] not in ('javascript', 'python')
                    or row['use'] not in ('internal', 'product')
                    or not isinstance(row['package'], str)
                    or not re.fullmatch(r'(?:@[a-z0-9_-]+/)?[a-zA-Z0-9_][a-zA-Z0-9_.-]*', row['package'])
                    or not isinstance(row['version'], str)
                    or not re.fullmatch(r'\d+\.\d+\.\d+(?:[-+][a-zA-Z0-9.-]+)?', row['version'])
                    or not isinstance(row['license'], str)
                    or not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9.()+ -]{0,100}', row['license'])):
                raise ValueError
            key = (row['profile'], row['package'].casefold())
            if key in seen:
                raise ValueError
            seen.add(key)
        sources = {'gitleaks': 'https://github.com/gitleaks/gitleaks',
                   'osv-scanner': 'https://github.com/google/osv-scanner'}
        seen_tools = set()
        for row in value['herramientas']:
            if (not isinstance(row, dict)
                    or set(row) != {'name', 'version', 'license', 'use', 'source'}
                    or not isinstance(row['name'], str) or row['name'] not in sources
                    or row['source'] != sources[row['name']] or row['use'] != 'internal'
                    or not isinstance(row['version'], str)
                    or not re.fullmatch(r'v\d+\.\d+\.\d+', row['version'])
                    or row['license'] != ('MIT' if row['name'] == 'gitleaks' else 'Apache-2.0')
                    or row['name'] in seen_tools):
                raise ValueError
            seen_tools.add(row['name'])
        return value
    except (Blocked, ValueError, TypeError, OSError):
        raise Blocked('DEPENDENCY_CATALOG_INVALID') from None


def _js_tokens(source):
    tokens, i = [], 0
    while i < len(source):
        c = source[i]
        if c.isspace():
            i += 1
        elif source.startswith('//', i):
            end = source.find('\n', i + 2)
            i = len(source) if end < 0 else end + 1
        elif source.startswith('/*', i):
            end = source.find('*/', i + 2)
            if end < 0:
                raise ValueError
            i = end + 2
        elif c in "\"'`":
            quote, start = c, i + 1
            i += 1
            while i < len(source) and source[i] != quote:
                if quote == '`' and source.startswith('${', i):
                    raise ValueError  # no hidden imports in template expressions
                if source[i] == '\\':
                    i += 1
                i += 1
            if i >= len(source):
                raise ValueError
            tokens.append(('string', source[start:i]))
            i += 1
        elif c.isascii() and (c.isalpha() or c in '_$'):
            start = i
            i += 1
            while i < len(source) and source[i].isascii() and (source[i].isalnum() or source[i] in '_$'):
                i += 1
            tokens.append(('id', source[start:i]))
        else:
            if c in ('\\', '/') or not c.isascii():
                # Slash may start a regexp containing quotes; never mis-tokenize
                # it as strings and overlook a later import. Division also needs
                # a future full parser; reject it instead of guessing here.
                raise ValueError  # escaped/obfuscated identifiers outside strings
            tokens.append(('symbol', c))
            i += 1
    return tokens


def _js_imports(source):
    tokens = _js_tokens(source)
    imports = []
    for i, (kind, word) in enumerate(tokens):
        if kind != 'id':
            continue
        if word in {'eval', 'Function', 'createRequire', '_load'}:
            raise ValueError
        tail = tokens[i + 1:]
        if word == 'require' or (word == 'import' and tail and tail[0][1] == '('):
            if (len(tail) < 3 or tail[0] != ('symbol', '(')
                    or tail[1][0] != 'string' or tail[2] != ('symbol', ')')
                    or (i and tokens[i-1][1] in ('.', '?'))):
                raise ValueError
            imports.append(tail[1][1])
        elif word == 'import':
            if not tail or tail[0][1] == '.':
                raise ValueError
            if tail[0][0] == 'string':
                imports.append(tail[0][1])
            else:
                for j, token in enumerate(tail):
                    if token == ('symbol', ';'):
                        raise ValueError
                    if token == ('id', 'from'):
                        if j + 1 >= len(tail) or tail[j+1][0] != 'string':
                            raise ValueError
                        imports.append(tail[j+1][1])
                        break
                else:
                    raise ValueError
        elif word == 'from' and tail and tail[0][0] == 'string':
            imports.append(tail[0][1])  # covers export ... from as well
    return imports


def _python_imports(source):
    tree = ast.parse(source)
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append('.' * node.level + (node.module or ''))
        elif isinstance(node, ast.Name) and node.id in {'__import__', '__builtins__', 'eval', 'exec', 'compile', 'getattr'}:
            raise ValueError
        elif isinstance(node, ast.Attribute) and node.attr in {'__import__', 'import_module', 'exec_module', 'load_module'}:
            raise ValueError
    return imports


def validate_dependencies(proposal, profile, catalog):
    validate_edits(proposal)
    paths = {edit['path'] for edit in proposal['edits']}
    approved = {r['package'] for r in catalog['packages'] if r['profile'] == profile and r['use'] == 'product'}
    found = set()
    try:
        if profile not in ('javascript', 'python'):
            raise ValueError
        for edit in proposal['edits']:
            if profile == 'javascript':
                from .js_analysis import javascript_imports
                modules = javascript_imports(edit['content'], conservative=_js_imports)
            else:
                modules = _python_imports(edit['content'])
            for module in modules:
                if not module or '\\' in module or '\0' in module:
                    raise ValueError
                if profile == 'javascript':
                    if module.startswith('.'):
                        parts = list(PurePosixPath(edit['path']).parent.parts)
                        for part in module.split('/'):
                            if part == '..':
                                if len(parts) <= 1:
                                    raise ValueError
                                parts.pop()
                            elif part not in ('', '.'):
                                parts.append(part)
                        if '/'.join(parts) not in paths:
                            raise ValueError
                        continue
                    if module.removeprefix('node:') in NODE_STDLIB:
                        continue
                    package = '/'.join(module.split('/')[:2]) if module.startswith('@') else module.split('/')[0]
                    if not re.fullmatch(r'(?:@[a-z0-9_-]+/)?[a-zA-Z0-9_][a-zA-Z0-9_.-]*', package):
                        raise ValueError
                else:
                    if module.startswith('.'):
                        # Explicit local relative module only; no ambiguous wildcard package.
                        level = len(module) - len(module.lstrip('.'))
                        parent = PurePosixPath(edit['path']).parent
                        for _ in range(level - 1):
                            parent = parent.parent
                        target = (parent / (module[level:].replace('.', '/') + '.py')).as_posix()
                        if not target.startswith('src/') or target not in paths:
                            raise ValueError
                        continue
                    package = module.split('.')[0]
                    if package in PY_STDLIB:
                        continue
                    if 'src/' + module.replace('.', '/') + '.py' in paths:
                        continue
                if package not in approved:
                    raise Blocked('DEPENDENCY_NOT_APPROVED')
                found.add(package)
        return sorted(found)
    except Blocked:
        raise
    except (ValueError, SyntaxError, RecursionError):
        raise Blocked('DEPENDENCY_ANALYSIS_BLOCKED') from None
