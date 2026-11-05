import argparse
import json
import os
from pathlib import Path
import subprocess
import uuid

from .contract import Blocked
from .material import download_archive
from .runtime import collect_file, preflight, prepare


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=('preflight', 'prepare', 'collect'))
    args = parser.parse_args()
    trusted = Path(__file__).resolve().parent.parent
    try:
        policy = json.loads((trusted / 'policy.json').read_text(encoding='utf-8'))
        # Block before subprocess or network in the delivered, disabled draft.
        if policy.get('execution_enabled') is not True:
            raise Blocked('EXECUTION_DISABLED')
        git_env = {k: v for k, v in os.environ.items() if k.upper() in ('PATH', 'SYSTEMROOT', 'TEMP', 'TMP')}
        git_env.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_COUNT='0',
                       GIT_TERMINAL_PROMPT='0')
        checkout_sha = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=trusted,
            env=git_env, check=True, capture_output=True, text=True).stdout.strip()
        provenance = preflight(policy, os.environ, checkout_sha)
        if args.command == 'preflight':
            print('PRIVATE_REVIEW_PREFLIGHT_OK')
            return 0
        work = Path(os.environ['REVIEW_WORKDIR'])
        if args.command == 'prepare':
            archive = download_archive(provenance['source_sha'])
            receipt, user = prepare(work, archive, provenance['source_sha'])
            delimiter = 'REVIEW_' + uuid.uuid4().hex
            while delimiter in user:
                delimiter = 'REVIEW_' + uuid.uuid4().hex
            with open(os.environ['GITHUB_OUTPUT'], 'a', encoding='utf-8') as output:
                output.write('material_sha256=' + receipt + '\n')
                output.write('user_prompt<<' + delimiter + '\n' + user + '\n' + delimiter + '\n')
            print('PUBLIC_SOURCE_PREPARED_NOT_EXECUTED')
            return 0
        folder = os.environ.get('RUNNER_TEMP')
        path = Path(folder) / 'claude-execution-output.json' if folder else None
        report = collect_file(work, os.environ.get('MATERIAL_SHA256', ''), provenance['source_sha'], path,
                              os.environ.get('CLAUDE_CONCLUSION'), provenance)
        print('PRIVATE_REVIEW_' + report['status'])
        return 0 if report['status'] == 'NEEDS_HUMAN_REVIEW' else 1
    except (Blocked, OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError):
        # No source, provider prose, exceptions, or credentials enter logs.
        print('PRIVATE_REVIEW_BLOCKED')
        return 2
