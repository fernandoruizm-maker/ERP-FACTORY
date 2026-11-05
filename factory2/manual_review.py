"""Local chat-review records. Hashes bind declarations; they authenticate nobody."""
from datetime import date
import hashlib
import json
from pathlib import Path, PurePosixPath
import re

from .core import Blocked

REVIEWER = 'Claude, chat, no autenticado'
CLEAR = 'SIN OBJECIONES TÉCNICAS'
MAX_BYTES = 100_000
SECRET_PATTERN = re.compile(
    r'-----BEGIN (?:OPENSSH |RSA |EC |DSA |ENCRYPTED )?PRIVATE KEY-----|'
    r'\bgh[pousr]_[A-Za-z0-9]{30,}|\bgithub_pat_[A-Za-z0-9_]{40,}|'
    r'\bsk-(?:ant-|proj-)?[A-Za-z0-9_-]{32,}|\bxox[baprs]-[A-Za-z0-9-]{20,}')


def text(value, limit=10000):
    return isinstance(value, str) and bool(value.strip()) and len(value) <= limit


def hex_value(value, length):
    return isinstance(value, str) and re.fullmatch('[0-9a-f]{'+str(length)+'}', value) and value != '0'*length


def validate_document(raw):
    try:
        if not isinstance(raw, bytes) or len(raw) > MAX_BYTES:
            raise ValueError
        document = raw.decode('utf-8')
        if SECRET_PATTERN.search(document):
            raise Blocked('MANUAL_REVIEW_POSSIBLE_SECRET')
        blocks = re.findall(r'^```json\s*\n(.*?)^```\s*$', document, re.MULTILINE | re.DOTALL)
        if len(blocks) != 1:
            raise ValueError
        record = json.loads(blocks[0])
        if (not isinstance(record, dict) or set(record) != {'schema_version','pr','base_sha','reviewed_sha',
                'scope','reviewer','findings','conclusion','date'} or type(record['schema_version']) is not int
                or record['schema_version'] != 1 or not text(record['pr'],500)
                or not hex_value(record['base_sha'],40) or not hex_value(record['reviewed_sha'],40)
                or record['reviewer'] != REVIEWER or record['conclusion'] not in (CLEAR,'CORREGIR')
                or not isinstance(record['date'],str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}',record['date'])):
            raise ValueError
        date.fromisoformat(record['date'])
        scope = record['scope']
        if (not isinstance(scope,dict) or set(scope) != {'mode','files','diff'}
                or scope['mode'] not in ('CAMBIOS_PR','FABRICA_COMPLETA') or not text(scope['diff'])
                or not isinstance(scope['files'],list) or not scope['files']
                or not all(isinstance(p,str) and re.fullmatch(r'[A-Za-z0-9_./-]+',p)
                    and not PurePosixPath(p).is_absolute()
                    and not any(part in ('','.','..') for part in p.split('/')) for p in scope['files'])
                or len(set(scope['files'])) != len(scope['files'])):
            raise ValueError
        findings = record['findings']
        if not isinstance(findings,list) or len(findings)>100:
            raise ValueError
        for finding in findings:
            if (not isinstance(finding,dict) or set(finding) != {'severity','file','line','description','recommendation'}
                    or finding['severity'] not in ('critical','high','medium','low')
                    or finding['file'] not in scope['files'] or type(finding['line']) is not int
                    or finding['line'] < 1 or not text(finding['description']) or not text(finding['recommendation'])):
                raise ValueError
        if record['conclusion'] == CLEAR and any(f['severity'] in ('critical','high') for f in findings):
            raise Blocked('MANUAL_REVIEW_CONTRADICTORY_CONCLUSION')
        return record
    except Blocked:
        raise
    except (ValueError, TypeError, KeyError, UnicodeError, RecursionError):
        raise Blocked('MANUAL_REVIEW_FORMAT_INVALID') from None


def read_document(path, root):
    path, root = Path(path).absolute(), Path(root).absolute()
    try:
        path.resolve().relative_to(root.resolve())
        for candidate in (path,*path.parents):
            if candidate.is_symlink() or (hasattr(candidate,'is_junction') and candidate.is_junction()):
                raise ValueError
        if path.suffix != '.md' or path.name == 'PLANTILLA.md' or not path.is_file() or path.stat().st_size>MAX_BYTES:
            raise ValueError
        with path.open('rb') as stream:
            raw = stream.read(MAX_BYTES+1)
        validate_document(raw)
        return raw
    except Blocked:
        raise
    except (OSError, ValueError):
        raise Blocked('MANUAL_REVIEW_PATH_OR_CONTENT_INVALID') from None


def metadata(raw):
    record = validate_document(raw)
    return {'review_id':'manual:'+hashlib.sha256(raw).hexdigest(), 'source_sha':record['reviewed_sha'],
            'base_sha':record['base_sha'], 'conclusion':record['conclusion'], 'scope':record['scope'],
            'provenance_authenticated':False, 'publication_allowed':False, 'human_approvals':0,
            'record':record}
