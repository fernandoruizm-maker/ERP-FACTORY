import copy
from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

from factory2.core import Blocked, canonical, compare, digest, file_digest
from factory2.comparison_permit import ComparisonPermit
from factory2.operations import Coordinator
from factory2.providers import ClaudeReviewer, CodexBuilder, Permit
from factory2.state import Store, identity
from tests.operation_fixtures import accept, artifacts, coordinator, store_fixture

ROOT = Path(__file__).resolve().parents[1]
BRIEF = json.loads((ROOT / 'fixtures/cliente.json').read_text(encoding='utf-8'))


class OperationalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.store, self.imported = store_fixture(self.root)
        self.code = digest('producto-ficticio')
        self.version = self.store.put_task('T', {'artifact_digest': self.code})

    def config(self, **changes):
        path = self.store.config_path
        data = json.loads(path.read_text())
        data.update(changes)
        path.write_text(canonical(data), encoding='utf-8')

    def acceptance(self, **changes):
        args = {'source_sha': self.imported['source_sha'], 'factory_digest': self.imported['factory_digest'],
                'review_id': self.imported['review_id'], 'expires_at': time.time()+60}
        args.update(changes)
        return self.store.accept('T', self.version, ' P E R S O N A-A\t', 'business', **args)

    def outcome(self, **changes):
        args = {'factory_review': self.imported['review_id'], 'source_sha': self.imported['source_sha'],
                'factory_digest': self.imported['factory_digest']}
        args.update(changes)
        return self.store.gate('T', self.version, self.code,
            {'artifact_digest': self.code, 'verdict': 'PASS', 'summary_es': 'Ficticio', 'findings': []},
            [{'status': 'PASS', 'test_count': 1, 'artifact_digest': self.code}], **args)

    def rewritten(self, run, mutate):
        folder, receipt = artifacts(self.root, run=run)
        report = json.loads((folder / 'report.json').read_bytes())
        mutate(report, receipt)
        (folder / 'report.json').write_bytes(canonical(report).encode('utf-8'))
        hashes = json.loads((folder / 'SHA256.json').read_bytes())
        hashes['report.json'] = hashlib.sha256((folder / 'report.json').read_bytes()).hexdigest()
        raw = canonical(hashes).encode('utf-8')
        (folder / 'SHA256.json').write_bytes(raw)
        receipt['sha256_index'] = hashlib.sha256(raw).hexdigest()
        return folder, receipt

    def test_identity_strips_all_whitespace_and_case(self):
        self.assertEqual(identity(' P e R\tS O N A-A\n'), 'persona-a')
        result = self.acceptance()
        self.assertFalse(result['identity_authenticated'])
        with self.store.connect() as db:
            row = db.execute('SELECT * FROM acceptances_v2').fetchone()
        self.assertEqual(row['person'], 'persona-a')
        self.assertEqual(row['person_id'], '101')
        self.assertEqual(row['review_id'], self.imported['review_id'])

    def test_no_silent_substitution_even_same_acceptant(self):
        self.acceptance()
        with self.assertRaisesRegex(Blocked, 'ALREADY_RECORDED'):
            self.acceptance()
        self.config(human_approvers={'business': {'login': 'persona-c', 'id': '303'},
                                    'accounting': {'login': 'persona-b', 'id': '202'}})
        with self.assertRaises(Blocked):
            self.store.accept('T', self.version, 'persona-c', 'business',
                source_sha=self.imported['source_sha'], factory_digest=self.imported['factory_digest'],
                review_id=self.imported['review_id'], expires_at=time.time()+60)
        with self.store.connect() as db:
            self.assertEqual(db.execute('SELECT person FROM acceptances_v2').fetchone()[0], 'persona-a')

    def test_same_person_different_case_or_spaces_cannot_fill_two_roles(self):
        for second in ({'login': ' P E R S O N A-A ', 'id': '202'}, {'login': 'persona-b', 'id': '101'}):
            self.config(human_approvers={'business': {'login': 'persona-a', 'id': '101'}, 'accounting': second})
            with self.assertRaises(Blocked):
                self.acceptance()

    def test_acceptance_binds_source_factory_and_imported_review(self):
        for change in ({'source_sha': 'd'*40}, {'factory_digest': 'e'*64}, {'review_id': 'made-up'}):
            with self.subTest(change=change), self.assertRaises(Blocked):
                self.acceptance(**change)

    def test_expiry_required_finite_future_and_rechecked(self):
        for expiry in (None, 0, float('nan'), float('inf'), True):
            with self.subTest(expiry=expiry), self.assertRaises(Blocked):
                self.acceptance(expires_at=expiry)
        self.acceptance()
        accept(self.store, 'T', self.version, 'accounting', self.imported)
        with patch('factory2.state.time.time', return_value=time.time()+120):
            self.assertIn('HUMAN_ACCEPTANCES_MISSING_STALE_OR_EXPIRED', self.outcome()['reasons'])

    def test_config_required_count_is_read_not_hardcoded(self):
        self.config(human_approvals_required=3)
        with self.assertRaises(Blocked):
            self.acceptance()
        self.config(human_approvers={'business': {'login': 'persona-a', 'id': '101'},
                    'accounting': {'login': 'persona-b', 'id': '202'},
                    'audit': {'login': 'persona-c', 'id': '303'}})
        self.assertEqual(self.store.roster()[0], 3)
        self.acceptance()
        accept(self.store, 'T', self.version, 'accounting', self.imported)
        self.assertIn('HUMAN_ACCEPTANCES_MISSING_STALE_OR_EXPIRED', self.outcome()['reasons'])

    def test_missing_people_or_invalid_count_block(self):
        for changes in ({'human_approvers': None}, {'human_approvals_required': None},
                        {'human_approvals_required': 1}, {'human_approvals_required': True}):
            with self.subTest(changes=changes):
                self.config(**changes)
                with self.assertRaises(Blocked):
                    self.acceptance()

    def test_complete_fixture_stays_blocked_without_real_authentication(self):
        self.acceptance()
        accept(self.store, 'T', self.version, 'accounting', self.imported)
        result = self.outcome()
        self.assertEqual(result['status'], 'BLOCKED')
        self.assertEqual(set(result['reasons']), {'HUMAN_AUTHENTICATION_PENDING', 'PRIVATE_REVIEW_AUTHENTICATION_PENDING'})
        self.assertFalse(result['publication_allowed'])

    def test_new_run_invalidates_previous_acceptances(self):
        self.acceptance()
        accept(self.store, 'T', self.version, 'accounting', self.imported)
        folder, receipt = artifacts(self.root, run='124')
        imported = self.store.import_factory_review(folder, receipt)
        self.assertIn('HUMAN_ACCEPTANCES_MISSING_STALE_OR_EXPIRED',
                      self.outcome(factory_review=imported['review_id'])['reasons'])

    def test_task_change_and_restore_invalidates_all_acceptances(self):
        self.acceptance()
        self.store.put_task('T', {'artifact_digest': 'other'})
        self.store.put_task('T', {'artifact_digest': self.code})
        with self.store.connect() as db:
            self.assertEqual(db.execute('SELECT count(*) FROM acceptances_v2').fetchone()[0], 0)

    def test_legacy_table_is_not_migrated_as_approval(self):
        with self.store.connect() as db:
            db.execute('INSERT INTO acceptances VALUES(?,?,?,?)', ('T', self.version, 'persona-a', 'business'))
        self.assertIn('HUMAN_ACCEPTANCES_MISSING_STALE_OR_EXPIRED', self.outcome()['reasons'])

    def test_gate_rejects_handwritten_pass_partial_and_old_format(self):
        for report in ({'verdict': 'PASS'}, {'status': 'PARTIAL'},
                       {'artifact_digest': self.imported['factory_digest'], 'verdict': 'PASS', 'summary_es': 'Ficticio', 'findings': []}):
            result = self.outcome(factory_review=report)
            self.assertEqual(result['status'], 'BLOCKED')
            self.assertIn('PRIVATE_FACTORY_REVIEW_INVALID', result['reasons'])

    def test_valid_import_requires_receipt_and_retains_provenance_and_hash(self):
        stored = self.store.factory_review(self.imported['review_id'])
        self.assertEqual(stored['provenance']['run_id'], '123')
        self.assertEqual(len(stored['artifact_index_sha256']), 64)
        self.assertFalse(stored['provenance_authenticated'])
        folder, receipt = artifacts(self.root, run='124')
        with self.assertRaises(Blocked):
            self.store.import_factory_review(folder, None)
        self.config(private_review_trust=None)
        with self.assertRaises(Blocked):
            self.store.import_factory_review(folder, receipt)

    def test_modified_artifact_or_hash_index_blocks_import(self):
        for run, filename in (('124', 'report.json'), ('125', 'SHA256.json')):
            folder, receipt = artifacts(self.root, run=run)
            with (folder / filename).open('ab') as stream:
                stream.write(b' ')
            with self.assertRaises(Blocked):
                self.store.import_factory_review(folder, receipt)

    def test_multipart_budget_attachment_is_hashed_but_not_authentication(self):
        folder, receipt = artifacts(self.root, run='124')
        (folder / 'budget.json').write_bytes(canonical({'synthetic': True, 'billing_verified': False}).encode())
        hashes = json.loads((folder / 'SHA256.json').read_bytes())
        hashes['budget.json'] = hashlib.sha256((folder / 'budget.json').read_bytes()).hexdigest()
        raw = canonical(hashes).encode()
        (folder / 'SHA256.json').write_bytes(raw)
        receipt['sha256_index'] = hashlib.sha256(raw).hexdigest()
        imported = self.store.import_factory_review(folder, receipt)
        self.assertFalse(imported['provenance_authenticated'])
        self.assertEqual(self.outcome(factory_review=imported['review_id'])['status'], 'BLOCKED')
        (folder / 'budget.json').write_bytes(b'{}')
        with self.assertRaises(Blocked): self.store.import_factory_review(folder, receipt)

    def test_wrong_provenance_repository_validator_actor_attempt_or_sha_blocks(self):
        for i, (field, value) in enumerate((('repository', 'PUBLIC'), ('validator_sha', 'e'*40),
                ('actor_id', '88'), ('run_attempt', 2), ('source_sha', 'e'*40), ('run_id', 'text'))):
            def mutate(report, receipt):
                report['provenance'][field] = value
                receipt['provenance'][field] = value
            folder, receipt = self.rewritten(str(200+i), mutate)
            with self.subTest(field=field), self.assertRaises(Blocked):
                self.store.import_factory_review(folder, receipt)

    def test_partial_or_forged_complete_report_cannot_import(self):
        for i, change in enumerate(({'status': 'PARTIAL'}, {'publication_allowed': True}, {'human_approvals': 2})):
            folder, receipt = artifacts(self.root, run=str(200+i), changes=change)
            with self.assertRaises(Blocked):
                self.store.import_factory_review(folder, receipt)
        folder, receipt = self.rewritten('300', lambda report, _: report['review'].update(cross=None))
        with self.assertRaises(Blocked):
            self.store.import_factory_review(folder, receipt)

    def test_stored_review_tampering_or_policy_change_is_revalidated(self):
        with self.store.connect() as db:
            db.execute('UPDATE private_reviews SET report=?', (b'{}',))
        self.assertIn('PRIVATE_FACTORY_REVIEW_INVALID', self.outcome()['reasons'])

    def test_unavailable_private_validator_blocks_instead_of_using_legacy(self):
        with patch('factory2.review_import.private_contract', side_effect=FileNotFoundError('ficticio')):
            self.assertIn('PRIVATE_FACTORY_REVIEW_INVALID', self.outcome()['reasons'])
        self.config(private_review_trust=None)
        self.assertIn('PRIVATE_FACTORY_REVIEW_INVALID', self.outcome()['reasons'])

    def test_extra_unvalidated_file_is_never_imported(self):
        folder, receipt = artifacts(self.root, run='124')
        (folder / 'response.unvalidated.txt').write_text('FICTICIO')
        with self.assertRaises(Blocked):
            self.store.import_factory_review(folder, receipt)

    def test_recovery_blocks_with_live_worker_without_changing_calls(self):
        other = Store(self.store.path, coordinator=Coordinator(self.store.coordinator.directory, simulation=True))
        with self.store.worker():
            self.store.reserve_call('c', 'T', 'fake', 'hash', max_calls=2, output_limit=10)
            with self.assertRaises(Blocked):
                other.recover()
            self.store.finish_call('c', 'COMPLETED')
        self.assertEqual(other.recover()['uncertain_calls'], 0)

    def test_lock_excludes_another_process(self):
        script = ('from factory2.operations import Coordinator\nfrom factory2.core import Blocked\n'
                  'import sys\ntry:\n with Coordinator(sys.argv[1], simulation=True).worker(): pass\n'
                  'except Blocked: sys.exit(7)\nsys.exit(0)')
        env = {k: v for k, v in os.environ.items() if k.upper() in ('PATH', 'SYSTEMROOT', 'TEMP', 'TMP')}
        with self.store.worker():
            result = subprocess.run([sys.executable, '-B', '-c', script, str(self.store.coordinator.directory)],
                                    cwd=ROOT, env=env, capture_output=True, timeout=10)
        self.assertEqual(result.returncode, 7)

    def test_reserve_and_finish_require_worker_lock(self):
        with self.assertRaises(Blocked):
            self.store.reserve_call('c', 'T', 'fake', 'hash', max_calls=2, output_limit=10)
        with self.assertRaises(Blocked):
            self.store.finish_call('c', 'COMPLETED')

    def test_expiring_marker_stops_next_call_but_does_not_lose_current_result(self):
        marker = self.store.coordinator.directory / 'active-factory.json'
        with self.store.worker():
            self.store.reserve_call('c', 'T', 'fake', 'hash', max_calls=2, output_limit=10)
            data = json.loads(marker.read_text())
            data['expires_at'] = 0
            marker.write_text(canonical(data))
            self.store.finish_call('c', 'COMPLETED')
            with self.assertRaises(Blocked):
                self.store.reserve_call('next', 'T', 'fake', 'hash', max_calls=2, output_limit=10)
        with self.store.connect() as db:
            self.assertEqual(db.execute('SELECT status FROM calls WHERE id=?', ('c',)).fetchone()[0], 'COMPLETED')

    def test_lock_is_released_on_exception(self):
        with self.assertRaises(RuntimeError):
            with self.store.worker():
                raise RuntimeError('Ficticio')
        with self.store.worker():
            self.store.coordinator.require_worker()

    def test_original_active_missing_expired_or_uncertain_marker_blocks(self):
        marker = self.store.coordinator.directory / 'active-factory.json'
        original = json.loads(marker.read_text())
        for change in ({'active_factory': 'original'}, {'original_stopped': False},
                       {'original_stopped': None}, {'expires_at': 0}, {'mode': 'REAL'}):
            marker.write_text(canonical({**original, **change}))
            with self.assertRaises(Blocked):
                self.store.recover()
        marker.unlink()
        with self.assertRaises(Blocked):
            self.store.recover()

    def test_real_coordination_blocks_even_with_valid_fixture_marker(self):
        real = Coordinator(self.store.coordinator.directory)
        with self.assertRaisesRegex(Blocked, 'NOT_VERIFIED'):
            with real.worker():
                self.fail('Real worker must stay blocked')

    def test_provider_guard_precedes_credential_and_transport(self):
        store = Store(self.root / 'unconfigured.sqlite3')
        with patch('factory2.providers.os.environ.get', side_effect=AssertionError('No credentials')):
            with self.assertRaises(Blocked):
                ClaudeReviewer({'external_calls_enabled': True}, store, lambda *_: self.fail()).review('T', {}, [], None)
        self.assertEqual(store.summary()['calls'], 0)

    def test_simulation_rejects_default_real_adapters(self):
        with self.assertRaisesRegex(Blocked, 'REAL_TRANSPORT_FORBIDDEN'):
            ClaudeReviewer({}, self.store).review('T', {}, [], None)
        with self.assertRaisesRegex(Blocked, 'REAL_TRANSPORT_FORBIDDEN'):
            CodexBuilder({}, self.store).build('T', {}, None)


class ComparisonPermitTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.path = self.root / 'evidence.txt'
        self.path.write_text('FICTICIO')
        self.catalog = {'base': 'BASE-FICTICIA', 'synthetic': True, 'capabilities': [
            {'requirement': 'BOT-01', 'decision': 'ADAPTAR', 'reason': 'Ficticio',
             'evidence': [{'path': 'evidence.txt', 'sha256': file_digest(self.path), 'supports': 'Ficticio'}]}]}
        self.permit = ComparisonPermit('persona-ficticia', 'BASE-FICTICIA', str(self.root.resolve()),
                                      ('evidence.txt',), time.time()+60, digest(self.catalog), True)

    def result(self, permit):
        return compare(BRIEF, self.catalog, evidence_root=self.root, permit=permit)['rows'][0]['decision']

    def test_scoped_fictitious_permission_allows_only_matching_evidence(self):
        self.assertEqual(self.result(self.permit), 'ADAPTAR')

    def test_bad_permission_is_pending_before_reading_any_evidence(self):
        variants = [None, True, replace(self.permit, authorized_by=' '), replace(self.permit, base='OTHER'),
                    replace(self.permit, root=str(self.root / 'other')), replace(self.permit, paths=('other.txt',)),
                    replace(self.permit, expires_at=0), replace(self.permit, expires_at=float('nan')),
                    replace(self.permit, catalog_digest='changed'), replace(self.permit, synthetic_only=False)]
        with patch('factory2.core.file_digest', side_effect=AssertionError('No evidence read')):
            for permit in variants:
                with self.subTest(permit=permit):
                    self.assertEqual(self.result(permit), 'PENDIENTE')

    def test_real_catalog_stays_pending_even_with_matching_local_record(self):
        self.catalog['synthetic'] = False
        with patch('factory2.core.file_digest', side_effect=AssertionError('No real ERP read')):
            self.assertEqual(self.result(replace(self.permit, catalog_digest=digest(self.catalog))), 'PENDIENTE')

    def test_unsafe_paths_and_modified_catalog_cannot_extend_permission(self):
        self.catalog['capabilities'][0]['evidence'][0]['path'] = '../outside'
        permit = replace(self.permit, paths=('../outside',), catalog_digest=digest(self.catalog))
        with patch('factory2.core.file_digest', side_effect=AssertionError('No outside read')):
            self.assertEqual(self.result(permit), 'PENDIENTE')

    def test_boolean_authorized_api_is_removed(self):
        with self.assertRaises(TypeError):
            compare(BRIEF, self.catalog, evidence_root=self.root, authorized=True)


if __name__ == '__main__':
    unittest.main()
