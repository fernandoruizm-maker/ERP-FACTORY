"""Persisted role gate. Only this controller publishes human-approval statuses."""
from datetime import datetime, timezone
import json
from .common import Blocked, digest
from .dual_approval import classify, evaluate, stamp
from ..memory import Brain

def refresh_roles(config, github, queue, job_id):
    job = queue.get(job_id)
    if not job or job['state'] not in {'WAITING_APPROVAL','APPROVED'}:
        raise Blocked('El trabajo no está esperando revisión')
    saved = json.loads(job['checkpoint'])
    sha = saved['pr']['head_sha']
    def invalidate(reason, head=sha):
        github.status(head,'factory/quality','failure','La versión o evidencia cambió; repetir comprobación')
        github.status(head,'factory/human-approval','pending',reason)
        queue.set(job_id,'BLOCKED',saved,error=reason)
        return 'BLOCKED'
    def same(pr):
        return (pr['state']=='open' and not pr.get('merged') and pr['head']['sha']==sha
            and (pr.get('draft') is True if config.get('trial_prs') else True)
            and pr['base']['sha']==saved['base_sha'] and pr['base']['ref']==config['base_branch']
            and pr['base']['repo']['full_name']==config['repository']
            and digest({'title':pr['title'],'body':pr.get('body') or ''})==saved['report_sha'])
    try:
        pr = github.get('/pulls/'+str(saved['pr']['number']))
        if pr['state']=='closed':
            if pr.get('merged'):
                if config.get('trial_prs'):
                    saved['integration']={k:pr.get(k) for k in ('merge_commit_sha','merged_at','merged_by')}
                    return invalidate('ALERTA: se integró un ensayo que debía cerrarse sin integrar')
                if (pr['head']['sha']!=sha or pr['base']['ref']!=config['base_branch']
                        or pr['base']['repo']['full_name']!=config['repository']):
                    return invalidate('Se integró un candidato distinto')
                saved['integration']={k:pr.get(k) for k in ('merge_commit_sha','merged_at','merged_by')}
                queue.set(job_id,'MERGED',saved)
                return 'MERGED'
            queue.set(job_id,'CLOSED',saved)
            return 'CLOSED'
        if (not same(pr) or github.base(config['base_branch'])!=saved['base_sha']
                or saved['config_sha']!=digest(config)
                or saved['brain_sha']!=Brain.load(config['brain_dir']).fingerprint):
            return invalidate('Cambió el código, destino, informe o configuración',pr['head']['sha'])
        paths = github.changed_paths(pr['number'])
        if set(paths)!=set(saved['changed_paths']):
            return invalidate('Cambió la lista real de archivos')
        classification = classify(paths)
        if any(classification[k]!=saved['classification'][k] for k in ('level','roles')):
            return invalidate('La clasificación no coincide con los archivos reales')
        events = github.issue_events(pr['number'])
        if any(e.get('event') in {'head_ref_force_pushed','head_ref_restored','base_ref_changed'}
               and stamp(e['created_at'])>=stamp(saved['approval_ready_at']) for e in events):
            return invalidate('La rama cambió después de preparar la revisión')
        github.governance(config['base_branch'])
        if not github.quality_passed(sha,config['approval_policy']['factory_login']):
            return invalidate('Falta calidad vigente publicada por la App')
        identities = {config['approval_policy'][key]['id'] for key in ('owner','specialist')}
        def relevant_reviews():
            return [r for r in github.reviews(pr['number']) if r.get('user',{}).get('id') in identities]
        reviews = relevant_reviews()
        seen = saved.get('review_bodies',{})
        for review in reviews:
            key=str(review['id']); fingerprint=digest(review.get('body') or '')
            if key in seen and seen[key]!=fingerprint:
                return invalidate('Se editó una revisión ya observada; repetir revisión')
            seen[key]=fingerprint
        saved['review_bodies']=seen
        decision = evaluate(config.get('approval_policy',{}),reviews,classification=classification,
            head=sha,author=pr['user'],now=datetime.now(timezone.utc),
            not_before=saved['approval_ready_at'],can_write=github.can_write)
        current=github.get('/pulls/'+str(pr['number']))
        if not same(current) or github.base(config['base_branch'])!=saved['base_sha']:
            return invalidate('La versión cambió mientras se revisaba',current['head']['sha'])
        # A concurrent revocation or edit must not be hidden by stale review data.
        if reviews!=relevant_reviews():
            decision={'approved':False,'reason':'Las revisiones cambiaron; se comprobarán de nuevo',
                      'roles':classification['roles']}
        state='APPROVED' if decision['approved'] else 'WAITING_APPROVAL'
        github.status(sha,'factory/human-approval','success' if decision['approved'] else 'pending',decision['reason'])
        saved['approval_decision']=decision
        queue.set(job_id,state,saved)
        return state
    except Exception as exc:
        # Network failures never become approval. Clear an existing success where possible.
        reason='No se pudo verificar la aprobación: '+type(exc).__name__
        try:
            github.status(sha,'factory/human-approval','pending',reason)
        finally:
            queue.set(job_id,'WAITING_APPROVAL',saved,error=reason)
        return 'WAITING_APPROVAL'
