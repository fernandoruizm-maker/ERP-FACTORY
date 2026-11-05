import copy
import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

from factory2.core import Blocked, canonical, digest
from factory2.manual_review import CLEAR, REVIEWER, validate_document
from factory2.state import Store
from tests.operation_fixtures import config, coordinator

ROOT = Path(__file__).resolve().parents[1]
SOURCE = 'a'*40


def document(record):
    return ('# Revision FICTICIA para pruebas, nunca Claude real\n\n```json\n'
            +canonical(record)+'\n```\n').encode('utf-8')


class ManualReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.folder=self.root/'docs/revisiones'
        self.folder.mkdir(parents=True)
        self.store=Store(self.root/'state.sqlite3',config_path=config(self.root),
                         coordinator=coordinator(self.root),reviews_directory=self.folder)
        self.factory=digest('fabrica-ficticia')
        self.product=digest('producto-ficticio')
        self.version=self.store.put_task('T',{'artifact_digest':self.product})
        self.record={'schema_version':1,'pr':'LOCAL:pr-ficticia','base_sha':'b'*40,'reviewed_sha':SOURCE,
            'scope':{'mode':'CAMBIOS_PR','files':['src/ficticio.py'],'diff':'FICTICIO: base..revisado, solo src/ficticio.py'},
            'reviewer':REVIEWER,'findings':[],'conclusion':CLEAR,'date':'2026-11-05'}
        self.imported=self.add_record(self.record,'first')

    def add_record(self,record,name):
        path=self.folder/(name+'.local.md')
        path.write_bytes(document(record))
        return self.store.import_manual_review(path)

    def accept(self,role,**changes):
        args={'manual_review_id':self.imported['review_id'],'source_sha':SOURCE,
              'factory_digest':self.factory,'expires_at':time.time()+600}
        args.update(changes)
        return self.store.accept('T',self.version,'persona-a' if role=='business' else 'persona-b',role,**args)

    def outcome(self,**changes):
        args={'manual_review_id':self.imported['review_id'],'source_sha':SOURCE,'factory_digest':self.factory}
        args.update(changes)
        return self.store.gate('T',self.version,self.product,
            {'artifact_digest':self.product,'verdict':'PASS','summary_es':'FICTICIO','findings':[]},
            [{'status':'PASS','test_count':1,'artifact_digest':self.product}],**args)

    def test_matching_record_and_two_declarations_ready_but_never_authenticated_or_published(self):
        with patch('factory2.review_import.private_contract',side_effect=AssertionError('No private reviewer needed')):
            self.assertFalse(self.accept('business')['identity_authenticated'])
            self.accept('accounting')
            result=self.outcome()
        self.assertEqual(result['status'],'READY_FOR_MANUAL_REVIEW')
        self.assertEqual(result['reasons'],[])
        self.assertFalse(result['provenance_authenticated'])
        self.assertFalse(result['publication_allowed'])
        self.assertFalse(result['human_acceptances_authenticated'])
        self.assertEqual(result['review_mode'],'MANUAL_CHAT')
        self.assertEqual(self.imported['human_approvals'],0)

    def test_record_for_another_exact_sha_blocks(self):
        self.accept('business'); self.accept('accounting')
        self.assertEqual(self.outcome(source_sha='c'*40)['status'],'BLOCKED')
        with self.assertRaisesRegex(Blocked,'VERSION_MISMATCH'):
            self.accept('business',source_sha='c'*40)

    def test_corrections_conclusion_cannot_be_accepted_or_pass_gate(self):
        record={**self.record,'conclusion':'CORREGIR'}
        review=self.add_record(record,'corregir')
        self.assertEqual(self.outcome(manual_review_id=review['review_id'])['status'],'BLOCKED')
        with self.assertRaisesRegex(Blocked,'REQUIRES_CORRECTION'):
            self.accept('business',manual_review_id=review['review_id'])

    def test_missing_accounting_acceptance_blocks(self):
        self.accept('business')
        result=self.outcome()
        self.assertEqual(result['status'],'BLOCKED')
        self.assertIn('HUMAN_ACCEPTANCES_MISSING_STALE_OR_EXPIRED',result['reasons'])

    def test_expired_acceptance_is_rechecked(self):
        self.accept('business'); self.accept('accounting')
        with patch('factory2.state.time.time',return_value=time.time()+1000):
            self.assertEqual(self.outcome()['status'],'BLOCKED')

    def test_old_technical_role_is_rejected_and_not_migrated(self):
        with self.assertRaisesRegex(Blocked,'ACCEPTANT_NOT_CONFIGURED'):
            self.accept('technical')
        self.accept('business'); self.accept('accounting')
        with self.store.connect() as db:
            db.execute("UPDATE acceptances_v2 SET role='technical' WHERE role='accounting'")
        self.assertEqual(self.outcome()['status'],'BLOCKED')
        cfg=self.store.config()
        cfg['human_approvers']['technical']=cfg['human_approvers'].pop('accounting')
        self.store.config_path.write_text(canonical(cfg))
        with self.assertRaises(Blocked): self.store.roster()

    def test_changed_review_invalidates_old_acceptances_even_at_same_source_sha(self):
        self.accept('business'); self.accept('accounting')
        changed=copy.deepcopy(self.record)
        changed['scope']['diff']='FICTICIO: alcance aclarado'
        review=self.add_record(changed,'second')
        self.assertEqual(self.outcome(manual_review_id=review['review_id'])['status'],'BLOCKED')

    def test_task_or_factory_change_invalidates_declarations(self):
        self.accept('business'); self.accept('accounting')
        self.assertEqual(self.outcome(factory_digest=digest('other'))['status'],'BLOCKED')
        self.store.put_task('T',{'artifact_digest':self.product,'changed':True})
        self.assertEqual(self.outcome()['status'],'BLOCKED')

    def test_manual_id_does_not_bypass_private_v2_path(self):
        self.accept('business'); self.accept('accounting')
        result=self.outcome(manual_review_id=None,factory_review=self.imported['review_id'])
        self.assertEqual(result['status'],'BLOCKED')
        self.assertIn('PRIVATE_FACTORY_REVIEW_INVALID',result['reasons'])
        self.assertIn('HUMAN_AUTHENTICATION_PENDING',result['reasons'])

    def test_two_review_paths_cannot_be_mixed(self):
        self.accept('business'); self.accept('accounting')
        self.assertEqual(self.outcome(factory_review='other')['status'],'BLOCKED')
        with self.assertRaisesRegex(Blocked,'REVIEW_PATH_AMBIGUOUS'):
            self.accept('business',review_id='other')

    def test_no_silent_replacement_or_duplicate_import(self):
        self.accept('business')
        with self.assertRaises(Blocked): self.accept('business')
        with self.assertRaisesRegex(Blocked,'ALREADY_IMPORTED'):
            self.store.import_manual_review(self.folder/'first.local.md')

    def test_modified_stored_document_fails_its_hash(self):
        self.accept('business'); self.accept('accounting')
        changed={**self.record,'pr':'LOCAL:otro-ficticio'}
        with self.store.connect() as db:
            db.execute('UPDATE manual_reviews SET document=?',(document(changed),))
        self.assertEqual(self.outcome()['status'],'BLOCKED')

    def test_outside_path_and_template_are_not_imported(self):
        outside=self.root/'outside.md'; outside.write_bytes(document(self.record))
        with self.assertRaises(Blocked): self.store.import_manual_review(outside)
        traversal=self.folder/'../../outside.md'
        with self.assertRaises(Blocked): self.store.import_manual_review(traversal)
        (self.folder/'PLANTILLA.md').write_bytes(document(self.record))
        with self.assertRaises(Blocked): self.store.import_manual_review(self.folder/'PLANTILLA.md')

    def test_invalid_reviewer_sha_date_and_ambiguous_documents_block(self):
        for changes in ({'reviewer':'Claude autenticado'},{'reviewed_sha':'a'*7},{'date':'2026-02-30'},
                        {'conclusion':'PASS'},{'schema_version':True}):
            with self.subTest(changes=changes),self.assertRaises(Blocked):
                validate_document(document({**self.record,**changes}))
        with self.assertRaises(Blocked): validate_document(document(self.record)*2)

    def test_secret_pattern_and_contradictory_findings_block(self):
        record=copy.deepcopy(self.record)
        record['scope']['diff']='github_pat_'+'x'*40
        with self.assertRaises(Blocked): validate_document(document(record))
        record=copy.deepcopy(self.record)
        record['findings']=[{'severity':'high','file':'src/ficticio.py','line':1,
                             'description':'FICTICIO','recommendation':'FICTICIO'}]
        with self.assertRaises(Blocked): validate_document(document(record))
        record['conclusion']='CORREGIR'
        self.assertEqual(validate_document(document(record))['conclusion'],'CORREGIR')

    def test_whole_factory_record_uses_same_version_bound_gate(self):
        record=copy.deepcopy(self.record); record['scope']['mode']='FABRICA_COMPLETA'
        self.imported=self.add_record(record,'whole')
        self.accept('business'); self.accept('accounting')
        self.assertEqual(self.outcome()['status'],'READY_FOR_MANUAL_REVIEW')


class ManualPolicyFilesTests(unittest.TestCase):
    def test_ruleset_requires_two_reviews_no_bypass_or_branch_exclusions(self):
        rule=json.loads((ROOT/'docs/github/ruleset-main.json').read_text(encoding='utf-8'))
        self.assertEqual(rule['target'],'branch')
        self.assertEqual(rule['enforcement'],'active')
        self.assertEqual(rule['bypass_actors'],[])
        self.assertEqual(rule['conditions'],{'ref_name':{'include':['refs/heads/main'],'exclude':[]}})
        rules={r['type']:r for r in rule['rules']}
        self.assertEqual(set(rules),{'deletion','non_fast_forward','pull_request'})
        params=rules['pull_request']['parameters']
        self.assertEqual(params['required_approving_review_count'],2)
        self.assertIs(params['dismiss_stale_reviews_on_push'],True)
        self.assertIs(params['required_review_thread_resolution'],True)
        self.assertIs(params['require_last_push_approval'],True)

    def test_declared_roles_future_caps_and_parked_blockers(self):
        cfg=json.loads((ROOT/'config.json').read_text())
        self.assertEqual(set(cfg['human_approvers']),{'business','accounting'})
        self.assertEqual(cfg['human_approvers']['business']['id'],'342326625')
        self.assertEqual(cfg['human_approvers']['accounting']['id'],'352290329')
        for flag in ('enabled','external_calls_enabled','erp_access_enabled','publication_enabled'):
            self.assertIs(cfg[flag],False)
        for config_path in ('config.json','ERP-FACTORY-revision/policy.json'):
            data=json.loads((ROOT/config_path).read_text())
            self.assertEqual(data['automatic_review_status'],'PARKED')
            self.assertEqual(data['budget_currency'],'USD')
            self.assertEqual(data['max_budget_usd_per_call'],'1.00')
            self.assertEqual(data['max_spend_per_execution'],'12.00')
            self.assertEqual(data['max_spend_total'],'13.00')
        policy=json.loads((ROOT/'ERP-FACTORY-revision/policy.json').read_text())
        self.assertIs(policy['execution_enabled'],False)
        self.assertEqual(policy['cumulative_strategy'],'manual_authorization')
        job=json.loads((ROOT/'ERP-FACTORY-revision/.github/workflows/review.yml').read_text())['jobs']['review']
        self.assertIn('false &&',job['if'])
        self.assertEqual(job['env']['TRUSTED_REVIEWER_SHA'],'0'*40)
        self.assertEqual(job['steps'][0]['with']['ref'],'0'*40)


if __name__=='__main__':
    unittest.main()
