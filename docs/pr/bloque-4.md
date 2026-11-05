# Propuesta de PR: condiciones locales de operacion (bloque 4, dos entregas)

## Estado actual de la entrega completa

La primera mitad, puntos 1-4, se entrego en
`84c5fe8af7488b5b6eef88ef82538ef79ab85283`. La segunda mitad, puntos 5-9,
continua desde ese SHA en la misma rama local fix/bloque-4-operacion. La base del
bloque completo sigue siendo ad91cb39609e589df72c8e0b01fc68c694fb4c83.
El segundo SHA se entrega al confirmar el commit. Este documento cubre ambos
commits; los detalles de la primera mitad se conservan como registro historico.

Resultado final de las suites completas: 129 raiz + 87 privadas + 7 JS + 3 TS =
226 casos, cero fallos, errores u omitidas. Sin red, proveedores, publicacion ni
activacion. La operacion real sigue bloqueada. Mas abajo se detallan comandos,
el ensayo fallido corregido y los limites de la segunda mitad.

## Registro de la primera mitad (puntos 1-4)

## Base, alcance y decisiones

Rama `fix/bloque-4-operacion`, rehecha desde
`ad91cb39609e589df72c8e0b01fc68c694fb4c83`, SHA informado antes de cambiar codigo.
Incluye los bloques 1, 2 y 3 completos. La rama anterior apuntaba a 0cb1882 sin
commits propios; se conserva como `archive/bloque-4-base-anterior`. Main intacto.

Fernando pidio dos entregas: esta implementa los puntos 1-4; los puntos 5-9 quedan
para la segunda mitad. Sin red, publicacion, activacion, ERP, credenciales ni
modificaciones de upstream/ o de la fabrica original. Datos de prueba ficticios.
El workflow multiparte sigue pendiente y no se construye en estas entregas.

Identidades declaradas por Fernando y guardadas en config.json, NO autenticadas:

| Funcion | Login declarado | ID declarado |
|---|---|---|
| Negocio | fernandoruizm-maker | 342326625 |
| Tecnica | FERRUMTJA | 352290329 |

`human_approvals_required=2` se lee desde config.json. Fernando autorizo 11 llamadas
por ejecucion; gasto por ejecucion y gasto acumulado siguen `null`, sin valor por
defecto. Los campos estan registrados; el registro monetario y su aplicacion son
del punto 7, aun no implementado. Ninguna operacion real puede ejecutarse en esta
mitad: falta coordinacion real y el modo de simulacion rechaza los transportes
reales predeterminados. Todos los flags de habilitacion permanecen en false.

## Cambios de los puntos 1-4

1. **Aceptaciones:** normalizacion Unicode, eliminacion de espacios y comparacion
   sin mayusculas; identidad vinculada tambien al ID configurado. Se registran
   task/version, source_sha, factory_digest, ID de revision privada y caducidad
   explicita. No hay caducidad implicita ni INSERT OR REPLACE. La restriccion unica
   impide sustituir un rol o contar la misma persona dos veces. Gate vuelve a
   comprobar configuracion, cantidad exigida, caducidad y vinculacion exacta.
   Modificar/restaurar requisitos invalida las aceptaciones, como antes.

2. **Importador unico de revision de fabrica:** `Store.import_factory_review()`
   recibe un directorio local de artefactos y un recibo esperado. Comprueba el
   SHA-256 de SHA256.json y de cada archivo, nombres permitidos, limites, el
   contrato privado V2 y NEEDS_HUMAN_REVIEW, sin aprobaciones ni permiso de publicar.
   Contrasta repositorio privado, SHA del validador, SHA de workflow, source_sha,
   run, primer intento y actor contra recibo/politica. El identificador local
   deriva de ese recibo y sus huellas. Solo se lee el validador desde la carpeta
   privada local fija; nunca desde los artefactos o desde una ruta del informe.
   Gate recibe el ID importado, revalida los bytes persistidos y rechaza un
   diccionario PASS, PARTIAL, formato antiguo, informe alterado o version distinta.
   No se copian respuestas no validadas al almacen de revisiones aceptables.

   **Limite de confianza:** un recibo y hashes locales verifican coherencia e
   integridad, NO autentican GitHub. `private_review_trust` sigue null; hacen falta
   un pin revisado y una adquisicion/verificacion autenticada del recibo en una
   etapa posterior. Incluso con politica y artefactos ficticios completos,
   `provenance_authenticated` es siempre false y gate queda BLOCKED. No existe
   bandera de configuracion para convertir esta simulacion en procedencia real.

3. **Exclusion y recuperacion:** candado del sistema operativo, mantenido durante
   toda la llamada simulada (reserva, transporte ficticio y registro del resultado).
   Recover debe adquirir el mismo candado antes de marcar IN_FLIGHT como UNKNOWN;
   no puede intervenir sobre un trabajador activo. El indicador exige fabrica 2,
   original detenida, modo de simulacion explicito y caducidad; se comprueba antes
   de entrar y antes de cada reserva. Si caduca durante una llamada ya iniciada,
   se conserva su resultado bajo el candado y se bloquea la siguiente llamada.
   No hay reintento ni liberacion automatica de presupuesto.

   **Limite de coordinacion:** el marcador ficticio no demuestra el estado de
   Ubuntu/Windows. La fabrica original no usa este candado y no se ha tocado.
   La via real falla con ORIGINAL_COORDINATION_NOT_VERIFIED, aun si hay un JSON
   local que diga que la original esta detenida. `coordination_directory` queda
   null para la futura integracion; esta version no lo usa para habilitar nada.
   No se afirma haber coordinado dos instalaciones reales. Se requiere un control
   compartido autenticado y una puesta en marcha autorizada antes de operar.

4. **Comparacion por permiso:** se elimina el parametro authorized booleano de
   compare/prepare. ComparisonPermit exige quien, base, raiz, rutas exactas,
   caducidad y huella del catalogo. Antes de leer evidencia se comprueba todo el
   alcance; permiso ausente, otra base/ruta, vencido o catalogo alterado dejan
   PENDIENTE. Solo se admiten catalogos/permiso explicitamente sinteticos; un
   registro escrito a mano no habilita acceso real al ERP. El permiso local no
   autentica al autorizante; la autorizacion real sigue pendiente.

La tabla historica acceptances no se convierte en aceptaciones V2. Se conserva
para no dar por autenticados registros antiguos. Las tablas nuevas se crean en
las bases temporales de prueba; no se migro ningun estado operativo existente.

## Hallazgos cubiertos y pendientes

| Hallazgo | Correccion local probada | Lo que sigue pendiente |
|---|---|---|
| B4 | Normalizacion de identidades, unicidad por nombre e ID | Autenticacion real |
| A3 | Version/run/caducidad, cantidad desde config, sin sustitucion silenciosa | Identidades autenticadas y reglas de GitHub |
| M2 | Gate rechaza PASS manual/antiguo/PARTIAL; importador V2 unico con hashes | Origen autenticado y pin revisado; gate permanece BLOCKED |
| M4 | Eliminado booleano; permiso con base/rutas/caducidad y lectura acotada | Autorizacion/acceso real al ERP |
| M5 | Recuperacion excluida por candado, indicador revisado antes de llamadas | Coordinacion compartida con original; operacion real bloqueada |

No se declaran cerrados A3/M2/M4/M5 en un entorno real. Los puntos 5-9 (M6, B3,
B5, P1/P2 y documentacion M7) quedan pendientes para la segunda entrega. El
validador y workflow publicos se conservan: se retiraran solo cuando el revisor
privado este activo y la migracion este autorizada, sin mantener dos validadores.
La politica privada de alcance incorpora expresamente los nuevos archivos de
esta mitad; no hay inclusion automatica de rutas desconocidas.

## Verificacion ejecutada, completa y local

Desde ERP-FACTORY-correcciones/ERP-FACTORY-revision:

```powershell
& "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -B -m unittest discover -s tests -v
```

Resultado: **87 pruebas, 0 fallos, 0 errores, 0 omitidas**.

Desde ERP-FACTORY-correcciones:

```powershell
& "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -B -m unittest discover -s tests -v
node --test --test-reporter=tap pilot-js/tests/bottles.test.mjs
node --experimental-strip-types --test --test-reporter=tap pilot-js/tests/bottles.test.ts
```

Resultados: **93 Python, 5 JavaScript y 3 TypeScript**, cada suite con 0 fallos,
0 errores y 0 omitidas. Total: **188 casos**. TypeScript sin comprobacion estatica
de tipos. El primer ensayo de la suite raiz paso 90 casos; despues se agregaron
dos pruebas de caducidad durante la llamada y liberacion del candado ante error,
y se repitieron las suites completas. Despues se agrego un bloqueo explicito
por validador privado ausente y se repitio la suite raiz completa: 93/93. Las
otras tres suites no se invalidaron por ese ajuste del importador local. No hubo
ensayos fallidos en esta mitad.

Los 33 casos nuevos de tests/test_operation.py cubren las vinculaciones de
aceptaciones, la procedencia declarada, corrupcion de archivos/estado, formatos
rechazados, permisos, ausencia de autentificacion, bloqueo antes de leer una
credencial, exclusion entre dos procesos locales y recuperacion concurrente.
El antiguo ensayo concurrente de reservas se adapta al requisito de un unico
trabajador: el presupuesto de llamadas se comprueba secuencialmente y la
exclusion se comprueba por separado entre procesos. Los dobles de proveedor
son ficticios. Ninguna prueba constituye una revision real de Claude.

Pruebas ejecutadas con autorizacion del ejecutor para temporales locales, sin
cambiar permisos del sistema ni instalar dependencias. Sin importar/ejecutar el
codigo del ERP o de la fabrica original.

## NO VERIFICADO

- Autenticacion de Fernando/FERRUMTJA, control real de sus cuentas o aprobaciones.
- Procedencia real de un run de GitHub, pin revisado, reglas de rama o importacion
  de artefactos privados reales. No se accedio a GitHub ni se crearon repositorios.
- Coordinacion con la fabrica original, estado real de servicios o uso compartido
  del candado. Solo se probo exclusion local de procesos de prueba en Windows.
- Integracion con Claude/Anthropic, Codex remoto, Docker y ERP; suite de upstream/.
- Workflow multiparte, limites de gasto efectivos, facturacion o minutos consumidos.
- Privacidad/retencion/borrado real de artefactos. No se publicaron informes.
- Deteccion error/errors contrastada con eventos reales de Claude Code; sigue
  siendo solo evidencia ficticia, como se documenta en el bloque 3.

## Recuperacion y entrega

No hay servicio activado ni estado real modificado que recuperar. Los tests usan
directorios temporales. Ante una llamada incierta se mantiene UNKNOWN sin
reintentar; una base de pruebas abierta con registros antiguos no los promueve.
El nuevo importador almacena bytes localmente, por lo que un futuro uso con
informes reales requiere un almacen privado protegido; no escribirlo en carpetas
publicables ni versionarlo. El acceso local a SQLite no es una firma criptografica.

Este documento cubre el unico commit nuevo de la primera mitad. Su SHA y los
diff --stat contra ad91cb3 y 0cb1882 se entregan al confirmar el commit; no se
incluye un SHA autorreferente. No push, PR remota, integracion en main ni activacion.
La segunda mitad continuara sobre ese SHA con los puntos 5-9, conservando esta
evidencia y las decisiones de Fernando. No hay autorizacion de un intento real.


## Segunda mitad: puntos 5-9

### 5. Orquestacion local y rutas del ejecutor

`factory2/orchestrator.py::run_simulated` recibe tres dobles explicitos y un
coordinador ficticio; no tiene clientes de proveedor ni ejecuta procesos/Docker.
Lee pruebas desde una raiz de confianza separada, exige sus hashes, monta el
candidato con esas pruebas y recorre construir -> perfiles de prueba en el orden
solicitado -> revisar. El constructor solo propone src/, nunca modifica pruebas.
Comprueba cambios en fuente/pruebas antes y despues de cada etapa y guarda un
checkpoint local. Ante fallo conserva la evidencia anterior y no reintenta.
SIMULATED_COMPLETE no es PASS operativo, mantiene publication_allowed=false y
human_approvals=0. La revision de producto ficticia no es revision V2 de fabrica.

`test_command` exige directory del candidato y archivos explicitos existentes,
rechaza duplicados, enlaces y rutas externas. Se elimina la rama muerta que
convertia tests en te: ['tests'] se rechaza expresamente. DockerRunner pasa la
carpeta del candidato, nunca Path.cwd(). No se ejecuto Docker ni codigo propuesto.

### 6. Envoltorio Codex con lista blanca

`factory2/codex_adapter.py` reemplaza el uso directo del adaptador heredado desde
factory2.providers. Upstream no expone un parametro para inyectar entorno: el
envoltorio implementa el limite de lanzamiento y reutiliza solo SYSTEM y el
validador de esquema. No edita upstream/ ni altera os.environ globalmente.
Solo pasa PATH, SYSTEMROOT, WINDIR, TEMP, TMP y PATHEXT; crea HOME, USERPROFILE y
CODEX_HOME en un temporal aislado. No hereda GITHUB_PAT, claves, proxies, variables
de inyeccion Python/Node o configuracion de usuario. Conserva restricciones de
herramientas y rechaza eventos de herramienta/error o resultados invalidos.
No se conecta un runner real. El ensayo suministra un doble que comprueba los
argumentos y escribe una propuesta ficticia. Codex CLI real sigue NO VERIFICADO.

### 7. Registro acumulado de intentos y topes

`factory2/budget.py::BudgetLedger` usa SQLite y BEGIN IMMEDIATE para reservar
antes de cada intento. Cada ejecucion queda ligada a source_sha, moneda y limites
al crearse; cada intento tiene ID unico, ejecucion, proveedor, contenido, reserva,
cargo conservador, importe reportado opcional y estado. El registro se conserva
al reabrir la base y controla el acumulado entre ejecuciones. No hay borrado,
reintento, devolucion o conciliacion automatica.

Los importes son cadenas decimales exactas de hasta seis decimales, convertidas
a enteros, no floats. Se exige moneda explicita. Fernando autorizo 11 llamadas
por ejecucion. max_spend_per_execution, max_spend_total y budget_currency siguen
null: no se eligen importes ni moneda sin Fernando, y esos parametros bloquean.
El permiso de cada intento debe incluir execution_id, source_sha y max_cost;
una ejecucion se registra explicitamente antes, nunca se crea automaticamente
al recibir una respuesta incierta.

Los adaptadores Claude/Codex de factory2 usan reserve_paid_call: la reserva
monetaria y el registro de llamada se escriben en una sola transaccion, antes del
transporte ficticio. Los parametros monetarios se comprueban antes de leer una
credencial. La via real sigue bloqueada por coordinacion no verificada. El metodo
historico reserve_call queda para ensayos locales de cola y no se usa en ningun
adaptador de proveedor; su antiguo max_calls_per_task no reemplaza el nuevo tope
por ejecucion.

UNKNOWN y REJECTED mantienen toda su reserva. Si se comunica un importe superior
al reservado, queda OVER_BUDGET, se contabiliza el mayor y se bloquean nuevas
reservas hasta una conciliacion futura autorizada. Incluso un importe reportado
menor no libera saldo automaticamente. billing_verified=false: las reservas no
son facturas ni consumo medido. Un techo local por si solo no impide que un
proveedor facture mas; falta verificar limites efectivos antes de un uso real.

Interfaz prevista para un futuro workflow multiparte: registrar ejecucion una vez,
reservar cada llamada, persistir su resultado validado inmediatamente, finalizar
estado sin reintento, y recuperar como UNKNOWN si se pierde la respuesta. El
ledger permite reserva/finalizacion dentro de una transaccion del coordinador.
Falta incorporar este modulo a una referencia privada revisada y disponer de
almacen persistente privado y compartido entre ejecuciones; una base efimera de
un runner o artefactos con retencion de 7 dias no acreditan control acumulado.
No se implemento el workflow multiparte ni esa infraestructura. El orquestador
local del punto 5 no es el workflow de pago y no consume presupuesto real.

### 8. Piloto ficticio

restore valida tipos/estructura, solicitudes, estados, aprobador distinto del
solicitante, un movimiento por solicitud despachada, cantidades, areas,
comprobantes, secuencia de saldos y saldo final. Rechaza incoherencias aun si se
recalcula la huella. La consulta de un movimiento ausente/duplicado produce
PilotError, no StopIteration. La huella sigue sin ser firma ni autenticacion.
JavaScript agrega pruebas de ID duplicado y de despacho/consulta desde otra area;
la solicitud original y el saldo permanecen intactos ante esos rechazos.

### 9. Documentacion y migracion

README.md, LEEME.md, docs/CLAUDE-OPCIONES.md y el encabezado de docs/ESTADO.md
reflejan que el archivo de workflow publico existe y que el diseno privado esta
bloqueado. Las entradas antiguas de ESTADO se conservan como historia, no como
estado operativo actual. El borrador .disabled esta marcado OBSOLETO. Los antiguos
ejemplos de tarifas no se reutilizan como presupuesto ni precios actuales.

El plan de retirada en CLAUDE-OPCIONES exige primero repositorio privado, referencia
revisada, autenticaciones, coordinacion, presupuesto y workflow multiparte
verificados. Cuando el revisor privado este activo y exista autorizacion, retirar
factory2/actions_review.py y .github/workflows/claude-factory-review.yml y adaptar
sus consumidores. No se retiraron ahora, no se movieron secretos ni se modificaron
protecciones. No se autorizan dos validadores operativos en paralelo.

## Verificacion de la segunda mitad

Desde ERP-FACTORY-correcciones/ERP-FACTORY-revision:

```powershell
& "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -B -m unittest discover -s tests -v
```

Resultado real: **87 pruebas, 0 fallos, 0 errores, 0 omitidas**.

Desde ERP-FACTORY-correcciones:

```powershell
& "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -B -m unittest discover -s tests -v
node --test --test-reporter=tap pilot-js/tests/bottles.test.mjs
node --experimental-strip-types --test --test-reporter=tap pilot-js/tests/bottles.test.ts
```

Resultados reales: **129 Python, 7 JavaScript y 3 TypeScript**, cero fallos,
errores u omitidas. Total con la suite privada: **226 casos**. TS sin comprobacion
estatica de tipos. Se agregan 16 pruebas de presupuesto/proveedores ficticios,
14 de orquestacion/envoltorio/rutas, 6 de restauracion Python y 2 de JavaScript.
Incluyen concurrencia SQLite, acumulado entre ejecuciones, once llamadas y rechazo
de la duodecima con saldo ficticio suficiente, UNKNOWN sin liberar presupuesto,
reservas anteriores al transporte ficticio, orden de etapas, conservacion de
pruebas ante fallos, mutacion del candidato y entorno sin credenciales heredadas.

Ensayo inicial: 129 pruebas raiz, 2 fallos de asercion, 0 errores y 0 omitidas.
La copia mediante JSON canonico ordenaba alfabeticamente los perfiles y ejecutaba
JavaScript antes que Python, alterando el orden configurado y la evidencia previa
al fallo. Se sustituyo por una copia independiente que conserva el orden. Se
repitieron las suites completas y pasaron como se indica arriba; el primer
ensayo no se presenta como validacion final.

No se ampliaron pruebas despues de obtener estos resultados sin un cambio que
lo justificara. Las verificaciones documentales y git diff --check son locales.

## Hallazgos de la segunda mitad y limites finales

- M6: flujo conectado y rutas del candidato corregidas, verificados con dobles.
  NO VERIFICADO el flujo real de Codex/Docker/Claude ni un modelo construyendo codigo.
- B3: lista blanca en el envoltorio factory2, comprobada en una llamada simulada;
  upstream intacto. NO VERIFICADA la autenticacion/ejecucion real de Codex.
- B5: ledger y topes locales acumulados y por ejecucion, probados con unidad TST
  ficticia. NO VERIFICADO gasto, factura, limites efectivos del proveedor ni uso
  del ledger en Actions. Faltan importes/moneda de Fernando e infraestructura.
- P1 y parte P2: coherencia de restauracion y nuevas negativas JS cubiertas.
  No se agregan cancelar/rechazar solicitudes (P3), area configurable o un
  comprobante JS mas completo: no forman parte de estos puntos. TS sin typecheck.
- M7: documentacion actualizada y borrador obsoleto; no cambia la infraestructura.

Se mantienen todos los NO VERIFICADO de la primera mitad: autenticacion humana,
procedencia GitHub, candado compartido con la original, ERP, Docker, proveedor,
privacidad/retencion real, minutos, suite heredada de upstream/ y eventos reales
error/errors de Claude Code. El importador permanece bloqueado para operar.
No se construyo el workflow multiparte obligatorio ni se preparo otro intento.

La entrega del bloque 4 comprende dos commits: primera mitad 84c5fe8 y el commit
final de esta segunda mitad, cuyo SHA completo se entrega en la respuesta junto
con los diff --stat contra ad91cb3 y 0cb1882. Sin push, PR, main ni activacion.
