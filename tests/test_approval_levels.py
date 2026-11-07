"""Approval levels on fictitious tasks/people; no GitHub or authenticated approval."""
import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

from factory2.core import Blocked, canonical, digest
from factory2.manual_review import CLEAR, REVIEWER
from factory2.state import Store
from tests.operation_fixtures import config, coordinator, accounting_target, artifacts, disabled_repository_config


SOURCE = 'a' * 40
FACTORY_TARGET = {'kind': 'factory', 'repository': 'fernandoruizm-maker/ERP-FACTORY'}


class ApprovalLevelTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.folder = self.root / 'reviews'
        self.folder.mkdir()
        self.store = Store(self.root / 'state.sqlite3', config_path=config(self.root),
                           coordinator=coordinator(self.root), reviews_directory=self.folder)
        self.code, self.factory = digest('codigo ficticio'), digest('fabrica ficticia')
        self.record = {'schema_version': 1, 'pr': 'LOCAL:ficticio', 'base_sha': 'b'*40,
            'reviewed_sha': SOURCE, 'scope': {'mode': 'CAMBIOS_PR', 'files': ['src/ficticio.py'],
                'diff': 'FICTICIO'}, 'reviewer': REVIEWER, 'findings': [],
            'conclusion': CLEAR, 'date': '2026-11-05'}
        self.review = self.import_record(self.record, 'first')
        self.target(FACTORY_TARGET)

    def import_record(self, record, name):
        path = self.folder / (name + '.local.md')
        path.write_text('# Revision FICTICIA\n```json\n' + canonical(record) + '\n```\n', encoding='utf-8')
        return self.store.import_manual_review(path)['review_id']

    def target(self, target):
        brief = {'artifact_digest': self.code}
        if target is not None:
            brief['approval_target'] = target
        self.version = self.store.put_task('T', brief)

    def accept(self, role='business', **changes):
        args = {'source_sha': SOURCE, 'factory_digest': self.factory,
                'manual_review_id': self.review, 'expires_at': time.time() + 300}
        args.update(changes)
        return self.store.accept('T', self.version, 'persona-a' if role == 'business' else 'persona-b', role, **args)

    def outcome(self, **changes):
        args = {'manual_review_id': self.review, 'source_sha': SOURCE, 'factory_digest': self.factory}
        args.update(changes)
        return self.store.gate('T', self.version, self.code,
            {'artifact_digest': self.code, 'verdict': 'PASS', 'summary_es': 'FICTICIO', 'findings': []},
            [{'status': 'PASS', 'test_count': 1, 'artifact_digest': self.code}], **args)

    def test_factory_needs_one_business_acceptance_never_publication(self):
        self.assertEqual(self.outcome()['status'], 'BLOCKED')
        self.accept()
        outcome = self.outcome()
        self.assertEqual(outcome['status'], 'READY_FOR_MANUAL_REVIEW')
        for flag in ('publication_allowed', 'provenance_authenticated', 'human_acceptances_authenticated'):
            self.assertIs(outcome[flag], False)
        self.assertEqual(self.store.roster('T')[0], 1)

    def test_factory_does_not_accept_accounting_or_technical_instead_of_business(self):
        for role in ('accounting', 'technical'):
            with self.subTest(role=role), self.assertRaisesRegex(Blocked, 'ACCEPTANT_NOT_CONFIGURED'):
                self.accept(role)
        self.assertEqual(self.outcome()['status'], 'BLOCKED')

    def test_accounting_product_requires_both_people(self):
        self.target(accounting_target())
        self.accept()
        self.assertEqual(self.outcome()['status'], 'BLOCKED')
        self.accept('accounting')
        self.assertEqual(self.outcome()['status'], 'READY_FOR_MANUAL_REVIEW')
        self.assertEqual(self.store.roster('T')[0], 2)

    def test_unknown_missing_or_contradictory_target_never_uses_factory_default(self):
        cases = [None, {}, {'kind': 'factory'}, {'kind': 'factory', 'repository': 'ficticio/producto'},
                 {'kind': 'accounting_product', 'repository': FACTORY_TARGET['repository']},
                 {'kind': 'non_accounting_product', 'repository': 'ficticio/producto'},
                 {**FACTORY_TARGET, 'override': True}, {**FACTORY_TARGET, 'repository': '../ERP-FACTORY'}]
        for target in cases:
            with self.subTest(target=target):
                self.target(target)
                with self.assertRaises(Blocked):
                    self.accept()
                self.assertEqual(self.outcome()['status'], 'BLOCKED')

    def test_changing_scope_invalidates_acceptances_even_with_same_code(self):
        self.accept()
        previous = self.version
        self.target(accounting_target())
        self.assertNotEqual(previous, self.version)
        with self.store.connect() as db:
            self.assertEqual(db.execute('SELECT count(*) FROM acceptances_v2').fetchone()[0], 0)
        self.accept()
        self.assertEqual(self.outcome()['status'], 'BLOCKED')

    def test_direct_brief_tampering_cannot_downgrade_scope(self):
        self.target(accounting_target())
        self.accept()
        with self.store.connect() as db:
            db.execute('UPDATE tasks SET brief=?', (canonical({'artifact_digest': self.code,
                                                              'approval_target': FACTORY_TARGET}),))
        with self.assertRaisesRegex(Blocked, 'APPROVAL_TARGET_VERSION_MISMATCH'):
            self.store.roster('T')
        self.assertEqual(self.outcome()['status'], 'BLOCKED')

    def test_factory_acceptance_still_expires_and_binds_exact_sha_and_digest(self):
        self.accept()
        self.assertEqual(self.outcome(source_sha='c'*40)['status'], 'BLOCKED')
        self.assertEqual(self.outcome(factory_digest='d'*64)['status'], 'BLOCKED')
        with patch('factory2.state.time.time', return_value=time.time() + 1000):
            self.assertEqual(self.outcome()['status'], 'BLOCKED')

    def test_correction_review_cannot_be_used_with_single_approval(self):
        self.review = self.import_record({**self.record, 'conclusion': 'CORREGIR'}, 'correction')
        with self.assertRaisesRegex(Blocked, 'REQUIRES_CORRECTION'):
            self.accept()
        self.assertEqual(self.outcome()['status'], 'BLOCKED')

    def test_factory_count_and_roles_must_match_decision(self):
        original = self.store.config()
        for changes in ({'human_approvals_required': True}, {'human_approvals_required': 0},
                        {'human_approvals_required': 2}, {'human_approval_roles': ['accounting']},
                        {'human_approval_roles': None}, {'human_approval_roles': ['business', 'business']}):
            with self.subTest(changes=changes):
                self.store.config_path.write_text(canonical({**original, **changes}))
                with self.assertRaises(Blocked):
                    self.accept()
                self.assertEqual(self.outcome()['status'], 'BLOCKED')

    def test_accounting_level_cannot_be_lowered_to_one_or_duplicate_roles(self):
        self.target(accounting_target())
        original = self.store.config()
        for policy in ({'human_approvals_required': 1, 'roles': ['business']},
                       {'human_approvals_required': 2, 'roles': ['business', 'business']}, None):
            with self.subTest(policy=policy):
                self.store.config_path.write_text(canonical({**original, 'accounting_product_approvals': policy}))
                with self.assertRaises(Blocked):
                    self.accept()

    def test_private_v2_keeps_authentication_blocks_with_one_factory_acceptance(self):
        folder, receipt = artifacts(self.root)
        imported = self.store.import_factory_review(folder, receipt)
        self.store.accept('T', self.version, 'persona-a', 'business', source_sha=SOURCE,
            factory_digest=imported['factory_digest'], review_id=imported['review_id'], expires_at=time.time()+300)
        outcome = self.outcome(manual_review_id=None, factory_review=imported['review_id'],
                               factory_digest=imported['factory_digest'])
        self.assertEqual(outcome['status'], 'BLOCKED')
        self.assertIn('HUMAN_AUTHENTICATION_PENDING', outcome['reasons'])
        self.assertIn('PRIVATE_REVIEW_AUTHENTICATION_PENDING', outcome['reasons'])

    def test_repository_config_preserves_disabled_flags_and_named_levels(self):
        cfg = json.loads(disabled_repository_config(self.root).read_text())
        self.assertEqual(cfg['human_approvals_required'], 1)
        self.assertEqual(cfg['human_approval_roles'], ['business'])
        self.assertEqual(cfg['accounting_product_approvals'],
                         {'human_approvals_required': 2, 'roles': ['business', 'accounting']})
        for flag in ('enabled', 'external_calls_enabled', 'erp_access_enabled', 'publication_enabled'):
            self.assertIs(cfg[flag], False)
