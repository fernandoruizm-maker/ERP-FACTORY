"""Preparation is offline; execution boundaries use explicit fictional doubles."""
import copy
import shutil
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
from tests.operation_fixtures import disabled_repository_config


class PreparationTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        shutil.copytree(ROOT / 'encargos', self.root / 'encargos')
        self.cfg = json.loads(disabled_repository_config(self.root).read_text())
        self.write_config()
        # Explicit local Docker query double; never contact an engine in this suite.
        self.docker = self.enterContext(patch('factory2.pilot_preflight.bounded_process',
            side_effect=lambda command: (0, 'npipe:////./pipe/docker_engine\n')
            if command[1] == 'context' else (0, 'linux/amd64\n')))

    def write_config(self):
        (self.root / 'config.json').write_text(canonical(self.cfg))

    def test_repository_config_is_disarmed_after_trial(self):
        cfg = json.loads((ROOT / 'config.json').read_text(encoding='utf-8'))
        for flag in ('enabled', 'external_calls_enabled', 'erp_access_enabled', 'publication_enabled'):
            self.assertIs(cfg[flag], False)

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
        self.assertEqual({p.name for p in self.root.iterdir()}, {'config.json', 'encargos'})

    def test_exact_requested_contract_and_standard_cost(self):
        data = prepare(self.root)
        payload = data['request']
        self.assertEqual(payload['model'], 'gpt-6.1-sol')
        self.assertEqual(payload['reasoning'], {'effort': 'medium'})
        self.assertEqual(payload['max_output_tokens'], 32000)
        self.assertEqual(payload['tools'], [])
        self.assertEqual(payload['tool_choice'], 'none')
        self.assertEqual(payload['service_tier'], 'default')
        self.assertEqual(payload['prompt_cache_options'], {'mode': 'explicit'})
        self.assertIsInstance(payload['input'], str)
        self.assertNotIn('prompt_cache_breakpoint', payload['text']['format']['schema'])
        self.assertIs(payload['store'], False)
        self.assertEqual(payload['text']['format']['type'], 'json_schema')
        self.assertIs(payload['text']['format']['strict'], True)
        self.assertEqual(data['request_bytes'], len(request_bytes(payload)))
        self.assertEqual(data['worst_case_cost_usd'], token_cost(self.cfg['pilot_cost_review'], data['request_bytes'], 32000))
        self.assertEqual(data['maximum_request_cost_usd'], '0.520000')

    def test_wrong_model_effort_price_or_global_activation_blocks(self):
        original = copy.deepcopy(self.cfg)
        cases = [('pilot_model', 'gpt-5.3-codex'), ('enabled', True), ('erp_access_enabled', True),
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

    def test_check_inspects_context_and_both_images_without_ledger_changes(self):
        from factory2.codex_adapter import PYTHON_IMAGE, NODE_IMAGE
        auth = self.authorized_fixture()
        store = self.reviewed_ledger(auth)
        before = store.path.read_bytes()
        with patch('factory2.trial_command.clean_head', return_value='a'*40), \
             patch('factory2.state.Store', side_effect=AssertionError('no ledger initialization')):
            preflight(auth, 'a'*40, self.root)
        self.assertEqual([c.args[0] for c in self.docker.call_args_list], [
            ['docker', 'context', 'inspect', '--format', '{{.Endpoints.docker.Host}}'],
            ['docker', 'image', 'inspect', PYTHON_IMAGE, '--format', '{{.Os}}/{{.Architecture}}'],
            ['docker', 'image', 'inspect', NODE_IMAGE, '--format', '{{.Os}}/{{.Architecture}}']])
        self.assertEqual(store.path.read_bytes(), before)
        self.assertFalse((self.root/'work').exists())

    def test_check_and_start_share_docker_failure_code_without_a_call(self):
        from factory2.orchestrator import PilotTrial
        auth = self.authorized_fixture()
        store = self.reviewed_ledger(auth)
        self.docker.side_effect = [(0, 'npipe:////./pipe/docker_engine'), (1, 'FICTICIO_PRIVATE_ERROR')]*2
        with patch('factory2.trial_command.clean_head', return_value='a'*40), \
             patch('factory2.orchestrator.clean_head', return_value='a'*40):
            with self.assertRaisesRegex(Blocked, '^PILOT_PINNED_IMAGES_REQUIRED$'):
                preflight(auth, 'a'*40, self.root)
            trial = PilotTrial(store, self.root/'work/ensayo-real')
            with self.assertRaisesRegex(Blocked, '^PILOT_PINNED_IMAGES_REQUIRED$'):
                trial.start(auth)
        self.assertEqual(trial.load()['reason_code'], 'PILOT_PINNED_IMAGES_REQUIRED')
        self.assertNotIn('FICTICIO_PRIVATE_ERROR', canonical(trial.load()))
        self.assertEqual(store.summary()['calls'], 0)
        self.assertEqual(store.budget.summary()['attempts'], 0)

    def test_bad_context_blocks_before_images_key_or_store(self):
        auth = self.authorized_fixture()
        store = self.reviewed_ledger(auth)
        before = store.path.read_bytes()
        self.docker.side_effect = None
        self.docker.return_value = (0, 'tcp://ficticio.invalid:2375')
        with patch('factory2.trial_command.clean_head', return_value='a'*40), \
             patch('factory2.state.Store', side_effect=AssertionError('no writes')):
            with self.assertRaisesRegex(Blocked, '^LOCAL_DOCKER_ENDPOINT_REQUIRED$'):
                execute(auth, 'a'*40, self.root, key_reader=lambda: self.fail('key read'))
        self.docker.assert_called_once()
        self.assertEqual(store.path.read_bytes(), before)

    def test_dirty_git_reason_is_persisted_without_docker_or_payment(self):
        from factory2.orchestrator import PilotTrial
        auth = self.authorized_fixture()
        store = self.reviewed_ledger(auth)
        trial = PilotTrial(store, self.root/'work/ensayo-real')
        with patch('factory2.orchestrator.clean_head', side_effect=Blocked('SOURCE_OR_CANDIDATE_NOT_CLEAN')):
            with self.assertRaisesRegex(Blocked, '^SOURCE_OR_CANDIDATE_NOT_CLEAN$'):
                trial.start(auth)
        self.assertEqual(trial.load()['reason_code'], 'SOURCE_OR_CANDIDATE_NOT_CLEAN')
        self.assertEqual(store.summary()['calls'], 0)
        self.assertEqual(store.budget.summary()['attempts'], 0)
        self.docker.assert_not_called()
        with self.assertRaisesRegex(Blocked, '^PILOT_ALREADY_RECORDED_NO_RETRY$'):
            trial.start(auth)

    def test_check_detects_candidate_before_key_or_attempt(self):
        auth = self.authorized_fixture()
        store = self.reviewed_ledger(auth)
        (self.root/'work/ensayo-real/bottles-1').mkdir(parents=True)
        before = store.path.read_bytes()
        with patch('factory2.trial_command.clean_head', return_value='a'*40):
            with self.assertRaisesRegex(Blocked, '^PILOT_CANDIDATE_ALREADY_EXISTS$'):
                execute(auth, 'a'*40, self.root, key_reader=lambda: self.fail('key read'))
        self.assertEqual(store.path.read_bytes(), before)

    def test_check_uses_worker_lock_without_consuming_attempt(self):
        auth = self.authorized_fixture()
        store = self.reviewed_ledger(auth)
        before = store.path.read_bytes()
        with store.worker(), patch('factory2.trial_command.clean_head', return_value='a'*40):
            with self.assertRaisesRegex(Blocked, '^WORKER_ALREADY_ACTIVE$'):
                preflight(auth, 'a'*40, self.root)
        self.docker.assert_not_called()
        self.assertEqual(store.path.read_bytes(), before)

    def test_check_rejects_other_unfinished_attempt(self):
        auth = self.authorized_fixture()
        store = self.reviewed_ledger(auth)
        with store.connect() as db:
            db.execute('CREATE TABLE pilot_trials(id TEXT PRIMARY KEY, data TEXT)')
            db.execute('INSERT INTO pilot_trials VALUES(?,?)', ('bottles-0', canonical({'status':'BUILDING'})))
        with patch('factory2.trial_command.clean_head', return_value='a'*40):
            with self.assertRaisesRegex(Blocked, '^PILOT_PREVIOUS_ATTEMPT_UNFINISHED$'):
                preflight(auth, 'a'*40, self.root)
        self.docker.assert_not_called()

    def test_cli_check_reports_closed_code_and_never_exception_text(self):
        import contextlib
        import io
        from factory2.trial_command import main
        auth_path = self.root/'authorization.json'
        auth_path.write_text('{}')
        for error, expected in ((Blocked('SOURCE_OR_CANDIDATE_NOT_CLEAN'), 'SOURCE_OR_CANDIDATE_NOT_CLEAN'),
                                (RuntimeError('FICTICIO_PRIVATE'), 'PILOT_PREFLIGHT_UNEXPECTED_NO_RETRY')):
            output = io.StringIO()
            with patch('sys.argv', ['trial_command', 'check', '--encargo', 'botellas', '--authorization', str(auth_path)]), \
                 patch('factory2.trial_command.preflight', side_effect=error), contextlib.redirect_stdout(output):
                self.assertEqual(main(), 2)
            self.assertEqual(json.loads(output.getvalue()), {'status':'BLOCKED','reason_code':expected})
            self.assertNotIn('FICTICIO_PRIVATE', output.getvalue())

    def second_attempt_fixture(self):
        auth = {**self.authorized_fixture(), 'attempt': 2}
        store = self.reviewed_ledger(auth)
        with store.connect() as db:
            db.execute('CREATE TABLE pilot_trials(id TEXT PRIMARY KEY, data TEXT)')
            db.execute('INSERT INTO pilot_trials VALUES(?,?)', ('bottles-1', canonical({
                'attempt':1, 'status':'BLOCKED', 'reason_code':'PILOT_PREFLIGHT_BLOCKED_NO_RETRY'})))
        return auth, store

    def test_attempt_two_accepted_with_one_blocked_without_consumption(self):
        auth, store = self.second_attempt_fixture()
        before = store.path.read_bytes()
        with patch('factory2.trial_command.clean_head', return_value='a'*40):
            result = preflight(auth, 'a'*40, self.root, attempt=2)
        self.assertEqual(result['attempt'], 2)
        self.assertEqual(result['authorization_draft']['attempt'], 2)
        self.assertFalse(result['attempt_consumed'])
        self.assertEqual(store.path.read_bytes(), before)
        self.assertEqual(store.summary()['calls'], 0)
        self.assertEqual(store.budget.summary()['attempts'], 0)

    def test_attempt_two_repeated_rejected(self):
        auth, store = self.second_attempt_fixture()
        with store.connect() as db:
            db.execute('INSERT INTO pilot_trials VALUES(?,?)', ('bottles-2', canonical({'status':'BLOCKED'})))
        before = store.path.read_bytes()
        with patch('factory2.trial_command.clean_head', return_value='a'*40):
            with self.assertRaisesRegex(Blocked, '^PILOT_ALREADY_RECORDED_NO_RETRY$'):
                execute(auth, 'a'*40, self.root, attempt=2, key_reader=lambda: self.fail('key read'))
        self.assertEqual(store.path.read_bytes(), before)
        self.docker.assert_not_called()

    def test_attempt_one_remains_rejected_after_its_block(self):
        auth, store = self.second_attempt_fixture()
        before = store.path.read_bytes()
        with patch('factory2.trial_command.clean_head', return_value='a'*40):
            with self.assertRaisesRegex(Blocked, '^PILOT_ALREADY_RECORDED_NO_RETRY$'):
                preflight({**auth, 'attempt':1}, 'a'*40, self.root, attempt=1)
        self.assertEqual(store.path.read_bytes(), before)
        self.docker.assert_not_called()

    def test_authorized_number_must_match_explicit_parameter(self):
        auth, store = self.second_attempt_fixture()
        before = store.path.read_bytes()
        for parameter, authorized in ((1,2), (2,1), (2,True), (2,'2')):
            with self.subTest(parameter=parameter, authorized=authorized), \
                 patch('factory2.trial_command.clean_head', return_value='a'*40):
                with self.assertRaisesRegex(Blocked, '^PILOT_AUTHORIZATION_REQUIRED$'):
                    execute({**auth, 'attempt':authorized}, 'a'*40, self.root, attempt=parameter,
                            key_reader=lambda: self.fail('key read'))
        self.assertEqual(store.path.read_bytes(), before)
        self.docker.assert_not_called()

    def test_prior_attempt_must_exist_and_be_blocked(self):
        auth, store = self.second_attempt_fixture()
        for previous in (None, 'BUILDING', 'WAITING_FOR_MANUAL_REVIEW'):
            with store.connect() as db:
                db.execute("DELETE FROM pilot_trials WHERE id='bottles-1'")
                if previous:
                    db.execute('INSERT INTO pilot_trials VALUES(?,?)', ('bottles-1', canonical({'status':previous})))
            with self.subTest(previous=previous), patch('factory2.trial_command.clean_head', return_value='a'*40):
                with self.assertRaisesRegex(Blocked, '^PILOT_PREVIOUS_ATTEMPT_UNFINISHED$'):
                    preflight(auth, 'a'*40, self.root, attempt=2)
        self.docker.assert_not_called()

    def test_trial_id_in_any_table_or_reference_blocks_reuse(self):
        auth, store = self.second_attempt_fixture()
        # Each table is otherwise empty. The double quotes also exercise schema quoting.
        for column in ('id','task','execution'):
            with store.connect() as db:
                db.execute(f'CREATE TABLE "ficticio""trace" ("{column}" TEXT)')
                db.execute(f'INSERT INTO "ficticio""trace" VALUES(?)', ('bottles-2',))
            with self.subTest(column=column), patch('factory2.trial_command.clean_head', return_value='a'*40):
                with self.assertRaisesRegex(Blocked, '^PILOT_ALREADY_RECORDED_NO_RETRY$'):
                    preflight(auth, 'a'*40, self.root, attempt=2)
            with store.connect() as db:
                db.execute('DROP TABLE "ficticio""trace"')
        self.docker.assert_not_called()

    def test_attempt_two_execution_port_receives_two_and_preserves_first(self):
        auth, store = self.second_attempt_fixture()
        before = store.path.read_bytes()
        with patch('factory2.trial_command.clean_head', return_value='a'*40), \
             patch.dict('os.environ', {}, clear=True), patch('factory2.trial_command.PilotTrial') as trial:
            trial.return_value.start.return_value = {'status':'WAITING_FOR_MANUAL_REVIEW',
                'attempt':2, 'publication_allowed':False}
            result = execute(auth, 'a'*40, self.root, attempt=2, key_reader=lambda:'FICTICIO')
        self.assertEqual(trial.call_args.kwargs, {'attempt':2, 'encargo':'botellas', 'encargos_root':self.root/'encargos'})
        trial.return_value.start.assert_called_once_with(auth)
        self.assertEqual(result['attempt'], 2)
        self.assertEqual(store.path.read_bytes(), before)

    def test_preparation_validates_attempt_and_preserves_costs(self):
        first = prepare(self.root, attempt=1)
        second = prepare(self.root, attempt=2)
        for field in ('request','request_bytes','worst_case_cost_usd','maximum_request_cost_usd',
                      'config_digest','context_digest'):
            self.assertEqual(first[field], second[field])
        for number in (None, True, '2', 0, -1, 1000001):
            with self.subTest(number=number), self.assertRaisesRegex(Blocked, '^PILOT_ATTEMPT_INVALID$'):
                prepare(self.root, attempt=number)

    def test_cli_propagates_attempt_to_all_modes(self):
        import contextlib
        import io
        from factory2.trial_command import main
        auth_path = self.root/'authorization.json'
        auth_path.write_text('{"attempt":2}')
        for mode, target in (('prepare','prepare'), ('check','preflight'), ('run','execute')):
            with self.subTest(mode=mode), patch('sys.argv', ['trial_command',mode,'--encargo','botellas','--attempt','2',
                 '--authorization',str(auth_path),'--expected-sha','a'*40]), \
                 patch('factory2.trial_command.'+target, return_value={'status':'FICTICIO'}) as port, \
                 contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(), 0)
                self.assertEqual(port.call_args.kwargs['attempt'], 2)
                self.assertEqual(port.call_args.kwargs['encargo'], 'botellas')

    def test_prepare_selected_job_binds_authorization_without_execution(self):
        bottles = prepare(self.root, encargo='botellas')
        caja = prepare(self.root, encargo='caja-chica')
        self.assertEqual(caja['authorization_draft']['encargo'], 'caja-chica')
        self.assertEqual(json.loads(caja['request']['input'])['profile'], 'python')
        self.assertNotEqual(bottles['context_digest'], caja['context_digest'])
        self.assertFalse(caja['execution_enabled'])
        self.assertFalse((self.root/'state').exists())

    def test_different_job_authorization_rejected_before_key(self):
        auth = self.authorized_fixture()
        store = self.reviewed_ledger(auth)
        before = store.path.read_bytes()
        with patch('factory2.trial_command.clean_head', return_value='a'*40):
            with self.assertRaisesRegex(Blocked, 'AUTHORIZATION_REQUIRED'):
                execute(auth, 'a'*40, self.root, encargo='caja-chica', key_reader=lambda: self.fail('key read'))
        self.assertEqual(store.path.read_bytes(), before)
        self.docker.assert_not_called()

    def test_new_job_preflight_ignores_other_job_history_but_keeps_budget(self):
        self.authorized_fixture()
        auth = {**prepare(self.root, encargo='caja-chica')['authorization_draft'],
                'source_sha':'a'*40, 'authorized_by':'Fernando', 'expires_at':time.time()+600}
        store = self.reviewed_ledger(auth)
        with store.connect() as db:
            db.execute('CREATE TABLE pilot_trials(id TEXT PRIMARY KEY, data TEXT)')
            db.execute('INSERT INTO pilot_trials VALUES(?,?)', ('bottles-2', canonical({'status':'WAITING_FOR_ACCEPTANCES'})))
        store.budget.begin('hist', 'a'*40, self.cfg)
        store.budget.reserve('hist', 'hist', 'ficticio', 'hash', 'a'*40, '1', self.cfg)
        store.budget.finish('hist', 'COMPLETED')
        before = store.path.read_bytes()
        with patch('factory2.trial_command.clean_head', return_value='a'*40):
            self.assertEqual(preflight(auth, 'a'*40, self.root, encargo='caja-chica')['encargo'], 'caja-chica')
        self.assertEqual(store.path.read_bytes(), before)
        self.assertEqual(store.budget.summary()['conservative_charge_units'], 1000000)


if __name__ == '__main__':
    unittest.main()
