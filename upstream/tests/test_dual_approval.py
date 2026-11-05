"""Synthetic decisions exercise the gate; they are never submitted to GitHub."""
import copy
from datetime import datetime, timedelta, timezone
import unittest

from factory.mvp.dual_approval import classify, evaluate

NOW = datetime(2026, 11, 4, 12, 0, tzinfo=timezone.utc)
HEAD = 'a' * 40
POLICY = {'owner': {'login':'owner', 'id':1},
          'specialist': {'login':'expert', 'id':2, 'roles':['CONTADOR','TECNICO']},
          'factory_login':'factory[bot]', 'ttl_hours':24}

def review(ident, login, user_id, *, state='APPROVED', roles=(), sha=HEAD, when=NOW):
    return {'id':ident, 'state':state, 'user':{'login':login, 'id':user_id, 'type':'User'},
            'commit_id':sha, 'submitted_at':when.isoformat(),
            'body':'FACTORY-VERSION: '+sha+'\n'+'\n'.join('FACTORY-ROL '+r+': APRUEBO' for r in roles)}

class DualApprovalTests(unittest.TestCase):
    def setUp(self):
        self.policy = copy.deepcopy(POLICY)
        self.classification = classify(['contabilidad/asientos.py'])
        self.owner = review(10,'owner',1)
        self.expert = review(20,'expert',2,roles=['CONTADOR'])

    def assess(self, reviews=None, **kwargs):
        options = dict(classification=self.classification, head=HEAD,
                       author={'login':'factory[bot]','id':99}, now=NOW,
                       not_before=(NOW-timedelta(minutes=10)).isoformat(), can_write=lambda login:True)
        options.update(kwargs)
        return evaluate(self.policy, [self.owner,self.expert] if reviews is None else reviews, **options)

    def test_accounting_files_require_accountant(self):
        for p in ['contabilidad/asientos.py','impuestos/calculo.py','cierres/mes.py','finance/money.py']:
            with self.subTest(path=p):
                result=classify([p]);self.assertEqual(result['level'],'alto');self.assertIn('CONTADOR',result['roles'])

    def test_technical_and_control_plane_files_require_technician(self):
        for p in ['permissions/access.py','database/models.py','migrations/001.sql','storage/files.py',
                  'ai-factory/factory/mvp/approval.py','.github/workflows/check.yml','src/api.py']:
            with self.subTest(path=p):self.assertEqual(classify([p])['roles'],['TECNICO'])

    def test_mixed_paths_require_both_roles(self):
        self.assertEqual(classify(['contabilidad/asientos.py','database/models.py'])['roles'],['CONTADOR','TECNICO'])

    def test_low_risk_does_not_include_control_plane_markdown(self):
        self.assertEqual(classify(['docs/user-guide/ayuda.md'])['level'],'bajo')
        self.assertEqual(classify(['ai-factory/brain/stack.md'])['level'],'alto')

    def test_unknown_and_deleted_critical_paths_are_high(self):
        self.assertEqual(classify(['unknown/file.xyz'])['level'],'alto')
        self.assertIn('CONTADOR',classify(['docs/user-guide/ayuda.md','contabilidad/old.py'])['roles'])

    def test_both_authentic_approvals_pass_accounting(self):
        self.assertTrue(self.assess()['approved'])

    def test_technical_approval_passes_with_technical_role(self):
        self.classification=classify(['database/schema.py']);self.expert=review(20,'expert',2,roles=['TECNICO'])
        self.assertTrue(self.assess()['approved'])

    def test_owner_only_or_expert_only_or_none_blocks(self):
        for rs in [[],[self.owner],[self.expert]]:
            with self.subTest(reviews=rs):self.assertFalse(self.assess(rs)['approved'])

    def test_native_approval_needs_no_comment_for_each_role_or_mixed(self):
        for paths in [['contabilidad/asientos.py'], ['database/models.py'],
                      ['contabilidad/asientos.py','database/models.py']]:
            self.classification=classify(paths)
            for body in ['', 'Apruebo', 'contable', 'tecnico']:
                with self.subTest(paths=paths, body=body):
                    self.expert['body']=body
                    self.assertTrue(self.assess()['approved'])

    def test_blank_comment_is_not_formal_approval(self):
        self.expert.update(body='',state='COMMENTED')
        self.assertFalse(self.assess()['approved'])

    def test_blank_approval_preserves_all_identity_and_freshness_checks(self):
        self.expert['body']=''
        for actor in [0,1]:
            for field,value in [('commit_id','b'*40),('state','CHANGES_REQUESTED'),
                                ('submitted_at',(NOW-timedelta(days=2)).isoformat())]:
                rs=copy.deepcopy([self.owner,self.expert]);rs[actor][field]=value
                self.assertFalse(self.assess(rs)['approved'])
        self.assertFalse(self.assess([self.expert])['approved'])
        self.assertFalse(self.assess([self.owner])['approved'])
        self.assertFalse(self.assess(author={'login':'expert','id':2})['approved'])
        self.assertFalse(self.assess(can_write=lambda login:login!='expert')['approved'])

    def test_explicit_cannot_evaluate_blocks_even_after_an_approval(self):
        self.expert['submitted_at']=(NOW-timedelta(seconds=2)).isoformat()
        decline=review(30,'expert',2,state='COMMENT',when=NOW-timedelta(seconds=1))
        decline['body']='FACTORY-VERSION: '+HEAD+'\nFACTORY-ROL CONTADOR: NO PUEDO EVALUAR'
        self.assertFalse(self.assess([self.owner,self.expert,decline])['approved'])
        later=review(40,'expert',2,roles=['CONTADOR'])
        self.assertTrue(self.assess([self.owner,self.expert,decline,later])['approved'])

    def test_decline_one_of_mixed_roles_blocks(self):
        self.classification=classify(['contabilidad/asientos.py','database/models.py'])
        self.expert=review(20,'expert',2,roles=['CONTADOR'])
        self.expert['body']+='\nFACTORY-ROL TECNICO: NO PUEDO EVALUAR'
        self.assertFalse(self.assess()['approved'])

    def test_old_commit_owner_or_expert_blocks(self):
        for actor in ['owner','expert']:
            with self.subTest(actor=actor):
                rs=copy.deepcopy([self.owner,self.expert]);rs[0 if actor=='owner' else 1]['commit_id']='b'*40
                self.assertFalse(self.assess(rs)['approved'])

    def test_optional_comment_version_does_not_override_github_commit(self):
        self.expert['body']=self.expert['body'].replace(HEAD,'b'*40)
        self.assertTrue(self.assess()['approved'])

    def test_approval_before_last_candidate_change_blocks(self):
        for index in [0,1]:
            rs=copy.deepcopy([self.owner,self.expert]);rs[index]['submitted_at']=(NOW-timedelta(hours=1)).isoformat()
            self.assertFalse(self.assess(rs)['approved'])

    def test_future_or_expired_approval_blocks(self):
        for when in [NOW+timedelta(seconds=1),NOW-timedelta(days=2)]:
            rs=copy.deepcopy([self.owner,self.expert]);rs[1]['submitted_at']=when.isoformat()
            self.assertFalse(self.assess(rs,not_before=(NOW-timedelta(days=3)).isoformat())['approved'])

    def test_latest_dismissal_or_changes_requested_by_either_human_blocks(self):
        for index in [0,1]:
            for state in ['DISMISSED','CHANGES_REQUESTED']:
                with self.subTest(index=index,state=state):
                    changed=copy.deepcopy([self.owner,self.expert][index]);changed.update(id=30,state=state)
                    self.assertFalse(self.assess([self.owner,self.expert,changed])['approved'])

    def test_actual_author_cannot_be_specialist_or_owner(self):
        for author in [{'login':'EXPERT','id':2},{'login':'owner','id':1}]:
            self.assertFalse(self.assess(author=author)['approved'])

    def test_same_identity_cannot_fill_owner_and_specialist(self):
        self.policy['specialist'].update(login='owner',id=1)
        self.assertFalse(self.assess()['approved'])

    def test_bot_cannot_fill_specialist(self):
        self.expert['user']['type']='Bot';self.assertFalse(self.assess()['approved'])

    def test_identity_is_bound_to_id_not_only_name(self):
        self.expert['user']['id']=999;self.assertFalse(self.assess()['approved'])

    def test_login_case_is_normalized(self):
        self.expert['user']['login']='EXPERT';self.assertTrue(self.assess()['approved'])

    def test_permission_is_checked_for_both_humans(self):
        for login in ['owner','expert']:
            self.assertFalse(self.assess(can_write=lambda x:x!=login)['approved'])

    def test_missing_policy_or_bad_timestamp_blocks(self):
        self.policy={};self.assertFalse(self.assess()['approved'])
        self.policy=copy.deepcopy(POLICY);self.assertFalse(self.assess(not_before='unknown')['approved'])

    def test_low_risk_still_requires_owner(self):
        self.classification=classify(['docs/user-guide/ayuda.md'])
        self.assertFalse(self.assess([])['approved'])
        self.assertTrue(self.assess([self.owner])['approved'])

    def test_comment_without_formal_approval_is_insufficient(self):
        self.expert['state']='COMMENT';self.assertFalse(self.assess()['approved'])

    def test_optional_repeated_role_text_does_not_replace_formal_approval(self):
        self.expert['body']+='\nFACTORY-ROL CONTADOR: APRUEBO'
        self.assertTrue(self.assess()['approved'])

    def test_unconfigured_role_cannot_be_claimed(self):
        self.policy['specialist']['roles']=['TECNICO'];self.assertFalse(self.assess()['approved'])

    def test_old_draft_id_submitted_later_revokes_approval(self):
        self.expert['submitted_at']=(NOW-timedelta(minutes=1)).isoformat()
        for state in ['CHANGES_REQUESTED','COMMENT']:
            refusal=review(5,'expert',2,state=state,when=NOW)
            refusal['body']='NO PUEDO EVALUAR'
            self.assertFalse(self.assess([self.owner,self.expert,refusal])['approved'])

    def test_later_approval_uses_submission_time_not_id(self):
        self.expert['submitted_at']=(NOW-timedelta(minutes=2)).isoformat()
        refusal=review(30,'expert',2,state='CHANGES_REQUESTED',when=NOW-timedelta(minutes=1))
        later=review(5,'expert',2,roles=['CONTADOR'],when=NOW)
        self.assertTrue(self.assess([self.owner,self.expert,refusal,later])['approved'])

    def test_ambiguous_same_time_opposite_decisions_block(self):
        refusal=review(5,'expert',2,state='CHANGES_REQUESTED')
        self.assertFalse(self.assess([self.owner,self.expert,refusal])['approved'])

    def test_optional_quoted_text_does_not_replace_formal_approval(self):
        original=self.expert['body']
        for body in ['```text\n'+original+'\n```','~~~text\n'+original+'\n~~~',
                     '\n'.join('> '+line for line in original.splitlines())]:
            self.expert['body']=body;self.assertTrue(self.assess()['approved'])

if __name__ == '__main__':
    unittest.main()
