"""Validate a declared retirement, never authenticate it or inspect the original."""
from datetime import date
import json
from pathlib import Path

from .core import Blocked


RECORD_PATH = Path(__file__).resolve().parent.parent / 'docs/retirada-original.json'
MAX_RECORD_BYTES = 16384


def _object(value, fields):
    if not isinstance(value, dict):
        raise Blocked('ORIGINAL_RETIREMENT_INVALID')
    if fields - set(value):
        raise Blocked('ORIGINAL_RETIREMENT_INCOMPLETE')
    if set(value) - fields:
        raise Blocked('ORIGINAL_RETIREMENT_INVALID')


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise Blocked('ORIGINAL_RETIREMENT_INVALID')
        result[key] = value
    return result


def _date(value):
    try:
        parsed = date.fromisoformat(value)
        if parsed.isoformat() != value or parsed > date.today():
            raise ValueError
        return parsed
    except (ValueError, TypeError):
        raise Blocked('ORIGINAL_RETIREMENT_INVALID') from None


def read_retirement(path=RECORD_PATH):
    """Return declaration metadata only; reread on each call, fail closed."""
    path = Path(path).absolute()
    try:
        for item in (path, *path.parents):
            if item.is_symlink() or (hasattr(item, 'is_junction') and item.is_junction()):
                raise Blocked('ORIGINAL_RETIREMENT_PATH_UNSAFE')
        with path.open('rb') as handle:
            raw = handle.read(MAX_RECORD_BYTES + 1)
        if len(raw) > MAX_RECORD_BYTES:
            raise Blocked('ORIGINAL_RETIREMENT_INVALID')
        record = json.loads(raw.decode('utf-8'), object_pairs_hook=_unique)
    except FileNotFoundError:
        raise Blocked('ORIGINAL_RETIREMENT_MISSING') from None
    except Blocked:
        raise
    except (OSError, ValueError, UnicodeError, RecursionError):
        raise Blocked('ORIGINAL_RETIREMENT_INVALID') from None

    _object(record, {'schema_version', 'kind', 'declared_on', 'declared_by',
                     'provenance_authenticated', 'vm', 'github_app',
                     'windows_inventory', 'openai', 'archive', 'original_restored'})
    _object(record['vm'], {'name', 'removed'})
    _object(record['github_app'], {'id', 'removed', 'private_key_removed',
                                   'installation_removed'})
    _object(record['windows_inventory'], {'checked_on', 'scope', 'factory_tasks_found',
                                          'factory_services_found', 'pilot_pause_preserved'})
    declared_on = _date(record['declared_on'])
    checked_on = _date(record['windows_inventory']['checked_on'])
    if type(record['original_restored']) is not bool:
        raise Blocked('ORIGINAL_RETIREMENT_INVALID')
    if record['original_restored']:
        raise Blocked('ORIGINAL_RESTORED')
    app = record['github_app']
    inventory = record['windows_inventory']
    if (type(record['schema_version']) is not int or record['schema_version'] != 1
            or record['kind'] != 'DECLARACION_NO_AUTENTICADA'
            or record['declared_by'] != 'Fernando'
            or record['provenance_authenticated'] is not False
            or record['vm']['name'] != 'RDC-Piloto-Aislado'
            or record['vm']['removed'] is not True
            or type(app['id']) is not int or app['id'] != 5603415
            or any(app[field] is not True for field in
                   ('removed', 'private_key_removed', 'installation_removed'))
            or inventory['scope'] != 'TAREAS_Y_SERVICIOS_FILTRADOS_EN_ESTE_PC'
            or inventory['factory_tasks_found'] is not False
            or inventory['factory_services_found'] is not False
            or inventory['pilot_pause_preserved'] is not True
            or checked_on > declared_on
            or record['openai'] != 'NO_EXISTIA'
            or record['archive'] != 'NO_POR_DECISION_DE_FERNANDO'):
        raise Blocked('ORIGINAL_RETIREMENT_CONTRADICTORY')
    return {'status': 'ORIGINAL_RETIRED_DECLARED',
            'declared_on': record['declared_on'], 'declared_by': record['declared_by'],
            'provenance_authenticated': False, 'publication_allowed': False}
