"""Optional offline Acorn adapter: no pulls, installation or candidate execution."""
import hashlib
import json
from pathlib import Path
import re
import tempfile
import uuid

from .core import Blocked
from .encargos import _json, _plain_path
from .runner import bounded_process

POLICY = Path(__file__).resolve().parents[1] / 'tools/acorn/policy.json'


def javascript_imports(source, *, conservative, policy_path=POLICY):
    try:
        _plain_path(Path(policy_path).absolute())
        policy = _json(Path(policy_path))
        if (not isinstance(policy, dict) or set(policy) != {'enabled', 'image', 'parser_version'}
                or type(policy['enabled']) is not bool or policy['parser_version'] != '8.19.0'):
            raise ValueError
        if not policy['enabled']:
            if policy['image'] is not None:
                raise ValueError
            return conservative(source)
        if (not isinstance(policy['image'], str) or not re.fullmatch(
                r'(?:[a-zA-Z0-9][a-zA-Z0-9./:_-]*@)?sha256:[a-f0-9]{64}', policy['image'])
                or not isinstance(source, str) or len(source.encode('utf-8')) > 100000):
            raise ValueError
        name = 'rdc2-acorn-' + uuid.uuid4().hex
        with tempfile.TemporaryDirectory(prefix='rdc2-acorn-') as folder:
            path = Path(folder).resolve()
            _plain_path(path)
            if ',' in str(path):
                raise ValueError
            (path/'input.json').write_text(json.dumps({'source': source}), encoding='utf-8')
            command = ['docker', 'run', '--rm', '--pull=never', '--name', name,
                       '--network=none', '--read-only', '--user=65534:65534',
                       '--cap-drop=ALL', '--security-opt=no-new-privileges',
                       '--pids-limit=32', '--memory=256m', '--cpus=1',
                       '--mount', f'type=bind,source={path},target=/input,readonly',
                       policy['image'], '/input/input.json']
            try:
                code, output = bounded_process(command, timeout=15, output_limit=100000)
            finally:
                try:
                    bounded_process(['docker', 'rm', '-f', name], timeout=5)
                except (Blocked, OSError):
                    pass
        def pairs(items):
            result = {}
            for key, value in items:
                if key in result:
                    raise ValueError
                result[key] = value
            return result
        result = json.loads(output, object_pairs_hook=pairs)
        if (code != 0 or not isinstance(result, dict)
                or set(result) != {'parser_version', 'source_sha256', 'imports'}
                or result['parser_version'] != policy['parser_version']
                or result['source_sha256'] != hashlib.sha256(source.encode('utf-8')).hexdigest()
                or not isinstance(result['imports'], list) or len(result['imports']) > 10000
                or not all(isinstance(x, str) and 0 < len(x) <= 1000 for x in result['imports'])):
            raise ValueError
        return result['imports']
    except (Blocked, ValueError, TypeError, OSError, RecursionError):
        raise Blocked('DEPENDENCY_ANALYSIS_BLOCKED') from None
