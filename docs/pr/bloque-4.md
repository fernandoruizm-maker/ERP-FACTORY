# Propuesta de PR: condiciones locales de operacion, primera mitad (1-4)

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
