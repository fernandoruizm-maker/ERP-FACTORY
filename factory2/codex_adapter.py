"""factory2 wrapper for the Codex ask protocol; never modifies upstream/global env.

The upstream adapter does not expose an environment injection point. We therefore
own the launch boundary here, reusing only its instruction and schema validator.
No live runner is wired: tests must supply an explicit local double.
"""
import json
import os
from pathlib import Path
import tempfile

from .core import Blocked
from upstream.factory.mvp.agents import SYSTEM
from upstream.factory.mvp.common import validate_schema


def allowlisted_environment(source, directory):
    allow = {'PATH', 'SYSTEMROOT', 'WINDIR', 'TEMP', 'TMP', 'PATHEXT'}
    env = {key: source[key] for key in source if key.upper() in allow}
    # Do not inherit credentials, user config, Python/Node injection or proxies.
    env.update(HOME=str(directory), USERPROFILE=str(directory),
               CODEX_HOME=str(directory / 'codex-home'), PYTHONDONTWRITEBYTECODE='1')
    return env


class SafeCodexAgent:
    def __init__(self, model=None, timeout=60, *, runner=None, executable=None):
        self.model, self.timeout = model, timeout
        self.runner, self.executable = runner, executable

    def ask(self, role, instruction, context, schema):
        if self.runner is None or self.executable is None:
            raise Blocked('CODEX_REAL_RUNNER_NOT_CONNECTED')
        with tempfile.TemporaryDirectory(prefix='factory2-agent-') as temporary:
            directory = Path(temporary)
            (directory / 'codex-home').mkdir()
            schema_file, output = directory / 'schema.json', directory / 'result.json'
            schema_file.write_text(json.dumps(schema), encoding='utf-8')
            command = [self.executable, 'exec', '--ignore-user-config', '--ephemeral',
                       '--skip-git-repo-check', '--sandbox', 'read-only', '--json',
                       '-C', str(directory), '--output-schema', str(schema_file),
                       '--output-last-message', str(output), '-c', 'web_search="disabled"',
                       '-c', 'project_doc_max_bytes=0', '-c', 'features.skip_host_skill_discovery=true']
            for feature in ('shell_tool', 'unified_exec', 'apps', 'browser_use', 'computer_use',
                            'hooks', 'remote_plugin', 'plugins', 'multi_agent', 'code_mode_host', 'skill_search'):
                command += ['--disable', feature]
            if self.model:
                command += ['--model', self.model]
            command.append('-')
            env = allowlisted_environment(os.environ, directory)
            prompt = SYSTEM + '\nROLE: ' + role + '\n' + instruction + '\nDATA:\n' + json.dumps(context)
            try:
                result = self.runner(command, input=prompt, text=True, encoding='utf-8',
                                     errors='replace', capture_output=True, timeout=self.timeout, env=env)
                if (result.returncode or not output.is_file() or output.is_symlink()
                        or output.stat().st_size > 200000 or len(result.stdout.encode('utf-8')) > 1000000):
                    raise Blocked('CODEX_OUTPUT_REJECTED')
                for line in result.stdout.splitlines():
                    event = json.loads(line)
                    if (not isinstance(event, dict) or event.get('type') == 'error'
                            or event.get('item', {}).get('type') in
                            {'command_execution', 'mcp_tool_call', 'file_change', 'web_search'}):
                        raise Blocked('CODEX_TOOL_OR_ERROR_REJECTED')
                value = json.loads(output.read_text(encoding='utf-8'))
                validate_schema(value, schema)
                return value
            except Exception:
                # Never expose provider output or process environment on errors.
                raise Blocked('CODEX_RESPONSE_INVALID_OR_UNCERTAIN') from None
