"""Single gated pilot with manual pauses, plus the legacy explicit-double exercise.

Imports never launch processes or providers. run_simulated remains entirely
simulated; PilotTrial needs future authorization and currently disabled config.
"""
import json
import hashlib
from copy import deepcopy
from pathlib import Path

from .core import Blocked, canonical, contained, digest, file_digest, validate_review
from .runner import test_command
from .workflow import stage


def bottle_input():
    """Fixed fictional requirements and trusted JS tests, not an ERP/catalog input."""
    root = Path(__file__).resolve().parents[1]
    brief = json.loads((root / 'fixtures/cliente.json').read_text(encoding='utf-8'))
    tests = (root / 'pilot-js/tests/bottles.test.mjs').read_bytes()
    return {'brief': brief, 'synthetic': True,
            'required_output': ['src/bottles.mjs'],
            'interface': 'ES module exporting Bottles. Implement the methods exercised by the fixed tests.',
            'trusted_tests': {'tests/bottles.test.mjs': tests.decode('utf-8')}}


def git_call(directory, *args):
    """Trusted local Git only; no remote, user hooks, signing or global identity."""
    import os
    import subprocess
    env = {k: v for k, v in os.environ.items() if k.upper() in
           {'PATH', 'SYSTEMROOT', 'WINDIR', 'TEMP', 'TMP', 'PATHEXT', 'COMSPEC'}}
    env.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM='1', GIT_TERMINAL_PROMPT='0',
               GIT_CONFIG_COUNT='0')
    command = ['git', '-c', 'core.hooksPath=' + os.devnull, '-c', 'commit.gpgSign=false',
               '-c', 'core.autocrlf=false', '-c', 'user.name=Factory local fictitious',
               '-c', 'user.email=ficticio@localhost', '-C', str(directory), *args]
    result = subprocess.run(command, env=env, capture_output=True, timeout=20)
    if result.returncode:
        raise Blocked('LOCAL_SNAPSHOT_GIT_FAILED')
    return result.stdout.decode('utf-8').strip()


def clean_head(directory):
    if git_call(directory, 'status', '--porcelain'):
        raise Blocked('SOURCE_OR_CANDIDATE_NOT_CLEAN')
    return git_call(directory, 'rev-parse', 'HEAD')


def snapshot_candidate(directory):
    git_call(directory, 'init', '-q')
    git_call(directory, 'add', '--', 'src', 'tests')
    git_call(directory, 'commit', '-q', '-m', 'Piloto ficticio local; no publicar')
    return clean_head(directory)


class PilotTrial:
    """Single durable trial, one API reservation, offline build/tests, then human pause.

    Explicit doubles are permitted only with a simulated Coordinator. No scheduler,
    CLI command, automatic approval, publication or retry is installed by this class.
    """
    ID = 'bottles-1'

    def __init__(self, store, work_root, *, builder=None, tester=None, snapshotter=None, head=None, attempt=1):
        if type(attempt) is not int or not 1 <= attempt <= 1000000:
            raise Blocked('PILOT_ATTEMPT_INVALID')
        self.ID = f'bottles-{attempt}'
        self.store, self.root = store, Path(work_root).absolute()
        for part in (self.root, *self.root.parents):
            if part.is_symlink() or (hasattr(part, 'is_junction') and part.is_junction()):
                raise Blocked('PILOT_WORK_ROOT_UNSAFE')
        self.builder, self.tester = builder, tester
        self.snapshotter, self.head = snapshotter, head
        if not store.coordinator.simulation and any(x is not None for x in (builder, tester, snapshotter, head)):
            raise Blocked('REAL_TRIAL_DOUBLES_FORBIDDEN')
        with store.connect() as db:
            db.execute('CREATE TABLE IF NOT EXISTS pilot_trials(id TEXT PRIMARY KEY, data TEXT NOT NULL)')
            db.execute('CREATE TABLE IF NOT EXISTS pilot_authorizations(id TEXT PRIMARY KEY, digest TEXT NOT NULL)')

    def config(self):
        from .budget import limits, units
        cfg = self.store.config()
        if cfg.get('external_calls_enabled') is not True:
            raise Blocked('PILOT_SWITCH_OFF')
        if any(cfg.get(k) is not False for k in ('enabled', 'erp_access_enabled', 'publication_enabled')):
            raise Blocked('PILOT_MUST_REMAIN_ISOLATED')
        limits(cfg)
        if cfg['budget_currency'] != 'USD':
            raise Blocked('PILOT_USD_REQUIRED')
        for key, ceiling in (('max_budget_usd_per_call', '1.00'),
                             ('max_spend_per_execution', '12.00'), ('max_spend_total', '13.00')):
            if units(cfg[key]) > units(ceiling):
                raise Blocked('PILOT_AUTHORIZED_CAP_EXCEEDED')
        return cfg

    def save(self, data):
        with self.store.connect() as db:
            db.execute('UPDATE pilot_trials SET data=? WHERE id=?', (canonical(data), self.ID))

    def load(self):
        with self.store.connect() as db:
            row = db.execute('SELECT data FROM pilot_trials WHERE id=?', (self.ID,)).fetchone()
        if row is None:
            raise Blocked('PILOT_NOT_FOUND')
        return json.loads(row[0])

    def unchanged(self, data):
        permitted = {data['config_digest']}
        # Turning the switch OFF after testing must not prevent reviewing the
        # already-built candidate. No other config change is silently accepted.
        if data['status'] in ('WAITING_FOR_MANUAL_REVIEW', 'WAITING_FOR_ACCEPTANCES'):
            permitted.add(data['disarmed_config_digest'])
        if digest(self.store.config()) not in permitted:
            raise Blocked('PILOT_CONFIG_CHANGED')
        candidate = contained(self.root, self.ID)
        actual = {}
        for path in candidate.rglob('*'):
            rel = path.relative_to(candidate)
            if rel.parts[0] == '.git':
                continue
            if path.is_symlink() or (hasattr(path, 'is_junction') and path.is_junction()):
                raise Blocked('PILOT_CANDIDATE_CHANGED')
            if path.is_file():
                actual[rel.as_posix()] = file_digest(path)
        if actual != data['files']:
            raise Blocked('PILOT_CANDIDATE_CHANGED')
        if data.get('candidate_sha'):
            head = self.head(candidate) if self.head else clean_head(candidate)
            if head != data['candidate_sha']:
                raise Blocked('PILOT_CANDIDATE_SHA_CHANGED')
        return candidate

    def start(self, authorization):
        import sqlite3
        if (not isinstance(authorization, dict) or type(authorization.get('attempt')) is not int
                or not 1 <= authorization['attempt'] <= 1000000):
            raise Blocked('PILOT_ATTEMPT_INVALID')
        with self.store.worker():
            self.ID = f"bottles-{authorization['attempt']}"
            with self.store.connect() as db:
                # Also honor trials recorded before numbered authorizations existed.
                if db.execute('SELECT 1 FROM pilot_trials WHERE id=?', (self.ID,)).fetchone():
                    raise Blocked('PILOT_ALREADY_RECORDED_NO_RETRY')
                for row in db.execute('SELECT data FROM pilot_trials'):
                    if json.loads(row[0])['status'] != 'BLOCKED':
                        raise Blocked('PILOT_PREVIOUS_ATTEMPT_UNFINISHED')
                try:
                    db.execute('INSERT INTO pilot_authorizations VALUES(?,?)', (self.ID, digest(authorization)))
                except sqlite3.IntegrityError:
                    raise Blocked('PILOT_ALREADY_RECORDED_NO_RETRY') from None
            try:
                return self._start(authorization)
            except Exception:
                # Consume even a preflight-blocked attempt; never store free text.
                with self.store.connect() as db:
                    if not db.execute('SELECT 1 FROM pilot_trials WHERE id=?', (self.ID,)).fetchone():
                        db.execute('INSERT INTO pilot_trials VALUES(?,?)', (self.ID, canonical({
                            'attempt': authorization['attempt'], 'status': 'BLOCKED',
                            'reason_code': 'PILOT_PREFLIGHT_BLOCKED_NO_RETRY', 'publication_allowed': False})))
                raise

    def _start(self, authorization):
        import math
        import sqlite3
        import time
        from .codex_adapter import DockerCodexBuilder, PYTHON_IMAGE, NODE_IMAGE
        from .manual_review import CLEAR, hex_value
        from .runner import DockerRunner, bounded_process
        cfg = self.config()  # Before provider/credential/process boundaries.
        context = bottle_input()
        from .core import discover
        discover(context['brief'])
        expected = {'source_sha', 'context_digest', 'config_digest', 'authorized_by', 'expires_at', 'factory_review_id', 'attempt'}
        if (not isinstance(authorization, dict) or set(authorization) != expected
                or authorization['authorized_by'] != 'Fernando'
                or authorization['context_digest'] != digest(context)
                or authorization['config_digest'] != digest(cfg)
                or not hex_value(authorization['source_sha'], 40)
                or type(authorization['expires_at']) not in (int, float)
                or not math.isfinite(authorization['expires_at']) or authorization['expires_at'] <= time.time()):
            raise Blocked('PILOT_AUTHORIZATION_REQUIRED')
        self.store.coordinator.require_worker()
        source = self.head(None) if self.head else clean_head(Path(__file__).resolve().parents[1])
        if source != authorization['source_sha']:
            raise Blocked('PILOT_FACTORY_SHA_CHANGED')
        reviewed = self.store.manual_review(authorization['factory_review_id'])
        if reviewed['source_sha'] != source or reviewed['conclusion'] != CLEAR:
            raise Blocked('PILOT_FACTORY_REVIEW_REQUIRED')
        adapter = self.builder or DockerCodexBuilder(cfg)
        if self.store.coordinator.simulation and (self.builder is None or self.tester is None
                                                 or self.snapshotter is None or self.head is None):
            raise Blocked('PILOT_SIMULATION_DOUBLES_REQUIRED')
        # Validate the real request contract even when transport is doubled.
        request = DockerCodexBuilder(cfg).request(context)
        if not self.store.coordinator.simulation:
            code, endpoint = bounded_process(['docker', 'context', 'inspect', '--format', '{{.Endpoints.docker.Host}}'])
            if code or endpoint.strip() not in ('npipe:////./pipe/docker_engine', 'npipe:////./pipe/dockerDesktopLinuxEngine'):
                raise Blocked('LOCAL_DOCKER_ENDPOINT_REQUIRED')
            for image in (PYTHON_IMAGE, NODE_IMAGE):
                code, info = bounded_process(['docker', 'image', 'inspect', image, '--format', '{{.Os}}/{{.Architecture}}'])
                if code or info.strip() != 'linux/amd64':
                    raise Blocked('PILOT_PINNED_IMAGES_REQUIRED')
        self.root.mkdir(parents=True, exist_ok=True)
        candidate = contained(self.root, self.ID)
        if candidate.exists():
            raise Blocked('PILOT_CANDIDATE_ALREADY_EXISTS')
        data = {'status': 'PREPARED', 'attempt': authorization['attempt'], 'factory_source_sha': source,
            'config_digest': digest(cfg), 'factory_digest': digest({'source': source, 'config': digest(cfg)}),
            'disarmed_config_digest': digest({**cfg, 'external_calls_enabled': False}),
            'tests': [], 'files': {}, 'publication_allowed': False,
            'provenance_authenticated': False, 'human_acceptances_authenticated': False,
            'evidence_mode': 'SIMULATED' if self.store.coordinator.simulation else 'REAL_TRIAL'}
        try:
            with self.store.connect() as db:
                db.execute('INSERT INTO pilot_trials VALUES(?,?)', (self.ID, canonical(data)))
        except sqlite3.IntegrityError:
            raise Blocked('PILOT_ALREADY_RECORDED_NO_RETRY') from None
        reserved = False
        try:
            self.store.put_task(self.ID, {'synthetic': True, 'phase': 'construction'})
            self.store.budget.begin(self.ID, source, {**cfg, 'max_calls_per_execution': 1})
            self.store.reserve_paid_call(self.ID, self.ID, 'codex', digest(request), execution_id=self.ID,
                source_sha=source, max_cost=cfg['pilot_cost_review']['max_call_usd'], output_limit=request['max_output_tokens'])
            reserved = True
            self.store.coordinator.require_worker()
            if digest(self.config()) != data['config_digest'] or time.time() >= authorization['expires_at']:
                raise Blocked('PILOT_AUTHORIZATION_CHANGED_OR_EXPIRED')
            data['status'] = 'BUILDING'
            self.save(data)
            from .codex_adapter import usage_record, request_bytes, token_cost
            review = cfg['pilot_cost_review']
            data['cost_basis'] = {k: review[k] for k in
                ('input_usd_per_million', 'output_usd_per_million', 'max_call_usd')}
            data['worst_case_cost_usd'] = token_cost(review, len(request_bytes(request)), request['max_output_tokens'])
            try:
                proposal = adapter.generate(context)
            finally:
                evidence = getattr(adapter, 'last_usage', None)
                if evidence is not None:
                    # Revalidate/filter the double/adapter metadata before persisting.
                    counts = evidence['usage']
                    data.update(usage_record({'usage': {
                        'input_tokens': counts['input_tokens'], 'output_tokens': counts['output_tokens'],
                        'output_tokens_details': {'reasoning_tokens': counts['reasoning_tokens']}}}, review))
                    self.save(data)
            if 'usage' not in data:
                raise Blocked('CODEX_USAGE_INVALID')
            from .core import validate_edits
            validate_edits(proposal)
            if [e['path'] for e in proposal['edits']] != ['src/bottles.mjs']:
                raise Blocked('PILOT_OUTPUT_SCOPE_INVALID')
            paid_status = self.store.finish_call(self.ID, 'COMPLETED', data['calculated_cost_usd'])
            reserved = False
            if (paid_status == 'OVER_BUDGET'
                    or data['usage']['input_tokens'] > len(request_bytes(request))
                    or data['usage']['output_tokens'] > request['max_output_tokens']):
                raise Blocked('CODEX_USAGE_EXCEEDS_AUTHORIZED_BOUND')
            self.store.coordinator.require_worker()
            if digest(self.config()) != data['config_digest']:
                raise Blocked('PILOT_CONFIG_CHANGED')
            adapter.materialize(proposal, candidate)
            expected_source = {'src/bottles.mjs': hashlib.sha256(proposal['edits'][0]['content'].encode()).hexdigest()}
            (candidate / 'tests').mkdir(exist_ok=False)
            for name, content in context['trusted_tests'].items():
                target = contained(candidate, name)
                target.write_bytes(content.encode('utf-8'))
                expected_source[name] = file_digest(target)
            data['files'] = expected_source
            data['artifact_digest'] = digest(expected_source)
            data['status'] = 'TESTING'
            self.save(data)
            self.unchanged(data)
            self.store.coordinator.require_worker()
            tester = self.tester or DockerRunner().run
            outcome = tester(candidate, NODE_IMAGE, 'javascript', ['tests/bottles.test.mjs'], data['artifact_digest'])
            self.unchanged(data)
            if (not isinstance(outcome, dict) or outcome.get('status') != 'PASS'
                    or outcome.get('exit_code') != 0 or outcome.get('profile') != 'javascript'
                    or outcome.get('artifact_digest') != data['artifact_digest']
                    or type(outcome.get('test_count')) is not int or outcome['test_count'] != 7):
                raise Blocked('PILOT_TESTS_FAILED')
            data['tests'] = [outcome]
            data['candidate_sha'] = (self.snapshotter or snapshot_candidate)(candidate)
            if not hex_value(data['candidate_sha'], 40):
                raise Blocked('PILOT_SNAPSHOT_INVALID')
            self.unchanged(data)
            data['version'] = self.store.put_task(self.ID, {'artifact_digest': data['artifact_digest'],
                'approval_target': {'kind': 'accounting_product', 'repository': 'ficticio/botellas'},
                'factory_source_sha': source, 'synthetic': True})
            data['status'] = 'WAITING_FOR_MANUAL_REVIEW'
            data['next'] = 'Fernando adjunta src/tests y evidencia a Claude; registrar revision del SHA candidato. No enviar automaticamente.'
        except Exception as exc:
            if reserved:
                self.store.finish_call(self.ID, 'UNKNOWN', data.get('calculated_cost_usd'))
            codes = {'CODEX_USAGE_INVALID', 'CODEX_USAGE_EXCEEDS_AUTHORIZED_BOUND', 'PER_CALL_SPEND_LIMIT', 'SPEND_LIMIT', 'EXECUTION_CALL_LIMIT',
                     'BUDGET_RECONCILIATION_REQUIRED', 'CODEX_RESPONSE_INVALID_OR_UNCERTAIN',
                     'PILOT_OUTPUT_SCOPE_INVALID', 'PILOT_TESTS_FAILED', 'DOCKER_BUILD_FAILED',
                     'DOCKER_BUILD_CONTENT_MISMATCH', 'PILOT_CONFIG_CHANGED',
                     'PILOT_CANDIDATE_CHANGED', 'PILOT_SNAPSHOT_INVALID',
                     'PILOT_AUTHORIZATION_CHANGED_OR_EXPIRED'}
            reason = str(exc) if isinstance(exc, Blocked) and str(exc) in codes else 'PILOT_STAGE_FAILED_NO_RETRY'
            data.update(failed_stage=data['status'], status='BLOCKED', reason_code=reason)
        self.save(data)
        return data

    def attach_review(self, path):
        from .manual_review import CLEAR
        with self.store.worker():
            data = self.load()
            if data['status'] != 'WAITING_FOR_MANUAL_REVIEW':
                raise Blocked('PILOT_NOT_WAITING_FOR_REVIEW')
            self.unchanged(data)
            review = self.store.import_manual_review(path)
            if (review['source_sha'] != data['candidate_sha'] or review['conclusion'] != CLEAR
                    or set(review['scope']['files']) != set(data['files'])):
                data.update(status='BLOCKED', reason_code='PILOT_REVIEW_REJECTED')
            else:
                data.update(status='WAITING_FOR_ACCEPTANCES', manual_review_id=review['review_id'])
            self.save(data)
            return data

    def accept(self, person, role, expires_at):
        with self.store.worker():
            data = self.load()
            if data['status'] != 'WAITING_FOR_ACCEPTANCES':
                raise Blocked('PILOT_NOT_WAITING_FOR_ACCEPTANCES')
            self.unchanged(data)
            return self.store.accept(self.ID, data['version'], person, role,
                source_sha=data['candidate_sha'], factory_digest=data['factory_digest'],
                manual_review_id=data['manual_review_id'], expires_at=expires_at)

    def gate(self):
        with self.store.worker():
            data = self.load()
            if data['status'] != 'WAITING_FOR_ACCEPTANCES':
                raise Blocked('PILOT_NOT_WAITING_FOR_ACCEPTANCES')
            self.unchanged(data)
            review = self.store.manual_review(data['manual_review_id'])
            product_review = {'artifact_digest': data['artifact_digest'],
                'verdict': 'PASS' if review['conclusion'] == 'SIN OBJECIONES TÉCNICAS' else 'BLOCK',
                'summary_es': 'Revision manual declarada, no autenticada; sin publicacion.',
                'findings': [{'severity': f['severity'], 'detail_es': f['description']} for f in review['record']['findings']]}
            return self.store.gate(self.ID, data['version'], data['artifact_digest'], product_review, data['tests'],
                factory_digest=data['factory_digest'], source_sha=data['candidate_sha'],
                manual_review_id=data['manual_review_id'])


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
