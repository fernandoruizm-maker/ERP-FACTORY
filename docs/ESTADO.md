# Estado vigente: preparacion de PR unica de bloques 1 a 7

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
