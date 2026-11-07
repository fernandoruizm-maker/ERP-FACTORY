"""Fictitious API/Docker/Git ports only. These tests never invoke those services."""
from concurrent.futures import ThreadPoolExecutor
import copy
import json
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

from factory2.core import Blocked, canonical, digest
from factory2.manual_review import CLEAR, REVIEWER
from factory2.state import Store
from factory2.orchestrator import PilotTrial, bottle_input
from factory2.codex_adapter import DockerCodexBuilder, ResponsesAPI, PYTHON_IMAGE, usage_record, token_cost, request_bytes
from factory2.docker_materialize import materialize
from tests.operation_fixtures import config, coordinator, disabled_repository_config

SOURCE, CANDIDATE = 'a'*40, 'c'*40
PROPOSAL = {'summary_es': 'FICTICIO', 'edits': [{'path': 'src/bottles.mjs', 'content': 'export class Bottles {}\n'}]}


def response(proposal=PROPOSAL):
    return {'status': 'completed', 'usage': {'input_tokens': 100, 'output_tokens': 20,
        'output_tokens_details': {'reasoning_tokens': 5}}, 'output': [{'type': 'message', 'role': 'assistant',
        'content': [{'type': 'output_text', 'text': canonical(proposal)}]}]}


def enabled_fixture(store):
    cfg = store.config()
    cfg.update(enabled=False, external_calls_enabled=True, erp_access_enabled=False, publication_enabled=False,
               budget_currency='USD', max_budget_usd_per_call='1.00', max_spend_per_execution='12.00',
               max_spend_total='13.00', pilot_model='codex-FICTICIO',
               pilot_cost_review={'model': 'codex-FICTICIO', 'basis': 'FICTICIO, NO TARIFA REAL',
                                  'max_request_bytes': 100000, 'max_output_tokens': 1024, 'max_call_usd': '1.00',
                                  'reasoning_effort': 'high', 'input_usd_per_million': '1.00',
                                  'output_usd_per_million': '2.00'})
    store.config_path.write_text(canonical(cfg))
    return cfg


class TrialTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.reviews = self.root / 'reviews'
        self.reviews.mkdir()
        self.store = Store(self.root/'state.sqlite3', config_path=config(self.root),
                           coordinator=coordinator(self.root), reviews_directory=self.reviews)
        self.cfg = enabled_fixture(self.store)
        self.seen = []
        self.generate = lambda context: copy.deepcopy(PROPOSAL)
        owner = self

        class Builder:
            def generate(self, context):
                owner.seen.append('provider')
                self.last_usage = usage_record(response(), owner.cfg['pilot_cost_review'])
                return owner.generate(context)

            def materialize(self, proposal, directory):
                owner.seen.append('docker-build-double')
                directory.mkdir()
                materialize(proposal, directory)

        def tester(directory, image, profile, files, artifact):
            self.seen.append('docker-test-double')
            return {'status': 'PASS', 'exit_code': 0, 'test_count': 7,
                    'profile': profile, 'artifact_digest': artifact}

        self.tester = tester
        self.trial = PilotTrial(self.store, self.root/'work', builder=Builder(),
                               tester=lambda *args: self.tester(*args), snapshotter=lambda _: CANDIDATE,
                               head=lambda directory: SOURCE if directory is None else CANDIDATE)
        factory_path = self.review('factory', SOURCE, ['factory2/orchestrator.py'])
        factory = self.store.import_manual_review(factory_path)
        self.auth = {'attempt': 1, 'source_sha': SOURCE, 'context_digest': digest(bottle_input()),
                     'config_digest': digest(self.cfg), 'authorized_by': 'Fernando',
                     'expires_at': time.time()+600, 'factory_review_id': factory['review_id']}

    def review(self, name, sha, files, conclusion=CLEAR):
        record = {'schema_version': 1, 'pr': 'LOCAL:FICTICIO', 'base_sha': 'b'*40,
                  'reviewed_sha': sha, 'scope': {'mode': 'CAMBIOS_PR', 'files': files, 'diff': 'FICTICIO'},
                  'reviewer': REVIEWER, 'findings': [], 'conclusion': conclusion, 'date': '2026-11-06'}
        path = self.reviews / (name+'.local.md')
        path.write_text('# SOLO FICTICIO\n```json\n'+canonical(record)+'\n```\n', encoding='utf-8')
        return path

    def change_config(self, **changes):
        self.cfg.update(changes)
        self.store.config_path.write_text(canonical(self.cfg))
        self.auth['config_digest'] = digest(self.cfg)

    def test_happy_path_pauses_for_chat_then_requires_two_people(self):
        data = self.trial.start(self.auth)
        self.assertEqual(data['status'], 'WAITING_FOR_MANUAL_REVIEW')
        self.assertEqual(self.seen, ['provider', 'docker-build-double', 'docker-test-double'])
        self.assertEqual(data['evidence_mode'], 'SIMULATED')
        with self.assertRaises(Blocked): self.trial.gate()
        path = self.review('product', CANDIDATE, list(data['files']))
        self.assertEqual(self.trial.attach_review(path)['status'], 'WAITING_FOR_ACCEPTANCES')
        self.trial.accept('persona-a', 'business', time.time()+60)
        self.assertEqual(self.trial.gate()['status'], 'BLOCKED')
        self.trial.accept('persona-b', 'accounting', time.time()+60)
        gate = self.trial.gate()
        self.assertEqual(gate['status'], 'READY_FOR_MANUAL_REVIEW')
        self.assertFalse(gate['publication_allowed'])
        self.assertFalse(gate['provenance_authenticated'])
        self.assertEqual(self.store.budget.summary()['conservative_charge_units'], 1000000)
        with self.assertRaises(Blocked): self.trial.start(self.auth)
        self.assertEqual(self.seen.count('provider'), 1)

    def test_tests_failure_stops_without_snapshot_or_review(self):
        self.tester = lambda *_: {'status': 'FAIL', 'exit_code': 1}
        data = self.trial.start(self.auth)
        self.assertEqual(data['status'], 'BLOCKED')
        self.assertNotIn('candidate_sha', data)
        with self.assertRaises(Blocked): self.trial.gate()
        self.assertEqual(self.store.budget.summary()['attempts'], 1)

    def test_attempt_number_required_and_preflight_failure_is_consumed(self):
        for bad in (None, 0, -1, True, '2'):
            with self.subTest(bad=bad), self.assertRaisesRegex(Blocked, 'ATTEMPT_INVALID'):
                self.trial.start({**self.auth, 'attempt': bad})
        self.change_config(external_calls_enabled=False)
        with self.assertRaisesRegex(Blocked, 'SWITCH_OFF'): self.trial.start(self.auth)
        self.assertEqual(self.trial.load()['reason_code'], 'PILOT_SWITCH_OFF')
        self.change_config(external_calls_enabled=True)
        with self.assertRaisesRegex(Blocked, 'NO_RETRY'): self.trial.start(self.auth)
        self.assertEqual(self.seen, [])
        data = self.trial.start({**self.auth, 'attempt': 2})
        self.assertEqual(data['attempt'], 2)
        self.assertEqual(data['status'], 'WAITING_FOR_MANUAL_REVIEW')

    def test_new_authorized_attempt_after_failure_preserves_old_evidence(self):
        original = self.tester
        self.tester = lambda *_: {'status': 'FAIL', 'exit_code': 1}
        first = self.trial.start(self.auth)
        self.assertEqual(first['status'], 'BLOCKED')
        with self.assertRaisesRegex(Blocked, 'NO_RETRY'): self.trial.start(self.auth)
        self.tester = original
        second = self.trial.start({**self.auth, 'attempt': 2})
        self.assertEqual(second['status'], 'WAITING_FOR_MANUAL_REVIEW')
        self.assertEqual(self.seen.count('provider'), 2)
        self.assertEqual(self.store.budget.summary()['conservative_charge_units'], 2000000)
        with self.store.connect() as db:
            self.assertEqual(json.loads(db.execute("SELECT data FROM pilot_trials WHERE id='bottles-1'").fetchone()[0]), first)
        with self.assertRaisesRegex(Blocked, 'UNFINISHED'):
            self.trial.start({**self.auth, 'attempt': 3})

    def test_thirteen_dollars_remains_shared_across_authorized_attempts(self):
        self.tester = lambda *_: {'status': 'FAIL', 'exit_code': 1}
        for attempt in range(1, 14):
            self.assertEqual(self.trial.start({**self.auth, 'attempt': attempt})['status'], 'BLOCKED')
        blocked = self.trial.start({**self.auth, 'attempt': 14})
        self.assertEqual(blocked['reason_code'], 'SPEND_LIMIT')
        self.assertEqual(self.seen.count('provider'), 13)
        self.assertEqual(self.store.budget.summary()['conservative_charge_units'], 13000000)

    def test_usage_is_saved_in_trial_and_paid_ledger(self):
        self.change_config(pilot_cost_review={**self.cfg['pilot_cost_review'], 'max_output_tokens': 32000})
        result = self.trial.start(self.auth)
        self.assertEqual(result['status'], 'WAITING_FOR_MANUAL_REVIEW')
        self.assertEqual(result['calculated_cost_usd'], '0.000140')
        self.assertEqual(result['usage']['reasoning_tokens'], 5)
        with self.store.connect() as db:
            self.assertEqual(db.execute('SELECT actual_units FROM paid_attempts').fetchone()[0], 140)
            self.assertEqual(db.execute('SELECT output_limit FROM calls').fetchone()[0], 32000)

    def test_over_budget_usage_stops_before_docker_and_blocks_later_attempts(self):
        huge = response()
        huge['usage']['output_tokens'] = 600000
        self.trial.builder = DockerCodexBuilder(self.cfg, transport=lambda _: huge)
        data = self.trial.start(self.auth)
        self.assertEqual(data['reason_code'], 'CODEX_USAGE_EXCEEDS_AUTHORIZED_BOUND')
        self.assertEqual(data['calculated_cost_usd'], '1.200100')
        self.assertEqual(self.seen, [])
        with self.store.connect() as db:
            self.assertEqual(db.execute('SELECT status FROM paid_attempts').fetchone()[0], 'OVER_BUDGET')
        following = self.trial.start({**self.auth, 'attempt': 2})
        self.assertEqual(following['reason_code'], 'BUDGET_RECONCILIATION_REQUIRED')

    def test_incomplete_usage_persisted_without_free_text_or_retry(self):
        item = response()
        item.update(status='incomplete', secret_text='FICTICIO_NO_GUARDAR')
        self.trial.builder = DockerCodexBuilder(self.cfg, transport=lambda _: item)
        data = self.trial.start(self.auth)
        self.assertEqual(data['status'], 'BLOCKED')
        self.assertEqual(data['calculated_cost_usd'], '0.000140')
        self.assertNotIn('FICTICIO_NO_GUARDAR', canonical(data))
        self.assertEqual(self.store.budget.summary()['unknown'], 1)

    def test_switch_off_never_reaches_ports(self):
        self.change_config(external_calls_enabled=False)
        with self.assertRaisesRegex(Blocked, 'PILOT_SWITCH_OFF'): self.trial.start(self.auth)
        self.assertEqual(self.seen, [])
        self.assertEqual(self.store.budget.summary()['attempts'], 0)

    def test_unrecognized_preflight_error_is_recorded_without_free_text(self):
        with patch.object(self.trial, '_start', side_effect=RuntimeError('FICTICIO_PRIVATE')):
            with self.assertRaises(RuntimeError):
                self.trial.start(self.auth)
        data = self.trial.load()
        self.assertEqual(data['reason_code'], 'PILOT_PREFLIGHT_UNEXPECTED_NO_RETRY')
        self.assertNotIn('FICTICIO_PRIVATE', canonical(data))
        self.assertEqual(self.seen, [])
        self.assertEqual(self.store.budget.summary()['attempts'], 0)

    def test_null_caps_and_model_review_stop_before_provider(self):
        original = copy.deepcopy(self.cfg)
        for key in ('max_budget_usd_per_call', 'max_spend_per_execution', 'max_spend_total',
                    'pilot_model', 'pilot_cost_review'):
            self.auth['attempt'] += 1
            self.cfg = copy.deepcopy(original)
            self.change_config(**{key: None})
            with self.subTest(key=key), self.assertRaises(Blocked): self.trial.start(self.auth)
        self.assertEqual(self.seen, [])

    def test_per_execution_cap_stops_before_call(self):
        self.change_config(max_spend_per_execution='0.50')
        self.assertEqual(self.trial.start(self.auth)['status'], 'BLOCKED')
        self.assertEqual(self.seen, [])
        self.assertEqual(self.store.budget.summary()['attempts'], 0)

    def test_per_call_authorized_ceiling_cannot_be_raised(self):
        self.change_config(max_budget_usd_per_call='1.01')
        with self.assertRaisesRegex(Blocked, 'PILOT_AUTHORIZED_CAP_EXCEEDED'):
            self.trial.start(self.auth)
        self.assertEqual(self.seen, [])

    def test_accumulated_cap_in_existing_ledger_stops_before_call(self):
        for run in ('previous1', 'previous2'):
            self.store.budget.begin(run, SOURCE, self.cfg)
        for index in range(13):
            self.store.budget.reserve('old'+str(index), 'previous1' if index < 11 else 'previous2',
                'ficticio', 'hash', SOURCE, '1' if index < 12 else '0.50', self.cfg)
            self.store.budget.finish('old'+str(index), 'COMPLETED')
        # Do not use the fixture's assertion of exactly one reserved attempt here.
        self.assertEqual(self.trial.start(self.auth)['status'], 'BLOCKED')
        self.assertEqual(self.seen, [])
        self.assertEqual(self.store.budget.summary()['conservative_charge_units'], 12500000)

    def test_invalid_provider_response_is_unknown_no_retry_and_no_raw_text(self):
        self.generate = lambda _: {'private_provider_text': 'FICTICIO_NO_REVELAR'}
        data = self.trial.start(self.auth)
        self.assertEqual(data['status'], 'BLOCKED')
        self.assertNotIn('FICTICIO_NO_REVELAR', canonical(data))
        self.assertEqual(self.store.budget.summary()['unknown'], 1)
        with self.assertRaises(Blocked): self.trial.start(self.auth)

    def test_two_simultaneous_runs_make_only_one_call(self):
        entered, release = threading.Event(), threading.Event()
        def delayed(_):
            entered.set()
            if not release.wait(10): raise AssertionError('test coordination timeout')
            return copy.deepcopy(PROPOSAL)
        self.generate = delayed
        with ThreadPoolExecutor(max_workers=2) as pool:
            first = pool.submit(self.trial.start, self.auth)
            try:
                self.assertTrue(entered.wait(5))
                with self.assertRaisesRegex(Blocked, 'WORKER_ALREADY_ACTIVE'):
                    self.trial.start(self.auth)
            finally:
                release.set()
            self.assertEqual(first.result()['status'], 'WAITING_FOR_MANUAL_REVIEW')
        self.assertEqual(self.seen.count('provider'), 1)

    def test_wrong_or_correction_manual_review_blocks(self):
        data = self.trial.start(self.auth)
        path = self.review('wrong', 'd'*40, list(data['files']), 'CORREGIR')
        self.assertEqual(self.trial.attach_review(path)['status'], 'BLOCKED')
        with self.assertRaises(Blocked): self.trial.accept('persona-a', 'business', time.time()+60)

    def test_candidate_mutation_and_config_mutation_block_resume(self):
        data = self.trial.start(self.auth)
        path = self.review('product', CANDIDATE, list(data['files']))
        (self.root/'work/bottles-1/src/bottles.mjs').write_text('ALTERADO')
        with self.assertRaisesRegex(Blocked, 'CANDIDATE_CHANGED'): self.trial.attach_review(path)
        self.store.config_path.write_text(canonical({**self.cfg, 'max_spend_total': '12'}))
        with self.assertRaisesRegex(Blocked, 'CONFIG_CHANGED'): self.trial.attach_review(path)

    def test_disarming_after_tests_preserves_manual_gate_but_blocks_new_call(self):
        data = self.trial.start(self.auth)
        self.store.config_path.write_text(canonical({**self.cfg, 'external_calls_enabled': False}))
        path = self.review('product', CANDIDATE, list(data['files']))
        self.assertEqual(self.trial.attach_review(path)['status'], 'WAITING_FOR_ACCEPTANCES')
        self.trial.accept('persona-a', 'business', time.time()+60)
        self.trial.accept('persona-b', 'accounting', time.time()+60)
        self.assertEqual(self.trial.gate()['status'], 'READY_FOR_MANUAL_REVIEW')
        with self.assertRaisesRegex(Blocked, 'NO_RETRY'): self.trial.start(self.auth)
        self.assertEqual(self.seen.count('provider'), 1)

    def test_authorization_binds_source_context_and_configuration(self):
        for key in ('source_sha', 'context_digest', 'config_digest', 'factory_review_id'):
            self.auth['attempt'] += 1
            with self.subTest(key=key), self.assertRaises(Blocked):
                self.trial.start({**self.auth, key: 'bad'})
        with self.assertRaises(Blocked): self.trial.start({**self.auth, 'attempt': 99, 'expires_at': 0})
        self.assertEqual(self.seen, [])


class APIAdapterTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.store = Store(self.root/'state.sqlite3', config_path=config(self.root))
        self.cfg = enabled_fixture(self.store)

    def test_32000_output_and_reasoning_effort_are_sent(self):
        self.cfg['pilot_cost_review'].update(max_output_tokens=32000, reasoning_effort='xhigh')
        payload = DockerCodexBuilder(self.cfg).request(bottle_input())
        self.assertEqual(payload['max_output_tokens'], 32000)
        self.assertEqual(payload['reasoning'], {'effort': 'xhigh'})
        for changes in ({'max_output_tokens': 32001}, {'max_output_tokens': True},
                        {'reasoning_effort': 'arbitrary'}, {'reasoning_effort': None}):
            cfg = copy.deepcopy(self.cfg)
            cfg['pilot_cost_review'].update(changes)
            with self.subTest(changes=changes), self.assertRaises(Blocked):
                DockerCodexBuilder(cfg).request(bottle_input())

    def test_worst_case_uses_exact_serialized_bytes_and_boundary(self):
        review = self.cfg['pilot_cost_review']
        payload = DockerCodexBuilder(self.cfg).request({'fiction': 'ñ漢'})
        cost = token_cost(review, len(request_bytes(payload)), payload['max_output_tokens'])
        review['max_call_usd'] = cost
        self.assertEqual(DockerCodexBuilder(self.cfg).request({'fiction': 'ñ漢'}), payload)
        from factory2.budget import units
        lower = units(cost) - 1
        review['max_call_usd'] = f'{lower // 1000000}.{lower % 1000000:06d}'
        with self.assertRaisesRegex(Blocked, 'WORST_CASE_EXCEEDS_CAP'):
            DockerCodexBuilder(self.cfg).request({'fiction': 'ñ漢'})

    def test_missing_or_invalid_prices_block_without_transport(self):
        for key in ('input_usd_per_million', 'output_usd_per_million'):
            for invalid in (None, '0', '-1', 'NaN', 1.5):
                cfg = copy.deepcopy(self.cfg)
                cfg['pilot_cost_review'][key] = invalid
                with self.subTest(key=key, invalid=invalid), self.assertRaises(Blocked):
                    DockerCodexBuilder(cfg).request(bottle_input())

    def test_usage_cost_reasoning_not_double_counted_and_no_free_text(self):
        item = response()
        item['usage']['secret_text'] = 'FICTICIO_NO_GUARDAR'
        record = usage_record(item, self.cfg['pilot_cost_review'])
        self.assertEqual(record['usage'], {'input_tokens': 100, 'output_tokens': 20, 'reasoning_tokens': 5})
        self.assertEqual(record['calculated_cost_usd'], '0.000140')
        self.assertNotIn('FICTICIO_NO_GUARDAR', canonical(record))
        self.assertEqual(token_cost({'input_usd_per_million': '0.000001',
                                     'output_usd_per_million': '0.000001'}, 1, 0), '0.000001')

    def test_incomplete_response_keeps_numeric_usage_but_not_proposal(self):
        item = response()
        item['status'] = 'incomplete'
        adapter = DockerCodexBuilder(self.cfg, transport=lambda _: item)
        with self.assertRaises(Blocked): adapter.generate(bottle_input())
        self.assertEqual(adapter.last_usage['calculated_cost_usd'], '0.000140')

    def test_malformed_usage_is_rejected_and_stale_usage_cleared(self):
        item = response()
        adapter = DockerCodexBuilder(self.cfg, transport=lambda _: item)
        adapter.generate(bottle_input())
        for bad in (None, {}, {'input_tokens': True, 'output_tokens': 1,
                              'output_tokens_details': {'reasoning_tokens': 0}},
                    {'input_tokens': 1, 'output_tokens': 1, 'output_tokens_details': {'reasoning_tokens': 2}}):
            item['usage'] = bad
            with self.subTest(bad=bad), self.assertRaises(Blocked): adapter.generate(bottle_input())
            self.assertIsNone(adapter.last_usage)

    def test_api_contract_has_no_tools_or_storage_and_validates_response(self):
        def fake(payload):
            self.assertEqual(payload['tools'], [])
            self.assertFalse(payload['store'])
            self.assertEqual(payload['tool_choice'], 'none')
            self.assertEqual(payload['text']['format']['type'], 'json_schema')
            return response()
        with patch('factory2.codex_adapter.os.environ.get', side_effect=AssertionError('No credentials')):
            self.assertEqual(DockerCodexBuilder(self.cfg, transport=fake).generate(bottle_input()), PROPOSAL)

    def test_invalid_incomplete_tool_or_secret_output_is_rejected(self):
        cases = [None, {'status': 'incomplete'}, {'status': 'completed', 'output': [{'type': 'function_call'}]},
                 response({'summary_es': 'github_pat_'+'x'*40, 'edits': PROPOSAL['edits']}),
                 response({'summary_es': 'FICTICIO', 'edits': [{'path': '../escape.py', 'content': 'x'}]})]
        for item in cases:
            with self.subTest(item=type(item).__name__), self.assertRaisesRegex(Blocked, 'INVALID_OR_UNCERTAIN'):
                DockerCodexBuilder(self.cfg, transport=lambda _: item).generate(bottle_input())

    def test_materialization_command_is_offline_and_pinned(self):
        commands = []
        def process(command, **_):
            commands.append(command)
            if command[1] == 'rm': return 0, ''
            self.assertIn(PYTHON_IMAGE, command)
            for value in ('--network=none', '--read-only', '--pull=never', '--user=65534:65534',
                          '--cap-drop=ALL', '--security-opt=no-new-privileges'):
                self.assertIn(value, command)
            mounts = [command[i+1] for i, value in enumerate(command) if value == '--mount']
            src = Path(mounts[0].split('source=')[1].split(',target=')[0])
            dst = Path(mounts[1].split('source=')[1].split(',target=')[0])
            materialize(json.loads((src/'proposal.json').read_text()), dst)
            return 0, 'BUILT\n'
        DockerCodexBuilder(self.cfg, process=process).materialize(PROPOSAL, self.root/'candidate')
        self.assertEqual(len(commands), 2)
        self.assertEqual((self.root/'candidate/src/bottles.mjs').read_text(), PROPOSAL['edits'][0]['content'])

    def test_docker_process_boundary_uses_only_allowlisted_environment(self):
        from types import SimpleNamespace
        from factory2.runner import bounded_process
        def fake_process(command, **kwargs):
            allowed = {'PATH', 'SYSTEMROOT', 'WINDIR', 'TEMP', 'TMP', 'PATHEXT', 'COMSPEC',
                       'PYTHONDONTWRITEBYTECODE', 'PYTHONIOENCODING'}
            self.assertTrue(set(k.upper() for k in kwargs['env']) <= allowed)
            self.assertNotIn('OPENAI_API_KEY', kwargs['env'])
            self.assertNotIn('HTTPS_PROXY', kwargs['env'])
            self.assertNotIn('NODE_OPTIONS', kwargs['env'])
            kwargs['stdout'].write(b'FICTICIO')
            return SimpleNamespace(returncode=0, poll=lambda: 0)
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'FICTICIO', 'HTTPS_PROXY': 'FICTICIO',
                                        'NODE_OPTIONS': 'FICTICIO'}), \
                patch('factory2.runner.subprocess.Popen', side_effect=fake_process):
            self.assertEqual(bounded_process(['FICTICIO_NO_EXECUTABLE']), (0, 'FICTICIO'))

    def test_worker_refuses_traversal_and_overwrite(self):
        materialize(PROPOSAL, self.root)
        with self.assertRaises(FileExistsError): materialize(PROPOSAL, self.root)
        with self.assertRaises(ValueError):
            materialize({'summary_es':'FICTICIO','edits':[{'path':'src/../escape.py','content':'x'}]}, self.root)

    def test_real_transport_error_does_not_expose_fixture_key_and_does_not_retry(self):
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'FICTICIO_NO_REVELAR'}), \
                patch('urllib.request.build_opener') as opener:
            opener.return_value.open.side_effect = RuntimeError('FICTICIO_NO_REVELAR')
            with self.assertRaisesRegex(Blocked, '^CODEX_RESPONSE_INVALID_OR_UNCERTAIN$'):
                ResponsesAPI()({'model': 'FICTICIO'})
            self.assertEqual(opener.return_value.open.call_count, 1)

    def test_prepared_config_keeps_execution_disabled(self):
        cfg = json.loads(disabled_repository_config(self.root).read_text())
        for key in ('enabled', 'external_calls_enabled', 'erp_access_enabled', 'publication_enabled'):
            self.assertIs(cfg[key], False)
        self.assertEqual(cfg['pilot_model'], 'gpt-6.1-sol')
        self.assertEqual(cfg['pilot_cost_review']['reasoning_effort'], 'medium')
        self.assertEqual(cfg['pilot_cost_review']['max_output_tokens'], 32000)
        self.assertEqual(cfg['max_budget_usd_per_call'], '1.00')
        self.assertEqual(cfg['max_spend_per_execution'], '12.00')
        self.assertEqual(cfg['max_spend_total'], '13.00')
