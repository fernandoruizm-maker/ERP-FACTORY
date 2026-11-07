"""Numbered trial entrypoint. Default is offline preparation, without Store or secrets."""
import argparse
import json
import math
import os
from pathlib import Path
import sqlite3
import sys
import time

from .core import Blocked, digest, canonical
from .codex_adapter import DockerCodexBuilder, request_bytes, token_cost
from .orchestrator import bottle_input, clean_head, PilotTrial
from .manual_review import metadata, CLEAR
from .pilot_preflight import inspect_start, reason_code
from .operations import Coordinator

ROOT = Path(__file__).resolve().parents[1]


def prepare(root=ROOT, *, attempt=1):
    if type(attempt) is not int or not 1 <= attempt <= 1000000:
        raise Blocked('PILOT_ATTEMPT_INVALID')
    cfg = json.loads((root / 'config.json').read_text(encoding='utf-8-sig'))
    if any(cfg.get(k) is not False for k in ('enabled', 'erp_access_enabled', 'publication_enabled')):
        raise Blocked('PILOT_MUST_REMAIN_ISOLATED')
    if cfg.get('pilot_model') != 'gpt-6.1-sol':
        raise Blocked('ATTEMPT_1_MODEL_MISMATCH')
    review = cfg['pilot_cost_review']
    expected = {'max_output_tokens': 32000, 'reasoning_effort': 'medium',
                'input_usd_per_million': '2.00', 'output_usd_per_million': '10.00',
                'max_call_usd': '1.00'}
    if any(review.get(k) != v for k, v in expected.items()):
        raise Blocked('ATTEMPT_1_COST_REVIEW_MISMATCH')
    for key, value in (('max_budget_usd_per_call', '1.00'),
                       ('max_spend_per_execution', '12.00'), ('max_spend_total', '13.00')):
        if cfg.get(key) != value:
            raise Blocked('ATTEMPT_1_LIMIT_MISMATCH')
    context = bottle_input()
    # A COPY is used solely to validate/serialize the hypothetical request.
    # No config mutation, transport, credential, Docker, Store or reservation.
    request = DockerCodexBuilder({**cfg, 'external_calls_enabled': True}).request(context)
    size = len(request_bytes(request))
    return {'status': 'PREPARED_NOT_EXECUTED', 'attempt': attempt,
            'execution_enabled': cfg.get('external_calls_enabled') is True,
            'attempt_consumed': False, 'publication_allowed': False,
            'config_digest': digest(cfg), 'context_digest': digest(context),
            'request_sha256': digest(request), 'request_bytes': size,
            'worst_case_cost_usd': token_cost(review, size, request['max_output_tokens']),
            'maximum_request_cost_usd': token_cost(review, review['max_request_bytes'], 32000),
            'request': request,
            'authorization_draft': {'attempt': attempt, 'source_sha': None,
                'config_digest': digest(cfg), 'context_digest': digest(context),
                'authorized_by': None, 'expires_at': None, 'factory_review_id': None},
            'ledger_relative_path': 'state/factory2.sqlite3',
            'ledger_present': (root / 'state/factory2.sqlite3').is_file()}


def preflight(authorization, expected_sha, root=ROOT, *, attempt=1):
    prepared = prepare(root, attempt=attempt)
    if not prepared['execution_enabled']:
        raise Blocked('PILOT_SWITCH_OFF')
    if (not isinstance(expected_sha, str) or len(expected_sha) != 40
            or clean_head(root) != expected_sha):
        raise Blocked('SOURCE_SHA_OR_CLEAN_CHECK_FAILED')
    wanted = set(prepared['authorization_draft'])
    if (not isinstance(authorization, dict) or set(authorization) != wanted
            or type(authorization['attempt']) is not int or authorization['attempt'] != attempt
            or authorization['source_sha'] != expected_sha
            or authorization['config_digest'] != prepared['config_digest']
            or authorization['context_digest'] != prepared['context_digest']
            or authorization['authorized_by'] != 'Fernando'
            or type(authorization['expires_at']) not in (int, float)
            or not math.isfinite(authorization['expires_at'])
            or authorization['expires_at'] <= time.time()):
        raise Blocked('PILOT_AUTHORIZATION_REQUIRED')
    ledger = root / 'state/factory2.sqlite3'
    for path in (ledger, *ledger.parents):
        if path.is_symlink() or (hasattr(path, 'is_junction') and path.is_junction()):
            raise Blocked('LEDGER_PATH_UNSAFE')
    if not ledger.is_file():
        raise Blocked('EXISTING_RECONCILED_LEDGER_REQUIRED')
    # Do not bootstrap an empty ledger to bypass accumulated spend. No writes.
    db = sqlite3.connect(ledger.resolve().as_uri() + '?mode=ro', uri=True)
    try:
        review_row = db.execute('SELECT document FROM manual_reviews WHERE id=?',
                               (authorization['factory_review_id'],)).fetchone()
        if review_row is None:
            raise Blocked('FACTORY_REVIEW_REQUIRED')
        review = metadata(review_row[0])
        if (review['review_id'] != authorization['factory_review_id']
                or review['source_sha'] != expected_sha or review['conclusion'] != CLEAR):
            raise Blocked('FACTORY_REVIEW_REQUIRED')
        if db.execute("SELECT 1 FROM paid_attempts WHERE status IN ('IN_FLIGHT','UNKNOWN','OVER_BUDGET')").fetchone():
            raise Blocked('BUDGET_RECONCILIATION_REQUIRED')
        total = db.execute('SELECT coalesce(sum(charged_units),0) FROM paid_attempts').fetchone()[0]
        if total + 1000000 > 13000000:
            raise Blocked('SPEND_LIMIT')
        if db.execute("SELECT 1 FROM paid_executions WHERE currency<>'USD'").fetchone():
            raise Blocked('BUDGET_CURRENCY_CHANGED')
        tables = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        trial_id = f'bottles-{attempt}'
        # Check every table for this trial's identity/references, including orphan
        # tasks, paid attempts and future tables. Quote schema identifiers; bind data.
        for table in sorted(tables):
            quoted = '"' + table.replace('"', '""') + '"'
            columns = {row[1] for row in db.execute(f'PRAGMA table_info({quoted})')}
            for column in sorted(columns & {'id', 'task', 'execution'}):
                if db.execute(f'SELECT 1 FROM {quoted} WHERE "{column}"=?', (trial_id,)).fetchone():
                    raise Blocked('PILOT_ALREADY_RECORDED_NO_RETRY')
        blocked_trials = set()
        if 'pilot_trials' in tables:
            for trial_id, data in db.execute('SELECT id,data FROM pilot_trials'):
                if json.loads(data)['status'] != 'BLOCKED':
                    raise Blocked('PILOT_PREVIOUS_ATTEMPT_UNFINISHED')
                blocked_trials.add(trial_id)
        if any(f'bottles-{previous}' not in blocked_trials for previous in range(1, attempt)):
            raise Blocked('PILOT_PREVIOUS_ATTEMPT_UNFINISHED')
        # Same locked, read-only checks as PilotTrial._start. No Store construction,
        # table creation, reservation, credential read or attempt consumption here.
        coordinator = Coordinator(ledger.parent)
        def read_review(review_id):
            row = db.execute('SELECT document FROM manual_reviews WHERE id=?', (review_id,)).fetchone()
            if row is None:
                raise Blocked('FACTORY_REVIEW_REQUIRED')
            return metadata(row[0])
        with coordinator.worker():
            coordinator.require_worker()
            inspect_start(json.loads((root / 'config.json').read_text(encoding='utf-8-sig')),
                          authorization, source_reader=lambda: clean_head(root),
                          review_reader=read_review, work_root=root / 'work/ensayo-real')
    finally:
        db.close()
    return prepared


def execute(authorization, expected_sha, root=ROOT, *, attempt=1, key_reader=None):
    preflight(authorization, expected_sha, root, attempt=attempt)
    if key_reader is None:
        key_reader = lambda: sys.stdin.readline(4097).rstrip('\r\n')
    # Only the explicitly requested run path reads a key, after all preflight gates.
    key = key_reader()
    if not isinstance(key, str) or not 1 <= len(key) <= 4096 or any(c.isspace() for c in key):
        raise Blocked('PRIVATE_CREDENTIAL_INPUT_INVALID')
    try:
        os.environ['OPENAI_API_KEY'] = key
        from .state import Store
        store = Store(root / 'state/factory2.sqlite3', config_path=root / 'config.json',
                      reviews_directory=root / 'docs/revisiones')
        result = PilotTrial(store, root / 'work/ensayo-real', attempt=attempt).start(authorization)
        return {k: result[k] for k in ('status', 'attempt', 'reason_code', 'usage',
                                       'calculated_cost_usd', 'publication_allowed') if k in result}
    finally:
        os.environ.pop('OPENAI_API_KEY', None)
        key = None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('prepare', 'check', 'run'), default='prepare', nargs='?')
    parser.add_argument('--authorization')
    parser.add_argument('--expected-sha')
    parser.add_argument('--attempt', type=int, default=1)
    args = parser.parse_args()
    try:
        if args.mode == 'prepare':
            result = prepare(attempt=args.attempt)
        else:
            path = Path(args.authorization or '')
            if not path.is_file() or path.stat().st_size > 10000:
                raise Blocked('AUTHORIZATION_FILE_REQUIRED')
            authorization = json.loads(path.read_text(encoding='utf-8-sig'))
            if args.mode == 'check':
                preflight(authorization, args.expected_sha, attempt=args.attempt)
                result = {'status': 'PREFLIGHT_OK_NOT_EXECUTED'}
            else:
                result = execute(authorization, args.expected_sha, attempt=args.attempt)
        print(canonical(result))
        return 2 if result.get('status') == 'BLOCKED' else 0
    except Exception as exc:
        # No exception text, authorization contents, provider output or environment.
        print(canonical({'status': 'BLOCKED', 'reason_code': reason_code(exc)}))
        return 2


if __name__ == '__main__':
    sys.exit(main())
