# Estado vigente: bloque 14, armado local y catálogo

7-11-2026. Base origin/main comprobada: 3988ce4fca1ca61d9d70a73a345b166d9b2454ea.
Rama feat/bloque-14-armado-local, mensaje 4 PERMITIDO del buzón. Configuración
versionada con los cuatro interruptores false, sin cambios. Armado por archivo
local state/armado.json, con encargo/intento/huella y vigencia máxima de 24 horas.
La autorización de Fernando y revisión exacta siguen obligatorias. No se arma ni
se ejecuta un ensayo real. El historial de bottles-N/caja-chica-N no se modifica.

Catálogo externo vacío, módulos estándar explícitos y análisis estático de salida
antes de construir el candidato. JS conservador: puede rechazar código legítimo;
no es un sandbox. Versiones instaladas y licencias no verificadas; sin instalaciones.
Ver docs/ARMADO-LOCAL.md y docs/CATALOGO-DEPENDENCIAS.md.

Suites completas: 300 raíz, 113 privada, 7 JS y 3 TS; 423 aprobadas, cero fallos,
errores u omitidas. Datos temporales/dobles; no acreditan proveedor ni Docker real.
TS sin comprobación de tipos. Detalle de comandos y ejecuciones iniciales fallidas
en docs/pr/bloque-14.md. Auxiliares locales pendientes de adaptar/revisar.

GitHub CLI: configuración predeterminada de Windows, única cuenta permitida
fernandocodex64-sudo; auth status antes de publicar. Buzón en .git/info/exclude.
Mensaje 5 de conciliación de gasto reservado: requiere «buzón, autorizado» de
Fernando y NO se ejecutó. No se toca el ERP, original, upstream ni revisor privado.

## Historial anterior (sus estados no sustituyen al vigente)

# Estado vigente: bloque 13, encargos ficticios generales

6-11-2026 (America/La_Paz). Rama feat/bloque-13-encargos desde origin/main
confirmado en 5bf2add46f6c22009875c6fe9f825cd8c02ab267, unico fetch autorizado.
Encargos estrictos: requisitos, pruebas fijas y salida cerrada. Botellas usa JS
y siete pruebas; caja chica usa Python y ocho pruebas, pendientes de revision
humana del contrato nuevo. El constructor nunca modifica esas pruebas.

PilotTrial y trial_command reciben el encargo. Lanzador scripts/ensayo.ps1 con
-Encargo y -Intento. IDs nuevos <nombre>-N; botellas conserva bottles-N como alias
historico, sin migrar filas ni carpetas ni permitir repetir un numero usado.
Revisiones, aceptaciones y puerta del historial probadas con datos temporales.
Presupuesto comun y candado intactos. Cuatro interruptores false; no hay activacion.

Suites: raiz 278, privada 113, JS 7, TS 3 = 401 pasadas; cero fallos, errores u
omitidas. Caja chica: ocho pruebas sobre doble local y prueba negativa que detecta
omitir el tope diario. API y Docker no verificados; TS sin comprobacion de tipos.
Lanzador real probado solo en Preparar para ambos encargos, sin gastar ni consumir
intentos. No hubo llamadas, claves, cambios al registro real, upstream o revisor privado.
La huella del registro real no cambio; correccion de bottles-2 sigue pendiente.

Envio DISABLED, sin subida ni PR. Decision futura registrada: al autorizar Fernando
la publicacion, Codex subira y abrira PR con gh como fernandocodex64-sudo; nunca
aprobara ni integrara. gh no se usa ni configura aqui.
Detalles: [guia de encargos](ENCARGOS.md) y [entrega del bloque 13](pr/bloque-13.md).

---

# Historia: bloque 12, liquidacion del gasto calculado

7-11-2026. Rama fix/bloque-12-gasto-real desde origin/main confirmado por el
unico fetch autorizado en f745cde657c18fb7cefcacf4e2c05ea96a5527ba.
Las llamadas COMPLETED con uso validado liquidan el coste calculado dentro de
la reserva. Uso ausente, invalido o resultado incierto conserva la reserva;
un exceso bloquea nuevas llamadas para conciliacion. No equivale a factura.
Topes USD 1/12/13 intactos; cuatro interruptores false, sin activar nada.

No se migra ni reescribe el historial. Registro real con huella sin cambios.
La correccion de bottles-2 (cargo USD 1.000000, calculado USD 0.015946) queda
como propuesta separada pendiente de autorizacion, preservando ambos valores.
Ver [pr/bloque-12.md](pr/bloque-12.md) para comportamiento, pruebas y propuesta.

Suites finales: raiz 252, privada 113, JS 7 y TS 3: 375 pasadas, cero fallos,
errores u omitidas. Dobles ficticios; TS sin comprobacion estatica de tipos.
Sin llamadas, claves, Docker real ni cambios en upstream/ o el revisor privado.
Sin subida ni PR; envio DISABLED. Facturacion e integraciones reales no verificadas.

---

# Historia: bloque 11 preparado localmente, ensayo concluido y desarmado

7-11-2026. Rama feat/bloque-11-ensayo desde piloto/intento-1 en aa6fcb1.
Fetch autorizado: origin/main confirmado en f7d973c. No se sube ni integra.
El intento 1 quedo bloqueado por el candado antes del proveedor, sin gasto.
El intento 2 completo el piloto ficticio con gpt-6.1-sol: 1153 tokens de entrada,
1364 de salida, USD 0.015946 calculados y 7/7 pruebas del candidato aprobadas.
Claude declaro SIN OBJECIONES TECNICAS, con un hallazgo minimo sobre decidir
la separacion de aprobacion y despacho antes de usarlo con clientes reales.
Fernando y FERRUMTJA declararon sus aceptaciones locales no autenticadas.
La puerta devolvio READY_FOR_MANUAL_REVIEW, sin bloqueos; publicacion desactivada.

Los cuatro interruptores estan false. Se ajusta la prueba de configuracion
real para exigir este estado final. Suites del bloque: raiz 242, privada 113,
JS 7 y TS 3: 365 pasadas, cero fallos, errores u omitidas. TS sin comprobar tipos.
Las suites locales no repiten el ensayo real. Sin proveedor, clave, Docker real
ni cambios al registro durante este bloque. state/, work/, entregas-locales/ y
revisiones *.local.md no se incorporan a Git. Envio DISABLED.
Resultado publico, comandos y limites: [pr/bloque-11.md](pr/bloque-11.md).

---

# Historia: numero de intento generalizado; intento 2 pendiente

7-11-2026, rama piloto/intento-1, base 42c0c23. El lanzador conserva su nombre
ensayo-intento-1.ps1 y ahora recibe -Intento N; Python recibe --attempt N.
Autorizacion con el mismo numero, bottles-N sin registros previos y todos los
intentos 1..N-1 existentes como BLOCKED. PilotTrial recibe attempt=N.
El intento 1 sigue cerrado. No se elige numero automaticamente ni se reintenta.

Sin cambios en configuracion, interruptores, modelo, topes o logica de gasto.
Suites completas: raiz 242, privada 113, JS 7, TS 3 = 365 pasadas; otras 5
pruebas ficticias del auxiliar externo. Cero fallos, errores y omitidas.
TS sin comprobacion estatica de tipos; sin proveedor ni Docker reales.
Ver comandos, evidencias y limites en [pr/intento-2.md](pr/intento-2.md).

Fuera del repositorio quedan la plantilla de revision del SHA nuevo (PENDIENTE),
el borrador de autorizacion attempt=2 sin firmar y gestionar-paso-3.py adaptado.
No se importan ni firman documentos reales. El auxiliar externo necesita revision
separada; no se atribuye a Claude la revision de este nuevo SHA ni del auxiliar.
Registro real intacto, sin red, clave, ensayo o subida; envio DISABLED.

---

# Historia: intento 1 cerrado; fase previa corregida

7-11-2026, rama piloto/intento-1, base 5850899. Causa reproducida:
state/worker.lock no estaba excluido de Git; _start lo encontraba despues de
tomar el candado. Docker y ambas imagenes responden correctamente bajo el
entorno reducido, mediante consultas locales de lectura autorizadas.

Se excluye solo ese candado; check y _start comparten las comprobaciones de
configuracion/autorizacion/Git/revision/Docker/candidato. PowerShell usa el
mismo constructor de entorno reducido para check y run. Fallos concretos de
lista cerrada, sin texto libre ni reintentos. Un OK no garantiza estados futuros:
las comprobaciones se repiten antes de la llamada y bajo el candado.

Suites: raiz 233 + privada 113 + JS 7 + TS 3 = 356 pasadas, cero fallos,
errores u omitidas. TS sin comprobacion estatica de tipos. Sin proveedor real,
red ni contenedores. Ver evidencia, comandos y limites en
[pr/intento-1-preflight.md](pr/intento-1-preflight.md).

El registro real no se modifica: SHA-256 intacto, 0 llamadas, 0 intentos
pagados. bottles-1 conserva BLOCKED/PILOT_PREFLIGHT_BLOCKED_NO_RETRY.
El siguiente sera attempt 2, con nuevo expediente/autorizacion y revision de
Claude; no se prepara ni ejecuta aqui. El lanzador del intento 1 no se reutiliza.
Config.json y sus interruptores intactos; no se pide clave, firma, importa
revision ni publica. Envio DISABLED. upstream/ y fabrica original intactos.

---

# Historia: correccion de pruebas tras def4b58, sin ejecutar

7-11-2026, rama piloto/intento-1. Se corrigen seis pruebas para usar una copia
temporal de config.json con external_calls_enabled=false. Se conservan todas
las aserciones anteriores. Una nueva prueba comprueba la configuracion real:
external_calls_enabled=true; enabled, erp_access_enabled y publication_enabled=false.
No se cambia config.json ni codigo de produccion en esta correccion.

Suites completas: raiz 220, privada 113, JavaScript 7 y TypeScript 3:
343 pasadas, 0 fallos, 0 errores, 0 omitidas. Python se ejecuto con el auxiliar
externo ejecutar-suite-sin-red.py, que bloquea conexiones y procesos externos
reales y elimina credenciales heredadas del entorno. Comandos y logs en
docs/pr/intento-1.md. TS ejecuta pruebas sin comprobacion estatica de tipos.

El registro permanente ya existe: 1 declaracion de Fernando (6-11-2026),
0 llamadas, 0 intentos pagados, 0 ejecuciones pagadas y 0 revisiones importadas.
No se reinicializa. PowerShell 7.6.9 ya estaba instalado: Codex solo consulto
pwsh --version; no instalo nada. Revision del nuevo SHA y autorizacion concreta
siguen pendientes. Sin red, proveedor real, Docker real, clave, ejecucion del
ensayo ni publicacion. El envio sigue DISABLED. Los auxiliares de entregas-locales
estan fuera del commit y requieren revision separada antes de usarlos.

---

# Historia: intento 1 con gpt-6.1-sol antes del paso 3

Cambio autorizado el 6-11-2026 sobre 8f69fe9, misma rama piloto/intento-1.
Compatibilidad documental confirmada para Responses, json_schema strict,
tools=[] y tool_choice=none, medium, store=false y 32000 tokens.
Precios estandar 2.00/10.00 USD por millon. service_tier=default y cache en
modo explicit sin puntos de cache para evitar cargos de escritura.

Calculo local: 4723 bytes, peor coste 0.329446 USD; al limite completo de
100000 bytes, 0.520000 USD. No es coste medido. Todos los interruptores false,
intento 1 no consumido, clave no leida, ninguna llamada a proveedores ni push.
Las huellas anteriores se invalidan al cambiar modelo y configuracion.
Suites completas tras el cambio: raiz 219, privada 113, JS 7, TS 3. Total 342
pasadas, sin fallos/errores ni omitidas. TS no comprueba tipos.
Sigue pendiente el registro acumulado permanente y la revision del SHA final.
Fuentes y resultados: [pr/intento-1.md](pr/intento-1.md).

---

# Historia: preparacion anterior con gpt-5.3-codex

# Estado vigente: intento 1 preparado, sin ejecutar

Rama piloto/intento-1 desde 5dc2a61fb8794439fa706f535e1d8e7e5ef96199.
Documentacion oficial consultada en lectura el 6-11-2026: gpt-5.3-codex,
Responses, json_schema strict, tools vacio/none, medium, store=false y 32000
compatibles documentalmente. Tarifa estandar 1.75/14.00 USD por millon;
service_tier=default explicito. Modelo con retirada prevista 1-4-2027.

Configuracion preparada: importes 1/12/13 USD, modelo y precios definidos.
Los cuatro interruptores siguen false. Clave NO leida. No se llamo a proveedores.
Script scripts/ensayo-intento-1.ps1, modo por defecto Preparar, sin consumir
attempt=1. Peticion de 4682 bytes; peor caso 0.456194 USD; limite completo
100000 bytes + 32000 tokens: 0.623000 USD. No es gasto medido ni factura.

No existe state/factory2.sqlite3 en este clon. No se inicializo ni se presume
saldo cero: pendiente confirmar el registro permanente/reconciliado antes de
cualquier ejecucion. Detalle, fuentes y limites: [pr/intento-1.md](pr/intento-1.md).
Suites completas: raiz 219, privada 113, JS 7, TS 3: 342 pasadas, cero
fallos/errores y cero omitidas. TS sin comprobacion de tipos. Parser PowerShell
sin errores y modo Preparar ejecutado sin claves ni consumo del intento.

---

# Historia: bloque 10 y correccion

# Estado vigente: bloque 10 preparado, no ejecutado

Rama feat/bloque-10-piloto desde main verificado c55453edd9f04c7274a5fabfddc54c21eda53b30,
mediante el unico fetch autorizado. Fernando eligio modelo Codex por API; no CLI
dentro de Docker. La peticion futura sale solo del host, con una reserva previa,
sin herramientas/reintentos/redirecciones. El codigo se materializa y prueba en
Docker sin red; despues se detiene para revision manual y aceptaciones.

external_calls_enabled permanece false y es el unico interruptor previsto para
el ensayo. enabled, erp_access_enabled y publication_enabled tambien siguen false.
Importes por llamada/ejecucion/acumulado: null. Propuesta pendiente USD 1.00/12.00/13.00.
Modelo y revision de coste: null. La reserva de una llamada (como maximo USD 1.00)
no se presenta como garantia de la factura API; exige verificacion antes de autorizar.

El registro durable bottles-N y el candado evitan repetir un intento. Cada numero
nuevo exige autorizacion nueva; todos comparten el tope acumulado de USD 13.
Fallos/resultado incierto bloquean sin reintento ni devolucion de reserva. La
revision usa SHA del candidato y huellas, con business y accounting; nunca publica
ni autentica personas. Apagar el interruptor despues de las pruebas permite
completar solo la revision/aceptaciones pendientes, sin nuevas llamadas.

Solo pruebas con dobles explicitos: ningun proveedor, Docker, credencial real,
descarga o publicacion. Contrato API/modelo/coste e integracion nueva NO VERIFICADOS.
Suites historicas de 0d51883: raiz 199, privada 113, JavaScript 7, TypeScript 3; total 322,
sin fallos/errores ni omitidas. TypeScript no comprueba tipos. Resultados,
comandos y permisos pendientes: [pr/bloque-10.md](pr/bloque-10.md).

Correccion local posterior a la revision de Claude: max_output_tokens hasta
32000, esfuerzo configurable, peor coste calculado con bytes/precios declarados,
registro numerico de uso/coste y autorizaciones por numero. Las tarifas siguen
sin verificar; no se activan importes ni modelo. Resultados de la correccion:
raiz 211, privada 113, JavaScript 7 y TypeScript 3: 334 pasadas, cero fallos/errores
y cero omitidas. TypeScript sin comprobacion de tipos. Los costes calculados no
son facturas autenticadas. Sin red ni proveedores; config sin cambios.

---

# Historia: bloques 8 y 9 combinados localmente

El 6-11-2026 se trajo origin/main mediante el unico fetch autorizado:
54b5bda8170a886755c768b1e2b7bfba5ac5eae4 (merge del bloque 8). Se combina con
docs/bloque-9-docker en 6ce6af02b8c885c320761923c670615151204777, conservando
el Coordinator con retirada declarada y roster(task) con aprobaciones por niveles.
Fernando comunica que Claude reviso 6ce6af0 sin objeciones tecnicas; esto no
equivale a una revision del nuevo SHA combinado ni a una aprobacion autenticada.
Unico conflicto textual: este documento; se conservan ambos bloques e historia.
La prueba de retirada ahora declara destino factory para comprobar especificamente
la falta de aceptaciones bajo la nueva politica, sin relajar el bloqueo.

Fernando arranco el motor y declaro cumplir los
limites de licencia gratuita. Descargas autorizadas: Python 3.13 slim y Node 24
slim, fijadas por digest en DOCKER.md. Sin mas red ni proveedores.

DockerRunner real, sin modificarlo: 13 pruebas Python, 7 JavaScript y 3 de
aislamiento pasaron. Codigo montado de solo lectura, UID/GID 65534, sin privilegios,
sin red del contenedor ni pulls durante el ensayo; huellas del host intactas.
No se instalo/configuro/actualizo Docker; no se apago el motor de Fernando.

Politica local: ERP-FACTORY requiere Fernando (1); productos con impacto contable
requieren Fernando y FERRUMTJA (2). Destino no clasificado o nivel no decidido:
BLOCKED. La clasificacion forma parte del expediente versionado; cambiarla invalida
aceptaciones. No autentica personas. Revision, caducidad y controles restantes
siguen vigentes; config.json mantiene sus cuatro interruptores false.
No se cambiaron reglas de GitHub: la plantilla de dos aprobaciones es anterior
y no debe confundirse con esta politica local. Guia vigente en GUIA-APROBAR.md.

Suites completas del arbol combinado: raiz 178, privada 113, JS 7 y TS 3;
301 pruebas en total, 0 fallos/errores, 0 omitidas. Todas con salida 0.
Las anteriores fueron raiz 161, privada 113, JS 7 y TS 3 sin fallos/omitidas.
Se conserva la evidencia anterior de 23 pruebas Docker: runner.py y el auxiliar
no cambian y no se repite Docker por instruccion de Fernando.
Comandos y limites: [pr/bloque-9.md](pr/bloque-9.md).
Sin revision Claude de este SHA ni activacion/publicacion. Riesgo aceptado de no
tener revisor tecnico humano y auditoria externa previa a datos reales/ERP vigentes.

---

# Historia: bloque 9, inventario Docker (solo documentacion local)

Rama docs/bloque-9-docker desde la referencia local origin/main
877dd757f83f5fece05e2216ddfdea36843f0c4a; sin fetch en esta fase sin red.
Docker Desktop 4.98.0.245422 y cliente 29.9.2 instalados. WSL 3.0.3.0:
Ubuntu-24.04 (predeterminada) y docker-desktop, ambas WSL 2 y detenidas.
El motor Linux no responde en su tuberia local. No se arranco ningun componente.
Inventario, limites y plan para Fernando: [DOCKER.md](DOCKER.md).
Solo revision documental contra el runner y las pruebas; no suites ni contenedores
ejecutados. Licencia actual, compatibilidad e integracion Docker NO VERIFICADAS.
No hay instalacion, configuracion, activacion, descarga ni publicacion.

---

# Bloque 8: retirada declarada incorporada desde main

Procedencia historica: rama `fix/bloque-8-retirada-registrada`, desde origin/main
`877dd757f83f5fece05e2216ddfdea36843f0c4a`, obtenido mediante el unico fetch autorizado.
`docs/retirada-original.json` registra la declaracion de Fernando del 5-11-2026:
VM eliminada, App 5603415 eliminada con clave e instalacion, inventario acotado
de Windows sin tareas/servicios propios y pausa conservada, OpenAI NO_EXISTIA,
archivo NO_POR_DECISION_DE_FERNANDO. No contiene firmas ni autentica personas.

El Coordinator sustituye ORIGINAL_COORDINATION_NOT_VERIFIED por la validacion
del registro. Ausente, incompleto, contradictorio, invalido o restauracion declarada
bloquean. Se relee antes de recover y de reservar llamadas, manteniendo el candado.
Los cuatro interruptores de config.json siguen en false. Revision, aceptaciones,
presupuesto y permisos no cambian. No hay activacion, publicacion ni proveedores.
La revision automatica privada permanece aparcada y con sus tres bloqueos.

Suites historicas del bloque 8: raiz 166, privada 113, JS 7 y TS 3; 289 pruebas en total,
0 fallos/errores y 0 omitidas. Comandos y limitaciones: [bloque-8.md](pr/bloque-8.md).
No se vuelven a verificar remotamente las declaraciones, ni se detecta una
restauracion no comunicada. No se ha recibido revision de Claude de este cambio.

---

# Historia: preparacion de PR unica de bloques 1 a 7

## Retirada original comunicada por Fernando: 5-11-2026

Fernando declara la retirada completada: rdc con 0 PR abiertas y 25 cerradas,
archivado y con reglas sin cambios. VM RDC-Piloto-Aislado exportada a OVA sin
errores y despues eliminada de VirtualBox por decision suya. **Retirada SIN ARCHIVO**:
Fernando no conserva ese respaldo como archivo oficial, por decision expresa.
No se crea otro archivo ni se promete restauracion; no se verifica borrado de discos
u otras copias ni se afirma que el OVA se haya borrado fisicamente.
GitHub App **RDC Factory Fernando**, **App ID 5603415**, eliminada con su clave y
su instalacion en rdc, segun Fernando. OpenAI: **no existia** clave de la fabrica
original, confirmado expresamente por Fernando; no corresponde revocacion. No
se consulto el proveedor ni se realizo una auditoria remota para esta anotacion.
Windows: el inventario previo de Codex no identifico tareas ni servicios propios
de la fabrica; su alcance era limitado. pilot.pause se conserva segun Fernando.
No se volvieron a consultar VM, Windows, Ubuntu, rdc, GitHub o proveedores aqui.

Registro y explicacion vigente en docs/RETIRADA-ORIGINAL.md. El plan anterior
queda como historia en el anexo tecnico y Git; sus exigencias de archivo no siguen
vigentes. En esta etapa historica solo se documento la propuesta, sin cambiar
ORIGINAL_COORDINATION_NOT_VERIFIED; el bloque 8 descrito arriba la implementa.

Decision expresa de Fernando: publicacion/bloques-1-7 nace de origin/main
930528e2aad40aace0903311fc997c3d34024bd6 y contiene la fuente completa
0ff127fd2a6fc65ec5d9064087c91b3bfcda6b91, incluido b0da873 del bloque 1.
La combinacion local no tuvo conflictos. El aviso docs/PRUEBA-PROTECCION.md se
elimina en esta misma propuesta. No se integra una retirada separada.
ERP-FACTORY-revision/ se incluye sin cambios, aparcado y con los tres bloqueos.
No se activa ninguna fabrica, workflow ni proveedor. upstream/ queda intacto.

Se ejecutan las suites completas raiz, privada, JS y TS; el resultado real y
SHA final se entregan junto con los logs locales fuera del repositorio. No usar
los resultados historicos de abajo como si fueran la prueba del nuevo candidato.
No se afirma revision de Claude del SHA combinado hasta recibirla. Cuenta maquina
nunca aprueba ni integra; nadie integra sin decision expresa de Fernando tras
la revision de Claude. No se abre, aprueba ni integra PR desde Codex.

La publicacion de esta rama requiere la aprobacion puntual de red; envio a
DISABLED despues del intento. Plan vigente en docs/PUBLICACION.md. Lo que sigue
es historia; la prohibicion anterior de incluir la carpeta privada fue sustituida
por la nueva decision para esta PR unica, sin autorizar secretos ni ejecuciones.

---

# Estado actual: bloque 7, cuenta Codex y publicacion pendiente

Rama actual fix/bloque-7-cuenta-codex; actualizacion documental desde 893df54.
La implementacion del bloque 6 procede de 31abe68.
Claude revisa cada PR (solo cambios) en el chat y, antes de hitos importantes,
toda la fabrica en una conversacion nueva. Registro en docs/revisiones/:
Claude, chat, no autenticado. No es aprobacion humana ni prueba de cobertura real.
No se ha recibido ni fabricado una revision de Claude de este bloque.

Personas declaradas (no autenticadas en esta tarea):
- business: fernandoruizm-maker, ID 342326625; aprobacion de negocio.
- accounting: FERRUMTJA, ID 352290329; contador con experiencia en ERP,
  aprobacion contable y funcional. El rol technical antiguo se rechaza.

**Riesgo aceptado expresamente por Fernando:** ninguna de esas personas programa
ni hay una persona revisora tecnica. Claude no sustituye ese control humano.
**Auditoria tecnica externa obligatoria antes de usar datos reales de clientes
o conectar el ERP.** No se contrata ni realiza esa auditoria aqui.

Via manual alternativa con SHA exacto, conclusion SIN OBJECIONES TÉCNICAS y
aceptaciones vigentes vinculadas a revision/version/huella. Incluso lista para
revision, provenance_authenticated=false y publication_allowed=false. La via V2
mantiene su validacion y sus bloqueos de autenticacion; no se sustituye por un PASS manual.
Los informes reales *.local.md se excluyen de commits para no cambiar el SHA revisado.

Actions APARCADO: if false, execution_enabled=false y pin cero intactos. Sin
repositorio privado por ahora. Registrados para futura reactivacion: USD, 1.00 por
llamada, 12.00 por ejecucion, 13.00 acumulado, 11 llamadas, opcion 1 manual. No es
permiso de gasto; el adaptador sigue sin conectar. Configuracion local desactivada.

Avances comunicados por Fernando el 2026-11-05 (Codex no los verifico por red):

- Cuenta **fernandocodex64-sudo**, con dos pasos; invitacion de colaboradora aceptada.
- Ruleset activo **main - dos aprobaciones sin excepciones**, ID **26650549**.
  Segun Fernando, Claude verifico en lectura por API publica PR obligatoria,
  dos aprobaciones, invalidacion de antiguas, aprobacion del ultimo cambio por
  otra persona, conversaciones resueltas, prohibicion de borrar y force push.
- Bypass no visible sin credenciales: Fernando lo comprueba en pantalla; no se
  registra aun confirmacion de que este vacio. Prueba funcional de PR pendiente.
- Token NO creado. Decision: clasico con solo public_repo y 30 dias. Sustituye
  el de grano fino, incompatible en este caso segun la comprobacion de Claude
  comunicada por Fernando. No se consulto documentacion externa en esta tarea.
- public_repo no limita el token a un repositorio seleccionado: la escritura en
  repositorios ajenos se acota por las colaboraciones actuales de la cuenta (solo
  ERP-FACTORY segun Fernando). Nuevos accesos o repositorios propios publicos
  ampliarian el alcance. Main protegida no restringe todas las acciones del token.

Orden pendiente: token -> configuracion local por Codex autorizada y verificada
por Claude -> PR ficticia autorizada, cerrar sin integrar -> bloque 1 con permiso
expreso. Cada subida sigue necesitando autorizacion expresa hasta completar la
verificacion funcional de proteccion, incluido bypass. Envio DISABLED sin cambios.
Configuracion local ya aplicada por autorizacion posterior: usuario
fernandocodex64-sudo (ID 353061596), nombre visible fenando-codex; correo
353061596+fernandocodex64-sudo@users.noreply.github.com. Usuario/ID y colaboracion
verificados por Claude segun Fernando, no por red en esta tarea de Codex.
Ver CONFIG-LOCAL-CODEX.md para opciones antes/despues y limites.
Siguen pendientes las dependencias de publicacion selectiva sin carpeta privada.
No hubo red, acceso a credenciales, cambios de remotos, publicacion ni activacion.
Se modificaron solo las opciones locales de Git expresamente autorizadas.
Verificacion documental local: lectura, enlaces relativos y git diff --check.
No se repiten suites por cambios solo documentales. Los resultados siguientes
son historicos del bloque 6, no una nueva ejecucion:
Suites completas: 149 raiz + 113 privadas + 7 JS + 3 TS = 272, cero fallos,
errores u omitidas. TS sin typecheck. Comandos y limites en docs/pr/bloque-6.md.

## Aplicacion local y via web (ultima actualizacion del bloque 7)

Usuario correcto fernandocodex64-sudo, ID 353061596; fenando-codex es su nombre
visible. Se corrige la confusion anterior en estas guias. Fernando informa de la
verificacion por Claude en API publica y lista de colaboradores (Collaborator).
Se completaron los ajustes autorizados de pasos 1 a 10 sin red ni token: identidad,
helper local con reinicio de herencia y manager, useHttpPath=true, wincred, pat,
y usuario asociado a la URL exacta del repositorio. Antes no existian esos valores
locales; despues coinciden con lo autorizado. Envio DISABLED antes y despues.
SHA-256 del archivo global identificado por Git e identidad global sin cambios.
No se leyeron ni modificaron credenciales. GCM 2.9.1 observado anteriormente; su
ayuda local fallo por restriccion Windows 0xC0000022, sin reintentar ni eludirla.
La comprobacion de valores Git paso, pero uso real del gestor NO VERIFICADO.
gh no localizado en PATH previamente; sin instalarlo ni usarlo. Fernando abrira
las PR de prueba y bloque 1 en la web como fernandocodex64-sudo. Codex solo prepara
textos y subira ramas con autorizacion posterior. Claude aun debe revisar los
ajustes. Enlaces y git diff --check verificados; no se ejecutan suites por cambios
documentales y de configuracion Git local. No hay conexion, subida o activacion.

## Registro historico de bloques anteriores (no es el modelo vigente)

# Estado actual: bloque 5 multiparte preparado localmente y bloqueado

Rama fix/bloque-5-multiparte desde 8ffb8115843fcb0f05b8c6a7c28adc0ce87c3934.
Pasos privados secuenciales, checkpoints inmutables antes/despues de cada llamada,
topes y sin reintentos. 0cb1882: 10 partes + cross, 11 llamadas ficticias probadas.
Suites completas: 131 raiz + 113 privadas + 7 JS + 3 TS = 254, cero fallos,
errores u omitidas. TS sin typecheck. Comandos y limites en docs/pr/bloque-5.md.
Tres bloqueos intactos: if false, execution_enabled=false y pin cero. Importes null.
Opciones de acumulado documentadas, ninguna elegida. Solo reserva/importacion local
comun; falta adaptador al ledger real. No se opero GitHub ni Claude; no se publicaron
archivos ni se toco la fabrica original. recover() real sigue sin coordinacion.
No hay otro ZIP. Ejecucion real de Actions/eventos/coste/duracion NO VERIFICADOS.

## Registro del bloque 4 (historico)

Correccion posterior desde 992fcb1: literales SQL con comillas simples y prueba
SQLite estricta (DQS_DML/DQS_DDL desactivados). Suites completas: 130 raiz,
87 privadas, 7 JS y 3 TS; 227 aprobadas, cero fallos, errores u omitidas.
Pendientes del bloque 5: almacenamiento/aplicacion del presupuesto acumulado en
GitHub y coordinacion real con la fabrica original antes de poder usar recover().
No se inicia el bloque 5. El ZIP de 992fcb1 no incluye esta correccion.
SHA y detalle de entrega en docs/pr/bloque-4.md y acta local referenciada alli.

### Registro de la entrega anterior

Las dos mitades estan implementadas y probadas en fix/bloque-4-operacion. Base
ad91cb3; primera mitad 84c5fe8. Suites finales: 129 raiz + 87 privadas + 7 JS +
3 TS = 226, cero fallos, errores u omitidas. El primer ensayo de la segunda
mitad tuvo 2 fallos de orden de perfiles, corregidos antes de repetir las suites.
Ver comandos, evidencia y limites en docs/pr/bloque-4.md.

Existe el archivo de workflow publico historico, que se conserva hasta la
migracion autorizada. No se consulto su estado actual en GitHub. El diseno privado
esta bloqueado y su workflow multiparte real sigue pendiente. .disabled es OBSOLETO.
Las entradas anteriores de instalacion y llamadas remotas quedan abajo como
historia; no describen el estado actual ni autorizan nuevas conexiones.

Orquestador solo con dobles ficticios, Codex con entorno limitado y sin runner
real, ledger persistente local de reservas y piloto con restauracion coherente.
Se registran 11 llamadas por ejecucion y moneda USD, elegida por Fernando.
Gasto por ejecucion y acumulado siguen null y bloquean. No hay gasto real medido.
Verificacion posterior de configuracion: USD/11/null/null e interruptores false;
limits(config) bloquea con BUDGET_AMOUNT_REQUIRED (Python local, salida 0).
Las 226 pruebas corresponden a d3d7319; no se repitieron para este ajuste de moneda.
Autenticacion, procedencia GitHub y coordinacion con la original siguen pendientes;
gate permanece BLOCKED. Sin red, proveedores, ERP, publicacion ni activacion.

## Registro historico (no sustituye el estado actual anterior)

# Estado de la segunda fábrica · 5 de noviembre de 2026

## Actualizacion: conexion mediante Actions preparada

Nota posterior: en el clon ERP-FACTORY-correcciones se trabaja sobre la base
0cb1882, exclusivamente en ramas locales y con push deshabilitado. Bloque 1:
diagnostico tipado, SHA-256 y PARTIAL sin aprobacion; 60 pruebas Python, 5 JS
y 3 TS correctas, sin omitidas. GitHub y proveedores reales no verificados.
Ver docs/pr/bloque-1.md. Las entradas historicas siguientes no describen una
activacion actual ni autorizan conexiones. Factoria original y factoria-2 intactas.

Fernando confirma que guardo `CLAUDE_CODE_OAUTH_TOKEN` en GitHub. Su valor no se
leyo. Se preparo un workflow manual con referencias fijas, autorizacion por SHA,
revision estatica sin herramientas y validador de cobertura/informe. Las 42
pruebas Python actuales pasan, incluidas siete nuevas de la integracion.
No se ejecuto Claude ni se probo aun la autenticacion real. Ver
[pasos y limites](ACTIVAR-CLAUDE.md). La consulta a GitHub muestra `main` del
repositorio nuevo sin proteccion; no se modifico. La doble aprobacion operativa
en ese repositorio todavia no esta acreditada. El estado anterior se conserva
abajo como registro de la entrega inicial; el secreto ya no esta pendiente
segun la confirmacion de Fernando.

## Entrega

Instalación local en `C:\Users\ferna\Documents\Codex\2026-11-05\task\factoria-2`.
No es un servicio Ubuntu instalado o habilitado. No existe consumidor nuevo de GitHub ni despliegue.

Referencia de origen: ZIP SHA-256 `9924878c35d6ffa23e15ef2d619d6ece1b8bed936f966b5a69eaa5cc65b53ba2`, previamente cotejado 53/53 con Ubuntu. Solo se extrajo `codigo/` a `upstream/`; no se copiaron configuración operativa, estado histórico o credenciales. La fábrica original, pausa Windows, doble aprobación y protecciones GitHub no se modificaron.

## Verificación ejecutada

- 35 pruebas Python de la nueva implementación: PASS, cero fallos, errores u omisiones. Registro: `outputs/test-factory.txt`.
- Piloto: 7 pruebas de dominio Python, incluidas en las 35 anteriores; 5 JavaScript y 3 TypeScript adicionales: PASS. Total de casos distintos ejecutados: 43.
- Piloto: stock inicial 10, final 0, un movimiento; repetir devuelve el mismo comprobante. Reapertura del estado ficticio conserva saldo e identidad de salida. Impresión no altera estado.
- Controles ensayados: otra área, autoaprobación, falta de aprobación, cantidades inválidas, saldo insuficiente, duplicados, rutas fuera de alcance, catálogo sin autorización o huella válida, presupuesto concurrente, permiso vencido o de otro contenido, ausencia de credencial, respuesta truncada, timeout incierto, revisión de otra versión, aceptación desactualizada, falta de revisión de la fábrica y revisión parcial.
- Las pruebas de proveedores usan dobles simulados y una cadena ficticia de prueba. No acreditan integración real con Anthropic o Codex CLI.
- Estado local observado: desactivado; 0 tareas, 0 llamadas, 0 llamadas inciertas. Sin conexiones externas.
- Runtime usado: Python proporcionado por Codex, Node v24.22.1. TypeScript ejecutado con `--experimental-strip-types`, sin comprobación estática de tipos.

## Incidencias resueltas durante las pruebas

El aislamiento del ejecutor denegó escrituras en sus temporales. Se solicitó y obtuvo ejecución autorizada de las pruebas, sin cambiar permisos o desactivar permanentemente el aislamiento. No se intentó limpiar manualmente las rutas denegadas.

La ejecución autorizada reveló conexiones SQLite que no se cerraban explícitamente, causando WinError 32 al retirar temporales. Se corrigió el gestor de conexiones para confirmar/revertir y cerrar en todos los casos. Las pruebas completas posteriores pasan. El primer ensayo del piloto, antes de crear su módulo, falló por módulo ausente; no se presenta como prueba de detección de un defecto de negocio.

## Pendientes y límites

1. Claude NO ha revisado todavía ni el producto ni la fábrica. Los paquetes locales de `outputs/revision-claude/` están preparados para revisión, con estado NOT_RUN, y no se transmitieron.
2. Fernando eligió GitHub Actions, el repositorio `fernandoruizm-maker/ERP-FACTORY` y su suscripción de Claude si es compatible. Se comprobó que el repositorio existe y es público. Fernando autorizó mantenerlo público y publicar el código. Pendientes: plan de Claude, credencial OAuth, modelo, contenido autorizado para Anthropic y presupuesto. Hay un borrador desactivado en docs/actions; no hay workflow instalado, App nueva, secreto generado ni integración activada.
3. No se accedió al ERP. La comparación real permanece pendiente; se comprobó solo el comparador con evidencia ficticia.
4. No se ejecutó el adaptador Docker ni se descargaron imágenes. Se probaron sus restricciones de comando; falta validarlas en un motor e imagen aprobados. No ejecutar propuestas de modelos en el host.
5. No se ejecutaron los tests del código `upstream` ni se certificó la fábrica heredada completa. Se preserva como referencia verificada y se incluye en los paquetes de revisión.
6. Los registros de aceptaciones locales no autentican a personas; falta vincular identidades y evidencia del proveedor en un entorno operativo. Ninguna puerta de esta entrega concede permiso de publicar.
7. El comprobante HTML se generó y su contenido se comprobó mediante pruebas; no se hizo revisión visual de paginación ni prueba de impresora.
8. Límites por llamadas, tamaño y tiempo no equivalen a un límite monetario contractual. No se midió consumo de proveedores porque no hubo llamadas.
9. La restauración completa en otra máquina y el cambio de fábrica activa requieren una etapa posterior autorizada. Nunca activar las dos fábricas a la vez.

## Continuidad

La implementación local y sus pruebas están entregadas. La conexión elegida es GitHub Actions, empezando por una revisión de la propia fábrica en ERP-FACTORY mediante suscripción Claude. La publicación pública está autorizada; falta completar autenticación. No se necesita tocar el ERP para esa revisión. Cualquier autorización futura debe delimitar los archivos enviados, proveedor/modelo, costo y destino; los paquetes permiten revisar el alcance antes de transmitir.
## Actualizacion: cuarto intento y correccion de entrega del informe

OAuth ya funciono en el run 41995251713. Claude proceso la solicitud pero termino
por limite de turnos, sin informe aceptable. No existe aun revision completa
acreditada. Registro: 3 turnos frente a 2 configurados, una denegacion y costo
estimado USD 1.039741. No se afirma que ese importe fuera facturado.

Se preparo una correccion que recibe JSON textual y conserva todas las
herramientas denegadas. Las 12 pruebas locales del modulo Actions pasan.
No se ejecuto un quinto intento. Ver [evidencia y limites](CORRECCION-INFORME.md).
Las entradas anteriores son historicas y no sustituyen esta actualizacion.

## Actualizacion: quinto intento autorizado

Se integro PR #4 y termino el run 41996918613: Claude completo la llamada en un
turno, sin denegaciones, con USD 1.0870979 estimados. El validador rechazo el
resultado, por lo que no hay informe de revision aceptado. El diagnostico
generico no permite conocer la regla exacta que fallo.

Se preparo una correccion local del diagnostico, sin relajar la validacion.
Las 14 pruebas del modulo Actions pasan; no se hizo un sexto intento.
Ver [evidencia, integridad del artefacto y limites](QUINTO-INTENTO.md).



## Bloque 2: borrador privado local, sin ejecucion remota

Carpeta nueva ERP-FACTORY-revision/, en rama local independiente desde 0cb1882.
Un trabajo confiable privado; candidato publico leido como tar/JSON sin ejecutar.
Workflow bloqueado, politica desactivada y pin privado revisado pendiente.
23 pruebas privadas + 49 Python de base + 5 JS + 3 TS aprobadas (80, sin fallos ni
omitidas). Ver comandos y limites en docs/pr/bloque-2.md. No verificados Actions,
visibilidad de artefactos, minutos consumidos, proveedores o identidades. No se
creo repositorio, no se movieron secretos, no se publico ni se activo la fabrica.

### Ajuste adicional del bloque 2

Los fallos tempranos de archivo de ejecucion o verificacion del material producen
ahora artefactos BLOCKED con codigos fijos y huellas, sin texto del proveedor.
Resultado final: 31 pruebas privadas + 49 Python de base + 5 JS + 3 TS = 88,
sin fallos ni omitidas. El primer ensayo del cambio detecto una concatenacion
incorrecta, corregida y comprobada al repetir la suite privada completa.
Publicacion futura: exportar solo ERP-FACTORY-revision/ al repositorio PRIVADO;
no fusionar esta rama en ERP-FACTORY. Bloque 3 partira de la rama 2 actualizada.
El retiro del validador/workflow publico y secreto se reserva para la migracion
autorizada al revisor privado. Ver orden y reconciliacion documental en la PR local.

### Conservacion restringida autorizada por Fernando

Respuestas no validadas solo para los codigos de formato/version/evidencia
autorizados, tras comprobar evento exitoso, tamaño y SECRET_PATTERN del original.
Se guardan exactamente en response.unvalidated.txt privado con huella; el informe
sigue BLOCKED y no incluye el texto. Sin revalidacion ni reintento automaticos.
57 pruebas privadas + 49 Python de base + 5 JS + 3 TS = 114 aprobadas, sin fallos
ni omitidas. La futura base local del bloque 3 debe contener tambien el bloque 1
y pasar sus suites completas antes de añadir funcionalidad de revision por partes.

### Base combinada verificada para iniciar el bloque 3

Bloque 1: b0da873b1dc3ff37bbafdf93eb6b8027d911885e.
Bloque 2 completo: f28844123d62cf0a491875c713cdc3fc8fce3d05, incluido a8cfa18.
Integracion solo local en fix/bloque-3-cobertura, conservando ambos registros de
estado. Sin cambios nuevos de codigo: suites completas 57 privadas + 60 raiz +
5 JS + 3 TS = 125 aprobadas, sin fallos, errores u omitidas. No hubo red,
proveedores, publicacion o activacion. La implementacion del bloque 3 sigue pendiente.


## Bloque 3: protocolo privado local por partes

Base combinada: fa650d7322e136093e445b6801b90bd37d93fd4c, con bloque 1 y bloque 2
completo. Inventario Git exacto y clasificacion expresa; lineas numeradas, huellas
por parte y pasada final ligada a todos los resultados. Contrato privado unico
y cobertura calculada desde rangos/partes validados, sin aprobacion ni publicacion.
La secuencia se prueba con dobles ficticios; prepare bloquea la antigua llamada
monolitica. El workflow y la politica siguen desactivados.

Resultado final: 86 privadas + 60 raiz + 5 JS + 3 TS = 154 pruebas, cero fallos,
errores u omitidas. El primer ensayo privado tuvo un error de sintaxis en una
prueba, corregido antes de repetir la suite completa. Ver comandos, incidencia
y limites en docs/pr/bloque-3.md. Las entradas anteriores son historicas.
No verificados integracion real, GitHub, privacidad/retencion de artefactos,
minutos, Docker, identidades ni ERP. No se ejecuto upstream/. Sin red, secretos,
proveedores, publicacion o activacion; original y factoria-2 intactas.


### Aclaracion adicional del bloque 3

Se documentan los tres contratos de factory2/ obsoletos para el revisor privado.
Se agrega la prueba de pasada final con source_sha o factory_digest de otra
version. Suites completas: 87 privadas + 60 raiz + 5 JS + 3 TS = 155, sin
fallos, errores u omitidas. NO VERIFICADO: campos error/errors en cualquier
evento frente a eventos reales de Claude Code; solo se usaron eventos ficticios.
Sin cambios de codigo operativo, red, publicacion ni activacion.


### Calculo documental previo al bloque 4

Con el codigo 49aadc8, el SHA original 0cb1882548fc141f4b764e82ff2e5154cfae2762
genera 10 partes para sus 91 archivos: una revision completa supondria 11 llamadas
(10 partes + 1 interacciones), condicionada a validacion y limite del mensaje final.
Cero llamadas reales, sin coste medido. La pasada final recibe resultados e
inventario, no codigo fuente. Queda obligatorio construir posteriormente el
workflow secuencial con guardado inmediato de cada parte validada, conservacion
ante fallos, topes autorizados de llamadas/gasto y sin reintentos automaticos.
No se construyo ahora. error/errors sigue NO VERIFICADO frente a eventos reales.
Solo documentacion y calculo local; suites no repetidas porque el codigo no cambia.
Se espera instruccion de Fernando antes del bloque 4. Ver docs/pr/bloque-3.md.


## Bloque 4, primera mitad: puntos 1-4

Rama fix/bloque-4-operacion rehecha desde ad91cb39609e589df72c8e0b01fc68c694fb4c83.
Aceptaciones normalizadas con version/run/caducidad, sin sustitucion silenciosa;
importador V2 privado con integridad y autenticacion pendiente; candado local
y marcador ficticio; comparacion solo mediante permiso acotado y datos ficticios.
Gate permanece BLOCKED por autenticacion pendiente aun con fixtures completos.
La coordinacion real con la original no se simula como resuelta y esta bloqueada.
Fernando declaro las identidades negocio fernandoruizm-maker ID 342326625 y
tecnica FERRUMTJA ID 352290329; no se autentico ninguna. Tope declarado: 11
llamadas/ejecucion; ambos gastos siguen null. El registro monetario es del punto 7.
Pruebas completas: 93 raiz + 87 privadas + 5 JS + 3 TS = 188; cero fallos,
errores u omitidas. Sin red, credenciales, proveedores, publicacion o activacion.
Original, factoria-2, upstream/ y main intactos. Ver comandos, limites y hallazgos
parcialmente resueltos en docs/pr/bloque-4.md. Puntos 5-9 para la segunda mitad.

## Bloque 7: guia local para la cuenta de Codex

Base: 31abe689a20aff9ab886c0f0ff59248c7f2dc44f. Rama fix/bloque-7-cuenta-codex.
Solo documentacion: guia de cuenta separada, permisos minimos, caducidad propuesta
de 30 dias, configuracion futura por clon y revocacion. PUBLICACION.md establece
cuenta/token, proteccion de main, prueba ficticia autorizada sin integrar y despues
publicacion del bloque 1 con autorizacion expresa. Repositorio publico sin cambios.
Verificacion local: lectura de los documentos, enlaces relativos y git diff --check.
No se ejecutaron suites: no cambia codigo. NO VERIFICADOS: pantallas de GitHub,
compatibilidad del token de grano fino con un colaborador de otro propietario
personal, aislamiento efectivo del gestor de credenciales y proteccion de main.
La guia exige detenerse si no se puede cumplir el alcance exacto del token.
Sin red, cuentas nuevas, tokens, cambios de configuracion, credenciales o remotos.
No se rehabilito el envio DISABLED. Sin publicacion ni activacion; upstream/,
la fabrica original y factoria-2 intactos.
