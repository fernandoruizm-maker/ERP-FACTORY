# Propuesta de PR: contrato privado de revision por partes y cobertura calculada

## Resultado y procedencia

Rama local: `fix/bloque-3-cobertura`. Base combinada comprobada ANTES de desarrollar:
`fa650d7322e136093e445b6801b90bd37d93fd4c`. Contiene bloque 1 b0da873 y bloque 2
completo f288441, incluido a8cfa18 y la conservacion privada autorizada.
La base paso 57 pruebas privadas, 60 raiz, 5 JS y 3 TS: 125 sin fallos ni omitidas.

El protocolo vive exclusivamente en ERP-FACTORY-revision/. No se modifica el
validador publico ni upstream/. El inventario de un SHA local exacto parte de
git ls-files con indice temporal; ninguna ruta se omite por extension. La politica
enumera inclusiones y exclusiones motivadas. Archivos nuevos no clasificados
bloquean antes de leer su contenido. No ejecuta el codigo inventariado.

Las partes contienen lineas originales numeradas, huellas y rangos comprobados.
El codigo viaja como JSON delimitado en el turno de usuario; el sistema contiene
solo instrucciones y esquema. Cada respuesta se vincula a SHA, huella de fabrica
y huella de parte. La pasada final incorpora todos los resultados validados y
sus huellas. El validador calcula cobertura desde partes/rangos; declaraciones
complete o PASS no suplen partes ni autorizan publicar. Una declaracion incompleta
sigue bloqueando el estado NEEDS_HUMAN_REVIEW. PARTIAL siempre tiene cero
aceptaciones y publication_allowed=false. Una parte BLOCK nunca queda anulada
por un PASS final.

Los tres puntos de entrada privados comparten el contrato V2 en validation.py.
El antiguo objeto monolitico ya no cuenta como revision privada. Los tres formatos
publicos se conservan intactos como dependencia historica hasta la migracion;
no se afirma haber corregido aun la puerta operativa publica (M2, bloque 4).

Contratos obsoletos para el revisor privado: `factory2/core.py::validate_review`,
`factory2/review_packet.py::validate_complete` y
`factory2/actions_review.py::validate_result`. No se importan ni se aceptan como
alternativas al contrato V2 privado. Se mantienen fisicamente para no modificar
el flujo publico en esta etapa; su retirada/adaptacion de consumidores corresponde
a la migracion autorizada y al bloque 4. No estan eliminados de la fabrica local.

Se amplian patrones de credenciales habituales, incluido github_pat_. Es una
heuristica, no una garantia de ausencia de secretos. Se mantiene la decision
restringida del bloque 2 para response.unvalidated.txt: solo privado, BLOCKED,
limite de 100.000 bytes, escaneo original, lista cerrada y sin reintentos.

## Hallazgos tratados y limites pendientes

- A1: partes ligadas a contenido, agregacion y cobertura estructural calculada.
- M1 y B2: datos fuera del sistema y lineas numeradas con validacion de rangos.
- M3: inventario Git y clasificacion explicita; prueba sobre los 91 archivos reales.
- B1: patrones adicionales, probados con cadenas ficticias.
- Contrato privado unificado; M2 operativo, A3 y restantes condiciones del bloque 4
  siguen pendientes. No se altera upstream/ ni se arreglan aqui sus adaptadores.

El flujo completo se ejercita SOLO con responder ficticio y se marca
SIMULATED_NOT_PROVIDER_INTEGRATION. No hay transporte de produccion. El CLI
prepare bloquea con MULTIPART_WORKFLOW_NOT_CONNECTED: el workflow monolitico
anterior no puede representar el protocolo nuevo y permanece desactivado.
El lector/coleccion de tar y eventos se mantiene como soporte de pruebas del
bloque 2; no sustituye el inventario Git ni constituye un colector operativo
de multiples llamadas. Sus pruebas con un bundle ficticio mantienen el limite
de respuesta de 100.000 bytes. El agregador local valida cada informe por separado.

Cada mensaje de usuario admite hasta 60.000 bytes, el inventario hasta 2 MB y
128 partes. Una linea indivisible o una pasada final demasiado grande bloquea;
no hay truncado, resumen automatico ni reintento de pago. Son limites de bytes,
no garantias de ventana de contexto ni de coste. Validar cobertura no acredita
que Claude haya leido o comprendido realmente todas las lineas.

## Pruebas ejecutadas

Desde `ERP-FACTORY-correcciones/ERP-FACTORY-revision`:

```powershell
& "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m unittest discover -s tests -v
```

Suite privada completa: 87 pruebas, 0 fallos, 0 errores, 0 omitidas. Incluye
32 controles privados/estaticos, 29 de protocolo y 26 de conservacion restringida.
Prueba partes ausentes, duplicadas o de otra version; huellas alteradas; intervalos
incompletos; hallazgos fuera de archivo o parte; JSON fuera del sistema; pasada
final ligada a cada resultado; contexto excesivo; tipos de archivo no clasificados;
inventario real de los 91 archivos del SHA base; y patrones de tokens ficticios.
El commit adicional comprueba explicitamente una pasada final de otra version
(source_sha o factory_digest), ademas de la prueba existente de pasada ausente
y de la huella ligada a todos los resultados. Todo usa datos ficticios.

Registro de desarrollo: la primera ejecucion privada reporto 60 casos, 0 fallos
de asercion y 1 error de importacion por un error de sintaxis en la prueba de
conservacion. Las 26 pruebas de ese modulo no llegaron a ejecutarse. Se corrigio
y se repitio la suite completa; ese ensayo fallido no se presenta como validacion.

Desde `ERP-FACTORY-correcciones`:

```powershell
& "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -B -m unittest discover -s tests -v
node --test --test-reporter=tap pilot-js/tests/bottles.test.mjs
node --experimental-strip-types --test --test-reporter=tap pilot-js/tests/bottles.test.ts
```

Suite raiz: 60 Python; JavaScript: 5; TypeScript: 3. Cero fallos, errores u
omitidas. Total final: 155 casos. TS se ejecuta sin comprobar tipos estaticamente.
Las pruebas Python usaron la via autorizada del ejecutor para temporales, sin
cambiar permisos del sistema. No se descargaron dependencias.

## No verificado

**NO VERIFICADO:** la deteccion de errores del proveedor mediante los campos
`error`/`errors` en cualquier evento no se ha contrastado con eventos reales de
Claude Code. Solo se ha probado con eventos ficticios; no se acredita que esos
campos, tipos y significados coincidan con todas las salidas reales del proveedor.
No se obtuvieron eventos reales ni se hizo una llamada para comprobarlo.

Integracion real con Claude/Anthropic, Codex remoto u otros proveedores; ejecucion
del workflow en GitHub; existencia/configuracion del repositorio privado; pin real
revisado; autenticacion e identidades; visibilidad, descarga, retencion o borrado
real de artefactos; minutos y costes; Docker; ERP; suite heredada de upstream/.
No hubo ninguna llamada, publicacion, acceso a credenciales o activacion.
La comprobacion estatica del YAML no acredita que GitHub lo acepte o ejecute.

## Publicacion posterior y comprobacion

No fusionar esta rama en ERP-FACTORY ni subir sus informes. La publicacion futura
del revisor consiste en exportar exactamente ERP-FACTORY-revision/ al repositorio
PRIVADO separado, solo tras autorizacion escrita para este bloque. El bloque 1
publico conserva su rama independiente. Las notas combinadas de docs/ESTADO.md
conservan ambas historias, sin sustituir la una por la otra.

Cuando el revisor privado este activo, retirar factory2/actions_review.py y el
workflow publico segun la migracion autorizada, para no mantener dos validadores.
Hasta entonces siguen historicos e intactos. El bloque 4 depende de esta rama.

El SHA final y git diff --stat contra 0cb1882 se entregan fuera del propio commit
para evitar autorreferencia. Antes de una publicacion autorizada, cotejar el SHA
exacto entregado; si cambia, detenerse. El repositorio privado tendra historia y
SHA propios: cotejar ademas el arbol exportado. Ningun cambio de bloqueos ni un
nuevo intento Claude estan autorizados por esta entrega.
