"""Closed, locally auditable blueprint; JSON is a subset of YAML. No execution."""
PRIVATE = 'fernandoruizm-maker/ERP-FACTORY-revision'
PIN = '0' * 40
CHECKOUT = 'actions/checkout@11d5960a326750d5838078e36cf38b85af677262'
CLAUDE = 'anthropics/claude-code-action@c0949c50a78c1ec8ce2647db36629b870e715d0c'
UPLOAD = 'actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02'


def upload(identifier, gate, checkpoint):
    return {'id': identifier, 'name': 'Conservar checkpoint privado ' + identifier,
            'if': gate, 'uses': UPLOAD, 'timeout-minutes': 1,
            'with': {'name': 'review-${{ github.run_id }}-${{ github.run_attempt }}-' + identifier,
                     'path': '${{ runner.temp }}/private-review/checkpoints/' + checkpoint + '/artifacts/',
                     'if-no-files-found': 'error', 'retention-days': 7}}


def blueprint():
    env = {'TRUSTED_REVIEWER_SHA': PIN, 'INPUT_SOURCE_SHA': '${{ inputs.source_sha }}',
           'REPOSITORY_PRIVATE': '${{ github.event.repository.private }}',
           'TRIGGERING_ACTOR': '${{ github.triggering_actor }}',
           'AUTHORIZE_ANTHROPIC': '${{ inputs.authorize_anthropic }}',
           'WORKFLOW_SHA': '${{ github.workflow_sha }}',
           'REVIEW_WORKDIR': '${{ runner.temp }}/private-review'}
    steps = [
        {'name': 'Validador privado fijado, nunca checkout publico', 'uses': CHECKOUT,
         'timeout-minutes': 2, 'with': {'repository': PRIVATE, 'ref': PIN, 'path': 'trusted',
                                       'persist-credentials': False}},
        {'id': 'preflight', 'name': 'Verificar bloqueos, procedencia y topes', 'timeout-minutes': 1,
         'run': 'python3 -I -B trusted/entrypoint.py mp-preflight'},
        {'id': 'prepare', 'name': 'Material publico solo como datos y presupuesto reservado',
         'timeout-minutes': 3, 'run': 'python3 -I -B trusted/entrypoint.py mp-init'},
        upload('upload_initial', "${{ always() && steps.prepare.outcome == 'success' }}", 'initial'),
    ]
    for slot in range(1, 12):
        previous = 'prepare' if slot == 1 else 'collect_' + str(slot-1)
        previous_upload = 'upload_initial' if slot == 1 else 'upload_result_' + str(slot-1)
        ready = '' if slot == 1 else " && steps." + previous + ".outputs.continue == 'true'"
        select_id, call, collect = 'select_'+str(slot), 'claude_'+str(slot), 'collect_'+str(slot)
        gate = "${{ success() && steps." + previous_upload + ".outcome == 'success'" + ready + ' }}'
        steps.append({'id': select_id, 'name': 'Preparar y reservar llamada ' + str(slot),
                      'if': gate, 'timeout-minutes': 1,
                      'env': {'STATE_FILE': '${{ steps.'+previous+'.outputs.state_file }}',
                              'STATE_SHA256': '${{ steps.'+previous+'.outputs.state_sha256 }}'},
                      'run': 'python3 -I -B trusted/entrypoint.py mp-select --slot '+str(slot)})
        steps.append(upload('upload_reserved_'+str(slot),
            "${{ always() && steps."+select_id+".outcome == 'success' }}",
            '${{ steps.'+select_id+'.outputs.checkpoint }}'))
        steps.append({'id': call, 'name': 'Claude sin herramientas, llamada '+str(slot),
            'if': "${{ success() && steps."+select_id+".outputs.ready == 'true' && steps.upload_reserved_"+str(slot)+".outcome == 'success' }}",
            'timeout-minutes': 6, 'uses': CLAUDE,
            'with': {'github_token': '${{ github.token }}',
                     'claude_code_oauth_token': '${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}',
                     'prompt': '${{ steps.'+select_id+'.outputs.user_prompt }}',
                     'claude_args': '--safe-mode --disallowedTools "*" --max-turns 2 --max-budget-usd ${{ steps.'+select_id+'.outputs.max_budget_usd }} --model sonnet --append-system-prompt-file ${{ runner.temp }}/private-review/input/system.txt',
                     'show_full_output': 'false', 'display_report': 'false',
                     'classify_inline_comments': 'false', 'include_fix_links': 'false'}})
        steps.append({'id': collect, 'name': 'Validar y guardar inmediatamente llamada '+str(slot),
            'if': "${{ always() && steps."+select_id+".outputs.ready == 'true' }}",
            'timeout-minutes': 1,
            'env': {'STATE_FILE': '${{ steps.'+select_id+'.outputs.state_file }}',
                    'STATE_SHA256': '${{ steps.'+select_id+'.outputs.state_sha256 }}',
                    'CLAUDE_CONCLUSION': '${{ steps.'+call+'.outcome }}'},
            'run': 'python3 -I -B trusted/entrypoint.py mp-collect --slot '+str(slot)})
        steps.append(upload('upload_result_'+str(slot),
            "${{ always() && steps."+collect+".outputs.checkpoint != '' }}",
            '${{ steps.'+collect+'.outputs.checkpoint }}'))
    return {'name': 'Revision privada V2 multiparte (bloqueada)',
        'on': {'workflow_dispatch': {'inputs': {
            'source_sha': {'description': 'SHA completo PUBLICO autorizado', 'required': True, 'type': 'string'},
            'authorize_anthropic': {'description': 'Nueva autorizacion expresa de envio y coste',
                                    'required': True, 'type': 'boolean', 'default': False}}}},
        'permissions': {}, 'concurrency': {'group': 'private-factory-review', 'cancel-in-progress': False},
        'jobs': {'review': {
            'if': "${{ false && github.event.repository.private == true && github.repository == '"+PRIVATE+"' && github.ref == 'refs/heads/main' && github.actor_id == '342326625' && github.triggering_actor == 'fernandoruizm-maker' && github.run_attempt == 1 && inputs.authorize_anthropic == true }}",
            'runs-on': 'ubuntu-24.04', 'timeout-minutes': 120,
            'permissions': {'contents': 'read'}, 'env': env, 'steps': steps}}}
