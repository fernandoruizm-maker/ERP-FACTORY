# Informe sin herramientas: correccion pendiente de ejecucion real

El cuarto intento autorizado autentico y proceso la solicitud, pero termino
con `error_max_turns`, sin informe valido:
https://github.com/fernandoruizm-maker/ERP-FACTORY/actions/runs/41995251713
Commit: `9f365dae8a1ad5d5b4e27c14dc7bac3073875e11`.
El registro indica 178619 ms, 3 turnos y una denegacion de herramienta. Se habian
configurado 2 turnos: no se atribuye la diferencia a una causa no comprobada.
El costo estimado registrado es USD 1.039741; no acredita un cargo a la cuenta.
La fabrica permanece bloqueada y no se inicio otro intento.

La documentacion de Anthropic explica que el esquema del SDK agrega una
herramienta interna StructuredOutput. Nuestra regla `--disallowedTools "*"`
deniega todas las herramientas. Es una incompatibilidad probable: el log
reducido del cuarto intento no conserva el nombre de la herramienta denegada.
No se afirma haber recuperado una revision ni confirmado ese nombre.

La correccion conserva safe-mode y la denegacion completa. El esquema pasa al
texto de la solicitud; se pide JSON puro sin Markdown. Se elimina --json-schema
para no solicitar la herramienta interna. El lector toma un unico resultado
del archivo fijo del Action en RUNNER_TEMP, limitado a 10 MB, sin enlaces
simbolicos. Exige resultado success, is_error=false, 1-2 turnos, cero denegaciones
y un objeto JSON que supere la validacion de version, cobertura y hallazgos.
Un texto libre o parcial falla cerrado. No se publican las sesiones originales.

El diagnostico agrega etiquetas fijas para limite de turnos y denegaciones,
su numero y si StructuredOutput aparece expresamente; nunca guarda argumentos
de herramientas ni mensajes arbitrarios del proveedor.

Validacion local ejecutada: 12 pruebas del modulo Actions, todas correctas.
Incluyen errores, limites, texto no JSON, falta del archivo, cobertura parcial,
hallazgos contradictorios y ausencia de aprobacion/publicacion automatica.
No acreditan que Claude vaya a devolver un informe valido. Falta un nuevo
intento expresamente autorizado. Se mantienen 2 turnos, 10 minutos y presupuesto
CLI de USD 2, que no constituye una garantia contractual de facturacion.

Fuentes revisadas:
- https://code.claude.com/docs/en/agent-sdk/structured-outputs
- https://code.claude.com/docs/en/cli-reference
- https://github.com/anthropics/claude-code-action/blob/c0949c50a78c1ec8ce2647db36629b870e715d0c/base-action/src/run-claude-sdk.ts

El Action fijado guarda el resultado textual en el archivo de ejecucion incluso
sin json-schema y oculta su contenido cuando show_full_output=false. Se conserva
esa opcion. No habilitar depuracion completa de Actions: la implementacion del
proveedor permite que ACTIONS_STEP_DEBUG=true anule esa ocultacion.

Recuperacion: descartar esta propuesta conserva el main del cuarto intento;
no se alteran credenciales ni estado local. No ejecutar nuevamente esa version
sin resolver el formato. No hay cambios en ERP, Ubuntu o permisos GitHub.
