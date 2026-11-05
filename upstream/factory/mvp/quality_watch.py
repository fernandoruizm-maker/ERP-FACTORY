"""Fail-closed test monitoring for operator-authorized PRs outside the job queue.

Never grants quality success: tests alone do not replace the full review pipeline.
The allowlist lives in the operator-owned config, not in untrusted PR content.
"""
import json
import re
from .common import Blocked, RateLimited, safe_path, digest


def watch(config, github, runner, queue, *, should_pause=lambda: False):
    numbers = config.get('quality_watch_prs', [])
    if (not isinstance(numbers, list) or len(numbers) > 20
            or any(type(n) is not int or n < 1 for n in numbers)):
        raise Blocked('quality_watch_prs requires at most 20 explicit PR numbers')
    if not numbers:
        return []
    tracked, protected_heads = set(), set()
    for item in queue.list():
        saved = json.loads(queue.get(item['id'])['checkpoint'])
        if saved.get('pr'):
            tracked.add(saved['pr']['number'])
            protected_heads.add(saved['pr'].get('head_sha'))
    def protected(head):
        current_heads = {github.get(f'/pulls/{n}')['head']['sha'] for n in tracked}
        return head in protected_heads or head in current_heads
    results = []
    for number in dict.fromkeys(numbers):
        if should_pause():
            break
        if number in tracked:
            continue  # Do not overwrite the full pipeline's approval/review gate.
        try:
            pr = github.get(f'/pulls/{number}')
        except RateLimited:
            raise
        except Exception:
            results.append({'pr': number, 'state': 'error'})
            continue
        def eligible(p):
            return (p.get('state') == 'open' and not p.get('merged')
                and p.get('base', {}).get('ref') == config['base_branch']
                and (p.get('base', {}).get('repo') or {}).get('full_name') == config['repository']
                and (p.get('head', {}).get('repo') or {}).get('full_name') == config['repository'])
        if not eligible(pr):
            continue
        head = pr['head']['sha']
        if protected(head):
            continue  # Commit statuses are shared across PRs with the same SHA.
        if not re.fullmatch('[a-f0-9]{40}', head):
            raise Blocked('Invalid watched commit')
        base = github.base(config['base_branch'])
        key = f'quality-watch:v2:{config["repository"]}:{number}:{head}:{base}:{digest(config)}'
        github.status(head, 'factory/human-approval', 'pending',
                      'Sin aprobación automática: requiere el proceso completo de revisión humana')
        github.status(head, 'factory/quality', 'pending', 'Ejecutando pruebas aisladas del commit exacto')
        try:
            comparison = github.get(f'/compare/{base}...{head}')
            entries = comparison.get('files')
            if not isinstance(entries, list) or len(entries) >= 300:
                raise Blocked('Immutable comparison incomplete or oversized')
            paths = [safe_path(e[k]) for e in entries for k in ('filename', 'previous_filename') if k in e]
            if any(p != 'README.md' and not any(p.startswith(prefix) for prefix in
                   config['context_prefixes']) for p in paths):
                raise Blocked('Outside test context')
            files = github.snapshot(head, config['context_prefixes'])
            result = runner.run(files)
            if result.exit_code not in (0, 1):
                raise Blocked('Execution infrastructure failed')
            state = 'failure' if not result.green or result.skipped else 'pending'
            description = (f'Pruebas: {result.tests_run}; fallos: {result.failures}; '
                           f'errores: {result.errors}; omitidas: {result.skipped}')
            if state == 'pending':
                description = 'Pruebas correctas; faltan revisores y el proceso completo de aprobación'
            record = {'pr': number, 'head': head, 'base': base, 'state': state,
                      'tests': result.tests_run, 'failures': result.failures,
                      'errors': result.errors, 'skipped': result.skipped}
        except RateLimited:
            raise
        except Exception:
            # No exception text or untrusted test output in public status descriptions.
            state, description = 'error', 'No se pudieron verificar las pruebas dentro del alcance autorizado'
            record = {'pr': number, 'head': head, 'base': base, 'state': state}
        current = github.get(f'/pulls/{number}')
        if (not eligible(current) or current['head']['sha'] != head
                or github.base(config['base_branch']) != base or should_pause()
                or protected(head)):
            continue
        github.status(head, 'factory/quality', state, description)
        if state != 'error':
            queue.meta_set(key, record)
        results.append(record)
    return results
