import base64
import copy
from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from factory.mvp.common import Blocked
from factory.mvp.github import GitHub


class RulesetTransport(GitHub):
    def __init__(self):
        self.repository = 'o/r'
        self.governance_mode = 'rulesets'
        self.app_id = 123
        self.calls = []
        self.rules = [
            {'type': 'deletion'}, {'type': 'non_fast_forward'},
            {'type': 'pull_request', 'parameters': {
                'required_approving_review_count': 1,
                'dismiss_stale_reviews_on_push': True,
                'require_last_push_approval': True,
                'required_review_thread_resolution': True}},
            {'type': 'required_status_checks', 'parameters': {
                'strict_required_status_checks_policy': True,
                'required_status_checks': [
                    {'context': 'factory/quality', 'integration_id': 123},
                    {'context': 'factory/human-approval', 'integration_id': 123}]}}]
        self.detail = {'id': 42, 'target': 'branch', 'enforcement': 'active',
                       'source_type': 'Repository', 'source': 'o/r', 'bypass_actors': [],
                       'rules': copy.deepcopy(self.rules)}

    def get(self, path):
        self.calls.append(path)
        if path.startswith('/rules/branches/main?'):
            return [dict(r, ruleset_id=42, ruleset_source_type='Repository',
                         ruleset_source='o/r') for r in self.rules]
        if path == '/rulesets/42':
            return self.detail
        raise AssertionError('Unexpected endpoint: ' + path)


class RulesetTests(unittest.TestCase):
    def test_active_ruleset_is_supported_without_classic_protection(self):
        gh = RulesetTransport()
        gh.governance('main')
        self.assertFalse(any('/protection' in p for p in gh.calls))

    def test_missing_checks_bypass_stale_reviews_and_wrong_source_block(self):
        for mutation in ('missing_checks', 'bypass', 'missing_bypass_field',
                         'disabled', 'wrong_app', 'any_app', 'stale', 'last_push',
                         'delete', 'force', 'no_review', 'non_strict'):
            with self.subTest(mutation=mutation):
                gh = RulesetTransport()
                if mutation == 'missing_checks':
                    gh.rules.pop()
                    gh.detail['rules'].pop()
                elif mutation == 'bypass':
                    gh.detail['bypass_actors'] = [{'actor_id': 5, 'actor_type': 'Integration'}]
                elif mutation == 'missing_bypass_field':
                    del gh.detail['bypass_actors']
                elif mutation == 'disabled':
                    gh.detail['enforcement'] = 'disabled'
                elif mutation in ('wrong_app', 'any_app'):
                    gh.rules[-1]['parameters']['required_status_checks'][0]['integration_id'] = (
                        999 if mutation == 'wrong_app' else None)
                elif mutation in ('stale', 'last_push', 'no_review'):
                    key = {'stale': 'dismiss_stale_reviews_on_push',
                           'last_push': 'require_last_push_approval',
                           'no_review': 'required_approving_review_count'}[mutation]
                    gh.rules[2]['parameters'][key] = 0
                elif mutation == 'non_strict':
                    gh.rules[-1]['parameters']['strict_required_status_checks_policy'] = False
                else:
                    gh.rules.pop(0 if mutation == 'delete' else 1)
                gh.detail['rules'] = copy.deepcopy(gh.rules)
                with self.assertRaises(Blocked):
                    gh.governance('main')

    def test_rule_changed_between_reads_blocks(self):
        gh = RulesetTransport()
        gh.detail['rules'].pop()
        with self.assertRaises(Blocked):
            gh.governance('main')

    def test_read_only_app_accepts_only_unchanged_admin_audited_version(self):
        from factory.mvp.governance import attest_ruleset
        gh = RulesetTransport()
        gh.detail['updated_at'] = '2026-11-03T18:34:21.606-04:00'
        gh.detail['conditions'] = {'ref_name': {'include': ['refs/heads/main'], 'exclude': []}}
        gh.ruleset_attestations = {'42': attest_ruleset(gh.detail)}
        del gh.detail['bypass_actors']
        gh.detail['current_user_can_bypass'] = 'never'
        gh.detail['updated_at'] = '2026-11-03T22:34:21.606Z'
        gh.governance('main')
        for key, value in [('updated_at', '2026-11-03T22:35:21.606Z'),
                           ('current_user_can_bypass', 'always')]:
            with self.subTest(key=key):
                original = gh.detail[key]
                gh.detail[key] = value
                with self.assertRaises(Blocked):
                    gh.governance('main')
                gh.detail[key] = original
        gh.detail['conditions']['ref_name']['include'] = ['~ALL']
        with self.assertRaises(Blocked):
            gh.governance('main')

    def test_admin_audit_rejects_hidden_or_nonempty_bypass(self):
        from factory.mvp.governance import attest_ruleset
        for bypass in (None, [{'actor_id': 123}]):
            gh = RulesetTransport()
            gh.detail['bypass_actors'] = bypass
            with self.assertRaises(Blocked):
                attest_ruleset(gh.detail)


class AppAuthTests(unittest.TestCase):
    def test_real_rsa_signature_and_renewal_without_token_in_files(self):
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import padding, rsa
        from factory.mvp.auth import InstallationToken
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        now = [1_800_000_000.0]
        with tempfile.TemporaryDirectory() as folder:
            pem = Path(folder) / 'key.pem'
            pem.write_bytes(key.private_bytes(serialization.Encoding.PEM,
                serialization.PrivateFormat.TraditionalOpenSSL, serialization.NoEncryption()))
            auth = InstallationToken('o/r', 123, 456, pem, clock=lambda: now[0])
            jwt = auth.jwt()
            header, payload, signature = jwt.split('.')
            decode = lambda v: base64.urlsafe_b64decode(v + '=' * (-len(v) % 4))
            self.assertEqual(json.loads(decode(header))['alg'], 'RS256')
            claims = json.loads(decode(payload))
            self.assertEqual(claims['iss'], '123')
            self.assertEqual(claims['iat'], int(now[0]) - 60)
            self.assertLessEqual(claims['exp'] - now[0], 600)
            key.public_key().verify(decode(signature), (header + '.' + payload).encode(),
                                    padding.PKCS1v15(), hashes.SHA256())
            calls = []
            def api(method, path, data=None):
                calls.append((method, path, data))
                return {'token': 'ephemeral-' + str(len(calls)), 'expires_at':
                    datetime.fromtimestamp(now[0] + 3600, timezone.utc).isoformat()}
            with patch.object(auth, 'app_request', side_effect=api):
                self.assertEqual(auth.get_token(), auth.get_token())
                self.assertEqual(len(calls), 1)
                now[0] += 3301
                self.assertEqual(auth.get_token(), 'ephemeral-2')
                self.assertEqual(calls[0][2]['repositories'], ['r'])
                self.assertEqual(calls[0][2]['permissions']['administration'], 'read')
            self.assertEqual(list(Path(folder).iterdir()), [pem])

    def test_invalid_expiry_is_rejected(self):
        from factory.mvp.auth import InstallationToken
        auth = InstallationToken('o/r', 123, 456, 'unused.pem', clock=lambda: 1_800_000_000)
        with patch.object(auth, 'app_request', return_value={'token': 'secret',
                                                           'expires_at': '2020-01-01T00:00:00Z'}):
            with self.assertRaises(Blocked):
                auth.get_token()

    def test_cross_repository_app_request_is_rejected(self):
        from factory.mvp.auth import InstallationToken
        auth = InstallationToken('o/r', 123, 456, 'unused.pem')
        with self.assertRaises(Blocked):
            auth.app_request('GET', '/repos/another/private/installation')


if __name__ == '__main__':
    unittest.main()
