"""Monitor only explicit demo jobs; never ingest issues, invite users or merge."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import time
from .common import Blocked, load_config, RateLimited
from .github import GitHub
from .queue import Queue, worker_lock
from .role_gate import refresh_roles


def tick(config, github, queue):
    jobs=config.get('trial_jobs',[]);numbers=config.get('trial_prs',[])
    if len(jobs)!=2 or len(set(jobs))!=2 or len(numbers)!=2 or len(set(numbers))!=2:
        raise Blocked('Se requieren dos trabajos y dos PR distintos')
    mapping=[]
    for job_id in jobs:
        job=queue.get(job_id)
        if not job:raise Blocked('Falta el ensayo registrado')
        mapping.append(json.loads(job['checkpoint'])['pr']['number'])
    if len(set(mapping))!=2 or set(mapping)!=set(numbers):
        raise Blocked('Los dos trabajos deben corresponder a los dos PR autorizados')
    results=[]
    for job_id in config['trial_jobs']:
        job=queue.get(job_id)
        if not job:raise Blocked('Falta el ensayo registrado')
        saved=json.loads(job['checkpoint'])
        number=saved['pr']['number']
        if number not in config['trial_prs']:
            raise Blocked('PR fuera de los dos ensayos autorizados')
        state=job['state']
        if state in {'WAITING_APPROVAL','APPROVED'}:
            state=refresh_roles(config,github,queue,job_id)
        saved=json.loads(queue.get(job_id)['checkpoint'])
        if state=='APPROVED':
            pr=github.get('/pulls/'+str(number))
            if pr['state']=='open' and pr['draft'] and not pr.get('merged') and pr['head']['sha']==saved['pr']['head_sha']:
                # Preserve evidence of REAL reviews before closing, never merge.
                saved['real_approval_verified_at']=datetime.now(timezone.utc).isoformat()
                saved['verified_statuses']=github.get('/commits/'+pr['head']['sha']+'/status')
                queue.set(job_id,'APPROVED',saved)
                closed=github.request('PATCH',github.prefix+'/pulls/'+str(number),{'state':'closed'})
                if closed['state']=='closed' and not closed.get('merged'):
                    state='CLOSED';queue.set(job_id,state,saved)
            else:
                reason='El ensayo dejó de ser un borrador abierto de la versión comprobada'
                github.status(pr['head']['sha'],'factory/quality','failure',reason)
                github.status(pr['head']['sha'],'factory/human-approval','pending',reason)
                state='BLOCKED';queue.set(job_id,state,saved,error=reason)
        results.append({'pr':number,'state':state,'reason':saved.get('approval_decision',{}).get('reason'),
                        'genuine_approval_seen':bool(saved.get('real_approval_verified_at'))})
    return results


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--config',required=True);parser.add_argument('--once',action='store_true')
    args=parser.parse_args();config=load_config(args.config)
    if len(config.get('trial_jobs',[]))!=2 or len(set(config.get('trial_prs',[])))!=2:
        raise Blocked('Este monitor requiere exactamente dos ensayos explícitos')
    state=Path(config['state_dir']);queue=Queue(state/'mvp.sqlite3');github=GitHub.from_config(config)
    with worker_lock(state/'trial.lock'):
        while not (state/'STOP').exists():
            delay=300
            try:
                rows=tick(config,github,queue)
                result={'updated_at':datetime.now(timezone.utc).isoformat(),'trials':rows,'mode':'approval-only; never merge'}
            except RateLimited as exc:
                delay=max(delay,exc.retry_at-time.time());result={'error':'Límite de GitHub; esperando'}
            except Exception as exc:
                result={'error':type(exc).__name__,'message':'No se ha confirmado ninguna aprobación en este ciclo'}
            (state/'monitor-status.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
            if args.once or ('trials' in result and all(r['state']=='CLOSED' for r in rows)):break
            deadline=time.monotonic()+delay
            while time.monotonic()<deadline and not (state/'STOP').exists():time.sleep(1)


if __name__=='__main__':main()
