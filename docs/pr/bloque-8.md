# PR propuesta: registrar la retirada declarada de la fabrica original

Rama local: `fix/bloque-8-retirada-registrada`.
Base comprobada: `877dd757f83f5fece05e2216ddfdea36843f0c4a` (origin/main).
No publicada; no abrir ni integrar PR sin autorizacion de Fernando.

## Problema y cambio

La original esta retirada segun Fernando, pero el Coordinator bloqueaba siempre
con ORIGINAL_COORDINATION_NOT_VERIFIED. Ahora valida el registro sencillo
`docs/retirada-original.json` mediante `factory2/retirement.py`. No exige copias,
firmas ni autenticacion; devuelve ORIGINAL_RETIRED_DECLARED con
provenance_authenticated=false y publication_allowed=false.

Se comprueban fecha, responsable, VM, App ID 5603415 y retirada de clave/instalacion,
inventario acotado de Windows, pausa conservada, OpenAI NO_EXISTIA y archivo
NO_POR_DECISION_DE_FERNANDO. No se copian rutas privadas, credenciales ni datos ERP.
El registro usa esquema cerrado: faltantes, extras, duplicados, tipos incorrectos,
fechas imposibles/futuras y contenido excesivo no pasan. No sigue enlaces del archivo.

Codigos fijos de bloqueo: ORIGINAL_RETIREMENT_MISSING, ORIGINAL_RETIREMENT_INCOMPLETE,
ORIGINAL_RETIREMENT_INVALID, ORIGINAL_RETIREMENT_CONTRADICTORY,
ORIGINAL_RETIREMENT_PATH_UNSAFE y ORIGINAL_RESTORED. Nunca se incluyen los datos
invalidos ni errores libres de lectura en esos mensajes.

El registro se relee al entrar al trabajador y antes de reservar llamadas.
recover mantiene la exclusion mutua. Store usa por defecto el directorio de su
estado para worker.lock, en lugar de un Coordinator sin directorio configurado.
El candado protege trabajadores que comparten ese directorio; no es un candado
global entre instalaciones distintas. No se crea otro proceso ni servicio.
Se permite guardar el resultado de una llamada ya reservada tras invalidarse el
registro, sin iniciar nuevas llamadas ni reintentar.

Se mantiene intacta la simulacion con su indicador ficticio. No se modifican las
puertas de revision, aceptaciones, presupuesto, permisos ERP ni config.json.
Los cuatro interruptores de config.json siguen en false; upstream/ y el revisor
privado no cambian. El antiguo bloqueo de coordinacion se resuelve exclusivamente
mediante una declaracion consistente, no mediante una aprobacion de operacion.

## Pruebas locales

Resultados reales de las suites completas (salida 0 en las cuatro):

| Suite | Pruebas | Fallos/errores | Omitidas |
|---|---:|---:|---:|
| Python raiz | 166 | 0 | 0 |
| Python privada | 113 | 0 | 0 |
| JavaScript | 7 | 0 | 0 |
| TypeScript (sin comprobacion estatica de tipos) | 3 | 0 | 0 |
| Total | 289 | 0 | 0 |

Comprobacion focal previa: `python -B -m unittest tests.test_retirement
tests.test_operation -v`: 51 pruebas, 0 fallos/errores, 0 omitidas. Es un
subconjunto de las suites completas, no se suma al total de 289.

Comandos desde la raiz (Python instalado, sin descargas):

```powershell
& "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -B -m unittest discover -s tests -v
node --test --test-reporter=tap pilot-js/tests/bottles.test.mjs
node --experimental-strip-types --test --test-reporter=tap pilot-js/tests/bottles.test.ts
```

Suite privada: mismo comando Python desde `ERP-FACTORY-revision/`.
Python requiere la autorizacion del entorno para sus carpetas temporales; no
se cambian permisos del sistema ni se usa red. Los logs completos se conservan
fuera del repositorio, en `../entregas-locales/bloque-8-*.log`.

Las 17 pruebas nuevas cubren registro correcto, ausente, incompleto (cada campo),
contradictorio, restaurado, tipos, fechas, JSON malformado, claves duplicadas,
extras, longitud, errores de lectura, enlaces, relectura, candado y recuperacion.
Con config real desactivada, los dos adaptadores se bloquean antes de leer
credenciales o alcanzar transporte/CLI (interceptados con dobles que fallarian).
Tambien se comprueba que una declaracion valida no satisface revision/aceptaciones.
La prueba de coordinacion anterior ahora exige expresamente un registro ausente,
para comprobar que un indicador de simulacion no sustituye la declaracion real.

## NO VERIFICADO y limites

- No se contrasto de nuevo la retirada en VirtualBox, Ubuntu, Windows, GitHub o
  proveedores. La declaracion no autentica a Fernando ni detecta restauraciones
  ocultas/no comunicadas. Se debe declarar la restauracion antes de llevarla a cabo.
- No se hicieron llamadas reales, revisiones Claude, integraciones GitHub,
  ejecuciones de workflows, Docker ni accesos ERP. Los dobles no acreditan eso.
- No se auditaron credenciales ni se exigio respaldo oficial. Se conserva la
  decision SIN ARCHIVO; no se promete recuperacion de la original.
- El candado se prueba localmente en Windows; no se acredita su ejecucion Linux.
- TS se ejecuta con eliminacion de tipos, sin comprobacion estatica de tipos.
- El revisor privado sigue aparcado; antes de reactivarlo habra que revisar su
  alcance explicito contra el inventario vigente. No se prepara una ejecucion.
- No hay una revision de Claude ni nuevas aceptaciones humanas de este SHA.

## Reversion

Revertir el commit local de este bloque restablece el bloqueo incondicional previo.
No requiere tocar la original, configuracion, credenciales ni estado historico.
El SHA final y diff --stat se entregan fuera de este archivo para evitar una
referencia circular al commit que contiene el propio documento.
