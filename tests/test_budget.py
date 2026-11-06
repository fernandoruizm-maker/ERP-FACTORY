from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import sqlite3
import tempfile
import time
import unittest
from unittest.mock import patch

from factory2.budget import BudgetLedger, units
from factory2.core import Blocked, canonical, digest
from factory2.providers import ClaudeReviewer, Permit
from tests.operation_fixtures import store_fixture

SOURCE = 'a'*40


class BudgetTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'budget.sqlite3'
        self.ledger = BudgetLedger(self.path)
        self.config = {'budget_currency': 'TST', 'max_calls_per_execution': 11, 'max_budget_usd_per_call': '1',
                       'max_spend_per_execution': '2', 'max_spend_total': '3'}

    def reserve(self, call, run='e1', amount='1', config=None, source=SOURCE):
        self.ledger.reserve(call, run, 'ficticio', digest(call), source, amount, config or self.config)

    def test_missing_caps_currency_or_calls_block_without_attempts(self):
        for key in self.config:
            with self.subTest(key=key), self.assertRaises(Blocked):
                self.ledger.begin('e1', SOURCE, {**self.config, key: None})
        self.assertEqual(self.ledger.summary()['attempts'], 0)

    def test_money_uses_exact_units_rejecting_float_nan_negative_and_exponents(self):
        self.assertEqual(units('0.000001'), 1)
        self.assertEqual(units('1.234567'), 1234567)
        for value in (None, 1.0, True, '-1', 'NaN', '1e3', '0.0000001', '0'):
            with self.subTest(value=value), self.assertRaises(Blocked):
                units(value)

    def test_per_call_cap_blocks_before_reservation(self):
        self.ledger.begin('e1', SOURCE, self.config)
        with self.assertRaisesRegex(Blocked, 'PER_CALL_SPEND_LIMIT'):
            self.reserve('c1', amount='1.000001')
        self.assertEqual(self.ledger.summary()['attempts'], 0)

    def test_eleven_calls_then_block_with_sufficient_fictitious_money(self):
        config = {**self.config, 'max_spend_per_execution': '20', 'max_spend_total': '20'}
        self.ledger.begin('e1', SOURCE, config)
        for i in range(11):
            self.reserve('c'+str(i), config=config)
        with self.assertRaisesRegex(Blocked, 'CALL_LIMIT'):
            self.reserve('c12', config=config)
        self.assertEqual(self.ledger.summary()['attempts'], 11)

    def test_execution_limit_and_total_limit_apply_across_runs(self):
        self.ledger.begin('e1', SOURCE, self.config)
        self.reserve('c1'); self.reserve('c2')
        with self.assertRaisesRegex(Blocked, 'SPEND_LIMIT'):
            self.reserve('c3')
        self.ledger.begin('e2', SOURCE, self.config)
        self.reserve('c4', run='e2')
        with self.assertRaisesRegex(Blocked, 'SPEND_LIMIT'):
            self.reserve('c5', run='e2')
        self.assertEqual(self.ledger.summary()['conservative_charge_units'], 3000000)

    def test_unknown_and_rejected_keep_full_reservation_without_retry(self):
        self.ledger.begin('e1', SOURCE, self.config)
        for call, status in (('c1', 'UNKNOWN'), ('c2', 'REJECTED')):
            self.reserve(call)
            self.ledger.finish(call, status)
            with self.assertRaises(Blocked):
                self.reserve(call)
        self.assertEqual(self.ledger.summary()['conservative_charge_units'], 2000000)
        self.assertEqual(self.ledger.summary()['unknown'], 1)

    def test_reopening_database_keeps_accumulated_charges(self):
        self.ledger.begin('e1', SOURCE, self.config)
        self.reserve('c1')
        self.ledger = BudgetLedger(self.path)
        self.assertEqual(self.ledger.summary()['attempts'], 1)
        with self.assertRaises(Blocked):
            self.reserve('c1')

    def test_actual_below_reserve_does_not_release_and_is_not_verified_billing(self):
        self.ledger.begin('e1', SOURCE, self.config)
        self.reserve('c1')
        self.ledger.finish('c1', 'COMPLETED', actual_cost='0.25')
        summary = self.ledger.summary()
        self.assertEqual(summary['conservative_charge_units'], 1000000)
        self.assertFalse(summary['billing_verified'])
        self.assertEqual(summary['currency'], 'TST')

    def test_reported_overrun_freezes_future_attempts_for_reconciliation(self):
        self.ledger.begin('e1', SOURCE, self.config)
        self.reserve('c1')
        self.assertEqual(self.ledger.finish('c1', 'COMPLETED', actual_cost='1.5'), 'OVER_BUDGET')
        with self.assertRaisesRegex(Blocked, 'RECONCILIATION'):
            self.reserve('c2', amount='0.1')
        self.assertEqual(self.ledger.summary()['conservative_charge_units'], 1500000)

    def test_execution_source_and_currency_cannot_change(self):
        self.ledger.begin('e1', SOURCE, self.config)
        with self.assertRaises(Blocked):
            self.reserve('c1', source='b'*40)
        with self.assertRaises(Blocked):
            self.ledger.begin('e2', SOURCE, {**self.config, 'budget_currency': 'ZZZ'})

    def test_duplicate_execution_and_double_completion_are_rejected(self):
        self.ledger.begin('e1', SOURCE, self.config)
        with self.assertRaises(Blocked):
            self.ledger.begin('e1', SOURCE, self.config)
        self.reserve('c1'); self.ledger.finish('c1', 'COMPLETED')
        with self.assertRaises(Blocked):
            self.ledger.finish('c1', 'COMPLETED')

    def test_current_or_original_stricter_limit_wins(self):
        self.ledger.begin('e1', SOURCE, self.config)
        with self.assertRaises(Blocked):
            self.reserve('c1', amount='3', config={**self.config, 'max_spend_per_execution': '5'})
        with self.assertRaises(Blocked):
            self.reserve('c2', amount='1', config={**self.config, 'max_spend_per_execution': '0.5'})

    def test_atomic_reservations_cannot_overspend_under_concurrency(self):
        self.ledger.begin('e1', SOURCE, self.config)
        def attempt(i):
            try:
                self.reserve('c'+str(i))
                return True
            except Blocked:
                return False
        with ThreadPoolExecutor(max_workers=8) as pool:
            outcomes = list(pool.map(attempt, range(8)))
        self.assertEqual(sum(outcomes), 2)
        self.assertEqual(self.ledger.summary()['conservative_charge_units'], 2000000)


class PaidProviderTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.store, _ = store_fixture(self.temp.name)
        self.store.put_task('T', {'synthetic': True})
        self.store.budget.begin('run1', SOURCE, self.store.config())
        self.cfg = {'external_calls_enabled': True, 'claude_model': 'FICTICIO', 'max_output_tokens': 100}
        self.artifact = {'synthetic': True}
        self.payload = {'artifact': self.artifact, 'artifact_digest': digest(self.artifact), 'tests': []}
        self.permit = Permit('claude', digest(self.payload), time.time()+60, 'FICTICIO', 'call1', 'run1', SOURCE, '1')

    def test_reservation_exists_before_transport_and_timeout_keeps_charge(self):
        def transport(*_):
            self.assertEqual(self.store.budget.summary()['attempts'], 1)
            raise TimeoutError('FICTICIO')
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'FICTICIO-NO-CREDENTIAL'}):
            with self.assertRaises(Blocked):
                ClaudeReviewer(self.cfg, self.store, transport).review('T', self.artifact, [], self.permit)
        self.assertEqual(self.store.budget.summary()['unknown'], 1)
        self.assertEqual(self.store.budget.summary()['conservative_charge_units'], 1000000)

    def test_missing_budget_stops_before_credentials_or_transport(self):
        config = self.store.config()
        config['max_spend_total'] = None
        self.store.config_path.write_text(canonical(config))
        with patch('factory2.providers.os.environ.get', side_effect=AssertionError('No credentials')):
            with self.assertRaises(Blocked):
                ClaudeReviewer(self.cfg, self.store, lambda *_: self.fail()).review('T', self.artifact, [], self.permit)
        self.assertEqual(self.store.budget.summary()['attempts'], 0)

    def test_paid_reservation_and_call_are_one_transaction(self):
        with self.store.worker(), self.assertRaises(Blocked):
            self.store.reserve_paid_call('bad', 'unknown-task', 'ficticio', 'hash', execution_id='run1',
                                         source_sha=SOURCE, max_cost='1', output_limit=100)
        self.assertEqual(self.store.budget.summary()['attempts'], 0)
        self.assertEqual(self.store.summary()['calls'], 0)

    def test_recover_marks_paid_attempt_unknown_without_refund(self):
        with self.store.worker():
            self.store.reserve_paid_call('c', 'T', 'ficticio', 'hash', execution_id='run1',
                                         source_sha=SOURCE, max_cost='1', output_limit=100)
        self.assertEqual(self.store.recover()['uncertain_paid_attempts'], 1)
        self.assertEqual(self.store.budget.summary()['conservative_charge_units'], 1000000)
        self.assertEqual(self.store.recover()['uncertain_paid_attempts'], 0)

    @unittest.skipUnless(
        hasattr(sqlite3.Connection, 'setconfig')
        and hasattr(sqlite3, 'SQLITE_DBCONFIG_DQS_DML')
        and hasattr(sqlite3, 'SQLITE_DBCONFIG_DQS_DDL'),
        'Local Python/SQLite does not expose DQS_DML/DQS_DDL configuration')
    def test_recovery_and_summaries_with_double_quoted_text_disabled(self):
        original_connect = sqlite3.connect

        def strict_connect(*args, **kwargs):
            db = original_connect(*args, **kwargs)
            try:
                for option in (sqlite3.SQLITE_DBCONFIG_DQS_DML, sqlite3.SQLITE_DBCONFIG_DQS_DDL):
                    db.setconfig(option, False)
                    self.assertFalse(db.getconfig(option))
                # Prove that this connection rejects double-quoted text.
                with self.assertRaises(sqlite3.OperationalError):
                    db.execute('SELECT "fictitious_missing_column"')
                return db
            except BaseException:
                db.close()
                raise

        # Both modules use the same sqlite3 module; every new connection is strict.
        with patch('sqlite3.connect', side_effect=strict_connect):
            with self.store.worker():
                self.store.reserve_paid_call('strict1', 'T', 'ficticio', 'hash', execution_id='run1',
                                             source_sha=SOURCE, max_cost='1', output_limit=100)
            recovered = self.store.recover()
            self.assertEqual(recovered['uncertain_calls'], 1)
            self.assertEqual(recovered['uncertain_paid_attempts'], 1)
            self.assertEqual(recovered['retried'], 0)
            self.assertEqual(self.store.summary()['uncertain'], 1)
            self.assertEqual(self.store.budget.summary()['unknown'], 1)
            self.assertEqual(self.store.budget.summary()['conservative_charge_units'], 1000000)
            self.assertEqual(self.store.recover()['uncertain_paid_attempts'], 0)
            self.store.budget.reserve('strict2', 'run1', 'ficticio', 'hash', SOURCE, '1', self.store.config())
            self.store.budget.finish('strict2', 'COMPLETED', actual_cost='1.5')
            with self.assertRaisesRegex(Blocked, 'BUDGET_RECONCILIATION_REQUIRED'):
                self.store.budget.reserve('strict3', 'run1', 'ficticio', 'hash', SOURCE, '0.1', self.store.config())


if __name__ == '__main__':
    unittest.main()
