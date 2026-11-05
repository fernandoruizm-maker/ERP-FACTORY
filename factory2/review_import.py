"""Single offline V2 import path. Integrity is NOT authenticated GitHub origin.

An expected receipt must come from a future trusted acquisition step. This local
implementation always records provenance_authenticated=False, even in fixtures.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys

from .core import Blocked, canonical, digest

PRIVATE_REPOSITORY = 'fernandoruizm-maker/ERP-FACTORY-revision'
PROVENANCE_FIELDS = {'repository', 'source_sha', 'validator_sha', 'workflow_sha',
                     'run_id', 'run_attempt', 'actor_id'}
ARTIFACT_NAMES = {'report.json', 'manifest.json', 'diagnostic.json', 'INFORME.txt', 'response.txt', 'budget.json'}


def private_contract():
    # Fixed local trusted staging path, NEVER a path from an imported artifact.
    name = '_factory2_private_v2'
    root = Path(__file__).resolve().parent.parent / 'ERP-FACTORY-revision/reviewer'
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, root / '__init__.py',
                                                     submodule_search_locations=[str(root)])
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    return __import__(name + '.validation', fromlist=['validate_result'])


def hex_value(value, size):
    return isinstance(value, str) and re.fullmatch('[0-9a-f]{' + str(size) + '}', value) and value != '0' * size


def verify_documents(report_bytes, manifest_bytes, receipt, policy):
    try:
        if not isinstance(policy, dict) or not isinstance(receipt, dict):
            raise Blocked('REVIEW_TRUST_POLICY_PENDING')
        if set(policy) != {'repository', 'validator_sha', 'actor_id'}:
            raise Blocked('REVIEW_TRUST_POLICY_PENDING')
        if (policy['repository'] != PRIVATE_REPOSITORY or not hex_value(policy['validator_sha'], 40)
                or not isinstance(policy['actor_id'], str) or not policy['actor_id'].isdigit()):
            raise Blocked('REVIEW_TRUST_POLICY_PENDING')
        if set(receipt) != {'provenance', 'source_sha', 'factory_digest', 'sha256_index'}:
            raise Blocked('REVIEW_RECEIPT_INVALID')
        provenance = receipt['provenance']
        if (not isinstance(provenance, dict) or set(provenance) != PROVENANCE_FIELDS
                or any(provenance[k] != policy[k] for k in policy)
                or not hex_value(provenance['source_sha'], 40)
                or not hex_value(provenance['workflow_sha'], 40)
                or type(provenance['run_attempt']) is not int or provenance['run_attempt'] != 1
                or not isinstance(provenance['run_id'], str) or not provenance['run_id'].isdigit()
                or provenance['source_sha'] != receipt['source_sha']
                or not hex_value(receipt['factory_digest'], 64)
                or not hex_value(receipt['sha256_index'], 64)):
            raise Blocked('REVIEW_PROVENANCE_INVALID')
        report, manifest = json.loads(report_bytes), json.loads(manifest_bytes)
        if (report.get('status') != 'NEEDS_HUMAN_REVIEW'
                or report.get('publication_allowed') is not False
                or type(report.get('human_approvals')) is not int or report['human_approvals'] != 0
                or report.get('provenance') != provenance
                or report.get('unvalidated_response_saved') is True
                or any(report.get(k) != receipt[k] or manifest.get(k) != receipt[k]
                       for k in ('source_sha', 'factory_digest'))):
            raise Blocked('REVIEW_NOT_ACCEPTABLE')
        checked = private_contract().validate_result(manifest, report.get('review'))
        if checked['status'] != 'NEEDS_HUMAN_REVIEW' or any(report.get(k) != v for k, v in checked.items()):
            raise Blocked('REVIEW_CONTRACT_MISMATCH')
        optional_hashes = {'material_sha256', 'response_sha256'}
        allowed = set(checked) | {'source_sha', 'factory_digest', 'provenance'} | optional_hashes
        if set(report) - allowed or any(not hex_value(report[k], 64) for k in optional_hashes & set(report)):
            raise Blocked('REVIEW_CONTRACT_MISMATCH')
        return {'source_sha': receipt['source_sha'], 'factory_digest': receipt['factory_digest'],
                'review_id': digest(receipt), 'provenance': provenance,
                'artifact_index_sha256': receipt['sha256_index'],
                'provenance_authenticated': False, 'status': 'NEEDS_HUMAN_REVIEW'}
    except (ValueError, KeyError, TypeError, AttributeError, RecursionError, OSError, ImportError):
        raise Blocked('PRIVATE_REVIEW_IMPORT_BLOCKED') from None


def import_artifacts(directory, receipt, policy):
    """Read bounded, exact artifact names; no extraction, requests or execution."""
    root = Path(directory)
    try:
        for path in (root, *root.parents):
            if path.is_symlink() or (hasattr(path, 'is_junction') and path.is_junction()):
                raise Blocked('ARTIFACT_PATH_UNSAFE')
        index_path = root / 'SHA256.json'
        if index_path.is_symlink() or index_path.stat().st_size > 10000:
            raise Blocked('ARTIFACT_INDEX_INVALID')
        raw_index = index_path.read_bytes()
        if hashlib.sha256(raw_index).hexdigest() != receipt['sha256_index']:
            raise Blocked('ARTIFACT_INDEX_MISMATCH')
        hashes = json.loads(raw_index)
        if (not isinstance(hashes, dict) or not {'report.json', 'manifest.json'} <= set(hashes)
                or not set(hashes) <= ARTIFACT_NAMES
                or {p.name for p in root.iterdir()} != set(hashes) | {'SHA256.json'}):
            raise Blocked('ARTIFACT_INDEX_INVALID')
        files, size = {}, 0
        for name, expected in hashes.items():
            path = root / name
            if path.is_symlink() or not path.is_file() or not hex_value(expected, 64):
                raise Blocked('ARTIFACT_FILE_INVALID')
            size += path.stat().st_size
            if size > 20_000_000:
                raise Blocked('ARTIFACT_SIZE_LIMIT')
            files[name] = path.read_bytes()
            if hashlib.sha256(files[name]).hexdigest() != expected:
                raise Blocked('ARTIFACT_DIGEST_MISMATCH')
        metadata = verify_documents(files['report.json'], files['manifest.json'], receipt, policy)
        return metadata, files['report.json'], files['manifest.json'], raw_index
    except (OSError, ValueError, KeyError, TypeError, AttributeError, RecursionError):
        raise Blocked('PRIVATE_REVIEW_IMPORT_BLOCKED') from None


def verify_stored(record, policy):
    """Revalidate persisted bytes and current policy each time gate uses the ID."""
    try:
        receipt = json.loads(record['receipt'])
        hashes = json.loads(record['hash_index'])
        if (hashlib.sha256(record['hash_index']).hexdigest() != receipt['sha256_index']
                or hashlib.sha256(record['report']).hexdigest() != hashes['report.json']
                or hashlib.sha256(record['manifest']).hexdigest() != hashes['manifest.json']):
            raise Blocked('STORED_REVIEW_CHANGED')
        metadata = verify_documents(record['report'], record['manifest'], receipt, policy)
        if metadata['review_id'] != record['id']:
            raise Blocked('STORED_REVIEW_CHANGED')
        return metadata
    except (ValueError, KeyError, TypeError):
        raise Blocked('PRIVATE_REVIEW_IMPORT_BLOCKED') from None
