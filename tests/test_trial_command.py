"""Preparation is offline; execution boundaries use explicit fictional doubles."""
import copy
import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

from factory2.core import Blocked, canonical
from factory2.codex_adapter import token_cost, request_bytes
from factory2.trial_command import prepare, preflight, execute, ROOT
from factory2.state import Store
from factory2.manual_review import CLEAR, REVIEWER


class PreparationTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.cfg = json.loads((ROOT / 'config.json').read_text())
        self.write_config()

    def write_config(self):
        (self.root / 'config.json').write_text(canonical(self.cfg))

    def test_prepare_without_transport_credential_docker_state_or_attempt(self):
        original = (self.root / 'config.json').read_bytes()
        with patch('factory2.codex_adapter.ResponsesAPI.__call__', side_effect=AssertionError('no network')), \
             patch('factory2.state.Store', side_effect=AssertionError('no ledger creation')), \
             patch('factory2.codex_adapter.os.environ.get', side_effect=AssertionError('no key')), \
             patch('subprocess.Popen', side_effect=AssertionError('no Docker')):
            result = prepare(self.root)
        self.assertEqual(result['status'], 'PREPARED_NOT_EXECUTED')
        self.assertFalse(result['attempt_consumed'])
        self.assertFalse(result['execution_enabled'])
        self.assertFalse(result['ledger_present'])
        self.assertEqual(result['authorization_draft']['attempt'], 1)
        self.assertIsNone(result['authorization_draft']['authorized_by'])
        self.assertIsNone(result['authorization_draft']['source_sha'])
        self.assertEqual((self.root / 'config.json').read_bytes(), original)
        self.assertEqual({p.name for p in self.root.iterdir()}, {'config.json'})

    def test_exact_requested_contract_and_standard_cost(self):
        data = prepare(self.root)
        payload = data['request']
        self.assertEqual(payload['model'], 'gpt-5.3-codex')
        self.assertEqual(payload['reasoning'], {'effort': 'medium'})
        self.assertEqual(payload['max_output_tokens'], 32000)
        self.assertEqual(payload['tools'], [])
        self.assertEqual(payload['tool_choice'], 'none')
        self.assertEqual(payload['service_tier'], 'default')
        self.assertIs(payload['store'], False)
        self.assertEqual(payload['text']['format']['type'], 'json_schema')
        self.assertIs(payload['text']['format']['strict'], True)
        self.assertEqual(data['request_bytes'], len(request_bytes(payload)))
        self.assertEqual(data['worst_case_cost_usd'], token_cost(self.cfg['pilot_cost_review'], data['request_bytes'], 32000))
        self.assertEqual(data['maximum_request_cost_usd'], '0.623000')

    def test_wrong_model_effort_price_or_global_activation_blocks(self):
        original = copy.deepcopy(self.cfg)
        cases = [('pilot_model', 'other'), ('enabled', True), ('erp_access_enabled', True),
                 ('publication_enabled', True), ('max_spend_total', '14.00')]
        for key, value in cases:
            self.cfg = {**copy.deepcopy(original), key: value}
            self.write_config()
            with self.subTest(key=key), self.assertRaises(Blocked): prepare(self.root)
        for key, value in [('reasoning_effort', 'high'), ('input_usd_per_million', '0.01')]:
            self.cfg = copy.deepcopy(original)
            self.cfg['pilot_cost_review'][key] = value
            self.write_config()
            with self.subTest(key=key), self.assertRaises(Blocked): prepare(self.root)

    def test_real_entry_stops_at_false_switch_before_key_or_store(self):
        with patch('factory2.state.Store', side_effect=AssertionError('no Store')):
            with self.assertRaisesRegex(Blocked, 'SWITCH_OFF'):
                execute({}, 'a'*40, self.root, key_reader=lambda: self.fail('key read'))
        self.assertFalse((self.root / 'state').exists())

    def authorized_fixture(self):
        self.cfg['external_calls_enabled'] = True  # Fictitious temp config only.
        self.write_config()
        prepared = prepare(self.root)
        auth = {**prepared['authorization_draft'], 'source_sha': 'a'*40,
                'authorized_by': 'Fernando', 'expires_at': time.time()+600}
        return auth

    def reviewed_ledger(self, auth):
        folder = self.root / 'docs/revisiones'
        folder.mkdir(parents=True)
        store = Store(self.root / 'state/factory2.sqlite3', config_path=self.root / 'config.json', reviews_directory=folder)
        record = {'schema_version': 1, 'pr': 'LOCAL:FICTICIO', 'base_sha': 'b'*40,
                  'reviewed_sha': 'a'*40, 'scope': {'mode': 'CAMBIOS_PR', 'files': ['config.json'], 'diff': 'FICTICIO'},
                  'reviewer': REVIEWER, 'findings': [], 'conclusion': CLEAR, 'date': '2026-11-06'}
        path = folder / 'factory.local.md'
        path.write_text('# FICTICIO\n```json\n'+canonical(record)+'\n```\n', encoding='utf-8')
        auth['factory_review_id'] = store.import_manual_review(path)['review_id']
        return store

    def test_preflight_missing_ledger_does_not_create_one(self):
        auth = self.authorized_fixture()
        with patch('factory2.trial_command.clean_head', return_value='a'*40):
            with self.assertRaisesRegex(Blocked, 'EXISTING_RECONCILED_LEDGER'):
                preflight(auth, 'a'*40, self.root)
        self.assertFalse((self.root/'state').exists())

    def test_preflight_review_sha_expiry_and_reuse(self):
        auth = self.authorized_fixture()
        store = self.reviewed_ledger(auth)
        with patch('factory2.trial_command.clean_head', return_value='a'*40):
            self.assertEqual(preflight(auth, 'a'*40, self.root)['attempt'], 1)
            for change in ({'expires_at': 0}, {'attempt': 2}, {'source_sha': 'c'*40},
                           {'config_digest': 'bad'}, {'factory_review_id': 'manual:missing'}):
                with self.subTest(change=change), self.assertRaises(Blocked):
                    preflight({**auth, **change}, 'a'*40, self.root)
            with store.connect() as db:
                db.execute('CREATE TABLE pilot_authorizations(id TEXT PRIMARY KEY, digest TEXT)')
                db.execute('INSERT INTO pilot_authorizations VALUES(?,?)', ('bottles-1', 'FICTICIO'))
            with self.assertRaisesRegex(Blocked, 'NO_RETRY'): preflight(auth, 'a'*40, self.root)

    def test_preflight_shared_unknown_budget_stops(self):
        auth = self.authorized_fixture()
        store = self.reviewed_ledger(auth)
        store.budget.begin('ficticio', 'a'*40, self.cfg)
        store.budget.reserve('ficticio', 'ficticio', 'ficticio', 'hash', 'a'*40, '1.00', self.cfg)
        store.budget.finish('ficticio', 'UNKNOWN')
        with patch('factory2.trial_command.clean_head', return_value='a'*40):
            with self.assertRaisesRegex(Blocked, 'RECONCILIATION'): preflight(auth, 'a'*40, self.root)

    def test_execution_port_is_one_call_then_clears_fictitious_key(self):
        auth = self.authorized_fixture()
        self.reviewed_ledger(auth)
        with patch('factory2.trial_command.clean_head', return_value='a'*40), \
             patch.dict('os.environ', {}, clear=True), \
             patch('factory2.trial_command.PilotTrial') as fake_trial:
            fake_trial.return_value.start.return_value = {'status': 'WAITING_FOR_MANUAL_REVIEW',
                'attempt': 1, 'publication_allowed': False, 'private_text': 'DO_NOT_PRINT'}
            result = execute(auth, 'a'*40, self.root, key_reader=lambda: 'FICTICIO')
            fake_trial.return_value.start.assert_called_once_with(auth)
            self.assertNotIn('private_text', result)
            import os
            self.assertNotIn('OPENAI_API_KEY', os.environ)


if __name__ == '__main__':
    unittest.main()
