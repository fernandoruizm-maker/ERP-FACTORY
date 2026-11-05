import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from factory.mvp.common import Blocked
from factory.mvp.queue import Queue
from factory.mvp.trial_monitor import tick


class TrialMonitorTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.q=Queue(Path(self.tmp.name)/'queue.db');self.job=self.q.enqueue('trial',{'demo':1})
        self.saved={'pr':{'number':123,'head_sha':'a'*40}}
        self.q.set(self.job,'WAITING_APPROVAL',self.saved)
        self.second=self.q.enqueue('second',{'demo':2})
        self.q.set(self.second,'CLOSED',{'pr':{'number':124,'head_sha':'b'*40}})
        self.config={'trial_jobs':[self.job,self.second],'trial_prs':[123,124]};self.calls=[];self.statuses=[];self.draft=True
        owner=self
        class GH:
            prefix='/repos/owner/repo'
            def get(self,path):
                if path.endswith('/status'):return {'statuses':[{'context':'factory/human-approval','state':'success'}]}
                return {'state':'open','draft':owner.draft,'merged':False,'head':{'sha':'a'*40}}
            def status(self,*args):owner.statuses.append(args)
            def request(self,method,path,body):
                owner.calls.append((method,path,body));return {'state':'closed','merged':False}
        self.gh=GH()

    def test_pending_never_closes(self):
        with patch('factory.mvp.trial_monitor.refresh_roles',return_value='WAITING_APPROVAL'):
            result=tick(self.config,self.gh,self.q)
        self.assertEqual(self.calls,[]);self.assertFalse(result[0]['genuine_approval_seen'])

    def test_approved_trial_only_closes_without_merge(self):
        with patch('factory.mvp.trial_monitor.refresh_roles',return_value='APPROVED'):
            result=tick(self.config,self.gh,self.q)
        self.assertEqual(result[0]['state'],'CLOSED')
        self.assertEqual(self.calls,[('PATCH','/repos/owner/repo/pulls/123',{'state':'closed'})])
        self.assertIn('verified_statuses',json.loads(self.q.get(self.job)['checkpoint']))

    def test_unlisted_pr_cannot_be_touched(self):
        self.config['trial_prs']=[999]
        with self.assertRaises(Blocked):tick(self.config,self.gh,self.q)
        self.assertEqual(self.calls,[])

    def test_duplicate_jobs_rejected_before_writes(self):
        self.config['trial_jobs']=[self.job,self.job]
        with self.assertRaises(Blocked):tick(self.config,self.gh,self.q)
        self.assertEqual(self.calls,[])

    def test_two_jobs_cannot_point_to_same_pr(self):
        self.q.set(self.second,'CLOSED',self.saved)
        with self.assertRaises(Blocked):tick(self.config,self.gh,self.q)
        self.assertEqual(self.calls,[])

    def test_concurrent_ready_state_revokes_and_does_not_close(self):
        self.draft=False
        with patch('factory.mvp.trial_monitor.refresh_roles',return_value='APPROVED'):
            result=tick(self.config,self.gh,self.q)
        self.assertEqual(result[0]['state'],'BLOCKED')
        self.assertFalse(result[0]['genuine_approval_seen']);self.assertEqual(self.calls,[])
        self.assertEqual([s[2] for s in self.statuses],['failure','pending'])
