"""Trusted step boundaries; only init can use the existing anonymous downloader.

No credential/provider client. A future, explicitly selected cumulative adapter
must supply authorization.json; this module does not select/provision that adapter.
"""
import json
import os
from pathlib import Path
import uuid

from .contract import Blocked, canonical
from .execution_budget import execution_limits, money
from .material import archive_material, download_archive
from .packets import archive_packets
from .multipart import start, select, collect_path, _load
from .runtime import blocked_artifacts


def authorization(policy, work, commit):
    # Check caps before material, subprocesses, or an authorization adapter.
    money(policy.get('max_spend_per_execution'))
    money(policy.get('max_budget_usd_per_call'))
    if policy.get('cumulative_strategy') is None:
        raise Blocked('CUMULATIVE_STRATEGY_PENDING')
    # This name specifies only the common local contract, NOT which option supplies it.
    if policy['cumulative_strategy'] != 'reviewed-local-grant-v1':
        raise Blocked('CUMULATIVE_ADAPTER_NOT_REVIEWED')
    path = Path(work) / 'authorization.json'
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 4096:
        raise Blocked('LOCAL_ALLOWANCE_REQUIRED')
    grant = json.loads(path.read_text(encoding='utf-8'))
    execution_limits(policy, grant, commit)
    return grant


def outputs(values):
    target = os.environ.get('GITHUB_OUTPUT')
    if not target:
        raise Blocked('STEP_OUTPUT_REQUIRED')
    # Raw provider data never enters outputs. User code is an input only.
    with open(target, 'a', encoding='utf-8') as stream:
        for key, value in values.items():
            if type(value) is bool:
                value = 'true' if value else 'false'
            value = str(value)
            delimiter = 'END_' + uuid.uuid4().hex
            while delimiter in value:
                delimiter = 'END_' + uuid.uuid4().hex
            stream.write(key+'<<'+delimiter+'\n'+value+'\n'+delimiter+'\n')


def dispatch(command, slot, policy, provenance, work):
    work = Path(work)
    grant = authorization(policy, work, provenance['source_sha'])
    if command == 'mp-preflight':
        return 0
    if command == 'mp-init':
        raw = download_archive(provenance['source_sha'])
        material = archive_material(raw, provenance['source_sha'])
        manifest, parts = archive_packets(material)
        receipt = start(work, manifest, parts, policy, grant, provenance)
        outputs(receipt)
        return 0
    receipt = {'state_file': os.environ.get('STATE_FILE', ''), 'state_sha256': os.environ.get('STATE_SHA256', '')}
    if type(slot) is not int or not 1 <= slot <= 11:
        raise Blocked('SLOT_REQUIRED')
    try:
        state = _load(work, receipt)
    except (Blocked, OSError, ValueError, TypeError, KeyError):
        label = 'slot-'+str(slot)+'-stop'
        blocked_artifacts(work/'checkpoints'/label, 'MATERIAL_VERIFICATION_FAILED')
        outputs({'ready': False, 'continue': False, 'checkpoint': label})
        return 0
    if state['provenance'] != provenance or state['limits'] != execution_limits(policy, grant, provenance['source_sha']):
        raise Blocked('STEP_PROVENANCE_OR_CAP_CHANGED')
    # The pinned Action's historical output path. Real behavior remains unverified.
    runner = Path(os.environ['RUNNER_TEMP']).resolve()
    if work.resolve() != runner / 'private-review':
        raise Blocked('WORK_DIRECTORY_INVALID')
    execution = runner / 'claude-execution-output.json'
    if command == 'mp-select':
        # Never collect stale output from a previous call. Only this exact path.
        if execution.is_symlink() or execution.is_dir():
            raise Blocked('EXECUTION_FILE_INVALID')
        if execution.exists():
            execution.unlink()
        result = select(work, receipt, slot)
        values = {**result['receipt'], 'ready': result['ready'], 'checkpoint': result['checkpoint']}
        if result['ready']:
            folder = work / 'input'
            folder.mkdir(exist_ok=True)
            (folder / 'system.txt').write_text(result['request']['system'], encoding='utf-8')
            values.update(user_prompt=result['request']['user'], max_budget_usd=result['max_budget_usd'])
        outputs(values)
        return 0
    if command == 'mp-collect':
        result = collect_path(work, receipt, slot, execution, os.environ.get('CLAUDE_CONCLUSION'))
        outputs({**result['receipt'], 'checkpoint': result['checkpoint'], 'continue': result['continue']})
        return 0  # A safe blocked checkpoint is a successful collection, never approval.
    raise Blocked('UNKNOWN_MULTIPART_COMMAND')
