# Preparar el intento 2: numero explicito, sin ejecucion

Base: 42c0c236a01d0601166f2f5ba3f7941ecac7d7f8. Rama piloto/intento-1.
Fecha: 7-11-2026. Trabajo local sin red, claves ni escrituras al registro real.

## Cambios y controles

- trial_command.prepare/preflight/execute reciben attempt=N y el CLI --attempt N.
  PowerShell recibe -Intento N y lo transmite a preparar, check y run. Se conserva
  el nombre scripts/ensayo-intento-1.ps1 para no romper rutas existentes.
- N debe ser un entero entre 1 y 1000000, igual al rango de PilotTrial. El valor
  predeterminado sigue siendo 1 por compatibilidad; para el siguiente ensayo hay
  que indicar expresamente -Intento 2. Omitirlo no puede reabrir el intento 1.
- La autorizacion debe contener exactamente attempt=N; no se deduce el numero
  del documento ni se busca automaticamente el siguiente numero libre.
- Se comprueba bottles-N en todas las tablas del registro, en sus columnas de
  identidad/referencia id, task y execution. Se citan los nombres del esquema
  y se parametriza el identificador; las filas existentes nunca se sustituyen.
- Todos los intentos 1..N-1 deben existir en pilot_trials como BLOCKED. Un hueco
  o cualquier intento registrado sin terminar bloquea con
  PILOT_PREVIOUS_ATTEMPT_UNFINISHED. Un N ya registrado bloquea con
  PILOT_ALREADY_RECORDED_NO_RETRY, aunque su estado sea BLOCKED.
- La ejecucion construye PilotTrial(attempt=N). Se mantienen las comprobaciones
  comunes bajo candado, el entorno reducido, la revision del SHA exacto y todos
  los controles anteriores. Sin reintentos automaticos.

No cambian config.json, el modelo, las tarifas, las imagenes, los interruptores,
el constructor, la orquestacion ni budget.py. Topes: USD 1.00 por llamada,
12.00 por ejecucion y 13.00 acumulados. Sigue siendo una llamada por ensayo.
La peticion no cambia por el numero de intento: 4723 bytes, peor coste calculado
USD 0.329446; con el limite completo de entrada, USD 0.520000. No es gasto medido.
Los codigos historicos ATTEMPT_1_MODEL/COST_REVIEW/LIMIT_MISMATCH se conservan;
la discrepancia entre numero autorizado y parametro usa PILOT_AUTHORIZATION_REQUIRED.

## Pruebas ejecutadas

Comandos desde la raiz, salvo la suite privada:

```powershell
& "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -B ..\entregas-locales\ejecutar-suite-sin-red.py
# Desde ERP-FACTORY-revision:
& "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -B ..\..\entregas-locales\ejecutar-suite-sin-red.py
# Desde la raiz:
node --test --test-reporter=tap pilot-js/tests/bottles.test.mjs
node --experimental-strip-types --test --test-reporter=tap pilot-js/tests/bottles.test.ts
& "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -B ..\entregas-locales\test_gestionar_intento_2.py
```

Suites completas: raiz 242, privada 113, JS 7, TS 3: 365 pasadas.
Auxiliar externo: 5 pruebas adicionales con temporales y dobles explicitos.
Total ejecutado: 370 pruebas; 0 fallos, 0 errores, 0 omitidas; salidas 0.
Logs externos: intento-2-root.log, intento-2-private.log, intento-2-js.log,
intento-2-ts.log e intento-2-helper.log. El envoltorio de suites Python bloquea
red/procesos externos reales y elimina credenciales heredadas del entorno.

Casos solicitados: 2 admitido con 1 BLOCKED; 2 repetido rechazado; 1 cerrado
rechazado otra vez; numero de autorizacion distinto del parametro rechazado.
Ademas: intento previo ausente o sin terminar; referencias en cualquier tabla;
propagacion de N a los tres modos, ambos procesos PowerShell y PilotTrial;
valores invalidos; costes identicos; SQL temporal sin mutaciones en check.
El auxiliar se probo con importar/firmar/verificar simulados: attempt=2,
24 horas desde la confirmacion, sin sobrescrituras, rechazo de FIRMAR INTENTO 1.
Ninguna de esas pruebas importa, firma ni verifica un expediente real.

NO VERIFICADO: llamada real a proveedor, facturacion, red, Docker real,
ejecucion real del ensayo o autenticacion de Claude/Fernando. TS no comprueba
tipos. La prueba PowerShell solo carga la funcion que construye ProcessStartInfo;
no inicia el ensayo ni muestra una entrada de clave.

## Expediente externo pendiente

En ../entregas-locales/, ligados al SHA final del commit:
- revision-claude-intento-2.md: base 42c0c23, SHA nuevo, archivos del diff,
  findings=[], conclusion=PENDIENTE y date=null. No acredita una revision.
- autorizacion-intento-2.borrador.json: attempt=2, SHA y digests exactos;
  authorized_by, expires_at y factory_review_id siguen null. No autoriza nada.
- gestionar-paso-3.py: ahora trabaja exclusivamente con esos archivos y attempt=2.
  importar valida SHA/alcance; firmar exige FIRMAR INTENTO 2 y asigna 24 horas;
  verificar usa preflight(..., attempt=2). No se ejecuta aqui ninguna accion real.
- test_gestionar_intento_2.py: pruebas del auxiliar externo, solo datos ficticios.

El auxiliar no forma parte del commit; debe revisarse aparte. No se atribuye a
Claude una revision que no hizo. Los documentos del intento 1 se conservan.
El registro real mantiene su huella SHA-256:
00e52b0fb8601e0334ca7d802d6297e79b6d0d4cf281d0c951bec7ea207e5b7d.
No se abre con Store, no se reinicializa, no se importa revision ni se firma
autorizacion. Antes del ensayo faltan la revision de Claude y la autorizacion
expresa de Fernando. Sin publicacion; envio DISABLED; upstream/ intacto.
