import json
import os
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch
from concurrent.futures import ThreadPoolExecutor

from factory2.core import Blocked, compare, digest, discover, file_digest, validate_edits, validate_review
from factory2.providers import ClaudeReviewer, CodexBuilder, Permit, gate, NoRedirect
from factory2.runner import DockerRunner, assess, test_command
from factory2.state import Store
from factory2.workflow import prepare, stage

ROOT = Path(__file__).resolve().parent.parent
BRIEF = json.loads((ROOT / 'fixtures/cliente.json').read_text(encoding='utf-8'))


class DiscoveryTests(unittest.TestCase):
    def test_missing_questions_never_marks_scope_approved(self):
        result = discover({})
        self.assertEqual(result['status'], 'NEEDS_INPUT')
        self.assertEqual(len(result['questions']), 6)
        self.assertFalse(result['approved'])

    def test_complete_fixture_still_requires_scope_review(self):
        result = prepare(BRIEF)
        self.assertEqual(result['discovery']['status'], 'READY_FOR_SCOPE_REVIEW')
        self.assertFalse(result['scope_approved'])
        self.assertTrue(all(r['decision'] == 'PENDIENTE' for r in result['comparison']['rows']))

    def test_duplicate_requirements_rejected(self):
        with self.assertRaises(Blocked): discover({**BRIEF, 'requirements': [BRIEF['requirements'][0]] * 2})

    def test_evidence_requires_authorization_and_hash(self):
        with tempfile.TemporaryDirectory() as temp:
            file = Path(temp) / 'capability.txt'
            file.write_text('Capacidad ficticia inspeccionada por operador.', encoding='utf-8')
            catalog = {'base': 'FICTICIA', 'synthetic': True, 'capabilities': [{
                'requirement': 'BOT-01', 'decision': 'ADAPTAR', 'reason': 'Ensayo documentado',
                'evidence': [{'path': 'capability.txt', 'sha256': file_digest(file), 'supports': 'Solicitud de salida'}]}]}
            self.assertEqual(compare(BRIEF, catalog, evidence_root=temp)['rows'][0]['decision'], 'PENDIENTE')
            self.assertEqual(compare(BRIEF, catalog, evidence_root=temp, authorized=True)['rows'][0]['decision'], 'ADAPTAR')
            file.write_text('Cambiado', encoding='utf-8')
            self.assertEqual(compare(BRIEF, catalog, evidence_root=temp, authorized=True)['rows'][0]['decision'], 'PENDIENTE')

    def test_evidence_cannot_escape_scope(self):
        catalog = {'capabilities': [{'requirement':'BOT-01', 'decision':'REUTILIZAR', 'reason':'x',
                   'evidence':[{'path':'../outside', 'sha256':'0'*64, 'supports':'x'}]}]}
        with tempfile.TemporaryDirectory() as temp:
            self.assertEqual(compare(BRIEF, catalog, evidence_root=temp, authorized=True)['rows'][0]['decision'], 'PENDIENTE')


class StateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.store = Store(Path(self.temp.name) / 'state.sqlite3')
        self.artifact = {'src/demo.py': 'print(1)'}
        self.artifact_hash = digest(self.artifact)
        self.version = self.store.put_task('T1', {'brief': BRIEF, 'artifact_digest': self.artifact_hash})

    def test_two_distinct_people_and_version_bound(self):
        self.store.accept('T1', self.version, 'persona-a', 'business')
        with self.assertRaises(Blocked): self.store.accept('T1', self.version, 'PERSONA-A', 'technical')
        self.store.accept('T1', self.version, 'persona-b', 'technical')
        review = {'artifact_digest':self.artifact_hash, 'verdict':'PASS', 'summary_es':'Sin hallazgos en ensayo', 'findings':[]}
        tests = [{'status':'PASS','test_count':3,'artifact_digest':self.artifact_hash}]
        factory_hash=digest('factory-version')
        factory_review={**review,'artifact_digest':factory_hash}
        self.assertEqual(self.store.gate('T1',self.version,self.artifact_hash,review,tests,
                         factory_digest=factory_hash,factory_review=factory_review)['status'], 'READY_FOR_MANUAL_REVIEW')
        self.assertFalse(self.store.gate('T1',self.version,self.artifact_hash,review,tests)['publication_allowed'])
        self.store.put_task('T1', {'brief': BRIEF, 'artifact_digest': digest('changed')})
        self.assertEqual(self.store.gate('T1',self.version,self.artifact_hash,review,tests)['status'], 'BLOCKED')

    def test_factory_review_is_required_and_bound_to_its_version(self):
        self.store.accept('T1',self.version,'a','business'); self.store.accept('T1',self.version,'b','technical')
        review={'artifact_digest':self.artifact_hash,'verdict':'PASS','summary_es':'Ensayo','findings':[]}
        tests=[{'status':'PASS','test_count':1,'artifact_digest':self.artifact_hash}]
        for factory_review in (None,{**review,'artifact_digest':'outdated'}):
            result=self.store.gate('T1',self.version,self.artifact_hash,review,tests,
                                   factory_digest='current-factory',factory_review=factory_review)
            self.assertEqual(result['status'],'BLOCKED')

    def test_artifact_change_invalidates_acceptance_even_with_new_review(self):
        self.store.accept('T1',self.version,'a','business'); self.store.accept('T1',self.version,'b','technical')
        newhash = digest('different-code')
        review = {'artifact_digest':newhash,'verdict':'PASS','summary_es':'Ensayo','findings':[]}
        result = self.store.gate('T1',self.version,newhash,review,[{'status':'PASS','test_count':1,'artifact_digest':newhash}])
        self.assertEqual(result['status'],'BLOCKED')

    def test_missing_or_blocked_review_and_zero_tests_fail(self):
        self.store.accept('T1',self.version,'a','business'); self.store.accept('T1',self.version,'b','technical')
        review = {'artifact_digest':self.artifact_hash,'verdict':'BLOCK','summary_es':'Falta prueba','findings':[]}
        for r in (None, review):
            self.assertEqual(self.store.gate('T1',self.version,self.artifact_hash,r,[])['status'],'BLOCKED')

    def test_recovery_never_resends_uncertain_call(self):
        self.store.reserve_call('C1','T1','claude','abc',max_calls=2,output_limit=100)
        reopened = Store(self.store.path)
        self.assertEqual(reopened.recover()['uncertain_calls'],1)
        self.assertEqual(reopened.recover()['uncertain_calls'],0)
        with self.assertRaises(Blocked): reopened.reserve_call('C1','T1','claude','abc',max_calls=2,output_limit=100)
        self.assertEqual(reopened.summary()['uncertain'],1)

    def test_atomic_budget_with_concurrent_reservations(self):
        def reserve(i):
            try:
                self.store.reserve_call(str(i),'T1','claude','hash',max_calls=2,output_limit=100)
                return True
            except Blocked: return False
        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(reserve,range(8)))
        self.assertEqual(sum(results),2)
        self.assertEqual(self.store.summary()['calls'],2)


class ProviderTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.store = Store(Path(self.temp.name)/'s.sqlite3'); self.store.put_task('T',BRIEF)
        self.cfg = {'external_calls_enabled':True,'max_calls_per_task':2,'max_output_tokens':100,
                    'claude_model':'test-model-NOT-REAL','timeout_seconds':1}
        self.artifact = {'synthetic':'fixture'}
        self.payload = {'artifact':self.artifact,'artifact_digest':digest(self.artifact),'tests':[]}
        self.permit = Permit('claude',digest(self.payload),time.time()+60,'operador-de-ensayo','call1')
        self.review = {'artifact_digest':digest(self.artifact),'verdict':'PASS','summary_es':'Respuesta simulada para prueba de contrato','findings':[]}

    def test_disabled_provider_never_invokes_transport_or_reads_key(self):
        with patch('factory2.providers.os.environ.get',side_effect=AssertionError('no key read')):
            with self.assertRaises(Blocked): ClaudeReviewer({},self.store,lambda *_:self.fail()).review('T',self.artifact,[],self.permit)
        self.assertEqual(self.store.summary()['calls'],0)

    def test_permit_binds_provider_content_and_expiry(self):
        for permit in (Permit('codex',digest(self.payload),time.time()+60,'a','x'),
                       Permit('claude','wrong',time.time()+60,'a','x'),
                       Permit('claude',digest(self.payload),float('nan'),'a','x'),
                       Permit('claude',digest(self.payload),0,'a','x')):
            with self.assertRaises(Blocked): gate(self.cfg,permit,'claude',self.payload)

    def test_missing_credential_never_calls(self):
        with patch.dict(os.environ,{},clear=True):
            with self.assertRaises(Blocked): ClaudeReviewer(self.cfg,self.store,lambda *_:self.fail()).review('T',self.artifact,[],self.permit)
        self.assertEqual(self.store.summary()['calls'],0)

    def test_valid_simulated_contract_no_tools_and_output_bound(self):
        def transport(body,key,timeout):
            self.assertNotIn('tools',body); self.assertEqual(body['max_tokens'],100)
            return {'stop_reason':'end_turn','content':[{'type':'text','text':json.dumps(self.review)}]}
        with patch.dict(os.environ,{'ANTHROPIC_API_KEY':'TEST-ONLY-NOT-A-CREDENTIAL'}):
            self.assertEqual(ClaudeReviewer(self.cfg,self.store,transport).review('T',self.artifact,[],self.permit),self.review)
        self.assertEqual(self.store.summary()['calls'],1)

    def test_timeout_is_unknown_and_consumes_budget_without_retry(self):
        def transport(*_): raise TimeoutError('do-not-publish-this-body')
        with patch.dict(os.environ,{'ANTHROPIC_API_KEY':'TEST-ONLY-NOT-A-CREDENTIAL'}):
            with self.assertRaises(Blocked) as caught: ClaudeReviewer(self.cfg,self.store,transport).review('T',self.artifact,[],self.permit)
        self.assertNotIn('do-not-publish',str(caught.exception))
        self.assertEqual(self.store.summary()['uncertain'],1)

    def test_truncation_rejected(self):
        with patch.dict(os.environ,{'ANTHROPIC_API_KEY':'TEST-ONLY-NOT-A-CREDENTIAL'}):
            with self.assertRaises(Blocked):
                ClaudeReviewer(self.cfg,self.store,lambda *_:{'stop_reason':'max_tokens'}).review('T',self.artifact,[],self.permit)

    def test_wrong_artifact_and_severe_pass_rejected(self):
        with self.assertRaises(Blocked): validate_review(self.review,'another')
        with self.assertRaises(Blocked): validate_review({**self.review,'findings':[{'severity':'critical','detail_es':'Fallo grave'}]},digest(self.artifact))

    def test_redirect_does_not_forward_key(self):
        with self.assertRaises(Blocked): NoRedirect().redirect_request(None,None,302,'',{},'https://invalid.example')

    def test_codex_proposes_only_allowed_files(self):
        proposal={'summary_es':'Ensayo','edits':[{'path':'src/demo.py','content':'print(1)'}]}
        class FakeAgent:
            def ask(inner,*_): return proposal
        payload={'brief':BRIEF}
        permit=Permit('codex',digest(payload),time.time()+60,'operador-de-ensayo','codex1')
        self.assertEqual(CodexBuilder(self.cfg,self.store,FakeAgent()).build('T',payload,permit),proposal)


class RunnerAndProposalTests(unittest.TestCase):
    def test_rejects_configuration_tests_and_path_escape(self):
        for path in ('../src/a.py','src/../../config.json','tests/test_a.py','config.json','src/.env','src/a.py/../b.py'):
            with self.assertRaises(Blocked): validate_edits({'summary_es':'Ensayo','edits':[{'path':path,'content':'x'}]})

    def test_stage_never_overwrites(self):
        with tempfile.TemporaryDirectory() as temp:
            proposal={'summary_es':'Ensayo','edits':[{'path':'src/a.py','content':'x=1'}]}
            stage(temp,BRIEF,proposal)
            with self.assertRaises(Blocked): stage(temp,BRIEF,proposal)

    def test_docker_has_no_network_or_credentials_and_pinned_image(self):
        with tempfile.TemporaryDirectory() as temp:
            args=DockerRunner().command(temp,'python@sha256:'+'a'*64,'python',['tests/test_a.py'],'rdc2-test-fixture')
            for flag in ('--network=none','--read-only','--pull=never','--cap-drop=ALL','--security-opt=no-new-privileges'):
                self.assertIn(flag,args)
            self.assertNotIn('--privileged',args)
            with self.assertRaises(Blocked): DockerRunner().command(temp,'python:latest','python',['tests/test_a.py'],'x')

    def test_no_tests_skips_and_failed_process_never_green(self):
        self.assertEqual(assess('python',0,'Ran 0 tests in 0s\nOK')['status'],'FAIL')
        self.assertEqual(assess('python',0,'Ran 2 tests in 0s\nOK (skipped=1)')['status'],'FAIL')
        self.assertEqual(assess('javascript',1,'# tests 1\n# fail 0\n# skipped 0\n# cancelled 0')['status'],'FAIL')

    def test_profiles_cannot_inject_shell_flags(self):
        for profile,files in [('javascript',['--eval=bad']),('typescript',['tests/../../bad.test.ts']),('python',['tests/test_a.py;bad'])]:
            with self.assertRaises(Blocked): test_command(profile,files)


if __name__ == '__main__': unittest.main()
