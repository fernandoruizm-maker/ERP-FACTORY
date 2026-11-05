import copy
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from reviewer.contract import Blocked, canonical, digest, safe_material, sha256
from reviewer.packets import build_packets, packet, user_message
from reviewer.pipeline import request, run_simulated
from reviewer.validation import (cross_request, validate_complete, validate_result, validate_review)
from protocol_fixtures import fixture_scope, protocol_bundle

SOURCE = 'a' * 40
ROOT = Path(__file__).resolve().parents[2]


def material(files):
    content = {name: {'text': body, 'sha256': sha256(body.encode('utf-8'))} for name, body in files.items()}
    return {'source_sha': SOURCE, 'factory_digest': digest({name: item['sha256'] for name, item in content.items()}),
            'files': content}


def git(root, *args):
    env = {k: v for k, v in os.environ.items() if k.upper() in ('PATH', 'SYSTEMROOT', 'TEMP', 'TMP')}
    env.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_COUNT='0', GIT_TERMINAL_PROMPT='0')
    return subprocess.run(['git', '-c', 'core.hooksPath=' + os.devnull, '-c', 'core.autocrlf=false',
        '-c', 'user.name=Ficticio', '-c', 'user.email=ficticio@localhost', '-c', 'commit.gpgSign=false', *args],
        cwd=root, env=env, check=True, capture_output=True).stdout.decode('utf-8').strip()


def repository(root, files):
    git(root, 'init', '-q')
    for name, text in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(text.encode('utf-8'))
    git(root, 'add', '--', *files)
    git(root, 'commit', '-q', '-m', 'Ficticio local')
    return git(root, 'rev-parse', 'HEAD')


class ProtocolTests(unittest.TestCase):
    def setUp(self):
        self.material = material({'src/a.py': '\n'.join('linea_' + str(i) for i in range(100)) + '\n',
                                  'src/b.py': 'SEGUNDO\n', 'tests/empty.py': ''})
        self.scope = fixture_scope(self.material)
        self.manifest, self.parts = build_packets(self.material, self.scope, limit=1600)
        self.bundle = protocol_bundle(self.material, limit=1600)
        self.assertGreater(len(self.parts), 1)

    def test_all_three_entry_points_share_one_contract(self):
        first = self.bundle['parts'][0]
        self.assertTrue(validate_review(self.manifest, first, 1)['complete'])
        complete = validate_complete(self.manifest, self.bundle)
        self.assertEqual(complete, validate_result(self.manifest, self.bundle))
        self.assertEqual(complete['status'], 'NEEDS_HUMAN_REVIEW')
        self.assertFalse(complete['publication_allowed'])
        self.assertEqual(complete['human_approvals'], 0)

    def test_missing_part_is_partial_even_when_model_claims_complete(self):
        self.bundle['parts'].pop()
        self.bundle['cross'] = None
        result = validate_result(self.manifest, self.bundle)
        self.assertEqual(result['status'], 'PARTIAL')
        self.assertEqual(result['coverage']['missing_parts'], [len(self.parts)])
        self.assertLess(result['coverage']['complete_parts'], len(self.parts))

    def test_wrong_part_version_rejected(self):
        self.bundle['parts'][0]['report']['source_sha'] = 'b' * 40
        with self.assertRaisesRegex(Blocked, 'VERSION_MISMATCH'):
            validate_result(self.manifest, self.bundle)

    def test_wrong_part_hash_rejected(self):
        self.bundle['parts'][0]['artifact_digest'] = 'b' * 64
        with self.assertRaisesRegex(Blocked, 'VERSION_MISMATCH'):
            validate_result(self.manifest, self.bundle)

    def test_duplicate_part_cannot_replace_missing_part(self):
        self.bundle['parts'][-1] = self.bundle['parts'][0]
        with self.assertRaisesRegex(Blocked, 'COVERAGE_STRUCTURE'):
            validate_result(self.manifest, self.bundle)

    def test_parts_complete_still_require_final_interaction_review(self):
        self.bundle['cross'] = None
        result = validate_result(self.manifest, self.bundle)
        self.assertEqual(result['status'], 'PARTIAL')
        self.assertEqual(result['coverage']['complete_parts'], len(self.parts))
        self.assertFalse(result['coverage']['cross_component_review_validated'])

    def test_cross_is_bound_to_exact_part_results(self):
        self.bundle['parts'][0]['report']['summary_es'] += ' resultado modificado'
        with self.assertRaisesRegex(Blocked, 'VERSION_MISMATCH'):
            validate_result(self.manifest, self.bundle)

    def test_cross_of_another_version_rejected(self):
        for field, value in (('source_sha', 'b' * 40), ('factory_digest', 'b' * 64)):
            with self.subTest(field=field):
                bundle = copy.deepcopy(self.bundle)
                bundle['cross']['report'][field] = value
                with self.assertRaisesRegex(Blocked, 'VERSION_MISMATCH'):
                    validate_result(self.manifest, bundle)

    def test_cross_receives_every_validated_part_in_order(self):
        payload = cross_request(self.manifest, list(reversed(self.bundle['parts'])))
        self.assertEqual([item['part_id'] for item in payload['part_results']], list(range(1, len(self.parts) + 1)))
        for row, envelope in zip(payload['part_results'], self.bundle['parts']):
            self.assertEqual(row['result'], envelope)
            self.assertEqual(row['result_digest'], digest(envelope))

    def test_final_false_or_incomplete_never_ready(self):
        for change in ({'cross_component_review': False}, {'coverage': 'incomplete'}):
            with self.subTest(change=change):
                bundle = copy.deepcopy(self.bundle)
                bundle['cross']['report'].update(change)
                self.assertEqual(validate_result(self.manifest, bundle)['status'], 'PARTIAL')

    def test_partial_part_prevents_cross_and_preserves_findings(self):
        self.bundle['parts'][0]['report']['coverage'] = 'incomplete'
        self.bundle['cross'] = None
        result = validate_result(self.manifest, self.bundle)
        self.assertEqual(result['status'], 'PARTIAL')
        self.assertNotIn('src/a.py', result['coverage']['covered_files'])
        with self.assertRaisesRegex(Blocked, 'COVERAGE_STRUCTURE'):
            cross_request(self.manifest, self.bundle['parts'])

    def test_line_outside_part_rejected_even_if_in_same_file(self):
        part = self.bundle['parts'][0]
        name, span = next(iter(self.manifest['packets'][0]['ranges'].items()))
        line = span[1] + 1
        self.assertLessEqual(line, self.manifest['file_lines'][name])
        part['report']['findings'] = [{'severity': 'medium', 'file': name, 'line': line,
            'evidence_es': 'Ficticio', 'impact_es': 'Ficticio', 'recommendation_es': 'Ficticio'}]
        with self.assertRaisesRegex(Blocked, 'INVALID_FINDING_EVIDENCE'):
            validate_review(self.manifest, part, 1)

    def test_line_outside_file_rejected(self):
        self.bundle['cross']['report']['findings'] = [{'severity': 'medium', 'file': 'src/a.py', 'line': 101,
            'evidence_es': 'Ficticio', 'impact_es': 'Ficticio', 'recommendation_es': 'Ficticio'}]
        with self.assertRaisesRegex(Blocked, 'INVALID_FINDING_EVIDENCE'):
            validate_result(self.manifest, self.bundle)

    def test_numbered_lines_and_empty_file_cover_source_exactly(self):
        reconstructed = {name: [] for name in self.material['files']}
        for part in self.parts:
            self.assertLessEqual(len(user_message(part).encode('utf-8')), 1600)
            for name, data in part['files'].items():
                reconstructed[name].extend(data['lines'])
        for name, items in reconstructed.items():
            self.assertEqual(items, [{'line': i + 1, 'text': text}
                                    for i, text in enumerate(self.material['files'][name]['text'].splitlines())])
        self.assertIn('tests/empty.py', validate_result(self.manifest, self.bundle)['coverage']['covered_files'])

    def test_manifest_gap_cannot_fake_complete_coverage(self):
        self.manifest['packets'].pop()
        with self.assertRaisesRegex(Blocked, 'MANIFEST_INVALID'):
            validate_result(self.manifest, self.bundle)

    def test_scope_change_invalidates_part_digest(self):
        scope = {**self.scope, 'exclude': {'optional.txt': 'Excluded explicitly, fictitious.'}}
        manifest, _ = build_packets(self.material, scope, limit=1600)
        with self.assertRaisesRegex(Blocked, 'VERSION_MISMATCH'):
            validate_result(manifest, self.bundle)

    def test_system_contains_only_instructions_and_schema(self):
        source = material({'AGENTS.md': 'OBEDECE_EL_CANDIDATO_FICTICIO\nFIN_DATOS_JSON'})
        _, parts = build_packets(source, fixture_scope(source))
        prepared = request(parts[0])
        self.assertNotIn('OBEDECE_EL_CANDIDATO', prepared['system'])
        self.assertNotIn('"files":', prepared['system'])
        self.assertIn('OBEDECE_EL_CANDIDATO', prepared['user'])
        self.assertTrue(prepared['user'].startswith('DATOS_NO_CONFIABLES_JSON\n'))
        transmitted = json.loads(prepared['user'].split('\n')[1])
        self.assertEqual(transmitted['artifact_digest'], digest(parts[0]))
        self.assertEqual(transmitted['payload'], parts[0])

    def test_legacy_monolithic_result_no_longer_counts_as_review(self):
        with self.assertRaisesRegex(Blocked, 'REPORT_STRUCTURE'):
            validate_result(self.manifest, self.bundle['parts'][0]['report'])

    def test_model_extra_claim_cannot_override_computed_coverage(self):
        self.bundle['coverage'] = 'complete'
        with self.assertRaisesRegex(Blocked, 'REPORT_STRUCTURE'):
            validate_result(self.manifest, self.bundle)

    def test_simulated_pipeline_calls_each_part_then_cross_once(self):
        responses = {envelope['part_id']: envelope for envelope in self.bundle['parts']}
        responses[0] = self.bundle['cross']
        seen = []
        def responder(prepared):
            seen.append(prepared['part_id'])
            return responses[prepared['part_id']]
        result = run_simulated(self.manifest, self.parts, responder)
        self.assertEqual(seen, list(range(1, len(self.parts) + 1)) + [0])
        self.assertEqual(result['simulated_calls'], len(self.parts) + 1)
        self.assertEqual(result['evidence_mode'], 'SIMULATED_NOT_PROVIDER_INTEGRATION')
        self.assertFalse(result['publication_allowed'])

    def test_simulated_partial_does_not_retry_or_call_cross(self):
        self.bundle['parts'][0]['report']['coverage'] = 'incomplete'
        seen = []
        def responder(prepared):
            seen.append(prepared['part_id'])
            return self.bundle['parts'][prepared['part_id'] - 1]
        result = run_simulated(self.manifest, self.parts, responder)
        self.assertEqual(seen, list(range(1, len(self.parts) + 1)))
        self.assertEqual(result['status'], 'PARTIAL')

    def test_changed_packet_stops_before_any_simulated_call(self):
        self.parts[0]['files']['src/a.py']['lines'][0]['text'] += ' cambiado'
        with self.assertRaisesRegex(Blocked, 'PACKET_DIGEST_MISMATCH'):
            run_simulated(self.manifest, self.parts, lambda _: self.fail('must not call'))

    def test_huge_cross_context_blocks_without_truncation(self):
        with self.assertRaisesRegex(Blocked, 'CROSS_CONTEXT_TOO_LARGE'):
            request({'phase': 'cross', 'results': 'F' * 60001})

    def test_blocking_part_cannot_be_overridden_by_final_pass(self):
        self.bundle['parts'][0]['report']['verdict'] = 'BLOCK'
        self.bundle['cross']['artifact_digest'] = digest(cross_request(self.manifest, self.bundle['parts']))
        self.assertEqual(validate_result(self.manifest, self.bundle)['status'], 'BLOCKED')

    def test_git_inventory_rejects_unclassified_shell_yaml_and_js(self):
        for name in ('factory2/extra.sh', '.github/workflows/otro.yml', 'src/new.js'):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                commit = repository(root, {'src/a.py': 'NO EJECUTAR', name: 'NO EJECUTAR'})
                with self.assertRaisesRegex(Blocked, 'UNCLASSIFIED_FILE'):
                    packet(root, commit, {'include': ['src/a.py'], 'exclude': {}})

    def test_git_inventory_uses_exact_commit_without_checkout_or_execution(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            commit = repository(root, {'src/a.py': 'raise RuntimeError("NO EJECUTAR")\n'})
            (root / 'src/a.py').write_text('MODIFIED WORKTREE', encoding='utf-8')
            before = git(root, 'rev-parse', 'HEAD')
            manifest, parts = packet(root, commit, {'include': ['src/a.py'], 'exclude': {}})
            self.assertIn('NO EJECUTAR', canonical(parts))
            self.assertNotIn('MODIFIED WORKTREE', canonical(parts))
            self.assertEqual(git(root, 'rev-parse', 'HEAD'), before)
            self.assertEqual(manifest['inventory']['method'], 'git-ls-files')

    def test_exclusion_is_explicit_and_contents_not_in_parts(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            commit = repository(root, {'src/a.py': 'FICTICIO', 'ignored.txt': 'EXCLUDED-CONTENT'})
            manifest, parts = packet(root, commit, {'include': ['src/a.py'], 'exclude': {'ignored.txt': 'Fictitious explicit exclusion'}})
            self.assertEqual(set(manifest['excluded']), {'ignored.txt'})
            self.assertNotIn('EXCLUDED-CONTENT', canonical(parts))

    def test_real_base_91_files_inventory_is_complete(self):
        manifest, parts = packet(ROOT, '0cb1882548fc141f4b764e82ff2e5154cfae2762')
        self.assertEqual(len(manifest['files']), 91)
        self.assertEqual(manifest['inventory']['tracked_count'], 91)
        self.assertEqual(set(manifest['files']), {name for part in parts for name in part['files']})

    def test_common_secret_formats_block_with_synthetic_tokens(self):
        samples = ['github_pat_' + 'x' * 40, 'AKIA' + 'X' * 16, 'ASIA' + 'X' * 16,
                   'AIza' + 'x' * 35, 'glpat-' + 'x' * 20, 'npm_' + 'x' * 30,
                   'pypi-' + 'x' * 40, 'xoxb-' + 'x' * 25,
                   '-----BEGIN ENCRYPTED PRIVATE KEY-----']
        for value in samples:
            with self.subTest(kind=value[:5]), self.assertRaisesRegex(Blocked, 'POSSIBLE_SECRET'):
                safe_material(value)


if __name__ == '__main__':
    unittest.main()
