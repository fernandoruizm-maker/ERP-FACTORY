"""Local fictional contracts only. No provider, real ledger, Docker or credentials."""
import copy
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

from factory2.core import Blocked, canonical, digest
from factory2.encargos import ROOT, load_encargo, attempt_ids
from factory2.orchestrator import PilotTrial
from factory2.codex_adapter import NODE_IMAGE, PYTHON_IMAGE
from factory2.runner import test_command, bounded_process, assess
from tests import test_pilot_trial as trials
from tests.operation_fixtures import arm_fixture


class ContractTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name) / 'encargos'
        shutil.copytree(ROOT, self.root)
        self.folder = self.root / 'botellas'

    def write(self, file, obj):
        (self.folder / file).write_text(canonical(obj), encoding='utf-8')

    def test_both_profiles_and_fixed_bottle_tests(self):
        botellas = load_encargo('botellas', self.root)
        caja = load_encargo('caja-chica', self.root)
        self.assertEqual((botellas['profile'], botellas['expected_tests']), ('javascript', 7))
        self.assertEqual((caja['profile'], caja['expected_tests']), ('python', 8))
        original = (ROOT.parent / 'pilot-js/tests/bottles.test.mjs').read_text(encoding='utf-8')
        self.assertEqual(botellas['trusted_tests']['tests/bottles.test.mjs'], original)

    def test_names_paths_and_reserved_legacy_alias_rejected(self):
        for name in ('../botellas', '/botellas', 'A', 'caja/chica', 'bottles', 'con', 'x'*51, '', None):
            with self.subTest(name=name), self.assertRaisesRegex(Blocked, 'NAME_INVALID'):
                load_encargo(name, self.root)
        with self.assertRaisesRegex(Blocked, 'ENCARGO_MISSING'):
            load_encargo('inexistente', self.root)

    def test_requirements_are_closed_and_fictional(self):
        original = json.loads((self.folder/'requisitos.json').read_text(encoding='utf-8'))
        cases = [{**original, 'synthetic':False}, {**original, 'schema_version':True},
                 {**original, 'unknown':'field'}, {**original, 'brief':{}},
                 {**original, 'brief':{**original['brief'], 'users':[]}},
                 {**original, 'brief':{**original['brief'], 'objective':' '}},
                 {**original, 'brief':{**original['brief'], 'requirements':[original['brief']['requirements'][0]]*2}}]
        for item in cases:
            self.write('requisitos.json', item)
            with self.subTest(item=item), self.assertRaisesRegex(Blocked, 'REQUIREMENTS_INVALID'):
                load_encargo('botellas', self.root)

    def test_json_duplicates_nan_and_malformed_are_rejected(self):
        for raw in ('{"synthetic":true,"synthetic":false}', '{"synthetic":NaN}', '{'):
            (self.folder/'requisitos.json').write_text(raw)
            with self.subTest(raw=raw), self.assertRaisesRegex(Blocked, 'JSON_INVALID'):
                load_encargo('botellas', self.root)

    def test_output_list_is_closed_typed_unique_and_under_src(self):
        original = json.loads((self.folder/'salida.json').read_text())
        cases = [{'profile':'typescript'}, {'expected_tests':True}, {'expected_tests':0},
                 {'expected_tests':1001}, {'schema_version':False}, {'extra':1},
                 {'files':[]}, {'files':['tests/bottles.test.mjs']}, {'files':['src/../x.mjs']},
                 {'files':['src/a.mjs','src/A.mjs']}, {'files':['src/x.py']},
                 {'files':['src/con.mjs']}, {'files':['src/a//x.mjs']}, {'files':[None]}]
        for changes in cases:
            self.write('salida.json', {**original, **changes})
            with self.subTest(changes=changes), self.assertRaisesRegex(Blocked, 'OUTPUT_INVALID'):
                load_encargo('botellas', self.root)

    def test_missing_empty_wrong_profile_and_unclassified_files_block(self):
        path = self.folder/'tests/bottles.test.mjs'
        original = path.read_bytes()
        path.unlink()
        with self.assertRaisesRegex(Blocked, 'TESTS_INVALID'): load_encargo('botellas', self.root)
        path.write_bytes(b'')
        with self.assertRaisesRegex(Blocked, 'TESTS_INVALID'): load_encargo('botellas', self.root)
        path.write_bytes(original)
        wrong = self.folder/'tests/test_wrong.py'
        wrong.write_text('pass')
        with self.assertRaisesRegex(Blocked, 'TESTS_INVALID'): load_encargo('botellas', self.root)
        wrong.unlink()
        (self.folder/'unclassified.txt').write_text('FICTICIO')
        with self.assertRaisesRegex(Blocked, 'SCOPE_INVALID'): load_encargo('botellas', self.root)

    def test_symlink_and_junction_checks_fail_closed_without_following_links(self):
        target = self.folder/'tests/bottles.test.mjs'
        original = Path.is_symlink
        with patch.object(Path, 'is_symlink', lambda p: p == target or original(p)):
            with self.assertRaisesRegex(Blocked, 'PATH_UNSAFE'): load_encargo('botellas', self.root)
        if hasattr(Path, 'is_junction'):
            with patch.object(Path, 'is_junction', lambda p: p == self.folder):
                with self.assertRaisesRegex(Blocked, 'PATH_UNSAFE'): load_encargo('botellas', self.root)

    def test_context_digest_binds_requirements_tests_output_and_identity(self):
        baseline = digest(load_encargo('botellas', self.root))
        path = self.folder/'tests/bottles.test.mjs'
        path.write_bytes(path.read_bytes()+b'\n// FICTICIO cambio\n')
        self.assertNotEqual(digest(load_encargo('botellas', self.root)), baseline)
        before = digest(load_encargo('botellas', self.root))
        output = json.loads((self.folder/'salida.json').read_text())
        self.write('salida.json', {**output, 'expected_tests':8})
        self.assertNotEqual(digest(load_encargo('botellas', self.root)), before)
        copy_folder = self.root/'otro'
        shutil.copytree(self.folder, copy_folder)
        self.assertNotEqual(digest(load_encargo('otro', self.root)), digest(load_encargo('botellas', self.root)))
        before = digest(load_encargo('botellas', self.root))
        req = json.loads((self.folder/'requisitos.json').read_text(encoding='utf-8'))
        req['brief']['objective'] = 'Otro objetivo ficticio'
        self.write('requisitos.json', req)
        self.assertNotEqual(digest(load_encargo('botellas', self.root)), before)

    def test_content_size_and_fictitious_credential_pattern_block(self):
        path = self.folder/'tests/bottles.test.mjs'
        path.write_text('x'*100001)
        with self.assertRaisesRegex(Blocked, 'TESTS_INVALID'): load_encargo('botellas', self.root)
        path.write_text('# github_pat_' + 'a'*50)
        with self.assertRaisesRegex(Blocked, 'CONTENT_REJECTED'): load_encargo('botellas', self.root)


class JobTrialTests(unittest.TestCase):
    setUp = trials.TrialTests.setUp
    review = trials.TrialTests.review
    change_config = trials.TrialTests.change_config

    def use_job(self, name):
        self.trial.encargo = name
        self.auth.update(encargo=name, context_digest=digest(load_encargo(name)))
        arm_fixture(self.root, self.cfg, encargo=name)

    def test_python_job_flows_through_pinned_image_and_exact_fixed_tests(self):
        self.use_job('caja-chica')
        source = (Path(__file__).parent/'fixtures/caja_chica_reference.py').read_text(encoding='utf-8')
        self.generate = lambda _: {'summary_es':'FICTICIO', 'edits':[{'path':'src/caja_chica.py', 'content':source}]}
        seen = []
        def tester(directory, image, profile, files, artifact):
            seen.append((image, profile, files))
            command = test_command(profile, files, directory=directory)
            command[0] = sys.executable  # trusted local fixture, NOT Docker integration
            code, output = bounded_process(command, cwd=directory)
            result = assess(profile, code, output)
            self.assertEqual(result['test_count'], 8, output)
            self.assertEqual(result['status'], 'PASS', output)
            return {**result, 'artifact_digest':artifact, 'profile':profile}
        self.tester = tester
        data = self.trial.start(self.auth)
        self.assertEqual(data['status'], 'WAITING_FOR_MANUAL_REVIEW')
        self.assertEqual(self.trial.ID, 'caja-chica-1')
        self.assertEqual(seen, [(PYTHON_IMAGE, 'python', ['tests/test_caja_chica.py'])])
        self.assertEqual(data['evidence_mode'], 'SIMULATED')
        self.assertFalse(data['publication_allowed'])
        self.assertEqual((self.root/'work/caja-chica-1/tests/test_caja_chica.py').read_text(encoding='utf-8'),
                         load_encargo('caja-chica')['trusted_tests']['tests/test_caja_chica.py'])

    def test_botellas_uses_new_id_and_javascript_image(self):
        observed = []
        original = self.tester
        self.tester = lambda *args: (observed.append(args[1:4]) or original(*args))
        self.assertEqual(self.trial.start(self.auth)['status'], 'WAITING_FOR_MANUAL_REVIEW')
        self.assertEqual(self.trial.ID, 'botellas-1')
        self.assertEqual(observed, [(NODE_IMAGE, 'javascript', ['tests/bottles.test.mjs'])])

    def test_multiple_exact_output_files_can_arrive_in_any_order(self):
        local = self.root/'encargos'
        shutil.copytree(ROOT, local)
        manifest = local/'botellas/salida.json'
        output = json.loads(manifest.read_text())
        output['files'].append('src/support.mjs')
        manifest.write_text(canonical(output))
        self.trial.encargos_root = local
        self.auth['context_digest'] = digest(load_encargo('botellas', local))
        self.generate = lambda _: {'summary_es':'FICTICIO', 'edits':[
            {'path':'src/support.mjs', 'content':'export const fake = true;'}, *copy.deepcopy(trials.PROPOSAL['edits'])]}
        data = self.trial.start(self.auth)
        self.assertEqual(data['status'], 'WAITING_FOR_MANUAL_REVIEW')
        self.assertEqual(set(data['files']), {'src/bottles.mjs', 'src/support.mjs', 'tests/bottles.test.mjs'})

    def test_changed_operator_tests_invalidate_authorization_before_provider(self):
        local = self.root/'encargos'
        shutil.copytree(ROOT, local)
        self.trial.encargos_root = local
        path = local/'botellas/tests/bottles.test.mjs'
        path.write_bytes(path.read_bytes()+b'\n// FICTICIO cambio posterior\n')
        with self.assertRaisesRegex(Blocked, 'AUTHORIZATION_REQUIRED'):
            self.trial.start(self.auth)
        self.assertEqual(self.seen, [])
        self.assertEqual(self.store.budget.summary()['attempts'], 0)

    def test_cash_contract_detects_a_broken_daily_limit(self):
        source = (Path(__file__).parent/'fixtures/caja_chica_reference.py').read_text(encoding='utf-8')
        broken = source.replace("self.consumo(item['persona'], item['dia']) + item['monto_centavos'] > self.limite", 'False')
        self.assertNotEqual(source, broken)
        directory = self.root/'broken-reference'
        (directory/'src').mkdir(parents=True)
        (directory/'tests').mkdir()
        (directory/'src/caja_chica.py').write_text(broken, encoding='utf-8')
        contract = load_encargo('caja-chica')
        for name, text in contract['trusted_tests'].items():
            (directory/name).write_text(text, encoding='utf-8')
        command = test_command('python', list(contract['trusted_tests']), directory=directory)
        command[0] = sys.executable
        code, output = bounded_process(command, cwd=directory)
        self.assertEqual(assess('python', code, output)['status'], 'FAIL')
        self.assertIn('FAIL: test_revalida_tope_al_pagar', output)

    def test_provider_cannot_replace_fixed_tests_or_expand_output(self):
        for extra in ('tests/bottles.test.mjs', 'src/unapproved.mjs'):
            self.generate = lambda _, extra=extra: {'summary_es':'FICTICIO', 'edits':[
                {'path':'src/bottles.mjs', 'content':'FICTICIO'}, {'path':extra, 'content':'FICTICIO'}]}
            result = self.trial.start(self.auth)
            self.assertEqual(result['status'], 'BLOCKED')
            self.assertNotIn('docker-build-double', self.seen)
            self.auth['attempt'] += 1
            arm_fixture(self.root, self.cfg, attempt=self.auth['attempt'])
        self.assertEqual(self.store.budget.summary()['conservative_charge_units'], 2000000)

    def test_builder_double_cannot_mutate_the_trusted_context(self):
        original = load_encargo('botellas')['trusted_tests']['tests/bottles.test.mjs']
        def mutate(context):
            context['trusted_tests']['tests/bottles.test.mjs'] = 'FICTICIO_MODIFICADO'
            context['expected_tests'] = 1
            return copy.deepcopy(trials.PROPOSAL)
        self.generate = mutate
        self.assertEqual(self.trial.start(self.auth)['status'], 'WAITING_FOR_MANUAL_REVIEW')
        self.assertEqual((self.root/'work/botellas-1/tests/bottles.test.mjs').read_text(encoding='utf-8'), original)

    def test_wrong_test_count_blocks_before_manual_review(self):
        self.tester = lambda _, image, profile, files, artifact: {'status':'PASS', 'exit_code':0,
            'test_count':6, 'profile':profile, 'artifact_digest':artifact}
        result = self.trial.start(self.auth)
        self.assertEqual(result['reason_code'], 'PILOT_TESTS_FAILED')
        self.assertNotIn('candidate_sha', result)

    def test_authorization_of_another_job_stops_before_call(self):
        with self.assertRaisesRegex(Blocked, 'AUTHORIZATION_REQUIRED'):
            self.trial.start({**self.auth, 'encargo':'caja-chica'})
        self.assertEqual(self.seen, [])

    def test_old_bottles_history_can_be_read_without_rewriting(self):
        historic = {'attempt':2, 'status':'WAITING_FOR_MANUAL_REVIEW', 'legacy':'FICTICIO'}
        with self.store.connect() as db:
            db.execute('INSERT INTO pilot_trials VALUES(?,?)', ('bottles-2', canonical(historic)))
        old = PilotTrial(self.store, self.root/'work', attempt=2, encargo='botellas')
        before = self.store.path.read_bytes()
        self.assertEqual(old.load(), historic)
        self.assertEqual(old.ID, 'bottles-2')
        self.assertEqual(self.store.path.read_bytes(), before)
        with self.assertRaisesRegex(Blocked, 'NO_RETRY'):
            self.trial.start({**self.auth, 'attempt':2})

    def test_blocked_legacy_attempt_allows_next_new_name_but_not_reuse(self):
        with self.store.connect() as db:
            db.execute('INSERT INTO pilot_trials VALUES(?,?)', ('bottles-1', canonical({'status':'BLOCKED'})))
        with self.assertRaisesRegex(Blocked, 'NO_RETRY'): self.trial.start(self.auth)
        arm_fixture(self.root, self.cfg, attempt=2)
        self.assertEqual(self.trial.start({**self.auth, 'attempt':2})['status'], 'WAITING_FOR_MANUAL_REVIEW')
        self.assertEqual(self.trial.ID, 'botellas-2')

    def test_conflicting_legacy_and_new_ids_block_loading(self):
        with self.store.connect() as db:
            for ident in attempt_ids('botellas', 1):
                db.execute('INSERT INTO pilot_trials VALUES(?,?)', (ident, canonical({'status':'BLOCKED'})))
        with self.assertRaisesRegex(Blocked, 'LEGACY_ID_CONFLICT'): self.trial.load()

    def test_legacy_candidate_keeps_review_acceptances_and_gate_working(self):
        data = self.trial.start(self.auth)
        # Synthetic old layout ONLY in this test's temporary database/directory.
        (self.root/'work/botellas-1').rename(self.root/'work/bottles-1')
        with self.store.connect() as db:
            tables = [r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")]
            for table in tables:
                columns = {r[1] for r in db.execute(f'PRAGMA table_info("{table}")')}
                for column in columns & {'id', 'task', 'execution'}:
                    db.execute(f'UPDATE "{table}" SET "{column}"=? WHERE "{column}"=?', ('bottles-1','botellas-1'))
            data.pop('encargo')
            data.pop('context_digest')
            db.execute('UPDATE pilot_trials SET data=? WHERE id=?', (canonical(data), 'bottles-1'))
        legacy = PilotTrial(self.store, self.root/'work', encargo='botellas', attempt=1,
                            builder=self.trial.builder, tester=self.trial.tester,
                            head=self.trial.head, snapshotter=self.trial.snapshotter)
        path = self.review('legacy-product', trials.CANDIDATE, list(data['files']))
        self.assertEqual(legacy.attach_review(path)['status'], 'WAITING_FOR_ACCEPTANCES')
        import time
        legacy.accept('persona-a', 'business', time.time()+60)
        legacy.accept('persona-b', 'accounting', time.time()+60)
        self.assertEqual(legacy.gate()['status'], 'READY_FOR_MANUAL_REVIEW')
        self.assertFalse(legacy.gate()['publication_allowed'])

    def test_independent_job_numbering_does_not_reset_shared_budget(self):
        with self.store.connect() as db:
            db.execute('INSERT INTO pilot_trials VALUES(?,?)', ('caja-chica-1', canonical({'status':'WAITING_FOR_MANUAL_REVIEW'})))
        self.store.budget.begin('historico', trials.SOURCE, self.cfg)
        self.store.budget.reserve('hist', 'historico', 'ficticio', 'hash', trials.SOURCE, '1', self.cfg)
        self.store.budget.finish('hist', 'COMPLETED')
        self.assertEqual(self.trial.start(self.auth)['status'], 'WAITING_FOR_MANUAL_REVIEW')
        self.assertEqual(self.store.budget.summary()['conservative_charge_units'], 1000140)
