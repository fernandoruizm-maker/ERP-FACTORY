"""Local construction/test/review exercise with required explicit test doubles.

No model client, subprocess or Docker execution. Product review in this exercise
is not a V2 factory review and cannot be imported as one.
"""
import json
import hashlib
from copy import deepcopy
from pathlib import Path

from .core import Blocked, canonical, contained, digest, file_digest, validate_review
from .runner import test_command
from .workflow import stage


def run_simulated(work_root, brief, *, trusted_test_root, trusted_hashes, profiles,
                  builder, runner, reviewer, coordinator):
    if coordinator is None or not coordinator.simulation:
        raise Blocked('SIMULATED_COORDINATOR_REQUIRED')
    if not all(callable(port) for port in (builder, runner, reviewer)):
        raise Blocked('SIMULATION_DOUBLES_REQUIRED')
    tests_root = Path(trusted_test_root)
    if not isinstance(trusted_hashes, dict) or not trusted_hashes or not isinstance(profiles, dict) or not profiles:
        raise Blocked('TRUSTED_TEST_MANIFEST_REQUIRED')
    trusted_hashes = json.loads(canonical(trusted_hashes))
    profiles = deepcopy(profiles)  # Preserve the explicitly selected execution order.
    for part in (tests_root, *tests_root.parents):
        if part.is_symlink() or (hasattr(part, 'is_junction') and part.is_junction()):
            raise Blocked('TRUSTED_TEST_ROOT_UNSAFE')
    # The operator supplies this separate manifest, never the builder's proposal.
    source_tests = {}
    for name, expected in trusted_hashes.items():
        path = contained(tests_root, name)
        if not name.startswith('tests/') or not path.is_file():
            raise Blocked('TRUSTED_TEST_DIGEST_MISMATCH')
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != expected:
            raise Blocked('TRUSTED_TEST_DIGEST_MISMATCH')
        source_tests[name] = raw
    for profile, names in profiles.items():
        if not isinstance(names, list) or any(name not in trusted_hashes for name in names):
            raise Blocked('UNTRUSTED_TEST_SELECTED')
        test_command(profile, names, directory=tests_root)
    with coordinator.worker():
        coordinator.require_worker()
        proposal = builder(json.loads(canonical(brief)))
        manifest = stage(work_root, brief, proposal)
        candidate = contained(work_root, 'candidates/' + manifest['candidate_digest'])
        for name, raw in source_tests.items():
            target = contained(candidate, name)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
        expected_files = {edit['path']: file_digest(contained(candidate, edit['path'])) for edit in proposal['edits']}
        expected_files.update(trusted_hashes)
        artifact_hash = digest(expected_files)
        result = {'status': 'SIMULATED_BUILT', 'artifact_digest': artifact_hash,
                  'candidate_digest': manifest['candidate_digest'], 'trusted_tests': trusted_hashes,
                  'tests': [], 'review': None, 'publication_allowed': False, 'human_approvals': 0,
                  'evidence_mode': 'SIMULATED_NOT_PROVIDER_OR_DOCKER_INTEGRATION',
                  'review_kind': 'PRODUCT_SIMULATION_NOT_FACTORY_V2'}

        def checkpoint():
            (candidate / 'pipeline.json').write_text(canonical(result), encoding='utf-8')

        def unchanged():
            # Also reject newly added executable files after a double ran.
            found = {str(p.relative_to(candidate)).replace('\\', '/') for folder in ('src', 'tests')
                     for p in (candidate / folder).rglob('*') if p.is_file()}
            if found != set(expected_files) or any(file_digest(contained(candidate, name)) != value
                                                    for name, value in expected_files.items()):
                raise Blocked('CANDIDATE_OR_TRUSTED_TEST_CHANGED')

        checkpoint()
        try:
            for profile, names in profiles.items():
                unchanged()
                test_command(profile, names, directory=candidate)
                coordinator.require_worker()
                outcome = runner(candidate, profile, list(names), artifact_hash)
                if (not isinstance(outcome, dict) or outcome.get('execution') != 'SIMULATED'
                        or outcome.get('artifact_digest') != artifact_hash
                        or outcome.get('profile') != profile or outcome.get('status') != 'PASS'
                        or type(outcome.get('test_count')) is not int or outcome['test_count'] < 1):
                    raise Blocked('SIMULATED_TESTS_NOT_PASS')
                unchanged()
                result['tests'].append(outcome)
                checkpoint()
            coordinator.require_worker()
            review = reviewer({'artifact_digest': artifact_hash, 'files': expected_files,
                               'tests': json.loads(canonical(result['tests']))})
            unchanged()
            validate_review(review, artifact_hash)
            if review['verdict'] != 'PASS':
                raise Blocked('SIMULATED_REVIEW_BLOCKED')
            result.update(status='SIMULATED_COMPLETE', review=review)
        except Exception:
            # Preserve earlier validated test evidence; no re-execution/retry.
            result.update(status='BLOCKED', reason_code='SIMULATED_PIPELINE_INCOMPLETE')
        checkpoint()
        return result
