import copy
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import tempfile
import unittest

from factory.mvp.common import digest
from factory.mvp.queue import Queue
from factory.memory import Brain
from factory.mvp.role_gate import refresh_roles
from test_dual_approval import POLICY, HEAD, review

class GateTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.q=Queue(self.root/'q.db')
        self.config={'repository':'owner/repo','base_branch':'main','approval_policy':copy.deepcopy(POLICY),
                     'brain_dir':str(Path(__file__).parents[1]/'brain')}
        self.pr={'number':1,'state':'open','merged':False,'draft':True,'title':'Test','body':'Informe',
                 'user':{'login':'factory[bot]','id':99,'type':'Bot'},'head':{'sha':HEAD},
                 'base':{'sha':'base','ref':'main','repo':{'full_name':'owner/repo'}}}
        self.now=datetime.now(timezone.utc)
        self.reviews=[review(10,'owner',1,when=self.now),review(20,'expert',2,roles=['CONTADOR'],when=self.now)]
        self.saved={'pr':{'number':1,'head_sha':HEAD},'base_sha':'base','config_sha':digest(self.config),
                    'brain_sha':Brain.load(self.config['brain_dir']).fingerprint,
                    'report_sha':digest({'title':'Test','body':'Informe'}),
                    'approval_ready_at':(self.now-timedelta(minutes=1)).isoformat(),
                    'changed_paths':['contabilidad/asientos.py'],'classification':{'level':'alto','roles':['CONTADOR']}}
        self.job=self.q.enqueue('one',{'operator':True});self.q.set(self.job,'WAITING_APPROVAL',self.saved)
        self.statuses=[];self.events=[];self.permission=True;self.raise_review=False
        owner=self
        class GitHub:
            def get(self,path):return copy.deepcopy(owner.pr)
            def base(self,branch):return 'base'
            def governance(self,branch):pass
            def changed_paths(self,number):return list(owner.saved['changed_paths'])
            def issue_events(self,number):return copy.deepcopy(owner.events)
            def reviews(self,number):
                if owner.raise_review:raise RuntimeError('Unavailable')
                return copy.deepcopy(owner.reviews)
            def can_write(self,login):return owner.permission
            def status(self,*args):owner.statuses.append(args)
            def quality_passed(self,sha,login):return True
        self.gh=GitHub()

    def run_gate(self):return refresh_roles(self.config,self.gh,self.q,self.job)

    def test_two_correct_reviews_publish_success(self):
        self.assertEqual(self.run_gate(),'APPROVED');self.assertEqual(self.statuses[-1][2],'success')

    def test_one_review_publishes_pending(self):
        self.reviews=self.reviews[:1];self.assertEqual(self.run_gate(),'WAITING_APPROVAL')
        self.assertTrue(self.statuses)
        self.assertEqual(self.statuses[-1][2],'pending')

    def test_new_head_invalidates_both_checks(self):
        self.pr['head']['sha']='b'*40;self.assertEqual(self.run_gate(),'BLOCKED')
        self.assertEqual([s[2] for s in self.statuses],['failure','pending'])

    def test_report_or_target_edit_invalidates(self):
        for field in ['body','title','base']:
            with self.subTest(field=field):
                original=copy.deepcopy(self.pr)
                if field=='base':self.pr['base']['ref']='other'
                else:self.pr[field]='changed'
                self.q.set(self.job,'WAITING_APPROVAL',self.saved)
                self.assertEqual(self.run_gate(),'BLOCKED');self.pr=original

    def test_force_push_back_to_same_sha_is_not_reused(self):
        self.events=[{'event':'head_ref_force_pushed','created_at':self.now.isoformat()}]
        self.assertEqual(self.run_gate(),'BLOCKED')

    def test_role_derived_from_files_not_a_label(self):
        self.saved['classification']['roles']=['TECNICO'];self.q.set(self.job,'WAITING_APPROVAL',self.saved)
        self.assertEqual(self.run_gate(),'BLOCKED')

    def test_revoked_permission_revokes_existing_success(self):
        self.assertEqual(self.run_gate(),'APPROVED');self.permission=False
        self.assertEqual(self.run_gate(),'WAITING_APPROVAL');self.assertEqual(self.statuses[-1][2],'pending')

    def test_edited_review_body_invalidates_recorded_approval(self):
        self.assertEqual(self.run_gate(),'APPROVED');self.reviews[1]['body']+='\nchanged'
        self.assertEqual(self.run_gate(),'BLOCKED');self.assertEqual(self.statuses[-1][2],'pending')

    def test_api_error_removes_success_when_status_api_is_available(self):
        self.assertEqual(self.run_gate(),'APPROVED');self.raise_review=True
        self.assertEqual(self.run_gate(),'WAITING_APPROVAL');self.assertEqual(self.statuses[-1][2],'pending')

    def test_closed_examples_are_not_reopened_or_merged(self):
        self.pr.update(state='closed',merged=False)
        self.assertEqual(self.run_gate(),'CLOSED');self.assertEqual(self.statuses,[])

    def test_unrelated_public_review_edit_cannot_invalidate_evidence(self):
        self.reviews.append(review(30,'visitor',999,when=self.now))
        self.assertEqual(self.run_gate(),'APPROVED')
        self.reviews[-1]['body']='Edited unrelated review'
        self.assertEqual(self.run_gate(),'APPROVED')

    def test_trial_cannot_be_approved_after_leaving_draft(self):
        self.config['trial_prs']=[1,2];self.saved['config_sha']=digest(self.config)
        self.q.set(self.job,'WAITING_APPROVAL',self.saved);self.pr['draft']=False
        self.assertEqual(self.run_gate(),'BLOCKED')
        self.assertEqual([s[2] for s in self.statuses],['failure','pending'])

    def test_unexpected_trial_merge_is_a_violation_not_normal_completion(self):
        self.config['trial_prs']=[1,2];self.saved['config_sha']=digest(self.config)
        self.q.set(self.job,'WAITING_APPROVAL',self.saved);self.pr.update(state='closed',merged=True)
        self.assertEqual(self.run_gate(),'BLOCKED')
        self.assertIn('integration',json.loads(self.q.get(self.job)['checkpoint']))
