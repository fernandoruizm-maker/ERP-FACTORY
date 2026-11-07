# Correccion de la fase previa del intento 1 (sin ejecutar otro intento)

Base: 585089965bfb3288337c4f513f2c6edd46a548a1. Rama piloto/intento-1.
Diagnostico local del 7-11-2026, sin red, claves ni escrituras al registro real.

## Causa reproducida y salida real

El primer bloqueo reproducido es SOURCE_OR_CANDIDATE_NOT_CLEAN.
PilotTrial.start toma el candado y crea state/worker.lock; despues _start llama
a clean_head. Ese archivo no estaba excluido de Git. El check anterior se hacia
antes de crear el candado y no comprobaba Docker. Por eso podia dar OK antes de
que la propia ejecucion ensuciara el arbol. El codigo historico generico no
permite leer retrospectivamente su subcausa; este diagnostico reproduce la
comprobacion y explica el fallo segun el orden del codigo.

Entorno reducido utilizado, exactamente como el lanzador: PATH, SYSTEMROOT,
WINDIR, TEMP, TMP, PATHEXT, COMSPEC, PYTHONDONTWRITEBYTECODE=1 y
PYTHONIOENCODING=utf-8. Sin USERPROFILE, APPDATA, clave ni variables Docker.
Git conserva ademas sus opciones de aislamiento de configuracion y hooks.
Salida real de las consultas de lectura, antes de editar:

```text
git status --porcelain
exit=0; stdout="?? state/\n"; stderr=""
git ls-files --others --exclude-standard state/
state/worker.lock
git rev-parse HEAD
exit=0; stdout="585089965bfb3288337c4f513f2c6edd46a548a1\n"; stderr=""
clean_head: SOURCE_OR_CANDIDATE_NOT_CLEAN

Revision importada: source_sha=585089965bfb3288337c4f513f2c6edd46a548a1
conclusion=SIN OBJECIONES TECNICAS
review_id=manual:6c2c950a7219f559353fe33af0833b25e4329370b210afc792a13f6b2d93d589

docker context inspect --format {{.Endpoints.docker.Host}}
exit=0; stdout="npipe:////./pipe/docker_engine\n"; stderr=""
docker image inspect python@sha256:09a17cad02668ae61ece136b4fd36ac3849e14f670ebedb637ea3e15580525bc --format {{.Os}}/{{.Architecture}}
exit=0; stdout="linux/amd64\n"; stderr=""
docker image inspect node@sha256:01d566e8d94d8c619591d78652babfccd3c6992a3dffa9ed5ab39e11cf6c70e9 --format {{.Os}}/{{.Architecture}}
exit=0; stdout="linux/amd64\n"; stderr=""
```

Las primeras consultas de imagen desde el sandbox devolvieron exit=1,
stdout="\n" y stderr="permission denied while trying to connect to the docker
API at npipe:////./pipe/docker_engine\n". Se repitieron por la via formal de
aprobacion, limitada a esas lecturas locales, con las salidas correctas de arriba.
No se cambiaron permisos/configuracion ni se arranco ningun contenedor.
No se reprodujeron avisos de Docker ni falta de contexto por el entorno reducido.
No se agregan USERPROFILE/APPDATA ni se modifica runner.py por una sospecha no confirmada.

## Cambios

- Ignorar SOLO /state/worker.lock. Otros archivos imprevistos en state/ siguen
  bloqueando Git; una prueba usa un repositorio temporal real para demostrarlo.
- Extraer validate_config e inspect_start a factory2/pilot_preflight.py:
  configuracion, autorizacion, SHA limpio, revision, contrato de peticion,
  contexto Docker local, ambas imagenes fijadas, rutas y candidato inexistente.
  check y _start llaman al mismo codigo bajo el candado de un solo trabajador.
- check abre SQLite en mode=ro, relee la revision bajo el candado y no crea
  Store/tablas, reservas, candidatos ni registros de intento. Tambien comprueba
  intentos anteriores sin terminar y moneda acumulada. El candado es el unico
  archivo operativo que puede crear; no modifica SQLite.
- New-TrialProcessInfo construye tanto check como run con la misma lista de
  entorno reducido. El check precede al aviso de clave; run repite las
  comprobaciones antes de leer la entrada privada. No se amplia la lista.
- Los fallos de _start se conservan con un codigo concreto de lista cerrada,
  por ejemplo SOURCE_OR_CANDIDATE_NOT_CLEAN o PILOT_PINNED_IMAGES_REQUIRED.
  CLI y PowerShell muestran ese codigo, nunca el texto de una excepcion.
  Errores inesperados se clasifican como fallo de SQLite, proceso, E/S o
  PILOT_PREFLIGHT_UNEXPECTED_NO_RETRY. No se guardan detalles libres.

Un OK comprueba el estado EN ESE MOMENTO. No puede garantizar que Docker, Git,
la caducidad o el saldo permanezcan iguales despues. Por eso run repite las
comprobaciones y _start vuelve a verificarlas bajo el candado antes del proveedor.
Los fallos en check no consumen un intento; un intento ya registrado que falla
en _start conserva su bloqueo y no se reintenta automaticamente.

## Verificacion

Suites completas ejecutadas (raiz, privada, JS y TS):

```powershell
# Desde la raiz:
& "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -B ..\entregas-locales\ejecutar-suite-sin-red.py
# Desde ERP-FACTORY-revision:
& "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -B ..\..\entregas-locales\ejecutar-suite-sin-red.py
# Desde la raiz:
node --test --test-reporter=tap pilot-js/tests/bottles.test.mjs
node --experimental-strip-types --test --test-reporter=tap pilot-js/tests/bottles.test.ts
```

Resultados: raiz 233, privada 113, JavaScript 7, TypeScript 3; 356 pasadas,
0 fallos, errores y omitidas; salidas 0. Logs externos preflight-correccion-root.log,
preflight-correccion-private.log, preflight-correccion-js.log y preflight-correccion-ts.log.
Python usa el envoltorio que elimina credenciales heredadas y bloquea red y
procesos externos reales. Docker/proveedor son dobles ficticios en las suites.
La prueba PowerShell solo carga la funcion constructora mediante AST: no ejecuta
el lanzador, Process.Start ni los modos check/run. Sus caches quedan en un temporal.

Regresiones: candado no ensucia Git pero otros archivos si; check consulta ambas
imagenes; endpoint remoto rechazado; check/start devuelven el mismo fallo Docker;
Git sucio conserva su codigo; candidato existente y trabajador activo bloquean;
intento previo sin terminar bloquea; SQL permanece byte a byte igual en check;
errores no admitidos no filtran texto; intento fallido no se repite; entornos de
ambas fases identicos y sin variables de clave/perfil/proxy.

NO VERIFICADO: proveedor, red/API, facturacion, ejecucion real del ensayo,
contenedores de construccion/pruebas y autenticacion de personas. TS no comprueba
tipos. Las consultas reales autorizadas a Docker solo acreditan contexto e imagenes.

## Registro y siguiente intento

SQLite real conserva su SHA-256 original:
00e52b0fb8601e0334ca7d802d6297e79b6d0d4cf281d0c951bec7ea207e5b7d.
Se comprobo en lectura: 0 llamadas, 0 intentos pagados; bottles-1 sigue BLOCKED,
con su codigo historico PILOT_PREFLIGHT_BLOCKED_NO_RETRY. No se reescribe ese dato.
El intento 1 queda cerrado. No se firman/importan nuevos documentos ni se toca
su autorizacion. El siguiente sera attempt=2, con autorizacion nueva de Fernando
y revision de Claude del SHA final. Este parche no prepara ese segundo intento:
la entrada especifica trial_command/ensayo-intento-1 sigue limitada al intento 1.
Preparar la entrada y expediente del intento 2 es una etapa posterior, nunca
reutilizando la autorizacion, la revision o el identificador del intento cerrado.
Config.json, upstream/, la fabrica original y los remotos permanecen intactos;
envio DISABLED. No hay publicacion, clave, gasto ni activacion adicional.
