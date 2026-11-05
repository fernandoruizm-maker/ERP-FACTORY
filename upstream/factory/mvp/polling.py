"""Outbound-only ingress. A human label event authorizes one issue revision."""
from datetime import datetime, timezone
import json
from pathlib import Path
import time
from .common import Blocked, RateLimited, load_config, digest
from .queue import Queue, worker_lock


def latest_label_event(events, label):
    relevant = [e for e in events if e.get('event') in {'labeled', 'unlabeled'}
                and e.get('label', {}).get('name') == label]
    if any(type(e.get('id')) is not int for e in relevant):
        raise Blocked('Invalid label event identity')
    return max(relevant, key=lambda e: e['id']) if relevant else None


def timestamp(value):
    try:
        result = datetime.fromisoformat(value.replace('Z', '+00:00'))
        if result.tzinfo is None:
            raise ValueError('Timezone required')
        return result
    except (ValueError, TypeError, AttributeError):
        raise Blocked('Invalid issue event timestamp') from None


def authorized_grant(config, issue, event):
    if (not event or event.get('event') != 'labeled' or 'pull_request' in issue
            or issue.get('state') != 'open'
            or config['trigger_label'] not in [l['name'] for l in issue.get('labels', [])]):
        return False
    actor = event.get('actor') or {}
    return (actor.get('type') == 'User' and actor.get('login') in config['allowed_requesters']
            and timestamp(issue['updated_at']) <= timestamp(event['created_at']))


def validate_poll_request(config, github, issue, payload):
    if payload.get('ingress') != 'poll':
        return
    event = latest_label_event(github.issue_events(issue['number']), config['trigger_label'])
    if (not authorized_grant(config, issue, event)
            or event['id'] != payload.get('label_event_id')
            or event['actor']['login'] != payload['requester']):
        raise Blocked('Polling authorization changed; apply ai-factory again after finishing the issue')


def poll_once(config, github, queue):
    enqueued, skipped = [], []
    issues = github.open_issues(config['trigger_label'], queue)
    for listed in issues:
        if 'pull_request' in listed or listed.get('state') != 'open':
            continue
        issue = github.issue(listed['number'])
        event = latest_label_event(github.issue_events(issue['number']), config['trigger_label'])
        if not event:
            skipped.append({'issue': issue['number'], 'reason': 'missing_label_event'})
            continue
        delivery = f"poll:{config['repository']}:{event['id']}"
        if queue.delivery_job(delivery):
            continue  # Comments/edits/restarts never authorize another run of this label event.
        if not authorized_grant(config, issue, event):
            skipped.append({'issue': issue['number'], 'reason': 'fresh_human_label_required'})
            continue
        requester = event['actor']['login']
        if not github.can_write(requester):
            skipped.append({'issue': issue['number'], 'reason': 'requester_has_no_write_access'})
            continue
        ident = queue.enqueue(delivery, {'repository': config['repository'], 'requester': requester,
            'issue_number': issue['number'], 'issue_updated_at': issue['updated_at'],
            'ingress': 'poll', 'label_event_id': event['id']})
        enqueued.append(ident)
    return {'enqueued': enqueued, 'skipped': skipped, 'open_opted_in_issues': len(issues)}


def cycle(config, github, agent, runner, queue, *, now=None, should_pause=lambda: False):
    from .pipeline import Pipeline
    from .approval import refresh
    now = time.time() if now is None else now
    retry_at = queue.meta_get('pilot_retry_at', 0)
    if now < retry_at:
        return {'state': 'BACKOFF', 'retry_at': retry_at}
    job = None
    result = {}
    try:
        result.update(poll_once(config, github, queue))
        # Keep collected jobs queued while governance is incomplete; no model calls.
        github.governance(config['base_branch'])
        for item in queue.list():
            if item['state'] in {'WAITING_APPROVAL', 'APPROVED'}:
                refresh(config, github, queue, item['id'])
        if should_pause():
            return {**result, 'state': 'PAUSED'}
        from .quality_watch import watch
        try:
            result['quality_watch'] = watch(config, github, runner, queue, should_pause=should_pause)
        except RateLimited:
            raise
        except Exception:
            result['quality_watch'] = [{'state': 'error', 'reason': 'Monitor no verificable; sin aprobación'}]
        if should_pause():
            return {**result, 'state': 'PAUSED'}
        job = queue.claim()
        if job:
            result['result'] = Pipeline(config, github, agent, runner, queue).execute(job)
            result['job_id'] = job['id']
        pending = any(j['state'] == 'WAITING_APPROVAL' for j in queue.list())
        result['state'] = result.get('result', {}).get('state', 'WAITING_APPROVAL' if pending else 'WATCHING')
        queue.meta_set('pilot_retry_at', 0)
        queue.meta_set('pilot_error_count', 0)
    except RateLimited as exc:
        if job:
            queue.set(job['id'], 'QUEUED', error='Deferred by GitHub rate limit')
        queue.meta_set('pilot_retry_at', exc.retry_at)
        result.update(state='BACKOFF', retry_at=exc.retry_at)
    except Exception as exc:
        message = str(exc) if isinstance(exc, Blocked) else type(exc).__name__
        if job:
            current = queue.get(job['id'])
            state = 'PUBLISHING' if current['state'] == 'PUBLISHING' and not isinstance(exc, Blocked) else 'BLOCKED'
            queue.set(job['id'], state, error=message)
        result.update(state='BLOCKED', reason=message)
        if not isinstance(exc, Blocked):
            attempts = min(queue.meta_get('pilot_error_count', 0) + 1, 5)
            queue.meta_set('pilot_error_count', attempts)
            queue.meta_set('pilot_retry_at', now + 300 * 2 ** (attempts - 1))
    return result


def save_status(config, queue, result):
    report = {**result, 'updated_utc': datetime.now(timezone.utc).isoformat(),
              'repository': config['repository'], 'interval_seconds': config.get('poll_interval_seconds', 300),
              'jobs': queue.list(), 'automatic_merge': False, 'automatic_deployment': False}
    queue.meta_set('pilot_status', report)
    path = Path(config['state_dir']) / 'pilot-status.json'
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    temporary.replace(path)
    if config.get('pilot_status_file'):
        labels = {'WATCHING': 'Esperando tareas de GitHub', 'BLOCKED': 'Bloqueado: requiere atención',
                  'PAUSED': 'Pausado', 'BACKOFF': 'Esperando para volver a consultar GitHub',
                  'RUNNING': 'Consultando GitHub o preparando un cambio',
                  'WAITING_APPROVAL': 'PR preparado: aprobación humana pendiente', 'STOPPED': 'Detenido'}
        reason = report.get('reason', '')
        if 'strict factory/quality' in reason:
            reason = 'Faltan los dos checks obligatorios vinculados a la App en la Ruleset de main.'
        elif 'administrator audit' in reason:
            reason = 'La Ruleset cambió y necesita una nueva verificación administrativa.'
        elif 'Baseline must contain' in reason:
            reason = 'El repositorio necesita código y pruebas base que pasen antes del primer cambio automático.'
        text = ('PILOTO RDC\nEstado: ' + labels.get(report['state'], report['state']) + '\n'
                + (('Detalle: ' + reason + '\n') if reason else '')
                + f"Última revisión: {report['updated_utc']} (UTC)\n"
                + f"Tareas registradas: {len(report['jobs'])}\n"
                + 'Consulta cada cinco minutos mientras el PC y el piloto estén encendidos.\n'
                + 'Aprobación humana obligatoria. No integra ni despliega cambios automáticamente.\n')
        dest = Path(config['pilot_status_file'])
        tmp = dest.with_suffix('.tmp')
        try:
            tmp.write_text(text, encoding='utf-8-sig')
            tmp.replace(dest)
        except OSError:
            pass  # An open desktop viewer must not interfere with the safety gate.
    return report


def pilot(config_path, *, once=False):
    from .__main__ import components
    config = load_config(config_path)
    queue = Queue(Path(config['state_dir']) / 'mvp.sqlite3')
    pause_file = Path(config['state_dir']) / 'pilot.pause'
    with worker_lock(Path(config['state_dir']) / 'worker.lock'):
        queue.recover()
        last_state = None
        component_sha, components_value = None, None
        while True:
            fresh = load_config(config_path)
            if fresh['state_dir'] != config['state_dir']:
                raise Blocked('Restart the pilot after moving its state directory')
            config = fresh
            interval = config.get('poll_interval_seconds', 300)
            if type(interval) is not int or not 60 <= interval <= 3600:
                raise Blocked('Polling interval must be 60..3600 seconds')
            if pause_file.exists():
                result = {'state': 'PAUSED'}
            else:
                save_status(config, queue, {'state': 'RUNNING'})
                try:
                    if component_sha != digest(config):
                        components_value = components(config)
                        component_sha = digest(config)
                    github, agent, runner = components_value
                    result = cycle(config, github, agent, runner, queue, should_pause=pause_file.exists)
                    interval = max(interval, getattr(github, 'poll_interval', 0))
                except Exception as exc:
                    result = {'state': 'BLOCKED', 'reason': str(exc) if isinstance(exc, Blocked) else type(exc).__name__}
            report = save_status(config, queue, result)
            marker = (report['state'], report.get('reason'), report.get('job_id'))
            if marker != last_state or once:
                print(json.dumps({k: report.get(k) for k in ('state', 'reason', 'job_id', 'updated_utc')},
                                 ensure_ascii=False), flush=True)
                last_state = marker
            if once:
                return report
            until = time.monotonic() + interval
            was_paused = pause_file.exists()
            while time.monotonic() < until and pause_file.exists() == was_paused:
                time.sleep(1)
