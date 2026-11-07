"""Durable reservations for future paid attempts; no provider or network client.

Values use exact millionths of an explicitly selected currency. Validated completed
usage settles the reservation at calculated cost, NOT verified billing. Unknown
outcomes never release money. Opening a ledger never resettles existing records.
"""
from contextlib import contextmanager
from decimal import Decimal, InvalidOperation
import re
import sqlite3
import time

from .core import Blocked


def units(value, *, zero=False):
    # No floating point, inferred currency, implicit cap or scientific notation.
    if not isinstance(value, str) or not re.fullmatch(r'[0-9]+(?:\.[0-9]{1,6})?', value):
        raise Blocked('BUDGET_AMOUNT_REQUIRED')
    try:
        amount = Decimal(value) * 1_000_000
        if amount > 9_000_000_000_000_000 or amount < (0 if zero else 1):
            raise Blocked('BUDGET_AMOUNT_INVALID')
        return int(amount)
    except (InvalidOperation, OverflowError):
        raise Blocked('BUDGET_AMOUNT_INVALID') from None


def limits(config):
    currency = config.get('budget_currency')
    calls = config.get('max_calls_per_execution')
    if not isinstance(currency, str) or not re.fullmatch('[A-Z]{3}', currency):
        raise Blocked('BUDGET_CURRENCY_PENDING')
    if type(calls) is not int or calls < 1:
        raise Blocked('CALL_LIMIT_PENDING')
    units(config.get('max_budget_usd_per_call'))
    return currency, calls, units(config.get('max_spend_per_execution')), units(config.get('max_spend_total'))


def identifier(value):
    if not isinstance(value, str) or not re.fullmatch('[A-Za-z0-9_-]{1,100}', value):
        raise Blocked('BUDGET_IDENTIFIER_INVALID')
    return value


class BudgetLedger:
    def __init__(self, path):
        self.path = str(path)
        with self.connect() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS paid_executions(
                  id TEXT PRIMARY KEY, source_sha TEXT NOT NULL, currency TEXT NOT NULL,
                  max_calls INTEGER NOT NULL, max_units INTEGER NOT NULL,
                  total_limit_at_creation INTEGER NOT NULL, created REAL NOT NULL);
                CREATE TABLE IF NOT EXISTS paid_attempts(
                  id TEXT PRIMARY KEY, execution TEXT NOT NULL, provider TEXT NOT NULL,
                  payload TEXT NOT NULL, reserved_units INTEGER NOT NULL,
                  charged_units INTEGER NOT NULL, actual_units INTEGER,
                  status TEXT NOT NULL, created REAL NOT NULL);
            ''')

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=5)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    def begin(self, execution, source_sha, config):
        currency, calls, per_run, total = limits(config)
        identifier(execution)
        if not isinstance(source_sha, str) or not re.fullmatch('[0-9a-f]{40}', source_sha) or source_sha == '0'*40:
            raise Blocked('BUDGET_SOURCE_INVALID')
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            if db.execute('SELECT 1 FROM paid_executions WHERE currency<>?', (currency,)).fetchone():
                raise Blocked('BUDGET_CURRENCY_CHANGED')
            try:
                db.execute('INSERT INTO paid_executions VALUES(?,?,?,?,?,?,?)',
                           (execution, source_sha, currency, calls, per_run, total, time.time()))
            except sqlite3.IntegrityError:
                raise Blocked('EXECUTION_ALREADY_RECORDED') from None

    def reserve_in(self, db, call_id, execution, provider, payload, source_sha, max_cost, config):
        """Caller owns BEGIN IMMEDIATE; usable by a future multipart coordinator."""
        currency, calls, per_run, total = limits(config)
        identifier(call_id)
        identifier(execution)
        identifier(provider)
        if not isinstance(payload, str) or not payload:
            raise Blocked('BUDGET_PAYLOAD_REQUIRED')
        reserve = units(max_cost)
        if reserve > units(config.get('max_budget_usd_per_call')):
            raise Blocked('PER_CALL_SPEND_LIMIT')
        row = db.execute('SELECT * FROM paid_executions WHERE id=?', (execution,)).fetchone()
        if row is None or row['source_sha'] != source_sha or row['currency'] != currency:
            raise Blocked('EXECUTION_VERSION_OR_CURRENCY_MISMATCH')
        if db.execute("SELECT 1 FROM paid_attempts WHERE status='OVER_BUDGET'").fetchone():
            raise Blocked('BUDGET_RECONCILIATION_REQUIRED')
        if db.execute('SELECT 1 FROM paid_attempts WHERE id=?', (call_id,)).fetchone():
            raise Blocked('PAID_ATTEMPT_ALREADY_RECORDED_NO_RETRY')
        count, spent = db.execute('SELECT count(*),coalesce(sum(charged_units),0) FROM paid_attempts WHERE execution=?',
                                 (execution,)).fetchone()
        overall = db.execute('SELECT coalesce(sum(charged_units),0) FROM paid_attempts').fetchone()[0]
        if count >= min(calls, row['max_calls']):
            raise Blocked('EXECUTION_CALL_LIMIT')
        if spent + reserve > min(per_run, row['max_units']) or overall + reserve > total:
            raise Blocked('SPEND_LIMIT')
        db.execute('INSERT INTO paid_attempts VALUES(?,?,?,?,?,?,NULL,?,?)',
                   (call_id, execution, provider, payload, reserve, reserve, 'IN_FLIGHT', time.time()))

    def reserve(self, *args, **kwargs):
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            self.reserve_in(db, *args, **kwargs)

    def finish_in(self, db, call_id, status, actual_cost=None, *, usage_validated=False):
        if status not in ('COMPLETED', 'UNKNOWN', 'REJECTED'):
            raise Blocked('PAID_ATTEMPT_STATUS_INVALID')
        row = db.execute('SELECT * FROM paid_attempts WHERE id=?', (call_id,)).fetchone()
        if row is None or row['status'] != 'IN_FLIGHT':
            raise Blocked('PAID_ATTEMPT_NOT_IN_FLIGHT')
        actual = None if actual_cost is None else units(actual_cost, zero=True)
        reserve = row['reserved_units']
        recorded_status = status
        charged = reserve
        if actual is not None and actual > reserve:
            # Do not accept an out-of-bound value as valid actual spend or silently
            # clamp it. Keep the reservation and freeze further calls for review.
            recorded_status = 'OVER_BUDGET'
            actual = None
        elif status == 'COMPLETED' and usage_validated is True and actual is not None:
            charged = actual
        db.execute('UPDATE paid_attempts SET status=?,actual_units=?,charged_units=? WHERE id=?',
                   (recorded_status, actual, charged, call_id))
        return recorded_status

    def finish(self, call_id, status, actual_cost=None, *, usage_validated=False):
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            return self.finish_in(db, call_id, status, actual_cost, usage_validated=usage_validated)

    def summary(self):
        with self.connect() as db:
            currency = db.execute('SELECT currency FROM paid_executions LIMIT 1').fetchone()
            row = db.execute('SELECT count(*),coalesce(sum(charged_units),0),'
                             "sum(CASE WHEN status='UNKNOWN' THEN 1 ELSE 0 END) FROM paid_attempts").fetchone()
        return {'attempts': row[0], 'conservative_charge_units': row[1], 'unknown': row[2] or 0,
                'unit_scale': 1_000_000, 'currency': currency[0] if currency else None, 'billing_verified': False}
