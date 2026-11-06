# Bloque 9: Docker real y aprobaciones por niveles

Rama local docs/bloque-9-docker. La ampliacion inicial partio de
be3e026420bfc055296dc4478add970b2512eab3, sobre origin/main local
877dd757f83f5fece05e2216ddfdea36843f0c4a. Aquella ampliacion no incluyo el bloque 8.

## Actualizacion sobre main (6-11-2026)

Un fetch de origin autorizado trae main a
54b5bda8170a886755c768b1e2b7bfba5ac5eae4 (merge del bloque 8). Se combina mediante
merge local, conservando el historial revisado de 6ce6af0, sin rebase ni push.
Segun Fernando, Claude reviso 6ce6af02b8c885c320761923c670615151204777 sin
objeciones tecnicas. No se extiende esa revision al nuevo SHA combinado.

- Conflicto textual: docs/ESTADO.md. Se concilian las secciones de los bloques
  8 y 9, la evidencia historica y el estado combinado, sin elegir una sola version.
- factory2/state.py se combina automaticamente: conserva Coordinator(self.path.parent)
  del bloque 8 y roster(task) por niveles del bloque 9.
- tests/test_operation.py se combina automaticamente. tests/test_retirement.py
  requiere una adaptacion semantica: declarar el destino factory en el expediente
  que comprueba la falta de aceptaciones. Conserva BLOCKED y la razon esperada;
  no se rebaja la prueba ni se cambia la politica para admitir expedientes sin destino.
- PUBLICACION.md y este informe se actualizan para no seguir diciendo que falta
  incorporar el bloque 8. Los registros de retirada y su validador se conservan.

runner.py y tests/docker_pilot_check.py no cambian respecto a 6ce6af0. No se
repite el ensayo Docker ni se usa mas red. Configuracion desactivada, upstream/,
revisor privado y reglas remotas intactos. Envio DISABLED.

Suites completas del arbol combinado, ejecutadas sin red, todas con salida 0:

| Suite | Pruebas | Fallos/errores | Omitidas |
|---|---:|---:|---:|
| Python raiz (incluye las 17 del bloque 8) | 178 | 0 | 0 |
| Python privada | 113 | 0 | 0 |
| JavaScript local | 7 | 0 | 0 |
| TypeScript local, sin typecheck | 3 | 0 | 0 |
| Total | 301 | 0 | 0 |

Los comandos son los mismos de abajo; logs nuevos fuera del repositorio en
../entregas-locales/bloque-9-main-*.log. No confundirlos con resultados historicos.

## Cambio

Docker Desktop fue arrancado por Fernando; tambien declaro cumplir los umbrales
de licencia gratuita. Se descargaron una imagen oficial Python y una Node con
la aprobacion de red correspondiente, una vez cada una. Digests, comandos e
incidencias en [DOCKER.md](../DOCKER.md). El piloto y aislamiento se comprobaron
con DockerRunner real, sin modificar runner.py, sin red en los contenedores ni
descargas durante la ejecucion. Se anade un auxiliar optativo reproducible:
tests/docker_pilot_check.py, fuera del descubrimiento automatico de unittest.

Politica decidida por Fernando:

| Destino del expediente | Configuracion | Roles necesarios |
|---|---|---|
| fernandoruizm-maker/ERP-FACTORY, kind=factory | human_approvals_required=1; human_approval_roles=[business] | Fernando |
| Otro repositorio, kind=accounting_product | accounting_product_approvals: 2; roles business/accounting | Fernando y FERRUMTJA |

human_approvers conserva las dos identidades como directorio de personas; no
significa que ambas sean obligatorias para ERP-FACTORY. Las fixtures usan otras
personas ficticias. No se autentica ninguna identidad desde este codigo.

El expediente versionado contiene approval_target con exactamente kind y
repository. No se pasa un indicador para rebajar el nivel en gate() o accept().
Ejemplo de la fabrica:

```json
{"approval_target":{"kind":"factory","repository":"fernandoruizm-maker/ERP-FACTORY"}}
```

Producto contable de ensayo: kind=accounting_product y repository=ficticio/producto.
Clasificacion ausente, contradictoria o nivel no decidido bloquean. No hay
rebaja automatica para productos sin impacto contable. Los expedientes antiguos
sin este campo requieren una nueva declaracion revisada; no se migran ni se
reutilizan aceptaciones silenciosamente. put_task cambia la version y borra las
aceptaciones previas. roster verifica ademas la huella del brief guardado.
La clasificacion es una declaracion revisable por Fernando/Claude, no un detector
automatico de impacto contable ni una comprobacion remota del repositorio.

Se mantienen caducidad, SHA exacto, huella, revision importada, personas distintas,
sin sustituciones silenciosas, pruebas y publicacion siempre false. La via V2
sigue exigiendo procedencia/autenticacion; una sola aceptacion no la desbloquea.
Los cuatro interruptores de config.json siguen false; solo cambia la politica
de aceptaciones. No se modifica presupuesto, ERP, upstream/, credenciales ni
workflows. Tras incorporar el bloque 8, la coordinacion valida el registro de
retirada declarada; no autentica la retirada ni activa la fabrica.

Las guias, README/LEEME e instrucciones AGENTS se actualizan para no seguir
exigiendo dos en todos los casos. La plantilla de ruleset anterior sigue con 2:
no se aplica ni se cambia GitHub. PUBLICACION.md explica el ajuste futuro que
Fernando tendra que autorizar y comprobar; nunca se usa bypass para compensarlo.

## Pruebas y comandos ejecutados

Ensayo Docker final: 13 Python + 7 JavaScript + 3 aislamiento, 0 fallos/omitidas.
Usuario/grupo 65534, capacidades cero, NoNewPrivs=1, escrituras rechazadas,
solo interfaz lo, conexion ficticia ENETUNREACH, archivos host sin cambios y
0 eventos pull. Los contenedores usados se retiraron por su nombre unico.
TS no se ejecuto en Docker. El auxiliar realiza operaciones locales de Docker,
no inicia proveedores ni activa la fabrica. Comando exacto en DOCKER.md.

Prueba focal de la politica (antes de las suites):

```powershell
& "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -B -m unittest tests.test_approval_levels tests.test_operation tests.test_manual_review tests.test_factory -v
```

Resultado: 89 pruebas, 0 fallos/errores, 0 omitidas. Incluidas dentro de la suite
raiz, no sumarlas otra vez. Las 12 nuevas pruebas de niveles cubren 1 aceptacion
para fabrica, 2 para producto contable, roles equivocados, destino/impacto sin
clasificar, cambios de destino, manipulacion del brief, SHA/huella/caducidad,
CORREGIR, configuracion invalida, controles V2 y flags desactivados.

Suites historicas ejecutadas sobre 6ce6af0 antes de incorporar main, salida 0:

| Suite | Pruebas | Fallos/errores | Omitidas |
|---|---:|---:|---:|
| Python raiz | 161 | 0 | 0 |
| Python privada | 113 | 0 | 0 |
| JavaScript local | 7 | 0 | 0 |
| TypeScript local (sin typecheck) | 3 | 0 | 0 |
| Total de suites locales | 284 | 0 | 0 |

El ensayo Docker de 23 pruebas es una ejecucion adicional; 20 corresponden al
mismo piloto ya cubierto localmente, no son 23 casos funcionales nuevos. La raiz
de aquella revision no incluia las 17 pruebas de retirada del bloque 8.
No se omitieron pruebas de su suite: se explicita la diferencia entre bases.

Comandos completos (desde raiz salvo la suite privada):

```powershell
& "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -B -m unittest discover -s tests -v
node --test --test-reporter=tap pilot-js/tests/bottles.test.mjs
node --experimental-strip-types --test --test-reporter=tap pilot-js/tests/bottles.test.ts
# Desde ERP-FACTORY-revision/: mismo comando Python unittest discover.
```

Logs de suites en ../entregas-locales/bloque-9-*.log. Evidencia Docker en
../entregas-locales/bloque-9-docker-real-3/ (evidence.json y commands-and-output.json).
Los intentos previos 1 y 2 se conservan; sus incidencias estan explicadas en
DOCKER.md. No se presentan como ensayos completos aprobados.

## Limites y NO VERIFICADO

- No reglas/identidades/aprobaciones GitHub reales, ni revision Claude de este SHA.
- No activacion, ERP, datos reales, llamadas a proveedores o workflows.
- No auditoria de vulnerabilidades o prueba general de aislamiento frente a
  codigo hostil; solo el piloto y casos ficticios indicados en este PC.
- El motor puede tener red; --network=none se aplica al contenedor. /tmp es
  escribible y Docker usa disco local aunque el montaje del codigo sea readonly.
- Licencia vigente no consultada en linea; elegibilidad declarada por Fernando.
- TS local se ejecuta sin comprobacion estatica de tipos; no prueba TS en Docker.
- La integracion local con main 54b5bda se comprueba en la actualizacion de arriba;
  cambios remotos posteriores, aprobaciones GitHub y revision Claude del nuevo SHA
  no se han verificado. No se abre, aprueba ni integra ninguna PR.

Reversion: revertir este commit local devuelve la politica anterior; no afecta
a las imagenes descargadas ni al motor, cuyo borrado/parada requeriria otra
autorizacion. El SHA final se entrega fuera del documento para evitar autorreferencia.
