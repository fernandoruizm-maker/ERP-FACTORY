# Bloque 10: preparar UN ensayo ficticio, sin ejecutarlo

Rama feat/bloque-10-piloto desde main comprobado mediante el unico fetch autorizado:
**c55453edd9f04c7274a5fabfddc54c21eda53b30** (PR #14, bloques 1-9).
No se llama a proveedores, no se ejecuta Docker, no se instala nada ni se publica.
Las pruebas de este bloque son dobles ficticios. No acreditan la integracion real.

## Decision de Fernando y alcance

Fernando eligio **modelo Codex mediante API**, con llamada controlada desde el host
y construccion aislada en Docker. No se instala Codex CLI en las imagenes.
SafeCodexAgent conserva su compatibilidad anterior y sigue desconectado; la via
nueva es DockerCodexBuilder, usada exclusivamente por PilotTrial cuando se autorice.

El ensayo produce solo **src/bottles.mjs**, la version JavaScript de las botellas,
a partir de fixtures/cliente.json y las siete pruebas de confianza existentes.
No se envia la implementacion resuelta ni el ERP. El Python de la imagen se usa
para materializar los archivos propuestos; Node ejecuta las pruebas JavaScript.
No se solicita otra implementacion Python o TS ni se permiten ediciones de pruebas.

Las dos imagenes se reutilizan por los digests del bloque 9:

- Python: `python@sha256:09a17cad02668ae61ece136b4fd36ac3849e14f670ebedb637ea3e15580525bc`.
- Node: `node@sha256:01d566e8d94d8c619591d78652babfccd3c6992a3dffa9ed5ab39e11cf6c70e9`.

No hay pull/build de imagenes ni descarga de dependencias. Si falta una imagen
local o el destino Docker no es una de las tuberias locales permitidas, se bloquea
antes de llamar al proveedor. No se cambia el contexto Docker de Fernando.

## Que hara el ensayo autorizado

1. Leer config y exigir external_calls_enabled=true; hoy permanece **false**.
   enabled, erp_access_enabled y publication_enabled deben seguir false incluso
   durante el ensayo. No se ha anadido otro interruptor de activacion.
2. Validar requisitos ficticios, hashes del contexto/configuracion, autorizacion
   de Fernando con caducidad y revision manual previa de la fabrica en su SHA
   exacto. Exigir un checkout limpio: editar config sin revisar/confirmar el nuevo
   SHA no permite arrancar. La declaracion de retirada y el candado siguen vigentes.
3. Registrar el intento bottles-N en SQLite y reservar una sola llamada.
   La reserva se guarda antes de leer la credencial o transmitir. Otro trabajador
   se bloquea; un intento ya registrado no se repite ni se reintenta automaticamente.
   Otro numero requiere una nueva autorizacion de Fernando; no hay incrementos automaticos.
4. Hacer **una peticion POST** desde el host a
   `https://api.openai.com/v1/responses`, con modelo que Fernando debera elegir,
   sin herramientas, sin streaming, sin reintentos y con store=false. No seguir
   redirecciones ni heredar proxies. Timeout de la peticion: 60 segundos.
5. Validar JSON/estado/respuesta, rechazar herramientas, respuestas incompletas,
   secretos detectados y rutas fuera de src/bottles.mjs. Un fallo incierto conserva
   la reserva como UNKNOWN y bloquea, sin mostrar respuesta o excepcion del proveedor.
6. Materializar el codigo como texto dentro del contenedor Python, con worker
   propio revisable. El codigo generado **no se ejecuta en el host ni en ese worker**.
   El contenedor tiene red none, raiz readonly, usuario 65534, sin capacidades ni
   privilegios nuevos, limites de memoria/CPU/procesos y --pull=never. Solo la carpeta
   NUEVA del candidato es escribible; entrada y worker estan montados readonly.
7. Incorporar las pruebas de confianza y comprobar las huellas. DockerRunner
   ejecuta las siete pruebas Node con todo el candidato readonly y sin red.
   Cualquier fallo o cambio de archivos detiene la cadena.
8. Crear un commit Git **local** del candidato en una carpeta separada, sin remoto,
   hooks, firma ni identidad global. El nombre local ficticio no es una aprobacion.
   Guardar su SHA y las pruebas; detenerse en WAITING_FOR_MANUAL_REVIEW.
9. Fernando adjunta personalmente src/tests y evidencia en Claude. No hay envio
   automatico. Registrar el informe en docs/revisiones como *.local.md con el SHA
   exacto del **candidato**, distinto del SHA de la fabrica, y los dos archivos
   revisados. CORREGIR, SHA distinto o cobertura declarada incompleta bloquean.
10. Esperar aceptaciones vigentes de Fernando y FERRUMTJA: para este producto de
    inventario se usa conservadoramente el nivel accounting_product/ficticio/botellas.
    La regla de una aceptacion para ERP-FACTORY no se reutiliza como atajo para el
    producto. Solo se puede alcanzar READY_FOR_MANUAL_REVIEW, siempre con
    publication_allowed=false y provenance_authenticated=false. Nunca despliega.

Las interfaces preparadas son PilotTrial.start(authorization), attach_review(path),
accept(person, role, expires_at) y gate(). No se instala un comando, servicio,
workflow o temporizador que las ejecute automaticamente. La autorizacion contiene
source_sha (fabrica), context_digest, config_digest, authorized_by=Fernando,
expires_at, factory_review_id y attempt (entero positivo). Es una declaracion local, no autenticacion criptografica.
El resultado identifica el SHA candidato, la version del expediente y la huella.

## Red, entorno y claves

La **unica excepcion de red futura** es la peticion API del componente confiable
del host. Es necesaria para usar el modelo remoto elegido. Ningun contenedor
recibe red, credenciales, socket Docker ni el repositorio entero. No se ejecuta
codigo generado con red. La futura llamada transmite solo los requisitos y
pruebas ficticias, mas el esquema/instrucciones de construccion.

ResponsesAPI lee OPENAI_API_KEY del entorno del proceso host solo al transmitir.
No escribe ni imprime la clave, no la pone en argumentos o archivos y no la pasa
a Docker. Los procesos Docker usan la lista blanca de bounded_process, que elimina
claves, proxies e inyecciones Python/Node. No se crean ni cambian credenciales aqui.
El filtrado de patrones reduce riesgos de respuestas, no certifica ausencia absoluta
de cualquier dato sensible. La autenticacion real de la API sigue NO VERIFICADA.

El contrato Responses, el modelo compatible, su disponibilidad y tarifas actuales
no se verificaron por red: Fernando solo autorizo el fetch. La consulta a documentos
oficiales/API no se disfraza de comprobacion local. pilot_model y pilot_cost_review
permanecen null; no hay modelo ni tarifa elegidos automaticamente.

## Gasto: presupuesto preparado, no activado

| Limite previsto en USD | Valor previsto | Valor actual en config.json |
|---|---:|---|
| Por llamada | 1.00 | null |
| Por ejecucion | 12.00 | null |
| Acumulado en el registro local | 13.00 | null |

Con cualquiera de esos null, no empieza. BudgetLedger comprueba los tres topes
con importes decimales exactos y reserva atomica. El ensayo, aunque la configuracion
general conserve 11 llamadas, registra una ejecucion limitada a **una sola llamada**.
Con los valores propuestos reservaria como maximo **USD 1.00**. No gasta los USD 12
por tenerlos como techo: no hay bucle de reparaciones ni revisiones pagadas.

**USD 1.00 es el maximo autorizado/reservado para este ensayo, no una garantia
de la factura del proveedor.** Un registro local no puede cortar retroactivamente
un cargo. Antes de habilitarlo es obligatorio verificar el coste maximo de la
peticion para el modelo, tarifa y limite de salida elegidos; si no se puede
establecer un limite compatible con USD 1.00, no autorizar la llamada.

pilot_cost_review registra model, basis (evidencia de esa revision),
max_request_bytes (hasta 100000), max_output_tokens (hasta 32000), reasoning_effort,
input_usd_per_million, output_usd_per_million y max_call_usd (no superior al tope
por llamada). Los precios son cadenas decimales positivas en USD, hasta seis
decimales; no se admiten floats, exponentes ni valores ausentes. Ningun precio
real se inventa: config sigue null. Las tarifas y compatibilidad del esfuerzo
con el modelo elegido necesitan verificacion antes del ensayo.

Antes de transmitir, el calculo usa EXACTAMENTE los bytes UTF-8 que enviara HTTP:

    peor caso USD = (bytes_peticion * precio_entrada + max_output_tokens * precio_salida) / 1000000

Un byte se cuenta como un token de entrada: estimacion conservadora solicitada,
no tokenizacion medida. Se calcula con enteros y se redondea hacia ARRIBA al
millonesimo de USD. Si supera max_call_usd se bloquea sin llamar. reasoning_effort
se envia como reasoning.effort: none, minimal, low, medium, high o xhigh; esa
lista no certifica compatibilidad con cada modelo. 32000 es un techo permitido,
no un valor activado ni garantia de que la respuesta termine completa. Siguen
vigentes los limites de bytes de respuesta y los rechazos de salida incompleta.

Despues de responder se conservan solo usage.input_tokens, usage.output_tokens
y output_tokens_details.reasoning_tokens, coste calculado, precios declarados y
peor caso. Los tokens de razonamiento YA estan incluidos en output_tokens y no
se suman por segunda vez. Se ignoran todos los campos libres de usage. El coste
es (input_tokens * precio_entrada + output_tokens * precio_salida) / 1000000,
con el mismo redondeo conservador. No aplica descuentos de cache: tampoco supone
que existan. billing_verified=false; estos numeros no son una factura verificada.

Se guarda el uso numerico incluso si la respuesta es incompleta o su propuesta
no valida, siempre que exista y pase la validacion numerica y de seguridad previa.
Sin uso valido: resultado incierto, reserva conservada. El coste informado queda
tambien en paid_attempts.actual_units. Si supera la reserva, se registra
OVER_BUDGET, no se construye y se bloquean siguientes llamadas hasta reconciliar.
Si los tokens exceden la estimacion o el limite autorizado, se detiene igualmente.
La reserva ahora usa max_call_usd, no un importe mayor tomado del limite general.

UNKNOWN/REJECTED no liberan dinero. El registro acumulado se conserva en el mismo
SQLite: no se puede usar otro archivo vacio para fingir saldo disponible. El total
es el del registro, no el gasto global de una cuenta OpenAI. Antes de otra
autorizacion hay que reconciliar facturacion, incluyendo resultados inciertos.
Si se informa un coste superior a la reserva mientras se finaliza una reserva,
BudgetLedger marca OVER_BUDGET y bloquea intentos posteriores; no presupone que
esa evidencia de facturacion llegue automaticamente. No hay retries ni reembolso
automatico. Una caida requiere reconciliacion humana; recover no retransmite.

## Lista exacta pendiente para Fernando

1. Autorizar consultar documentacion oficial para verificar contrato Responses,
   modelo Codex disponible, condiciones de uso de su cuenta API, tarifa y limite
   de peticion/salida. No asumir que la suscripcion de ChatGPT paga esta API.
2. Aprobar modelo, contexto ficticio completo, imagenes y pruebas fijadas, y la
   revision de coste que permita autorizar como maximo USD 1.00 para una llamada.
   Confirmar/reconciliar el registro acumulado y su ubicacion permanente.
3. Autorizar por separado el cambio local de los tres null a 1.00/12.00/13.00,
   pilot_model, pilot_cost_review y **solo external_calls_enabled a true** para
   este ensayo. Mantener los otros tres flags false. Guardar el cambio en un
   commit local y obtener revision manual de Claude del SHA final de la fabrica.
4. Disponer una credencial temporal para el proceso host mediante entrada privada,
   sin chat, capturas, archivos del repositorio ni argumentos. No pedirla a Codex
   ni a Claude. Confirmar previamente el procedimiento de entrada segura; no se
   ha instalado un gestor ni autenticado una cuenta en este bloque.
5. Autorizar explicitamente **una llamada API**, su posible cargo y la transmision
   del contexto aprobado, con SHA/hash/caducidad y attempt=N. Cada nuevo numero
   requiere una nueva autorizacion expresa; nunca se crea automaticamente. Autorizar las carpetas nuevas
   locales del candidato y evidencias, el uso del registro existente y Docker
   sin red con las imagenes ya presentes; no implica permiso de descarga.
6. Autorizar el snapshot Git local del candidato y las pruebas. Al terminar la
   parte automatica, devolver external_calls_enabled a false con una operacion
   humana explicita; el codigo no cambia interruptores. Despues de las pruebas,
   la unica variacion de configuracion admitida al revisar/aceptar es ese apagado.
   Cualquier otro cambio bloquea. Apagar no modifica ni aprueba el candidato.
7. Fernando decide que adjunta a Claude. Registrar revision del SHA candidato;
   despues, Fernando y FERRUMTJA aceptan con caducidad. No publicar, conectar ERP
   ni ejecutar otro ensayo sin nueva autorizacion. Las aceptaciones se pueden
   registrar con el interruptor ya apagado: la marca durable bottles-N impide otra
   ejecucion del mismo numero y no se reactiva para completar una aprobacion.

Ninguno de esos permisos futuros se da por concedido ahora. La revision tecnica
externa antes de datos reales/ERP y las reglas de aprobacion por niveles siguen.

## Correccion tras la revision de Claude de 0d51883

Misma rama, sin red, proveedores ni publicacion. La autorizacion ahora incluye
attempt (1..1000000). Cada numero consume una sola autorizacion registrada por
huella; aun un bloqueo de preflight impide reutilizar ese numero. No se modifica
una fila anterior, ni se borra el candidato anterior. El id bottles-N sirve para
ensayo, ejecucion de presupuesto, llamada, tarea y carpeta. El constructor puede
recuperar un expediente con PilotTrial(..., attempt=N). Una ejecucion anterior
pendiente de revision/aceptaciones o interrumpida antes de finalizar bloquea un
nuevo intento; solo un expediente BLOCKED permite presentar otro numero.

Sigue siendo una declaracion local de Fernando, no autenticacion. Cambiar el
numero exige renovar expresamente su autorizacion con SHA/contexto/config/fecha;
el programa no pregunta al proveedor ni reintenta por su cuenta. Todos los
numeros comparten el MISMO registro de presupuesto y el tope total de USD 13.
No se reinicia el gasto al cambiar attempt. UNKNOWN conserva toda la reserva.
Un intento rechazado antes de llamar consume el numero, pero no cobra una llamada.

## Pruebas ejecutadas y limites

Pruebas focales iniciales: 35, sin fallos ni omitidas, con dobles. Se ampliaron
despues con comprobaciones de tope autorizado por llamada y entorno filtrado.
Resultados historicos de 0d51883 (sustituidos por la ejecucion de correccion indicada abajo):

| Suite | Pruebas | Fallos/errores | Omitidas |
|---|---:|---:|---:|
| Raiz Python | 199 | 0 | 0 |
| Revisor privado Python | 113 | 0 | 0 |
| JavaScript | 7 | 0 | 0 |
| TypeScript (sin comprobacion de tipos) | 3 | 0 | 0 |
| Total | 322 | 0 | 0 |

Las dos suites Python finalizaron con OK; Node comunico fail=0, cancelled=0,
skipped=0. Evidencia local fuera del repositorio: ../entregas-locales/
bloque-10-root.log, bloque-10-private.log, bloque-10-js.log y bloque-10-ts.log.
La ejecucion Python necesito permiso local para los directorios temporales;
ese permiso no autorizo ni utilizo red. No se ejecutaron pruebas de upstream/.

Comandos desde la raiz (sin red, proveedores ni Docker):

```powershell
& "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -B -m unittest tests.test_pilot_trial tests.test_budget -v
& "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -B -m unittest discover -s tests -v
node --test --test-reporter=tap pilot-js/tests/bottles.test.mjs
node --experimental-strip-types --test --test-reporter=tap pilot-js/tests/bottles.test.ts
# Desde ERP-FACTORY-revision/:
& "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -B -m unittest discover -s tests -v
```

Casos: cadena feliz con pausas, fallo de pruebas, nulls, interruptor apagado,
topes por llamada/ejecucion/acumulado, respuesta invalida/incierta sin reintento,
concurrencia, SHA/contexto/configuracion cambiados, revision CORREGIR, codigo
alterado, dos aceptaciones, worker offline, rutas/duplicados y entorno permitido.
No se ejecuto codigo propuesto por un modelo; las propuestas de pruebas son ficticias.

NO VERIFICADO: peticion Responses real, modelo/precios/autenticacion/facturacion,
nuevo worker de construccion en Docker real, snapshot Git del candidato en el
flujo real, revisiones/identidades humanas autenticas, GitHub, ERP y despliegue.
El Docker del bloque 9 solo acredita aquel piloto, no la integracion nueva.
TS local no comprueba tipos estaticamente. Las nuevas pruebas no usan providers,
Docker ni Git reales: todos esos puertos son dobles explicitos en modo simulado.

Reversion: revertir el commit local de este bloque; no restaura ni borra datos
de ensayos reales (no existen por esta tarea). No borrar el registro de gasto
para permitir reintentos. El SHA final se entrega fuera del documento.


## Verificacion de esta correccion

Pruebas focales: 50, cero fallos/errores y cero omitidas. Comando Python
`-B -m unittest tests.test_pilot_trial tests.test_budget -v` con el ejecutable
indicado arriba. Suites completas de la correccion, todas con salida 0:

| Suite | Pruebas | Fallos/errores | Omitidas |
|---|---:|---:|---:|
| Raiz Python | 211 | 0 | 0 |
| Revisor privado Python | 113 | 0 | 0 |
| JavaScript | 7 | 0 | 0 |
| TypeScript, sin comprobacion de tipos | 3 | 0 | 0 |
| Total | 334 | 0 | 0 |

Se ejecutaron los mismos cuatro comandos completos indicados arriba. Evidencia:
../entregas-locales/bloque-10-correccion-root.log,
bloque-10-correccion-private.log, bloque-10-correccion-js.log y
bloque-10-correccion-ts.log. Las 50 focales constan en
bloque-10-correccion-focused.log. Todas son locales; Python requirio acceso a
temporales, sin permiso ni uso de red. No se ejecutaron pruebas de upstream/.

Los nuevos casos comprueban 32000 tokens y esfuerzo, limite 32001 rechazado,
precios ausentes/invalidos, bytes UTF-8 exactos, frontera exacta del peor coste,
redondeo, razonamiento sin doble conteo, uso incompleto/invalido, persistencia
numerica en ensayo y presupuesto, sobrecoste, numero obligatorio, bloqueo antes
de transmitir consumido, nuevo intento expreso y total compartido hasta USD 13.
NO VERIFICADO: tarifas reales, compatibilidad real de reasoning.effort/32000,
formato real de usage y limites del servicio. Ninguna simulacion acredita API,
Docker o GitHub reales. No se ampliaron los permisos ni se cambio config.json.
