"""Static audit of our JSON-subset YAML; no YAML dependency or Actions execution."""
import re
from .contract import Blocked

PRIVATE = 'fernandoruizm-maker/ERP-FACTORY-revision'
PINS = {
    'actions/checkout@11d5960a326750d5838078e36cf38b85af677262',
    'anthropics/claude-code-action@c0949c50a78c1ec8ce2647db36629b870e715d0c',
    'actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02',
}


def audit(workflow):
    try:
        if set(workflow['on']) != {'workflow_dispatch'} or workflow['permissions'] != {}:
            raise Blocked('TRIGGER_OR_PERMISSION')
        if set(workflow['jobs']) != {'review'}:
            raise Blocked('UNREVIEWED_JOB')
        job = workflow['jobs']['review']
        if job['permissions'] != {'contents': 'read'}:
            raise Blocked('EXCESS_JOB_PERMISSION')
        conditions = ("github.event.repository.private == true", "github.repository == '" + PRIVATE + "'",
                          "github.ref == 'refs/heads/main'", "github.actor_id == '342326625'",
                          "github.triggering_actor == 'fernandoruizm-maker'", 'github.run_attempt == 1',
                          'inputs.authorize_anthropic == true')
        guard = ' && '.join(conditions)
        if job['if'] not in ('${{ ' + guard + ' }}', '${{ false && ' + guard + ' }}'):
            raise Blocked('MISSING_RUN_GUARD')
        pin = job['env']['TRUSTED_REVIEWER_SHA']
        if not re.fullmatch('[0-9a-f]{40}', pin):
            raise Blocked('VALIDATOR_REFERENCE_NOT_FIXED')
        steps = job['steps']
        if len(steps) != 6 or [s.get('id') for s in steps] != [None, None, 'prepare', 'claude', 'validate', None]:
            raise Blocked('STEP_ORDER_INVALID')
        checkouts = [step for step in steps if step.get('uses', '').startswith('actions/checkout@')]
        if len(checkouts) != 1 or checkouts[0]['with'] != {
                'repository': PRIVATE, 'ref': pin, 'path': 'trusted', 'persist-credentials': False}:
            raise Blocked('CHECKOUT_NOT_PRIVATE_FIXED')
        expected_runs = ['python3 -I -B trusted/entrypoint.py ' + command
                         for command in ('preflight', 'prepare', 'collect')]
        if [step['run'] for step in steps if 'run' in step] != expected_runs:
            raise Blocked('UNTRUSTED_EXECUTABLE_STEP')
        if {step['uses'] for step in steps if 'uses' in step} != PINS:
            raise Blocked('ACTION_REFERENCE_CHANGED')
        for step in steps:
            if 'secrets.' in str(step):
                if (step.get('id') != 'claude' or 'run' in step or 'env' in step
                        or step['with']['claude_code_oauth_token'] != '${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}'):
                    raise Blocked('SECRET_SCOPE_INVALID')
        if 'secrets.' in str(job.get('env')) or 'secrets.' in str(workflow.get('env')):
            raise Blocked('SECRET_SCOPE_INVALID')
        claude = next(step for step in steps if step.get('id') == 'claude')
        if claude['with']['prompt'] != '${{ steps.prepare.outputs.user_prompt }}':
            raise Blocked('PROMPT_SOURCE_INVALID')
        args = claude['with']['claude_args']
        if '--safe-mode' not in args or '--disallowedTools "*"' not in args or 'system.txt' not in args:
            raise Blocked('MODEL_TOOLS_NOT_DENIED')
        upload = next(step for step in steps if step.get('uses', '').startswith('actions/upload-artifact@'))
        if upload['with']['path'] != '${{ runner.temp }}/private-review/artifacts/':
            raise Blocked('ARTIFACT_SCOPE_INVALID')
        if upload['with']['retention-days'] != 7:
            raise Blocked('RETENTION_CHANGED')
        validate = next(step for step in steps if step.get('id') == 'validate')
        if validate['env']['MATERIAL_SHA256'] != '${{ steps.prepare.outputs.material_sha256 }}':
            raise Blocked('MATERIAL_RECEIPT_MISSING')
    except (KeyError, TypeError, StopIteration):
        raise Blocked('WORKFLOW_STRUCTURE_INVALID') from None
    pending = []
    if pin == '0' * 40:
        pending.append('PENDING_REVIEWED_PRIVATE_COMMIT')
    if 'false &&' in job['if']:
        pending.append('EXECUTION_DISABLED')
    return {'structural_checks': 'PASS', 'operational_readiness': 'BLOCKED' if pending else 'UNVERIFIED',
            'pending': pending, 'publication_allowed': False}
