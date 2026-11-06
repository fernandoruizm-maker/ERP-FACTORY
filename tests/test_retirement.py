"""Temporary declaration fixtures; no VM, credentials or provider is accessed."""
import copy
from datetime import date, timedelta
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from factory2.core import Blocked
from factory2.operations import Coordinator
from factory2.providers import ClaudeReviewer, CodexBuilder
from factory2.retirement import MAX_RECORD_BYTES, RECORD_PATH, read_retirement
from factory2.state import Store


ROOT = Path(__file__).resolve().parent.parent


class RetirementTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.path = self.root / 'declared-retirement.json'
        # Copies test the declared schema/known installation IDs, not their truth.
        self.record = json.loads(RECORD_PATH.read_text(encoding='utf-8'))
        self.write(self.record)
        self.coordinator = Coordinator(self.root, retirement_path=self.path)

    def write(self, record):
        self.path.write_text(json.dumps(record), encoding='utf-8')

    def store(self):
        return Store(self.root / 'fixture.sqlite3', config_path=ROOT / 'config.json',
                     coordinator=self.coordinator)

    def test_valid_record_is_declared_not_authenticated_or_approved(self):
        result = self.coordinator.check_active()
        self.assertEqual(result['status'], 'ORIGINAL_RETIRED_DECLARED')
        self.assertFalse(result['provenance_authenticated'])
        self.assertFalse(result['publication_allowed'])
        with self.coordinator.worker():
            self.coordinator.require_worker()

    def test_repository_record_does_not_require_an_archive_or_signature(self):
        self.assertEqual(self.record['archive'], 'NO_POR_DECISION_DE_FERNANDO')
        self.assertEqual(self.record['openai'], 'NO_EXISTIA')
        self.assertEqual(self.record['github_app']['id'], 5603415)
        self.assertFalse(read_retirement()['provenance_authenticated'])

    def test_missing_record_blocks(self):
        self.path.unlink()
        with self.assertRaisesRegex(Blocked, '^ORIGINAL_RETIREMENT_MISSING$'):
            self.coordinator.check_active()

    def test_incomplete_record_blocks_each_required_field(self):
        for group in (None, 'vm', 'github_app', 'windows_inventory'):
            fields = self.record if group is None else self.record[group]
            for field in fields:
                candidate = copy.deepcopy(self.record)
                del (candidate if group is None else candidate[group])[field]
                self.write(candidate)
                with self.subTest(group=group, field=field), self.assertRaisesRegex(
                        Blocked, '^ORIGINAL_RETIREMENT_INCOMPLETE$'):
                    self.coordinator.check_active()

    def test_contradictory_record_blocks(self):
        changes = [(None, 'declared_by', 'Otra persona ficticia'),
                   (None, 'provenance_authenticated', True),
                   (None, 'openai', 'PENDIENTE'),
                   (None, 'archive', 'ARCHIVADO'),
                   ('vm', 'removed', False), ('vm', 'name', 'Otra VM ficticia'),
                   ('github_app', 'id', 123), ('github_app', 'removed', False),
                   ('github_app', 'private_key_removed', False),
                   ('github_app', 'installation_removed', False),
                   ('windows_inventory', 'factory_tasks_found', True),
                   ('windows_inventory', 'factory_services_found', True),
                   ('windows_inventory', 'pilot_pause_preserved', False),
                   ('windows_inventory', 'scope', 'AUDITORIA_TOTAL')]
        for group, field, value in changes:
            candidate = copy.deepcopy(self.record)
            (candidate if group is None else candidate[group])[field] = value
            self.write(candidate)
            with self.subTest(group=group, field=field), self.assertRaisesRegex(
                    Blocked, '^ORIGINAL_RETIREMENT_CONTRADICTORY$'):
                self.coordinator.check_active()

    def test_restored_original_blocks(self):
        self.record['original_restored'] = True
        self.write(self.record)
        with self.assertRaisesRegex(Blocked, '^ORIGINAL_RESTORED$'):
            self.coordinator.check_active()

    def test_boolean_strings_and_numeric_booleans_do_not_pass(self):
        for group, field, value in [(None, 'original_restored', 'false'),
                (None, 'original_restored', 0), (None, 'schema_version', True),
                ('vm', 'removed', 1), ('github_app', 'removed', 'true')]:
            candidate = copy.deepcopy(self.record)
            (candidate if group is None else candidate[group])[field] = value
            self.write(candidate)
            with self.subTest(field=field, value=value), self.assertRaises(Blocked):
                self.coordinator.check_active()

    def test_invalid_future_or_reversed_dates_block(self):
        for field, value in [('declared_on', '2026-02-30'), ('declared_on', '20261105'),
                ('declared_on', (date.today() + timedelta(days=1)).isoformat()),
                ('declared_on', None), ('declared_on', '2026-11-04')]:
            candidate = copy.deepcopy(self.record)
            candidate[field] = value
            self.write(candidate)
            with self.subTest(value=value), self.assertRaises(Blocked):
                self.coordinator.check_active()

    def test_malformed_duplicate_unknown_and_oversized_records_block(self):
        original = json.dumps(self.record)
        invalid = ['not-json FICTICIO_NO_PUBLICAR', '[]',
                   original.replace('"original_restored": false',
                                    '"original_restored": true, "original_restored": false'),
                   json.dumps({**self.record, 'activation_allowed': True}),
                   '[' * 1500 + ']' * 1500, 'x' * (MAX_RECORD_BYTES + 1)]
        for raw in invalid:
            self.path.write_text(raw, encoding='utf-8')
            with self.subTest(length=len(raw)), self.assertRaisesRegex(
                    Blocked, '^ORIGINAL_RETIREMENT_INVALID$'):
                self.coordinator.check_active()

    def test_unreadable_or_linked_record_blocks_without_raw_error(self):
        with patch.object(Path, 'open', side_effect=PermissionError('FICTICIO_PRIVADO')):
            with self.assertRaisesRegex(Blocked, '^ORIGINAL_RETIREMENT_INVALID$'):
                self.coordinator.check_active()
        with patch.object(Path, 'is_symlink', return_value=True):
            with self.assertRaisesRegex(Blocked, '^ORIGINAL_RETIREMENT_PATH_UNSAFE$'):
                self.coordinator.check_active()

    def test_default_store_uses_its_state_directory_and_repository_record(self):
        store = Store(self.root / 'nested' / 'state.sqlite3')
        self.assertEqual(store.coordinator.directory, store.path.parent)
        self.assertEqual(store.coordinator.retirement_path, RECORD_PATH)
        with store.worker():
            store.coordinator.require_worker()

    def test_single_worker_lock_remains_required(self):
        other = Coordinator(self.root, retirement_path=self.path)
        with self.coordinator.worker():
            with self.assertRaisesRegex(Blocked, 'WORKER_ALREADY_ACTIVE'):
                with other.worker():
                    self.fail('A second worker must not enter')
        with other.worker():
            other.require_worker()

    def test_recovery_cannot_interrupt_live_worker(self):
        store = self.store()
        store.put_task('FICTICIO', {})
        other = Store(store.path, coordinator=Coordinator(self.root, retirement_path=self.path))
        with store.worker():
            store.reserve_call('fake-call', 'FICTICIO', 'fake', 'hash', max_calls=2, output_limit=10)
            with self.assertRaisesRegex(Blocked, 'WORKER_ALREADY_ACTIVE'):
                other.recover()
            store.finish_call('fake-call', 'COMPLETED')
        self.assertEqual(other.recover()['uncertain_calls'], 0)

    def test_restoration_is_reread_before_next_call_and_recovery(self):
        store = self.store()
        store.put_task('FICTICIO', {})
        with store.worker():
            store.reserve_call('fake-call', 'FICTICIO', 'fake', 'hash', max_calls=2, output_limit=10)
            self.record['original_restored'] = True
            self.write(self.record)
            with self.assertRaisesRegex(Blocked, 'ORIGINAL_RESTORED'):
                store.reserve_call('next', 'FICTICIO', 'fake', 'hash', max_calls=2, output_limit=10)
            # Preserve an already-started result, even after the declaration changes.
            store.finish_call('fake-call', 'COMPLETED')
        with self.assertRaisesRegex(Blocked, 'ORIGINAL_RESTORED'):
            store.recover()
        self.assertEqual(store.summary(), {'tasks': 1, 'calls': 1, 'uncertain': 0})

    def test_deletion_after_successful_check_blocks_next_check(self):
        self.coordinator.check_active()
        self.path.unlink()
        with self.assertRaisesRegex(Blocked, 'ORIGINAL_RETIREMENT_MISSING'):
            self.coordinator.check_active()

    def test_valid_record_with_disabled_config_prevents_both_real_providers(self):
        store = self.store()
        config = store.config()
        for key in ('enabled', 'external_calls_enabled', 'erp_access_enabled', 'publication_enabled'):
            self.assertIs(config[key], False)
        with patch('factory2.providers.os.environ.get', side_effect=AssertionError('No credentials')), \
                patch('factory2.providers.urllib.request.build_opener',
                      side_effect=AssertionError('No network')) as network, \
                patch('shutil.which', side_effect=AssertionError('No CLI')) as cli:
            with self.assertRaisesRegex(Blocked, 'Conexiones externas desactivadas'):
                ClaudeReviewer(config, store).review('FICTICIO', {}, [], None)
            with self.assertRaisesRegex(Blocked, 'Conexiones externas desactivadas'):
                CodexBuilder(config, store).build('FICTICIO', {}, None)
            network.assert_not_called()
            cli.assert_not_called()
        self.assertEqual(store.summary()['calls'], 0)

    def test_valid_record_does_not_satisfy_review_or_human_gate(self):
        store = self.store()
        version = store.put_task('FICTICIO', {
            'artifact_digest': 'a'*64,
            'approval_target': {'kind': 'factory', 'repository': 'fernandoruizm-maker/ERP-FACTORY'}})
        self.coordinator.check_active()
        result = store.gate('FICTICIO', version, 'a'*64, {}, [], source_sha='b'*40)
        self.assertEqual(result['status'], 'BLOCKED')
        self.assertFalse(result['publication_allowed'])
        self.assertFalse(result['provenance_authenticated'])
        self.assertIn('HUMAN_ACCEPTANCES_MISSING_STALE_OR_EXPIRED', result['reasons'])


if __name__ == '__main__':
    unittest.main()
