"""One operator-authorized, hash-bound contract transition; never model edits."""
import hashlib
from .common import Blocked

PATH = 'tests/test_health.py'
OLD = "self.assertEqual(json.loads(body), {'status': 'ok'})"
NEW = "self.assertEqual(json.loads(body), {'status': 'operativo'})"
VERSION_PATH = 'tests/test_factory_health_text.py'
VERSION_REPLACEMENTS = {
    PATH: [(NEW, "self.assertEqual(json.loads(body), {'status': 'operativo', 'version': '0.1.0'})", 3)],
    VERSION_PATH: [("b'{\"status\":\"operativo\"}'", "b'{\"status\":\"operativo\",\"version\":\"0.1.0\"}'", 2),
                   ("headers.get('Content-Length'), '22'", "headers.get('Content-Length'), '40'", 2)]}

def transition_details(issue_number):
    if issue_number == 12:
        return (5, 'El propietario autorizó actualizar exclusivamente el JSON exacto de /health con version=0.1.0 y su longitud exacta de 22 a 40 bytes. '
                   'Cinco pruebas existentes conservan todas sus aserciones; siete expectativas literales cambian en tests/test_health.py y tests/test_factory_health_text.py.')
    return (3, 'El propietario autorizó cambiar exactamente tres expectativas status ok por operativo en tests/test_health.py; no se elimina ni debilita ninguna aserción.')

def transition(config, issue_number, base, files):
    if issue_number == 12:
        grant = config.get('health_version_transition')
        if not grant:
            return {}
        if (config['repository'] != 'fernandoruizm-maker/rdc' or grant.get('issue') != 12
                or grant.get('base_sha') != base
                or set(grant.get('file_hashes', {})) != set(VERSION_REPLACEMENTS)):
            raise Blocked('Version transition authorization does not match repository/issue/base/files')
        updated = {}
        for path, replacements in VERSION_REPLACEMENTS.items():
            original = files.get(path, '')
            if hashlib.sha256(original.encode()).hexdigest() != grant['file_hashes'][path]:
                raise Blocked('Version transition test fingerprint changed')
            text = original
            for old, new, count in replacements:
                if text.count(old) != count:
                    raise Blocked('Version transition exact expectations changed')
                text = text.replace(old, new)
            updated[path] = text
        return updated
    grant = config.get('health_text_transition')
    if not grant or issue_number != 11:
        return {}
    if (config['repository'] != 'fernandoruizm-maker/rdc'
            or grant.get('issue') != 11 or grant.get('base_sha') != base):
        raise Blocked('Health transition authorization does not match repository/issue/base')
    original = files.get(PATH, '')
    if (hashlib.sha256(original.encode()).hexdigest() != grant.get('test_sha256')
            or original.count(OLD) != 3):
        raise Blocked('Health transition test fingerprint changed')
    # The entire file is pinned. Only three exact equality expectations change.
    # All test names, assertions, HTTP checks, errors and security checks remain.
    return {PATH: original.replace(OLD, NEW)}
