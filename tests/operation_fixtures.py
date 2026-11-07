"""Entirely fictitious artifacts/people/coordination. No real authentication."""
import hashlib
import json
from pathlib import Path
import time

from factory2.core import canonical, digest
from factory2.operations import Coordinator
from factory2.review_import import PRIVATE_REPOSITORY, private_contract
from factory2.state import Store


def arm_fixture(root, cfg, *, encargo='botellas', attempt=1):
    """Explicit fictitious arm in the test's temporary root only."""
    root = Path(root)
    if root.resolve() == Path(__file__).resolve().parents[1]:
        raise ValueError('TEST_ARM_MUST_BE_TEMPORARY')
    path = root / 'state/armado.json'
    path.parent.mkdir(exist_ok=True)
    now = time.time()
    path.write_text(canonical({'encargo': encargo, 'attempt': attempt,
        'issued_at': now, 'expires_at': now + 600, 'config_digest': digest(cfg)}), encoding='utf-8')
    return path


def disabled_repository_config(root):
    """Copy the repository config into a test temporary directory; only disarm calls."""
    source = Path(__file__).resolve().parents[1] / 'config.json'
    path = Path(root) / 'config.json'
    if path.resolve() == source.resolve():
        raise ValueError('TEST_CONFIG_MUST_BE_TEMPORARY')
    data = json.loads(source.read_text(encoding='utf-8'))
    data['external_calls_enabled'] = False
    path.write_text(canonical(data), encoding='utf-8')
    return path


def coordinator(root):
    root = Path(root) / 'coordination'
    root.mkdir(exist_ok=True)
    (root / 'active-factory.json').write_text(canonical({
        'mode': 'SIMULATED_ONLY', 'active_factory': 'factory2',
        'original_stopped': True, 'expires_at': time.time() + 600}), encoding='utf-8')
    return Coordinator(root, simulation=True)


def config(root):
    path = Path(root) / 'fixture-config.json'
    path.write_text(canonical({'human_approvals_required': 1,
        'human_approval_roles': ['business'],
        'accounting_product_approvals': {'human_approvals_required': 2, 'roles': ['business', 'accounting']},
        'budget_currency': 'TST', 'max_calls_per_execution': 11, 'max_budget_usd_per_call': '1',
        'max_spend_per_execution': '2', 'max_spend_total': '4',
        'human_approvers': {'business': {'login': 'persona-a', 'id': '101'},
                            'accounting': {'login': 'persona-b', 'id': '202'}},
        'private_review_trust': {'repository': PRIVATE_REPOSITORY, 'validator_sha': 'b' * 40,
                                 'actor_id': '999'}}), encoding='utf-8')
    return path


def accounting_target():
    return {'kind': 'accounting_product', 'repository': 'ficticio/producto'}


def artifacts(root, *, run='123', changes=None):
    v2 = private_contract()
    packets = __import__(v2.__package__ + '.packets', fromlist=['build_packets'])
    body = 'FICTICIO, NO EJECUTAR\n'
    material = {'source_sha': 'a' * 40, 'factory_digest': digest('fabrica-ficticia'),
                'files': {'src/ficticio.py': {'text': body, 'sha256': hashlib.sha256(body.encode()).hexdigest()}}}
    manifest, parts = packets.build_packets(material, {'include': ['src/ficticio.py'], 'exclude': {}})
    response = {'source_sha': material['source_sha'], 'factory_digest': material['factory_digest'],
        'reviewed_files': ['src/ficticio.py'], 'coverage': 'complete', 'cross_component_review': False,
        'verdict': 'PASS', 'summary_es': 'Ensayo ficticio', 'findings': [], 'limitations_es': ['Simulacion, no Claude.']}
    part = {'protocol_version': 2, 'phase': 'part', 'part_id': 1, 'artifact_digest': digest(parts[0]), 'report': response}
    cross = {'protocol_version': 2, 'phase': 'cross', 'part_id': 0,
             'artifact_digest': digest(v2.cross_request(manifest, [part])),
             'report': {**response, 'cross_component_review': True}}
    bundle = {'protocol_version': 2, 'source_sha': material['source_sha'],
              'factory_digest': material['factory_digest'], 'parts': [part], 'cross': cross}
    provenance = {'repository': PRIVATE_REPOSITORY, 'validator_sha': 'b' * 40,
                  'source_sha': material['source_sha'], 'workflow_sha': 'c' * 40,
                  'run_id': run, 'run_attempt': 1, 'actor_id': '999'}
    report = {**v2.validate_result(manifest, bundle), 'source_sha': material['source_sha'],
              'factory_digest': material['factory_digest'], 'provenance': provenance}
    report.update(changes or {})
    folder = Path(root) / ('artifacts-' + run)
    folder.mkdir()
    for name, value in (('report.json', report), ('manifest.json', manifest)):
        (folder / name).write_bytes(canonical(value).encode('utf-8'))
    hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in folder.iterdir()}
    index = canonical(hashes).encode('utf-8')
    (folder / 'SHA256.json').write_bytes(index)
    receipt = {'provenance': provenance, 'source_sha': material['source_sha'],
               'factory_digest': material['factory_digest'], 'sha256_index': hashlib.sha256(index).hexdigest()}
    return folder, receipt


def store_fixture(root):
    store = Store(Path(root) / 'state.sqlite3', config_path=config(root), coordinator=coordinator(root))
    folder, receipt = artifacts(root)
    imported = store.import_factory_review(folder, receipt)
    return store, imported


def accept(store, task, version, role, imported):
    return store.accept(task, version, 'persona-a' if role == 'business' else 'persona-b', role,
                        source_sha=imported['source_sha'], factory_digest=imported['factory_digest'],
                        review_id=imported['review_id'], expires_at=time.time() + 60)
