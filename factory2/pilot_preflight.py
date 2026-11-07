"""Shared offline start checks; no Store construction, credentials or reservations."""
import math
from pathlib import Path
import sqlite3
import subprocess
import time

from .core import Blocked, digest, discover, contained
from .budget import limits, units
from .manual_review import CLEAR, hex_value
from .codex_adapter import DockerCodexBuilder, PYTHON_IMAGE, NODE_IMAGE
from .runner import bounded_process
from .encargos import ROOT as ENCARGOS_ROOT, load_encargo, attempt_ids


REASON_CODES = frozenset('''
PILOT_SWITCH_OFF PILOT_MUST_REMAIN_ISOLATED PILOT_USD_REQUIRED
PILOT_AUTHORIZED_CAP_EXCEEDED PILOT_AUTHORIZATION_REQUIRED PILOT_ATTEMPT_INVALID
PILOT_FACTORY_SHA_CHANGED PILOT_FACTORY_REVIEW_REQUIRED PILOT_WORK_ROOT_UNSAFE
PILOT_CANDIDATE_ALREADY_EXISTS PILOT_ALREADY_RECORDED_NO_RETRY
PILOT_PREVIOUS_ATTEMPT_UNFINISHED PILOT_SIMULATION_DOUBLES_REQUIRED
SOURCE_OR_CANDIDATE_NOT_CLEAN SOURCE_SHA_OR_CLEAN_CHECK_FAILED LOCAL_SNAPSHOT_GIT_FAILED
LOCAL_DOCKER_ENDPOINT_REQUIRED PILOT_PINNED_IMAGES_REQUIRED
PILOT_DOCKER_QUERY_FAILED PILOT_DOCKER_QUERY_TIMEOUT
MANUAL_REVIEW_ID_REQUIRED MANUAL_REVIEW_NOT_FOUND MANUAL_REVIEW_CHANGED
MANUAL_REVIEW_FORMAT_INVALID MANUAL_REVIEW_POSSIBLE_SECRET MANUAL_REVIEW_CONTRADICTORY_CONCLUSION
FACTORY_REVIEW_REQUIRED AUTHORIZATION_FILE_REQUIRED PRIVATE_CREDENTIAL_INPUT_INVALID
ATTEMPT_1_MODEL_MISMATCH ATTEMPT_1_COST_REVIEW_MISMATCH ATTEMPT_1_LIMIT_MISMATCH
ATTEMPT_1_AUTHORIZATION_REQUIRED LEDGER_PATH_UNSAFE EXISTING_RECONCILED_LEDGER_REQUIRED
WORKER_LOCK_UNSAFE WORKER_ALREADY_ACTIVE WORKER_LOCK_REQUIRED
ACTIVE_FACTORY_NOT_CONFIGURED COORDINATION_PATH_UNSAFE ACTIVE_FACTORY_INVALID
ORIGINAL_RETIREMENT_INVALID ORIGINAL_RETIREMENT_INCOMPLETE ORIGINAL_RETIREMENT_PATH_UNSAFE
ORIGINAL_RETIREMENT_MISSING ORIGINAL_RESTORED ORIGINAL_RETIREMENT_CONTRADICTORY
BUDGET_AMOUNT_REQUIRED BUDGET_AMOUNT_INVALID BUDGET_CURRENCY_PENDING CALL_LIMIT_PENDING
BUDGET_RECONCILIATION_REQUIRED BUDGET_CURRENCY_CHANGED SPEND_LIMIT PER_CALL_SPEND_LIMIT
EXECUTION_CALL_LIMIT OPERATION_CONFIG_INVALID PILOT_MODEL_AND_COST_REVIEW_REQUIRED
CODEX_INPUT_REJECTED CODEX_WORST_CASE_EXCEEDS_CAP
PILOT_PREFLIGHT_LEDGER_ERROR PILOT_PREFLIGHT_PROCESS_TIMEOUT
PILOT_PREFLIGHT_IO_ERROR PILOT_PREFLIGHT_UNEXPECTED_NO_RETRY
ENCARGO_NAME_INVALID ENCARGO_PATH_UNSAFE ENCARGO_JSON_INVALID ENCARGO_MISSING
ENCARGO_SCOPE_INVALID ENCARGO_REQUIREMENTS_INVALID ENCARGO_OUTPUT_INVALID
ENCARGO_TESTS_INVALID ENCARGO_CONTENT_REJECTED PILOT_LEGACY_ID_CONFLICT
'''.split())


def reason_code(exc):
    if isinstance(exc, Blocked) and str(exc) in REASON_CODES:
        return str(exc)
    if isinstance(exc, sqlite3.Error):
        return 'PILOT_PREFLIGHT_LEDGER_ERROR'
    if isinstance(exc, subprocess.TimeoutExpired):
        return 'PILOT_PREFLIGHT_PROCESS_TIMEOUT'
    if isinstance(exc, OSError):
        return 'PILOT_PREFLIGHT_IO_ERROR'
    return 'PILOT_PREFLIGHT_UNEXPECTED_NO_RETRY'


def validate_config(cfg):
    if cfg.get('external_calls_enabled') is not True:
        raise Blocked('PILOT_SWITCH_OFF')
    if any(cfg.get(k) is not False for k in ('enabled', 'erp_access_enabled', 'publication_enabled')):
        raise Blocked('PILOT_MUST_REMAIN_ISOLATED')
    limits(cfg)
    if cfg['budget_currency'] != 'USD':
        raise Blocked('PILOT_USD_REQUIRED')
    for key, ceiling in (('max_budget_usd_per_call', '1.00'),
                         ('max_spend_per_execution', '12.00'), ('max_spend_total', '13.00')):
        if units(cfg[key]) > units(ceiling):
            raise Blocked('PILOT_AUTHORIZED_CAP_EXCEEDED')
    return cfg


def docker_query(command):
    try:
        return bounded_process(command)
    except subprocess.TimeoutExpired:
        raise Blocked('PILOT_DOCKER_QUERY_TIMEOUT') from None
    except (OSError, Blocked):
        raise Blocked('PILOT_DOCKER_QUERY_FAILED') from None


def inspect_start(cfg, authorization, *, source_reader, review_reader, work_root, simulation=False,
                  encargo='botellas', encargos_root=ENCARGOS_ROOT):
    """Called under the worker lock by both check and start. Reads only."""
    cfg = validate_config(cfg)
    context = load_encargo(encargo, encargos_root)
    discover(context['brief'])
    expected = {'source_sha', 'context_digest', 'config_digest', 'authorized_by',
                'expires_at', 'factory_review_id', 'attempt', 'encargo'}
    if (not isinstance(authorization, dict) or set(authorization) != expected
            or type(authorization['attempt']) is not int or not 1 <= authorization['attempt'] <= 1000000
            or authorization['encargo'] != encargo
            or authorization['authorized_by'] != 'Fernando'
            or authorization['context_digest'] != digest(context)
            or authorization['config_digest'] != digest(cfg)
            or not hex_value(authorization['source_sha'], 40)
            or type(authorization['expires_at']) not in (int, float)
            or not math.isfinite(authorization['expires_at']) or authorization['expires_at'] <= time.time()):
        raise Blocked('PILOT_AUTHORIZATION_REQUIRED')
    source = source_reader()
    if source != authorization['source_sha']:
        raise Blocked('PILOT_FACTORY_SHA_CHANGED')
    reviewed = review_reader(authorization['factory_review_id'])
    if (reviewed['review_id'] != authorization['factory_review_id']
            or reviewed['source_sha'] != source or reviewed['conclusion'] != CLEAR):
        raise Blocked('PILOT_FACTORY_REVIEW_REQUIRED')
    request = DockerCodexBuilder(cfg).request(context)
    if not simulation:
        code, endpoint = docker_query(['docker', 'context', 'inspect', '--format', '{{.Endpoints.docker.Host}}'])
        if code or endpoint.strip() not in ('npipe:////./pipe/docker_engine', 'npipe:////./pipe/dockerDesktopLinuxEngine'):
            raise Blocked('LOCAL_DOCKER_ENDPOINT_REQUIRED')
        for image in (PYTHON_IMAGE, NODE_IMAGE):
            code, info = docker_query(['docker', 'image', 'inspect', image, '--format', '{{.Os}}/{{.Architecture}}'])
            if code or info.strip() != 'linux/amd64':
                raise Blocked('PILOT_PINNED_IMAGES_REQUIRED')
    work_root = Path(work_root).absolute()
    for path in (work_root, *work_root.parents):
        if path.is_symlink() or (hasattr(path, 'is_junction') and path.is_junction()):
            raise Blocked('PILOT_WORK_ROOT_UNSAFE')
    identifiers = attempt_ids(encargo, authorization['attempt'])
    for ident in identifiers:
        if contained(work_root, ident).exists():
            raise Blocked('PILOT_CANDIDATE_ALREADY_EXISTS')
    candidate = contained(work_root, identifiers[0])
    return cfg, context, source, request, candidate
