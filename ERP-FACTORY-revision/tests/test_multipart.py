"""Only fictitious responses, grants and upload doubles; no real integrations."""
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from contextlib import redirect_stdout

from reviewer.contract import Blocked, canonical, digest, sha256
from reviewer.packets import build_packets, packet, archive_packets
from reviewer.multipart import run_simulated, start, select, collect_events, collect_path
from reviewer.execution_budget import execution_limits
from reviewer.allowance import LocalAllowances
from reviewer.workflow_audit import audit
from reviewer.workflow_spec import blueprint
from test_protocol import material
from test_private_review import archive
from reviewer.material import archive_material

SOURCE = 'a'*40
ROOT = Path(__file__).resolve().parents[2]
BASE = '0cb1882548fc141f4b764e82ff2e5154cfae2762'
PROVENANCE = {'repository': 'fernandoruizm-maker/ERP-FACTORY-revision', 'source_sha': SOURCE,
              'validator_sha': 'b'*40, 'workflow_sha': 'c'*40,
              'run_id': '123', 'run_attempt': 1, 'actor_id': '999'}


def event(request, *, partial=False, raw=None):
    data = json.loads(request['user'].split('\n',1)[1].rsplit('\n',1)[0])
    payload = data['payload']
    response = {'protocol_version': 2, 'phase': payload['phase'], 'part_id': payload.get('part_id',0),
        'artifact_digest': data['artifact_digest'], 'report': {
            'source_sha': payload['source_sha'], 'factory_digest': payload['factory_digest'],
            'reviewed_files': list(payload['files']), 'coverage': 'incomplete' if partial else 'complete',
            'cross_component_review': payload['phase']=='cross', 'verdict': 'PASS',
            'summary_es': 'FICTICIO, sin proveedor.', 'findings': [],
            'limitations_es': ['FICTICIO; no es integracion real.']}}
    return [{'type': 'result', 'subtype': 'success', 'is_error': False,
             'num_turns': 1, 'permission_denials': [],
             'result': canonical(response) if raw is None else raw}], 'success'


class MultipartTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.work = Path(self.temp.name) / 'work'
        data = material({'src/f'+str(i)+'.txt': 'FICTICIO '*140+'\n' for i in range(10)})
        self.manifest, self.parts = build_packets(data, {'include': sorted(data['files']), 'exclude': {}}, limit=2200)
        self.assertEqual(len(self.parts),10)
        self.policy = {'budget_currency': 'USD', 'max_calls_per_execution':11,
                       'max_spend_per_execution':'2', 'max_budget_usd_per_call':'0.1'}
        self.grant = {'grant_id':'ficticio-1','source_sha':SOURCE,'allowance_usd':'2'}
        self.calls, self.uploads = [], []

    def upload(self, folder):
        # Verify immutable artifacts immediately, before a following callback.
        hashes = json.loads((folder/'SHA256.json').read_text(encoding='utf-8'))
        for name,value in hashes.items():
            self.assertEqual(sha256((folder/name).read_bytes()),value)
        self.uploads.append(folder)

    def response(self, request):
        self.calls.append((request['phase'],request['part_id']))
        return event(request)

    def run_flow(self, response=None):
        return run_simulated(self.work,self.manifest,self.parts,self.policy,self.grant,PROVENANCE,
                             response or self.response,self.upload)

    def test_eleven_sequential_calls_with_immediate_private_checkpoints(self):
        def respond(request):
            self.assertEqual(len(self.uploads),2*len(self.calls)+2)
            return self.response(request)
        result=self.run_flow(respond)
        self.assertEqual(self.calls, [('part',i) for i in range(1,11)]+[('cross',0)])
        self.assertEqual(len(self.uploads),23)
        self.assertEqual(result['status'],'NEEDS_HUMAN_REVIEW')
        self.assertFalse(result['publication_allowed'])
        self.assertEqual(result['human_approvals'],0)

    def test_part_four_provider_failure_preserves_first_three_and_stops(self):
        def respond(request):
            self.calls.append(request['part_id'])
            if len(self.calls)==4:
                return [{'type':'error','error':'FICTICIO-PROVIDER-ERROR'}], 'failure'
            return event(request)
        result=self.run_flow(respond)
        self.assertEqual(self.calls,[1,2,3,4])
        self.assertEqual(result['status'],'BLOCKED')
        self.assertEqual(result['coverage']['validated_parts'],3)
        for i in range(1,4):
            self.assertTrue((self.work/f'checkpoints/slot-{i}-result/artifacts/response.txt').is_file())
        self.assertFalse(any('FICTICIO-PROVIDER-ERROR' in p.read_text(encoding='utf-8')
                             for p in self.work.glob('checkpoints/*/artifacts/*')))

    def test_uncertain_timeout_never_retries_and_keeps_reservation(self):
        def respond(request):
            self.calls.append(1)
            raise TimeoutError('FICTICIO-PRIVATE')
        result=self.run_flow(respond)
        self.assertEqual(len(self.calls),1)
        self.assertEqual(result['status'],'BLOCKED')
        budget=json.loads((self.uploads[-1]/'budget.json').read_text())
        self.assertEqual(budget['attempts'][0]['status'],'UNKNOWN')
        self.assertEqual(budget['attempts'][0]['charged_units'],100000)

    def test_call_limit_stops_before_next_call(self):
        self.policy['max_calls_per_execution']=3
        result=self.run_flow()
        self.assertEqual(len(self.calls),3)
        self.assertEqual(result['reason_code'],'CALL_LIMIT_REACHED')
        self.assertEqual(result['status'],'PARTIAL')

    def test_execution_spend_limit_stops_before_next_call(self):
        self.policy['max_spend_per_execution']='0.3'
        result=self.run_flow()
        self.assertEqual(len(self.calls),3)
        self.assertEqual(result['reason_code'],'SPEND_LIMIT_REACHED')

    def test_remaining_allowance_is_an_additional_cap(self):
        self.grant['allowance_usd']='0.2'
        self.assertEqual(self.run_flow()['reason_code'],'SPEND_LIMIT_REACHED')
        self.assertEqual(len(self.calls),2)

    def test_cross_context_too_large_preserves_ten_parts_without_call(self):
        with patch('reviewer.pipeline.MAX_PART_BYTES',3000):
            result=self.run_flow()
        self.assertEqual(len(self.calls),10)
        self.assertEqual(result['status'],'PARTIAL')
        self.assertEqual(result['reason_code'],'CROSS_CONTEXT_TOO_LARGE')

    def test_partial_part_stops_and_cross_is_not_called(self):
        def respond(request):
            self.calls.append(request['part_id'])
            return event(request,partial=request['part_id']==4)
        result=self.run_flow(respond)
        self.assertEqual(self.calls,[1,2,3,4])
        self.assertEqual(result['status'],'PARTIAL')
        self.assertEqual(result['coverage']['validated_parts'],4)
        self.assertEqual(result['coverage']['complete_parts'],3)

    def test_empty_caps_block_before_start_or_callback(self):
        for key in self.policy:
            policy={**self.policy,key:None}
            with self.subTest(key=key),self.assertRaises(Blocked):
                run_simulated(self.work,self.manifest,self.parts,policy,self.grant,PROVENANCE,
                              lambda _:self.fail('Provider must not run'),self.upload)
        self.assertFalse(self.work.exists())

    def test_retain_original_invalid_json_only_privately_and_block(self):
        raw='```json\nFICTICIO-NO-VALIDADO\n```'
        with redirect_stdout(io.StringIO()) as console:
            result=self.run_flow(lambda req:event(req,raw=raw))
        folder=self.uploads[-1]
        self.assertEqual(result['status'],'BLOCKED')
        self.assertEqual(result['reason_code'],'INVALID_JSON')
        self.assertEqual((folder/'response.unvalidated.txt').read_bytes(),raw.encode())
        self.assertEqual(result['response_sha256'],sha256(raw.encode()))
        for name in ('report.json','diagnostic.json','INFORME.txt'):
            self.assertNotIn(raw,(folder/name).read_text(encoding='utf-8'))
        self.assertEqual(console.getvalue(),'')

    def test_secret_or_provider_error_never_retains_unvalidated_text(self):
        for kind in ('secret','provider'):
            self.work=Path(self.temp.name)/kind
            def respond(req):
                events, conclusion=event(req,raw='github_pat_'+'x'*40 if kind=='secret' else 'invalid json')
                if kind=='provider': events.insert(0,{'type':'system','errors':['FICTICIO']})
                return events,conclusion
            result=self.run_flow(respond)
            self.assertEqual(result['status'],'BLOCKED')
            self.assertFalse((self.uploads[-1]/'response.unvalidated.txt').exists())

    def test_reported_overrun_stops_even_with_valid_part(self):
        def respond(req):
            self.calls.append(1)
            events,conclusion=event(req)
            events[0]['total_cost_usd']=0.2
            return events,conclusion
        result=self.run_flow(respond)
        self.assertEqual(len(self.calls),1)
        self.assertEqual(result['reason_code'],'PROVIDER_REPORTED_OVER_BUDGET')
        self.assertEqual(result['status'],'BLOCKED')

    def test_checkpoint_upload_failure_prevents_next_provider_call(self):
        def upload(folder):
            self.upload(folder)
            if 'slot-1-result' in str(folder): raise OSError('FICTICIO-UPLOAD')
        with self.assertRaises(OSError):
            run_simulated(self.work,self.manifest,self.parts,self.policy,self.grant,PROVENANCE,self.response,upload)
        self.assertEqual(len(self.calls),1)
        self.assertTrue((self.work/'checkpoints/slot-1-result/artifacts/report.json').exists())

    def test_interrupted_call_has_preuploaded_inflight_checkpoint(self):
        receipt=start(self.work,self.manifest,self.parts,self.policy,self.grant,PROVENANCE)
        chosen=select(self.work,receipt,1)
        self.upload(self.work/'checkpoints'/chosen['checkpoint']/'artifacts')
        budget=json.loads((self.uploads[-1]/'budget.json').read_text())
        self.assertEqual(budget['attempts'][0]['status'],'IN_FLIGHT')
        with self.assertRaises(Blocked): select(self.work,chosen['receipt'],2)

    def test_missing_execution_file_stops_without_raw_response(self):
        receipt=start(self.work,self.manifest,self.parts,self.policy,self.grant,PROVENANCE)
        chosen=select(self.work,receipt,1)
        result=collect_path(self.work,chosen['receipt'],1,self.work/'missing','success')
        self.assertFalse(result['continue'])
        self.assertEqual(result['report']['reason_code'],'EXECUTION_FILE_MISSING')

    def test_state_hash_prevents_changed_part_or_cap(self):
        receipt=start(self.work,self.manifest,self.parts,self.policy,self.grant,PROVENANCE)
        path=self.work/'state'/receipt['state_file']
        path.write_bytes(path.read_bytes()+b' ')
        with self.assertRaisesRegex(Blocked,'STATE_HASH_MISMATCH'): select(self.work,receipt,1)

    def test_complete_real_base_inventory_ten_parts_eleven_fictitious_calls(self):
        self.manifest,self.parts=packet(ROOT,BASE)
        self.assertEqual(len(self.manifest['files']),91)
        self.assertEqual(len(self.parts),10)
        provenance={**PROVENANCE,'source_sha':BASE}
        grant={**self.grant,'source_sha':BASE}
        result=run_simulated(self.work,self.manifest,self.parts,self.policy,grant,provenance,self.response,self.upload)
        self.assertEqual(len(self.calls),11)
        self.assertEqual(result['status'],'NEEDS_HUMAN_REVIEW')

    def test_archive_index_never_checks_out_source(self):
        source=archive_material(archive(),SOURCE)
        manifest,parts=archive_packets(source,{'include':list(source['files']),'exclude':{}})
        self.assertEqual(manifest['inventory']['method'],'git-ls-files-from-validated-archive')
        self.assertFalse(manifest['inventory']['git_commit_object_verified'])
        self.assertIn('NEVER EXECUTE',canonical(parts))

    def test_local_grant_reservation_import_is_idempotent_and_never_refunds(self):
        ledger=LocalAllowances(Path(self.temp.name)/'grants.sqlite3')
        self.grant=ledger.reserve('ficticio-1',SOURCE,'2','3')
        with self.assertRaisesRegex(Blocked,'ACCUMULATED_CAP_REACHED'):
            ledger.reserve('ficticio-2',SOURCE,'2','3')
        self.run_flow()
        folder=self.uploads[-1]
        index_hash=sha256((folder/'SHA256.json').read_bytes())
        result=ledger.import_checkpoint(folder,index_hash)
        self.assertTrue(result['recorded'])
        self.assertFalse(result['authenticated'])
        self.assertEqual(result['refunded_units'],0)
        self.assertTrue(ledger.import_checkpoint(folder,index_hash)['duplicate'])
        self.assertEqual(ledger.summary()['charged_units'],2000000)
        with self.assertRaises(Blocked): ledger.import_checkpoint(folder,'0'*64)
        budget_path=folder/'budget.json'
        budget=json.loads(budget_path.read_bytes())
        budget['provenance']['run_id']='124'
        budget_path.write_text(canonical(budget),encoding='utf-8')
        hashes=json.loads((folder/'SHA256.json').read_bytes())
        hashes['budget.json']=sha256(budget_path.read_bytes())
        (folder/'SHA256.json').write_text(canonical(hashes),encoding='utf-8')
        reused=ledger.import_checkpoint(folder,sha256((folder/'SHA256.json').read_bytes()))
        self.assertTrue(reused['grant_reused'])
        self.assertEqual(ledger.summary()['charged_units'],2200000)
        with self.assertRaisesRegex(Blocked,'ALLOWANCE_RECONCILIATION_REQUIRED'):
            ledger.reserve('another',SOURCE,'0.1','20')

    def test_step_cli_removes_stale_output_and_collects_only_new_fictitious_result(self):
        from reviewer.multipart_cli import dispatch
        self.work=Path(self.temp.name)/'private-review'
        receipt=start(self.work,self.manifest,self.parts,self.policy,self.grant,PROVENANCE)
        (self.work/'authorization.json').write_text(canonical(self.grant))
        output=Path(self.temp.name)/'outputs.txt'
        execution=Path(self.temp.name)/'claude-execution-output.json'
        execution.write_text('STALE-FICTICIO')
        policy={**self.policy,'cumulative_strategy':'reviewed-local-grant-v1'}
        context={'STATE_FILE':receipt['state_file'],'STATE_SHA256':receipt['state_sha256'],
                 'RUNNER_TEMP':self.temp.name,'GITHUB_OUTPUT':str(output)}
        def emitted():
            lines=output.read_text(encoding='utf-8').splitlines(); values={}; i=0
            while i<len(lines):
                name,delimiter=lines[i].split('<<'); i+=1; content=[]
                while lines[i]!=delimiter: content.append(lines[i]); i+=1
                values[name]='\n'.join(content); i+=1
            return values
        with patch.dict('os.environ',context,clear=True):
            self.assertEqual(dispatch('mp-select',1,policy,PROVENANCE,self.work),0)
        self.assertFalse(execution.exists())
        values=emitted()
        self.assertEqual(values['ready'],'true')
        self.assertEqual(values['max_budget_usd'],'0.1')
        events,_=event({'user':values['user_prompt']})
        execution.write_text(canonical(events),encoding='utf-8')
        context.update(STATE_FILE=values['state_file'],STATE_SHA256=values['state_sha256'],CLAUDE_CONCLUSION='success')
        with patch.dict('os.environ',context,clear=True):
            self.assertEqual(dispatch('mp-collect',1,policy,PROVENANCE,self.work),0)
        self.assertEqual(emitted()['continue'],'true')

    def test_step_cli_writes_safe_checkpoint_if_material_state_changes(self):
        from reviewer.multipart_cli import dispatch
        receipt=start(self.work,self.manifest,self.parts,self.policy,self.grant,PROVENANCE)
        (self.work/'authorization.json').write_text(canonical(self.grant))
        (self.work/'state'/receipt['state_file']).write_text('FICTICIO-PRIVATE-CORRUPTION')
        output=Path(self.temp.name)/'outputs.txt'
        policy={**self.policy,'cumulative_strategy':'reviewed-local-grant-v1'}
        with patch.dict('os.environ',{'STATE_FILE':receipt['state_file'],'STATE_SHA256':receipt['state_sha256'],
                                     'GITHUB_OUTPUT':str(output)},clear=True):
            self.assertEqual(dispatch('mp-select',1,policy,PROVENANCE,self.work),0)
        report=json.loads((self.work/'checkpoints/slot-1-stop/artifacts/report.json').read_text())
        self.assertEqual(report['status'],'BLOCKED')
        self.assertEqual(report['reason_code'],'MATERIAL_VERIFICATION_FAILED')
        self.assertNotIn('FICTICIO-PRIVATE-CORRUPTION',output.read_text())

    def test_pending_cumulative_choice_blocks_before_anonymous_download(self):
        from reviewer.multipart_cli import dispatch
        with patch('reviewer.multipart_cli.download_archive') as download,self.assertRaisesRegex(Blocked,'CUMULATIVE_STRATEGY_PENDING'):
            dispatch('mp-init',None,self.policy,PROVENANCE,self.work)
        download.assert_not_called()


class MultipartAuditTests(unittest.TestCase):
    def test_delivered_yaml_matches_audited_blueprint(self):
        workflow=json.loads((ROOT/'ERP-FACTORY-revision/.github/workflows/review.yml').read_text(encoding='utf-8'))
        self.assertEqual(audit(workflow)['operational_readiness'],'BLOCKED')
        steps=workflow['jobs']['review']['steps']
        calls=[s for s in steps if s.get('id','').startswith('claude_')]
        self.assertEqual([s['id'] for s in calls],['claude_'+str(i) for i in range(1,12)])
        self.assertEqual(len([s for s in steps if 'secrets.' in canonical(s)]),11)
        self.assertTrue(all(s['timeout-minutes']==6 and '--max-budget-usd' in s['with']['claude_args'] for s in calls))

    def test_workflow_mutations_are_rejected(self):
        mutations=[
            lambda j:j.update({'timeout-minutes':10}),
            lambda j:j.update({'strategy':{'matrix':{'part':[1,2]}}}),
            lambda j:j['env'].update({'TOKEN':'${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}'}),
            lambda j:j['steps'][4].update({'run':'python public/setup.py'}),
            lambda j:j['steps'][6].update({'timeout-minutes':60}),
            lambda j:j['steps'][6].update({'continue-on-error':True}),
            lambda j:j['steps'][6]['with'].update({'claude_args':'--max-budget-usd 2'}),
            lambda j:j['steps'][6].update({'if':'${{ always() }}'}),
            lambda j:j['steps'][7].update({'if':'${{ success() }}'}),
            lambda j:j['steps'][8]['with'].update({'path':'${{ runner.temp }}/'}),
            lambda j:j['steps'][8].update({'if':'${{ success() }}'}),
            lambda j:j['steps'][9].update({'if':'${{ always() }}'}),
            lambda j:j['steps'].pop(5),
            lambda j:j['steps'].reverse(),
            lambda j:j['steps'][6].update({'uses':'retry/action@main'}),
            lambda j:j.update({'if':j['if'].replace('false && ','')}),
        ]
        for i,mutation in enumerate(mutations):
            workflow=blueprint(); mutation(workflow['jobs']['review'])
            with self.subTest(mutation=i),self.assertRaises(Blocked): audit(workflow)

    def test_policy_missing_caps_or_removed_blockers_rejected(self):
        path=ROOT/'ERP-FACTORY-revision/policy.json'
        for field in ('max_calls_per_execution','max_spend_per_execution','max_budget_usd_per_call','cumulative_strategy'):
            policy=json.loads(path.read_text()); del policy[field]
            with self.subTest(field=field),self.assertRaises(Blocked): audit(blueprint(),policy)
        policy=json.loads(path.read_text()); policy['execution_enabled']=True
        with self.assertRaises(Blocked): audit(blueprint(),policy)

    def test_multipart_cli_remains_disabled_before_network_or_git(self):
        from reviewer.cli import main
        for command in ('mp-preflight','mp-init','mp-select','mp-collect'):
            with patch('sys.argv',['entrypoint.py',command]),patch('reviewer.material.download_archive') as network, \
                 patch('reviewer.cli.subprocess.run') as git, redirect_stdout(io.StringIO()):
                self.assertEqual(main(),2)
                network.assert_not_called(); git.assert_not_called()


if __name__=='__main__':
    unittest.main()
