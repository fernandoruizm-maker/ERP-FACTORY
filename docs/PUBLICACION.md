# Plan de publicacion — no ejecutado

ERP-FACTORY es publico. No subir datos reales de clientes, credenciales ni informacion
del ERP, ni siquiera a una rama, un informe, un comentario, una PR o un artefacto.
Revisar tambien el historial que se vaya a enviar. Borrar un dato del ultimo archivo
no lo borra de los commits anteriores. Ante una duda, detener la subida.

Decision vigente del bloque 7: usuario **fernandocodex64-sudo**, ID **353061596**;
**fenando-codex** es solo su nombre visible. Fernando comunica cuenta creada,
con dos pasos e invitacion
aceptada. Fernando y FERRUMTJA aprueban con sus propias cuentas. El repositorio
sigue siendo PUBLICO y propiedad de fernandoruizm-maker. El token NO esta creado.
Via intermedia: Fernando abrira la PR de prueba y la del bloque 1 desde la web,
con la sesion de fernandocodex64-sudo. Codex prepara titulo/texto y solo sube las ramas
cuando se autorice. Abrir PR con gh queda para una etapa posterior autorizada.

Fernando informa que el ruleset **main - dos aprobaciones sin excepciones**,
ID **26650549**, esta activo. Segun su informe, Claude comprobo por la API publica:
PR obligatoria, dos aprobaciones, invalidacion de aprobaciones antiguas, aprobacion
del ultimo cambio por otra persona, conversaciones resueltas y prohibicion de borrar
y force push. Bypass no visible sin credenciales: Fernando debe comprobar en pantalla
que la lista esta vacia. Codex registra lo comunicado, sin comprobacion de red propia.
La prueba funcional de la PR sigue pendiente; estos avances no autorizan envios.

## Permisos de Fernando

| Accion | Permiso aplicable |
|---|---|
| Trabajo local, pruebas ficticias y borradores | Dentro del alcance autorizado de cada tarea |
| Subir una rama antes de verificar la proteccion de main | Autorizacion expresa para cada subida |
| Subir ramas y abrir PR en ERP-FACTORY despues de que Claude verifique la proteccion | Permiso permanente condicionado a esa verificacion documentada |
| Integrar en main | Siempre autorizacion expresa; solo Fernando o FERRUMTJA realizan la integracion, nunca Codex |
| Crear repositorios; cambiar configuracion, permisos, protecciones o secretos | Siempre autorizacion expresa para la accion concreta |
| Activar workflows o gastar dinero | Siempre autorizacion expresa nueva; los limites registrados no son permiso para gastar |
| Cualquier accion sobre el ERP o la fabrica original | Siempre autorizacion expresa; antes de datos reales/conexion se exige auditoria tecnica externa |

**La condicion para el permiso permanente todavia NO se ha cumplido.** Esta tarea
no consulta ni configura GitHub. El permiso futuro no incluye integrar, auto-merge,
desactivar reglas, enviar informes sensibles o operar repositorios diferentes.
Si la proteccion cambia, deja de aplicarse o su estado es incierto, suspender el
uso de ese permiso y volver a comprobarla con Fernando. No usar una revision local
de JSON como sustituto de la verificacion real de Claude.

## Orden previo obligatorio: a, b, c y d

### a) Fernando crea el token clasico justo antes de la configuracion

- Cuenta e invitacion ya realizadas segun Fernando. Seguir
  [GUIA-CUENTA-CODEX.md](github/GUIA-CUENTA-CODEX.md) desde fernandocodex64-sudo:
  token CLASICO, solo public_repo, 30 dias; sin workflow ni otros permisos.
- Se sustituye el token de grano fino por la incompatibilidad que Fernando comunica
  verificada por Claude en documentacion oficial. Codex no la contrasto por red aqui.
- public_repo no tiene seleccion por repositorio: la escritura en repositorios
  ajenos depende de las colaboraciones de la cuenta, actualmente solo ERP-FACTORY
  segun Fernando. Otros accesos futuros ampliarian sus posibilidades. La proteccion
  de main limita esa rama, no convierte el token en uno de alcance por repositorio.
- Fernando introduce el token solo en la ventana segura de credenciales durante
  la prueba autorizada. Nunca lo muestra a Codex/Claude ni lo pega en otro sitio.
- Como deshacer: Fernando revoca el token clasico; no ampliar permisos ni sustituirlo
  por el token personal. Este paso no rehabilita el envio: sigue DISABLED.

### b) Configuracion local aplicada: pendiente de verificacion por Claude

- Seguir [CONFIG-LOCAL-CODEX.md](github/CONFIG-LOCAL-CODEX.md). Fernando no edita
  archivos ni ejecuta comandos. Codex configuro solo ERP-FACTORY-correcciones:
  nombre fernandocodex64-sudo, noreply proporcionado y opciones del gestor, sin
  tocar configuracion global. Autenticacion y almacenamiento real no verificados.
- La autorizacion actual cubre solo los pasos 1 a 10, sin red ni token. Correo:
  353061596+fernandocodex64-sudo@users.noreply.github.com. Identidad y opciones
  locales verificadas; huella del archivo global sin cambios. Envio DISABLED.
- Claude verifica en lectura los ajustes no secretos y su alcance. La configuracion
  no acredita aun una autenticacion remota. No se rehabilita el envio en este paso.
- La regla de main ya esta creada segun Fernando; no recrearla ni cambiarla. La
  [GUIA-PROTEGER-MAIN.md](github/GUIA-PROTEGER-MAIN.md) queda como referencia.
  Antes de la prueba, Fernando confirma en pantalla que bypass esta vacio. No dar
  acceso de excepcion a fernandocodex64-sudo ni rebajar aprobaciones para continuar.
- Como deshacer: con autorizacion, reponer solo las opciones locales cambiadas y
  retirar solo la credencial de maquina identificada, sin borrar las de Fernando.

### c) Prueba ficticia con autorizacion expresa

- Fernando autoriza concretamente rehabilitar el envio de ESTE clon solo hacia
  https://github.com/fernandoruizm-maker/ERP-FACTORY.git y subir una rama ficticia.
  Fernando abre la PR desde la web con la sesion de fernandocodex64-sudo y la cierra
  despues SIN integrarla; Codex prepara su titulo y texto para copiar y pegar.
  Esta documentacion no ejecuta ni concede por si sola esa autorizacion.
- Solo entonces Codex puede efectuar los cambios de envio autorizados, comprobar
  que no hay otro destino de push y subir la rama de prueba. Nunca incluir el token
  en una URL. La autenticacion se introduce por Fernando en el gestor seguro.
- Fernando comprueba la cuenta en el navegador antes de abrir la PR.
  La PR debe aparecer abierta por la cuenta de maquina. El nombre/correo de un
  commit no bastan para demostrarlo. Fernando y FERRUMTJA usan sus cuentas personales.
- Claude verifica en lectura repositorio, regla efectiva y estados de la PR:
  sin aprobaciones bloqueada, con una aun bloqueada, conversaciones abiertas
  bloquean y un cambio nuevo invalida las aprobaciones previas; se exige ademas
  aprobacion del ultimo cambio por otra persona. La prueba debe
  incluir ese cambio ficticio autorizado. Se inspeccionan las prohibiciones de
  force push/borrado sin intentar ejecutarlos. No integrar ni pulsar auto-merge.
- Documentar evidencia, SHA, cuenta autora y lo que no pudo verificarse. Un token
  que falla, una regla que no bloquea o un cambio de identidad inesperado detienen
  la prueba; no ampliar permisos ni eludir la regla.
- Al terminar, cerrar la PR sin integrarla. No borrar ramas ni cambiar mas remotos
  fuera de la autorizacion. Si falla la prueba, Fernando autoriza volver a DISABLED;
  entretanto, no hacer mas envios. Reabrir acceso o corregir permisos requiere permiso.
- Solo cuando Claude haya verificado el funcionamiento se cumple la condicion del
  permiso permanente limitado a subir ramas y abrir PR. No incluye integrar ni
  cambiar configuraciones, secretos o protecciones.

### d) Publicar el bloque 1 con autorizacion expresa

- Despues de a, b y c, Fernando autoriza expresamente la publicacion del bloque 1.
  Esta primera publicacion conserva ese requisito aunque la prueba anterior haya
  cumplido la condicion del permiso permanente para trabajo posterior.
- Seguir el paso siguiente, con el SHA exacto y la cuenta nueva; no publicar de
  golpe las ramas acumuladas de los bloques 4, 5, 6 o 7.

## Paso 1. Publicar y revisar el bloque 1

- Fernando autoriza expresamente esta subida del bloque 1, conforme al paso d.
- Codex prepara una rama de publicacion desde la base real vigente, con el contenido
  del bloque 1 (referencia local b0da873), su texto de PR y pruebas correspondientes.
  Revisa los archivos y el historial por datos que no deban publicarse. Antes de subir,
  entrega el SHA exacto; resolver cambios de base o conflictos genera otro SHA y
  requiere pruebas y revision de ese nuevo resultado. No empujar la rama del bloque 6.
- Codex entrega el titulo y texto propuestos de la PR del bloque 1. Fernando
  los pega y abre la PR desde la web con fernandocodex64-sudo; Codex no usa gh ni API
  para crearla en esta etapa.
- Claude revisa solo el diff de esa PR respecto a su base y registra el SHA completo.
  Codex transcribe el informe recibido en docs/revisiones/*.local.md, sin agregarlo
  al commit revisado. No afirma que Claude ya reviso un SHA distinto.
- Fernando y FERRUMTJA aplican GUIA-APROBAR.md; ambos deben aprobar la version vigente.
  Integrar requiere otra autorizacion expresa y lo hace una de esas dos personas.
- Como deshacer: antes de integrar, cerrar la PR (con autorizacion); despues, preparar
  una PR de reversion del cambio, revisarla y aprobarla igual. No reescribir main.

## Paso 2. Publicar la parte operativa del bloque 4 y el bloque 6

- Fernando confirma que el bloque 1 esta integrado y autoriza las subidas que aun
  requieran permiso individual. No autoriza con ello activar la fabrica.
- Codex prepara una nueva rama desde ese main con **factory2/ del bloque 4 y los
  cambios del bloque 6**, junto con config, pruebas y guias necesarias para entenderlos.
  No integrar ni hacer cherry-pick ciego de las ramas completas: incluirian el revisor
  automatico aparcado. No incluir ERP-FACTORY-revision/ ni activar/cambiar workflows.
- La seleccion necesita comprobar dependencias antes de publicar: actualmente algunas
  pruebas V2 de tests/operation_fixtures.py y el importador V2 usan la carpeta privada.
  La via manual no debe necesitarla. Resolver la distribucion de esas pruebas y la
  referencia V2 opcional es un requisito previo de la futura PR, no una excepcion
  para publicar pruebas rotas, marcar como verificada una suite no ejecutada o subir
  el revisor privado. Cualquier ajuste de codigo exige otro SHA y nueva revision.
- Codex ejecuta las suites aplicables sobre la seleccion exacta. No reutiliza sin
  comprobar los resultados de esta rama local, que aun contiene el codigo privado.
- Claude revisa el diff y las dependencias. Para una entrega importante, ademas abre
  una conversacion nueva y revisa toda la fabrica resultante, declarando su cobertura.
- Fernando y FERRUMTJA comprueban la propuesta y la version; solo una de esas personas
  integra con autorizacion expresa. Los limites de gasto y el informe de Claude no
  son una aprobacion humana ni permiten conectar sistemas.
- Como deshacer: cerrar la propuesta antes de integrar; despues, PR de reversion con
  pruebas y dos aprobaciones. Conservar los registros anteriores como historia.

## Paso 3. Mantener aparcada la automatizacion

- ERP-FACTORY-revision/ permanece solo en las ramas locales de desarrollo. No crear
  un repositorio privado por ahora ni incluir esa carpeta en los envios anteriores.
- Codex mantiene if false, execution_enabled=false y el pin de ceros; no lee secretos.
- Se registran para una posible reactivacion: USD, 1.00 por llamada, 12.00 por ejecucion,
  13.00 acumulado, 11 llamadas y opcion 1 (autorizacion manual). No hay ticket emitido,
  saldo real importado ni adaptador conectado. La opcion esta elegida, no instalada.
- Claude puede revisar el diseño local; usar Actions para un hito importante requiere
  que Fernando autorice especificamente repositorio, configuracion y gasto. Hace falta
  revisar el adaptador pendiente y fijar el validador antes de cambiar los bloqueos.
- Como deshacer una futura reactivacion: con autorizacion, deshabilitar su ejecucion,
  conservar reservas inciertas y evidencias privadas; nunca repetir una llamada incierta
  ni borrar el registro de gasto para aparentar saldo disponible.

## Antes de datos reales

Riesgo aceptado por Fernando: ninguna de las dos personas aprobadoras programa ni
hay revisor tecnico humano. Claude no esta autenticado y puede omitir errores.
**Auditoria tecnica externa obligatoria antes de usar datos reales de clientes o
conectar el ERP.** Tambien hacen falta las autorizaciones y controles de acceso y
coordinacion pendientes. La revision de un contador no sustituye esa auditoria.

## GitHub CLI posterior: no ejecutado

La consulta local no encontro gh instalado/accesible en PATH; no hay version
verificada. No instalarlo ni autenticarlo ahora. El plan de GH_CONFIG_DIR exclusivo
fuera del repositorio, entrada oculta por Fernando, verificacion y revocacion esta
en [CONFIG-LOCAL-CODEX.md](github/CONFIG-LOCAL-CODEX.md). gh debe aceptar solo
public_repo; si exige mas, detenerse y mantener la via web. Prohibido mostrar el
token (incluido gh auth token) o extraerlo del gestor. La autorizacion de configurar
Git localmente no autoriza gh, conexiones, subidas ni nuevas PR.
