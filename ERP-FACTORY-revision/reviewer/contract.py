import hashlib
import json
import re


class Blocked(ValueError):
    """Only fixed reason codes may reach logs."""


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def digest(value):
    return sha256(canonical(value).encode('utf-8'))


def source_sha(value):
    if not isinstance(value, str) or not re.fullmatch('[0-9a-f]{40}', value) or value == '0' * 40:
        raise Blocked('INVALID_COMMIT')
    return value


# Heuristic, not a guarantee that arbitrary text contains no secrets.
SECRET_PATTERN = re.compile(
    r'-----BEGIN (?:OPENSSH |RSA |EC )?PRIVATE KEY-----|'
    r'\bgh[pousr]_[A-Za-z0-9]{30,}|\bgithub_pat_[A-Za-z0-9_]{40,}|'
    r'\bsk-(?:ant-|proj-)?[A-Za-z0-9_-]{32,}|\bxox[baprs]-[A-Za-z0-9-]{20,}'
)


def safe_material(raw):
    if SECRET_PATTERN.search(raw):
        raise Blocked('POSSIBLE_SECRET')
