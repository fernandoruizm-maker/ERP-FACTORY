"""Deterministic risk and independent, explicit human decisions. No GitHub writes."""
from datetime import datetime, timedelta
import re
import unicodedata
from .common import Blocked, safe_path

ROLES = frozenset({'CONTADOR', 'TECNICO'})
ACCOUNTING = frozenset({'contabilidad','contador','accounting','impuesto','impuestos','tax','taxes',
    'cierre','cierres','closing','ledger','asiento','asientos','saldos','balances','money','dinero',
    'payments','pagos','finance','facturas','invoices','cobros','tesoreria'})
TECHNICAL = frozenset({'tecnico','technical','permission','permissions','permisos','auth','security',
    'seguridad','database','databases','db','base_datos','migrations','migration','migracion','migraciones',
    'storage','almacenamiento','files','archivos','borrado','delete','deletion','backups','respaldos'})

def normalize(value):
    return ''.join(c for c in unicodedata.normalize('NFKD', value.casefold()) if not unicodedata.combining(c))

def classify(paths):
    """Include old and new paths of renames and deleted paths. Unknown means high."""
    roles, reasons, levels = set(), [], []
    if not paths:
        raise Blocked('No hay archivos para clasificar')
    for value in sorted(set(paths)):
        path = normalize(safe_path(value))
        words = set(re.split(r'[^a-z0-9]+', path))
        found = set()
        if words & ACCOUNTING:
            found.add('CONTADOR')
        if words & TECHNICAL or path.startswith(('ai-factory/', '.github/', 'factory/', 'brain/')):
            found.add('TECNICO')
        if found:
            levels.append('alto'); roles.update(found)
            reasons.append(value + ': requiere ' + ' y '.join(sorted(found)))
        elif path.startswith('docs/user-guide/') and path.endswith('.md'):
            levels.append('bajo'); reasons.append(value + ': documentación de usuario autorizada')
        elif re.fullmatch(r'web/presentation/[a-z0-9_-]+\.css', path):
            levels.append('medio'); reasons.append(value + ': presentación sin permiso para tocar lógica')
        else:
            levels.append('alto'); roles.add('TECNICO')
            reasons.append(value + ': código o ruta sin clasificación segura; revisión técnica obligatoria')
    level = max(levels, key=['bajo','medio','alto'].index)
    return {'level':level, 'roles':sorted(roles), 'reasons':reasons}

def stamp(value):
    result = datetime.fromisoformat(value.replace('Z','+00:00'))
    if result.tzinfo is None:
        raise ValueError('Timestamp without timezone')
    return result

def validate_policy(policy):
    owner, specialist = policy['owner'], policy['specialist']
    for person in (owner, specialist):
        if (not isinstance(person['login'], str) or not re.fullmatch(r'[A-Za-z0-9-]+',person['login'])
                or type(person['id']) is not int or person['id'] <= 0):
            raise ValueError('Invalid user identity')
    if owner['id'] == specialist['id'] or owner['login'].casefold() == specialist['login'].casefold():
        raise ValueError('Two distinct users required')
    if not set(specialist['roles']).issubset(ROLES) or not specialist['roles']:
        raise ValueError('Invalid assigned roles')
    if policy.get('ttl_hours') != 24:
        raise ValueError('Approvals expire after 24 hours')
    if (not isinstance(policy['factory_login'],str) or not policy['factory_login'].endswith('[bot]')
            or policy['factory_login'].casefold() in {owner['login'].casefold(),specialist['login'].casefold()}):
        raise ValueError('Invalid factory identity')
    return owner, specialist

def matches(user, identity):
    return (user.get('type') == 'User' and user.get('id') == identity['id']
            and user.get('login','').casefold() == identity['login'].casefold())

def evaluate(policy, reviews, *, classification, head, author, now, not_before, can_write):
    roles = classification.get('roles', [])
    result = {'approved':False,'reason':'Faltan aprobaciones válidas','roles':roles,'review_ids':{}}
    def deny(reason):
        return {**result, 'reason':reason}
    try:
        owner, specialist = validate_policy(policy)
        boundary = stamp(not_before)
        if (not re.fullmatch('[a-f0-9]{40}',head) or boundary > now
                or classification['level'] not in {'bajo','medio','alto'}
                or not set(roles).issubset(ROLES)
                or (classification['level']=='alto' and not roles)
                or (classification['level']!='alto' and roles)):
            return deny('La versión o la clasificación no son verificables')
        people = [owner] + ([specialist] if classification['level']=='alto' else [])
        if not set(roles).issubset(set(specialist['roles'])):
            return deny('Falta una persona designada para alguno de los roles')
        for identity in people:
            if (author.get('id') == identity['id']
                    or author.get('login','').casefold() == identity['login'].casefold()):
                return deny('El autor del PR no puede cubrir una aprobación independiente')
            if not can_write(identity['login']):
                return deny(identity['login'] + ': falta acceso de colaborador con escritura')
            own = sorted([r for r in reviews if matches(r.get('user',{}), identity) and r.get('state')!='PENDING'],
                         key=lambda r:stamp(r['submitted_at']))
            effective = [r for r in own if r['state'] in {'APPROVED','DISMISSED','CHANGES_REQUESTED'}]
            if not effective or effective[-1]['state'] != 'APPROVED':
                return deny(identity['login'] + ': falta una aprobación formal vigente')
            approval = effective[-1]
            submitted = stamp(approval['submitted_at'])
            if sum(stamp(r['submitted_at'])==submitted for r in effective)!=1:
                return deny('Dos decisiones coinciden en el tiempo; enviar una nueva revisión inequívoca')
            if (approval.get('commit_id') != head or submitted < boundary
                    or not timedelta(0) <= now-submitted < timedelta(hours=24)):
                return deny(identity['login'] + ': aprobación anterior al cambio, caducada o de otra versión')
            # A later explicit inability to evaluate revokes this candidate until a new approval.
            if any(stamp(r['submitted_at']) >= submitted and r.get('commit_id') == head
                   and 'NO PUEDO EVALUAR' in normalize(r.get('body') or '').upper() for r in own):
                return deny(identity['login'] + ': no puedo evaluar esto; se mantiene bloqueado')
            # The authenticated GitHub APPROVED event covers the file-derived roles.
            # Optional prose never grants approval; explicit inability still revokes it above.
            result['review_ids'][identity['login']] = approval['id']
        return {**result, 'approved':True,'reason':'Aprobaciones auténticas, distintas y vigentes para todos los roles'}
    except (KeyError, TypeError, ValueError, AttributeError):
        return deny('Datos de aprobación incompletos o no verificables')
