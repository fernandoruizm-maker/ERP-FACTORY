# Primera revision de la propia fabrica

Fernando confirmo que guardo `CLAUDE_CODE_OAUTH_TOKEN` en los secretos de Actions.
No se leyo el valor ni se verifico todavia su autenticacion real. El token se usa
solo en el paso de Claude; no se guarda en el repositorio, informes o estado local.

## Alcance preparado

El workflow `.github/workflows/claude-factory-review.yml` es exclusivamente manual.
No se ejecuta al subir codigo, abrir PR o mencionar bots. Requiere `main`, el usuario
Fernando, el SHA completo igual al commit del job y autorizacion expresa de envio
a Anthropic. No admite reejecutar el mismo run. Concurrencia: una revision.

La revision envia codigo publico de esta fabrica: controlador, referencia upstream,
pruebas, piloto ficticio, documentacion, configuracion desactivada y este workflow.
No incluye ERP, secretos, estado, tareas antiguas ni resultados locales. La lista
exacta y las huellas quedan en el manifiesto. Una deteccion basica de patrones de
credenciales bloquea; no constituye un escaner exhaustivo de secretos.

Modelo propuesto: alias `sonnet` de la suscripcion. Una invocacion, maximo dos turnos,
10 minutos para el job, hasta 600.000 bytes de contexto. El limite de USD 2 en
`--max-budget-usd` es una estimacion del CLI, puede excederse y no es un tope de
factura ni traduce la cuota de la suscripcion a dolares. No habilita gasto extra
ni cambia el plan. No hay reintentos automaticos del workflow; el proveedor/CLI
puede realizar sus propios reintentos de transporte.

Los datos se cargan desde un archivo de contexto, evitando pasar cientos de miles
de caracteres por variables de entorno. Se deshabilitan herramientas integradas
y MCP, y la carga automatica de hooks/configuraciones mediante `--bare`. El modelo
no puede leer otros archivos, ejecutar pruebas, editar, comentar PR o integrar.
El token de GitHub solo tiene `contents: read`. No instala una GitHub App nueva.

Las tres acciones principales estan fijadas a commits. Esto no fija todas las
dependencias transitivas ni el modelo resuelto por el alias. La instalacion de
dependencias de la Action ocurre en un runner efimero de GitHub tras autorizar
la ejecucion; no modifica la computadora ni la fabrica Ubuntu.

## Evidencia y fallos

El controlador exige el SHA y la huella de fabrica correctos, lista completa sin
duplicados, analisis de interacciones y hallazgos con archivo/linea validos.
Un error, timeout, salida invalida o cobertura incompleta bloquea. Un PASS con
hallazgos critical/high tambien bloquea. El informe es JSON y texto plano en un
artefacto de Actions retenido 7 dias. No se suben transcripciones ni el token.

PASS produce `NEEDS_HUMAN_REVIEW`, cero aprobaciones y `publication_allowed=false`.
La cobertura declarada por el modelo no prueba comprension completa. La revision
es estatica; no acredita ejecucion de pruebas. El recibo registra SHA, run, intento
y actor del job; solo confiar en el artefacto recuperado del run verificado en
GitHub, nunca en un JSON local suelto. La importacion automatica al controlador
local sigue pendiente. Este flujo no activa ninguna fabrica ni despliega productos.

## Puesta en marcha posterior a la autorizacion

1. Revisar e integrar la propuesta de workflow sin cambiar las protecciones existentes.
2. En Actions seleccionar `Revision manual de la fabrica por Claude`, `Run workflow`.
3. Seleccionar `main`, introducir su SHA completo y marcar la autorizacion de envio.
4. Revisar el resultado y descargar el artefacto `revision-fabrica-...`.
5. Corregir hallazgos; repetir solo con una nueva decision y nueva ejecucion manual.

La rama `main` de ERP-FACTORY aparecia sin proteccion al consultarla. Esto no
significa que la doble aprobacion este aplicada en GitHub: sigue pendiente definir
dos revisores humanos y configurar su cumplimiento antes de operar. No se altero
la configuracion ni las protecciones de la fabrica original.

## Retirada

Deshabilitar este workflow en Actions detiene nuevas solicitudes. No hay servicio
local que detener. Para retirar acceso persistente, eliminar el secreto de GitHub
y revocar tambien el token en Claude; eliminar solo el secreto no revoca el token.
Estas acciones requieren una solicitud expresa. No borrar la fabrica original.

Fuentes: https://code.claude.com/docs/en/github-actions y
https://code.claude.com/docs/en/cli-reference. Integracion real aun no ejecutada.
