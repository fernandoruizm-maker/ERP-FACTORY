"""Spanish decision report, derived from controller evidence rather than a vote."""
from .common import Blocked, digest


def verify_created_report(pr, *, title, body, head):
    expected={'title':title[:240],'body':body.replace('{{FACTORY_HEAD}}',head)}
    if (pr.get('state')!='open' or pr.get('draft') is not True or pr.get('head',{}).get('sha')!=head
            or pr.get('title')!=expected['title'] or (pr.get('body') or '')!=expected['body']):
        raise Blocked('El informe o borrador de GitHub difiere de la evidencia generada')
    return digest(expected)

def role_form(roles, version='{{FACTORY_HEAD}}'):
    return ('## Cómo responde la persona especialista\n'
        'Roles que cubre su aprobación: **'+(', '.join(roles) or 'ninguno')+'**. '
        'En **Files changed → Submit review**, leer el informe y elegir **Approve**, '
        'sin escribir un comentario. Pulsar el botón **Submit review** dentro del formulario. '
        'En cambios mixtos, una sola aprobación cubre ambos roles indicados.\n\n'
        '**No puedo evaluar esto:** elegir **Request changes**; si GitHub pide texto, '
        'escribir **NO PUEDO EVALUAR**. Esa negativa también bloquea en un comentario de revisión. '
        'No responder nunca equivale a aprobar. Los comentarios sueltos no aprueban. '
        'El propietario también debe aprobar desde su propia cuenta. La App comprueba '
        'la versión directamente en GitHub, sin códigos copiados. Las aprobaciones caducan '
        'a las 24 horas. Si cambia el código o el informe, se repiten las comprobaciones.\n')


def render(checkpoint, *, owner, specialist, requested, manual_steps, accounting=None, trial=False):
    risk=checkpoint['classification']; tdd=checkpoint['tdd']
    roles=risk['roles']
    if 'CONTADOR' in roles and not accounting:
        raise Blocked('Falta tabla contable con resultados esperados y obtenidos verificables')
    lines=[('**ENSAYO: NO INTEGRAR. Se cerrará tras las revisiones humanas.**\n' if trial else ''),
        '# Informe para decidir sin leer código',
        '## Qué se pidió', requested,
        '## Qué cambió y qué áreas puede afectar',checkpoint['business_change'],
        '**Riesgo: '+risk['level'].upper()+'**. Roles requeridos: '+(', '.join(roles) or 'propietario')+'.',
        '\n'.join('- '+r for r in risk['reasons']),
        '## Pruebas antes y después',
        '| Comprobación | Pruebas | Fallos | Errores | Omitidas |',
        '|---|---:|---:|---:|---:|']
    for phase,label in [('baseline','Antes'),('red','Antes del cambio, prueba nueva'),('green','Después, prueba nueva'),('regression','Después, conjunto completo')]:
        if checkpoint.get('validation_mode')=='coverage_only' and phase=='red':
            label='Cobertura nueva sobre ruta existente (ya pasaba)'
        value=tdd[phase]
        lines.append(f"| {label} | {value['tests_run']} | {value['failures']} | {value['errors']} | {value['skipped']} |")
    lines += [checkpoint['test_changes'], '## Hallazgos de los revisores y resolución']
    if checkpoint.get('validation_mode')=='coverage_only':
        r=tdd['coverage_before']
        lines.insert(-1, f"La ruta /ping ya funcionaba. No hubo ni se inventó fase roja. Batería completa inicial: {r['tests_run']} pruebas, "
            f"{r['failures']} fallos, {r['errors']} errores y {r['skipped']} omitidas. Se repitió el mismo conjunto al final. "
            'Solo se añadieron cobertura HTTP y documentación; no se modificó código de la aplicación.')
    if 'full_red' in tdd:
        r=tdd['full_red']
        lines.insert(-1, 'Batería completa antes de implementar, con las mismas pruebas que al final: '
            f"{r['tests_run']} ejecutadas, {r['failures']} fallos esperados, {r['errors']} errores y {r['skipped']} omitidas. "
            'Los fallos iniciales comprueban que el comportamiento antiguo no satisface el nuevo contrato.')
    for role,review in checkpoint['reviews'].items():
        lines += ['- '+{'security':'Seguridad','architecture':'Arquitectura','tests':'Pruebas','ux':'Interfaz/API'}.get(role,role)+': '+review['verdict']+'. '+review['rationale']]
        lines += ['  Hallazgo pendiente: '+finding for finding in review['findings']]
    if accounting:
        lines += ['## Revisión CONTADOR',
                  '**Ejemplo inventado; no son movimientos del ERP ni asesoramiento fiscal.**',
                  '| Operación de prueba | Asiento esperado | Asiento obtenido | Saldos afectados | Diferencia |',
                  '|---|---|---|---|---|']
        for row in accounting:
            lines.append('| '+' | '.join(str(row[k]).replace('|','/') for k in ('operation','expected','actual','balances','difference'))+' |')
        lines += ['Comprobar que cada asiento obtenido coincide con el esperado, que el debe y el haber '
                  'cuadran, que los saldos corresponden y que no se ocultó ninguna diferencia. '
                  'Las reglas fiscales o contables reales deben ser definidas y revisadas por una persona competente.']
    if 'TECNICO' in roles:
        lines += ['## Revisión TÉCNICO', 'Comprobar el alcance, los hallazgos anteriores, las pruebas '
            'añadidas/modificadas/eliminadas, los riesgos siguientes y que no se alteran permisos '
            'ni datos reales fuera del alcance. Archivos afectados:',
            '\n'.join('- `'+path+'`' for path in sorted(checkpoint['changes']))]
    lines += ['## Riesgos y lo que NO se verificó',checkpoint['limitations'],
              '## Pasos para comprobar el resultado en pantalla',manual_steps,
              '## Aprobaciones necesarias',
              f'Propietario: **{owner}**. Especialista designado: **{specialist}**. '
              'La App comprueba identidad, acceso y versión. Tener una cuenta distinta no acredita por sí solo la competencia profesional.',
              role_form(roles),
              'Las consultas son periódicas: el check puede tardar en actualizarse. Si el PC o GitHub '
              'no están disponibles, no se debe integrar usando un resultado antiguo. '
              'Este controlador no integra ni despliega.']
    return '\n\n'.join(lines)
