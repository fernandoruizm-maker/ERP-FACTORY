# Retirada permanente y archivo de la fabrica original

**Decision de Fernando:** detener permanentemente la fabrica original y archivarla,
sin borrar codigo, historial, trabajos ni evidencias. La fabrica nueva sigue
inactiva; retirar la anterior no autoriza activar la nueva.

**Este documento es solo un plan local.** No se ha accedido a Ubuntu, rdc, GitHub,
credenciales ni red para prepararlo. No se ha pausado ni detenido ningun servicio.
Cada etapa de cambios se ejecutara cuando Fernando la autorice especificamente.
Fernando puede seguir la lista; los pasos tecnicos los realiza un operador
identificado y autorizado, con Fernando presente. No hay que programar ni improvisar.

## 1. Que sabemos y que hay que confirmar

Referencias historicas comunicadas: VM RDC-Piloto-Aislado, Ubuntu, codigo en
/opt/rdc/factory y servicio rdc-pilot. No se comprobo su estado actual ni la version
instalada. Confirmar el propietario y nombre exactos de rdc; NO confundirlo con
fernandoruizm-maker/ERP-FACTORY. No usar los IDs de ruleset de ERP-FACTORY para rdc.

Lectura local de referencia, sin ejecutar upstream/:

- upstream/factory/mvp/polling.py: la pausa usa pilot.pause dentro de state_dir;
  no interrumpe un trabajo ya iniciado. El estado PAUSED no significa servicio parado.
- upstream/factory/mvp/queue.py: base mvp.sqlite3, modo WAL, trabajos con id/state;
  recover vuelve a poner RUNNING y PUBLISHING en QUEUED. El piloto llama recover
  al arrancar, incluso antes de comprobar la pausa. **No reiniciar para probar**.
- upstream/factory/mvp/__main__.py: el comando jobs construye Queue y puede crear
  tablas/cambiar modo de diario. No tratarlo como una consulta estrictamente de lectura.
- upstream/factory/mvp/github.py: la comprobacion espera factory/quality y
  factory/human-approval asociados al ID de la App, ademas de las reglas de PR.
- factory2/operations.py: en modo real se bloquea siempre con
  ORIGINAL_COORDINATION_NOT_VERIFIED. Un archivo local afirmando que todo paro
  no elimina ese bloqueo ni constituye prueba de retirada.

Estos hechos describen los archivos de esta copia. El operador debe cotejarlos
con la instalacion real antes de usar sus nombres o procedimientos.

## 2. Informacion que debe traer Fernando, sin secretos

Prepare una hoja privada llamada **Inventario de retirada**, con fecha/hora y zona
horaria, nombre de quien comprobo cada punto y su resultado. Comparta solo un resumen
redactado: no adjunte bases, logs completos, configuraciones completas ni la VM.

| Que comprobar | Como obtenerlo en la etapa de lectura autorizada | Que traer |
|---|---|---|
| Instalacion correcta | Abrir la VM habitual y confirmar su nombre; el operador identifica el equipo y el servicio | Alias del equipo/VM, nombre exacto de unidad y ruta del codigo; no IP publica ni datos de acceso |
| Estado del polling | Consultas limitadas de systemctl indicadas abajo | Activo/inactivo, subestado, PID principal, hora y resultado |
| Arranque automatico y otros ejecutores | Revisar habilitacion, unidades de usuario, timers, cron, contenedores y supervisores vinculados solo a la fabrica; revisar tambien Windows/WSL si existen | Nombres y estados de cada lanzador, si reinicia solo y como se deshabilita; no comandos con secretos |
| Version y estado local | El operador identifica commit y si hay cambios locales sin leer contenidos sensibles | SHA, cambios presentes si/no, ubicacion y huella del inventario privado |
| Cola y trabajo en curso | Lectura SQLite directa en modo solo lectura, con ruta confirmada; sin importar el proyecto | Cantidades por estado, IDs de trabajo y ultima actualizacion; nunca payload, checkpoint, error libre o credenciales |
| PR abiertas en rdc | En la web, sesion personal autorizada, repositorio exacto > Pull requests > Open; revisar todas las paginas y drafts | Numero/enlace, SHA completo, estado, trabajo asociado y decision pendiente; sin pegar codigo o informacion de clientes |
| Reglas de rdc | Settings > Rules > Rulesets y, si existe, proteccion clasica de ramas; comprobar reglas efectivas, incluidas heredadas | Rama afectada, ID/nombre, checks exigidos y App emisora, aprobaciones, excepciones y reglas solapadas |
| Pausa de Windows | Revisar indicador de pausa de la instalacion Windows y sus tareas/servicios conocidos, sin iniciarlos | Pausa presente y ruta verificada, lanzadores activos/inactivos, ultima ejecucion y hora de comprobacion |
| Credenciales dependientes | Pantallas que muestran solo nombres/IDs y repositorios autorizados, sin abrir valores | App/instalacion/key IDs, nombre de secreto webhook y referencia de clave OpenAI si existe, propietario y otros consumidores |

### Lecturas sencillas de Ubuntu (no ejecutadas por este documento)

Cuando se autorice esa consulta y se confirme que el nombre es rdc-pilot, el
operador puede obtener un resumen que no muestra variables ni lineas de ejecucion:

```text
systemctl show rdc-pilot -p Id -p LoadState -p ActiveState -p SubState -p UnitFileState -p MainPID -p NRestarts -p Restart
systemctl show rdc-pilot -p FragmentPath -p TriggeredBy -p WantedBy -p RequiredBy
systemctl is-enabled rdc-pilot
```

Anotar resultados; inactive es distinto de disabled: uno describe ejecucion y
otro arranque automatico. is-enabled puede terminar con salida distinta de cero
cuando esta deshabilitado; leer la palabra que devuelve. Si la unidad no existe,
no inventar otro nombre ni ejecutar comandos sobre otro servicio.

No compartir systemctl cat, Environment, ExecStart, volcados del entorno,
configuraciones enteras ni journalctl completo: podrian revelar claves, rutas
sensibles o datos de trabajos. Para evidencias de logs, el operador extrae solo
hora, evento y estado, revisa que no haya secretos y conserva el original privado.

### Cola y Windows, sin inventar rutas

El operador confirma state_dir de esa instalacion y la ruta exacta a mvp.sqlite3
sin copiar los demas campos de configuracion. Para el inventario usa una conexion
SQLite con URI mode=ro y consultas limitadas a id, state, updated y conteos por
state. No usar SELECT *, ni imprimir payload/checkpoint/error/metadata, ni ejecutar
recover, worker, pilot, retry o jobs para obtener el inventario.

Si el esquema real difiere o el archivo no existe, detener esa consulta y aclararlo;
no crear una base vacia ni modificar la real. Anotar los estados reales, incluidos
QUEUED, RUNNING, PUBLISHING, WAITING_APPROVAL, APPROVED o BLOCKED si aparecen.

En Windows, Fernando abre Programador de tareas y Servicios y localiza solo las
entradas conocidas de la fabrica original. Trae nombres, estado y habilitacion,
no la pestaña de acciones si puede mostrar secretos. El indicador pilot.pause
solo sirve si se confirma que ese ejecutor lo respeta. No iniciar una tarea para
comprobar la pausa. La VM encendida no demuestra que el polling este trabajando;
la VM apagada tampoco demuestra que no volvera a arrancar.

## 3. Orden de retirada: una etapa cada vez

### Paso A. Pausar nuevas entradas y conservar el punto de partida

1. Fernando autoriza la pausa de la instalacion exacta. Registrar hora, estado y
   lanzadores antes de cambiar nada. La nueva fabrica permanece inactiva.
2. Mantener la pausa de Windows. El operador activa la pausa soportada de Ubuntu
   en el state_dir comprobado, sin sustituir la base ni inventar comandos. Si se
   utiliza el mecanismo pilot.pause, comprobar primero la version instalada.
3. Suspender nuevos encargos/etiquetas de automatizacion. Inventariar webhooks u
   otros consumidores: la pausa del piloto no prueba que el receptor deje de
   encolar. El operador pausa esos ingresos o sus consumidores con autorizacion,
   conservando los eventos ya recibidos; no eliminar issues ni borrar colas.
4. Esperar un punto seguro del trabajo ya en curso. Registrar si queda RUNNING o
   PUBLISHING. Pausar no cancela una llamada externa. Si tarda o queda incierta,
   no reiniciar ni reenviar: investigar el resultado antes de decidir.
5. Tomar un inventario inicial de trabajos y PR; mantenerlo actualizado durante
   la reconciliacion. Si no se puede pausar con seguridad, detener el procedimiento
   y pedir una decision especifica; no declarar retirada completada.

Deshacer A: solo con autorizacion y comprobando que la nueva sigue parada, reponer
la entrada anterior. No quitar pilot.pause ni reactivar disparadores automaticamente.
Si hubo trabajos inciertos, resolverlos antes de reanudar para evitar duplicados.

### Paso B. Resolver cada trabajo y cada PR abierta en rdc

Crear una fila por trabajo y una por PR, enlazandolos cuando corresponda. Si un
trabajo no tiene PR o una PR no tiene trabajo, tambien hay que decidir su destino.
Para cada PR abierta, Fernando elige **cerrar** o **terminar a mano**. No basta
poner todas las filas como archivadas sin una decision individual.

| Campo del acta privada | Contenido |
|---|---|
| Trabajo / PR / SHA | IDs y version exacta; no datos de clientes |
| Estado observado | Pendiente, en ejecucion, publicado, incierto, pendiente de aprobacion, etc. |
| Decision de Fernando | Cerrar, terminar a mano, o cancelacion explicita del trabajo aun sin PR |
| Responsable y evidencia | Persona, fecha, enlace/resultado y huella del acta |
| Resultado final | Cerrada sin integrar; integrada manualmente tras revision y decision; trabajo cancelado sin reintento; o pendiente que bloquea la retirada |

- **Cerrar:** Fernando autoriza esa PR; conservar rama, commits, conversaciones y
  evidencia. Cerrar no borra el trabajo ni equivale a aprobarlo. Registrar el motivo.
- **Terminar a mano:** persona responsable revisa el SHA y los resultados con Claude,
  las dos personas aprueban y Fernando decide expresamente si integrar. Nunca usar
  la cuenta de maquina para aprobar o integrar, ni pulsar el boton solo porque aparece.
- Si factory/quality o factory/human-approval impiden terminar una PR, resolver
  primero la decision de reglas del apartado 4. No fabricar checks verdes ni
  retirar toda la proteccion. Cerrar una PR no requiere darla por aprobada.
- Un trabajo QUEUED sin PR no se migra a la fabrica nueva automaticamente. Registrar
  cancelacion/archivo o nueva solicitud futura con otra autorizacion, sin duplicarlo.
- RUNNING o PUBLISHING pueden haber escrito en GitHub aunque la respuesta se perdiera.
  Comparar PR, commits y evidencia; no volver a ejecutar para averiguarlo. El arranque
  original llama recover y puede reencolar: no usarlo como herramienta de diagnostico.
- WAITING_APPROVAL o APPROVED local no prueba que el SHA siga vigente ni autoriza
  integrar. Conservar el estado historico; no editar SQL para simular un final exitoso.

Antes de pasar al cierre normal: cero trabajos realmente ejecutandose, todas las PR
abiertas inventariadas con resultado y ninguna publicacion incierta sin aclarar.
Los registros historicos pueden conservar estados antiguos: el acta explica su
resolucion; no borrar ni maquillar la base. Recontar PR abiertas tras reconciliar.
Si hay un trabajo atascado que obliga a parar antes, Fernando autoriza esa excepcion;
se conserva como incierto y la retirada no se certifica como completa hasta resolverlo.

Deshacer B: una PR cerrada puede reabrirse solo si la plataforma y la decision lo
permiten; volver a revisar su SHA y aprobaciones. Una integracion no se borra:
reversion por otra PR revisada y autorizada. No restablecer la cola desde una copia
vieja ni reanudar trabajos resueltos para deshacer un error del acta.

### Paso C. Detener y desactivar de forma permanente los ejecutores

Solo despues del punto seguro y de las decisiones de reconciliacion:

1. El operador autorizado detiene rdc-pilot, una vez confirmado el nombre. Procedimiento
   previsto: systemctl stop rdc-pilot, con privilegios autorizados si son necesarios.
2. Deshabilita su arranque automatico: systemctl disable rdc-pilot. Deshabilitar no
   sustituye detener. No desinstalar paquetes ni borrar codigo o archivos de unidad.
3. Deshabilita tambien timers, tareas cron, unidades de usuario, contenedores con
   politica de reinicio y tareas de Windows de ESTA fabrica que puedan relanzarla.
   Registrar cada cambio. No detener servicios del ERP ni otros sistemas compartidos.
4. Comprobar inactive/dead, MainPID=0 y ausencia de procesos hijos/otros workers
   identificados. Verificar unidades deshabilitadas y que ninguna otra ruta las lance.
   Un estado failed puede indicar que paro con error: conservarlo y aclararlo.
5. Valorar un bloqueo persistente de la unidad (mask) para impedir un arranque casual.
   Es un cambio adicional que se autoriza expresamente tras revisar la unidad. Si
   systemd no permite enmascararla por como esta instalada, no borrar ni mover su
   archivo para forzarlo: un tecnico debe proponer el cambio conservando evidencia.
6. Registrar antes/despues. No reiniciar Ubuntu ni el servidor para hacer una prueba
   ahora: un ensayo tras reinicio requiere ventana y permiso aparte, verificando
   antes que no afectara al ERP. Si no se prueba, marcarlo NO VERIFICADO.

Detencion permanente significa sin autoarranque, entradas/consumidores retirados,
credenciales revocadas segun el paso E y prohibicion de reactivar sin una nueva
decision. No es solo pulsar Stop una vez. Mantener Windows pausado y sin lanzadores.

Deshacer C: no arrancar inmediatamente. Primero detener cualquier operacion de la
nueva, invalidar su constancia de retirada, revisar trabajos y aprobaciones, restaurar
solo los lanzadores previstos y comprobar credenciales/reglas. Con otra autorizacion,
quitar un mask si se puso y reponer el estado de habilitacion anterior. Arrancar solo
cuando se haya previsto que recover puede reencolar y se haya evitado el duplicado.
No hay ejecucion paralela de ambas fabricas, ni durante una prueba de recuperacion.

### Paso D. Archivar codigo, estado y evidencias sin borrar originales

1. Elegir un archivo PRIVADO, con responsable, acceso limitado y almacenamiento
   cifrado. No usar ERP-FACTORY publico, un chat ni adjuntarlo a Claude. Mantener
   tambien una copia protegida independiente. Fernando decide ubicacion y custodia.
2. Guardar el codigo exacto, historial Git completo (incluidos cambios locales,
   ramas/commits pendientes) y un inventario de versiones y huellas SHA-256.
   No hacer push de ese historial para archivarlo. Conservar configuracion operativa
   no sensible y nombres/IDs de dependencias; separar material secreto del expediente.
3. Confirmar todos los escritores de SQLite detenidos, incluidos receptores webhook
   o workers distintos del polling. Confirmar ruta/propietario de cada base; no asumir
   que solo existe mvp.sqlite3. No borrar archivos -wal/-shm ni forzar VACUUM/checkpoint.
4. **Copiar cada SQLite mediante su API de backup**, no copiando a mano solo el
   archivo .sqlite3. El operador usara sqlite3.Connection.backup de Python o la
   API equivalente: origen existente con URI mode=ro, destino NUEVO que no exista,
   conexion de destino local y copia completa hasta finalizar. No importar modulos
   del proyecto ni abrir Queue, porque pueden modificar la base. Registrar resultado;
   si falla o se deniega acceso, detenerse, no cambiar permisos ni improvisar otra via.
5. Cerrar las conexiones y verificar en la COPIA PRAGMA integrity_check: debe
   devolver ok. Comparar esquema y conteos por tabla con el origen parado sin
   imprimir filas sensibles. Calcular SHA-256 de la copia cerrada, tamaño y fecha;
   una huella demuestra igualdad de bytes, no autenticidad ni ausencia de secretos.
6. Conservar el SQLite original y sus ficheros auxiliares en su ubicacion, intactos.
   Archivar tambien acta de reconciliacion, resultados de servicio, lista de
   disparadores, PR/SHA, decisiones y reglas antes/despues. Los logs completos y
   bases pueden contener datos privados: custodia restringida, no publicacion.
7. Probar lectura/restauracion de la copia en un entorno aislado, sin lanzar la
   fabrica, sin red y sin credenciales activas. No sustituir la base original.
   Confirmar que se puede consultar y que las cantidades concuerdan. Registrar
   exactamente lo ensayado; una copia que no se pudo comprobar no se da por buena.
8. Preparar manifiesto privado de archivos/huellas y una version resumida sin secretos
   para auditoria. Registrar quien custodia, quien puede recuperar y donde estan
   las copias. No establecer fecha de borrado: esta decision exige conservar evidencia.

No incluir claves activas en el paquete de revision. Si el archivo historico original
ya contiene material secreto, conservarlo aislado/cifrado bajo custodia y revocar su
capacidad de uso; no difundirlo ni borrar historia para esconderlo. No se accede al ERP
para completar el archivo de la fabrica.

Deshacer D: una copia adicional no sustituye el original. Si la comprobacion falla,
marcar esa copia NO VALIDA y conservar la evidencia del fallo; no borrar el original
ni sobreescribir otra copia. Restaurar solo en un destino aislado autorizado y
reconciliar con los resultados remotos antes de plantear una reactivacion.

## 4. Decidir que hacer con las reglas de rdc

Situacion descrita: rdc exige los estados factory/quality y factory/human-approval
publicados por la App original. Sin la App no habra estados nuevos para los SHA
nuevos. Las PR pueden quedar esperando indefinidamente; los checks verdes antiguos
no prueban cambios posteriores. **Fernando debe elegir una opcion**, no se cambia
ninguna regla por este plan. La configuracion remota real sigue pendiente de verificar.

| Opcion | Cuando sirve | Que se cambia y que se conserva | Limite / deshacer |
|---|---|---|---|
| A. Mantener rdc como archivo sin nuevas integraciones | No se va a desarrollar alli | Conservar reglas y evidencias; cerrar PR pendientes. Opcionalmente archivar el repositorio desde GitHub solo con otra autorizacion | El bloqueo de nuevas PR es deliberado. Desarchivar no devuelve checks: exige nueva decision de reglas y permisos |
| B. Continuar rdc con dos aprobaciones humanas | Se quiere trabajar a mano sin App original | Sustituir solo los dos checks dependientes de esa App por PR obligatoria y dos aprobaciones; invalidar al cambiar el SHA, aprobacion del ultimo cambio por otra persona, conversaciones resueltas, sin excepciones, borrado ni force push. Conservar otros checks utiles | Las personas no sustituyen pruebas tecnicas; mantener revision Claude y evidencia de pruebas. Reponer checks originales solo con productor valido disponible, sin dejar una ventana sin proteccion |
| C. Sustituir la App por otro verificador independiente | Se requiere una señal tecnica automatica real | Diseñar y autorizar otro productor para el SHA exacto, con identidad propia y pruebas de confianza; cambiar solo los checks afectados tras validar la sustitucion | Proyecto posterior, no esta instalado ni autorizado. No fabricar success ni usar una App aparente para heredar confianza; la retirada puede quedar pendiente de esta decision |

Si se elige B, Fernando debe confirmar quienes son las dos personas en rdc y que
pueden aprobar las PR: no asumir que los accesos de ERP-FACTORY existen tambien alli.
La cuenta autora no aprueba su propia PR. La cuenta de maquina NUNCA aprueba ni
integra; nadie integra sin decision expresa de Fernando tras la revision de Claude.
La opcion B reduce la dependencia de controles automaticos: Fernando debe aceptar
explicitamente ese cambio y sus limites, sin llamarlo una equivalencia tecnica.

### Aplicacion futura por Fernando, si elige B

1. En la web, confirmar propietario/rdc > Settings > Rules > Rulesets. Documentar
   antes el ID, la rama, checks y emisores, excepciones y otras reglas efectivas.
   Revisar tambien proteccion clasica y reglas heredadas; una regla superpuesta
   puede seguir exigiendo los checks aunque se quite otra.
2. Preparar primero las dos aprobaciones y demas condiciones de proteccion. Revisar
   la propuesta con Claude y Fernando antes de guardar. No desactivar el ruleset entero.
3. Con permiso especifico, retirar solo las exigencias factory/quality y
   factory/human-approval de la App retirada. No publicar success ficticio, no
   agregar bypass, no cambiar a otra App sin validar su responsabilidad.
4. Probar una PR ficticia, sin integrar: sin aprobaciones bloqueada, con una
   bloqueada, con cambios las aprobaciones se invalidan, conversaciones abiertas
   bloquean. Verificar reglas efectivas y ausencia de excepciones; no basta ver
   habilitado el boton. Conservar evidencia del SHA y cerrar la prueba sin integrar.
5. Resolver manualmente las PR del paso B que dependian de esta decision. Si la
   proteccion no se verifica, detener integraciones; no rebajarla para salir del paso.

Esta decision se prepara antes de reconciliar las PR y debe estar resuelta antes
de desinstalar la App. Puede elegirse cerrar todas las PR y dejar rdc archivado:
no es obligatorio terminar ninguna integracion para retirar la fabrica.

Deshacer la transicion de reglas: mantener las integraciones congeladas, recuperar
la configuracion anterior comprobada y asegurar que su App/productor funciona antes
de volver a exigirlo. Tras la revocacion, puede necesitar una nueva instalacion e
IDs; no prometer que reponer el JSON antiguo restaura el servicio. Todo con permiso.

## 5. Paso E: revocar accesos DESPUES de la parada y el archivo verificado

Antes de revocar: servicios y lanzadores detenidos, inventario reconciliado,
archivo comprobado y decision de reglas resuelta. Confirmar si cada credencial
pertenece solo a la original: no revocar una compartida por otro sistema sin plan
separado. Nunca pedir a Fernando que pegue su valor en un chat o terminal visible.

1. **Clave privada de la GitHub App:** en la cuenta propietaria de esa App,
   Settings > Developer settings > GitHub Apps > App correcta > Private keys,
   identificar la clave por ID/fecha y revocarla. Confirmar que se identifico la App
   original, no la cuenta de maquina de la nueva. No mostrar ni descargar el PEM.
   Si hay otras claves de la misma App, inventariar cuales daban acceso a la original.
2. **Instalacion de la App:** desde la cuenta/organizacion propietaria de rdc,
   Settings > Applications / Installed GitHub Apps > App correcta > Configure,
   revisar los repositorios afectados y desinstalar la instalacion autorizada.
   Una instalacion compartida requiere separar su alcance o acordar su retirada
   con los otros responsables. No borrar el registro de la App ni sus evidencias
   como sustituto de desinstalar. Las etiquetas de pantalla se confirmaran alli.
3. Registrar eliminacion de la clave e instalacion, hora, IDs y responsable. Una
   clave revocada por si sola no demuestra que todos los tokens emitidos antes
   dejaran de servir inmediatamente. Verificar la revocacion de la instalacion y
   la caducidad/revocacion de tokens conocidos mediante evidencia administrativa,
   sin intentar usarlos para escribir. Hasta resolver esa incertidumbre, no dar
   por sellada la retirada ni autorizar operaciones reales de la nueva.
4. **Webhook:** identificar si era webhook de repositorio o de la App. Con permiso,
   deshabilitar/eliminar solo el enlace de la original y detener su receptor si
   era exclusivo. Retirar o rotar el secreto en el gestor autorizado, conservando
   solo nombre/ID y evidencia de la baja. No dejar un receptor reutilizable con
   el secreto antiguo. No cambiar URLs, TLS o red de otros sistemas automaticamente.
5. **OpenAI, si habia clave:** identificar su proyecto/propietario y uso compartido.
   Fernando revoca la clave exclusiva desde la consola correspondiente y registra
   ID/referencia, fecha y resultado, nunca su valor. No cancelar cuentas ni borrar
   historiales de facturacion. Si compartida, migrar primero consumidores autorizados
   a credenciales distintas; esa migracion requiere otra autorizacion.
6. Revisar otros accesos inventariados de la original (sin buscar secretos por
   todo el equipo). Mantener separadas la credencial de fernandocodex64-sudo y las
   credenciales personales. No borrar credenciales de Windows de Fernando.
7. Guardar recibos de revocacion redactados y vincularlos al acta. Las copias
   historicas de claves revocadas, si existen, quedan bajo custodia privada; no
   se publican ni se vuelven a importar. No borrar codigo o historial para retirarlas.

Deshacer E NO es recuperar el secreto viejo: una clave revocada no se vuelve valida.
Reactivar exigiria nuevas credenciales, reinstalar/reautorizar la App si procede,
revisar IDs de instalacion/emisor y reglas, y rotar el webhook. Son cambios nuevos
con autorizacion especifica. No conservar una clave activa "por si acaso" ni probar
una revocada contra GitHub/OpenAI. Codigo y evidencia permanecen conservados.

## 6. Registrar la retirada en la fabrica nueva: diseño, NO implementado

No editar active-factory.json para poner original_stopped=true. Hoy solo es un
marcador SIMULATED_ONLY y Coordinator.check_active bloquea todos los usos reales.
No quitar ORIGINAL_COORDINATION_NOT_VERIFIED, no activar simulation=True para una
operacion real, no considerar una foto o este documento como autenticacion.

### Expediente privado propuesto

Un **acta de retirada** identificada y versionada, con:

- ID unico de retirada; instalacion original, equipo/VM y replicas cubiertas;
  repositorio rdc y SHA/version del codigo original, sin URLs con credenciales.
- Momento de cada comprobacion, identidad verificable del operador y decision de
  Fernando. Alcance Ubuntu, Windows y otros lanzadores realmente encontrados.
- Evidencia de servicio inactivo, PID ausente, autoarranque deshabilitado y controles
  de relanzamiento; comprobacion tras reinicio si se autorizo, o limite pendiente.
- Inventario de trabajos/PR, decisiones y resoluciones, con referencias y huellas;
  ningun ejecutor en curso ni efecto remoto incierto sin reconciliar.
- Manifiesto de archivo SQLite/codigo/evidencias, huellas, integridad y ensayo de
  restauracion aislada; ubicacion privada y custodio, no la base ni secretos.
- Decision y evidencia de reglas de rdc; recibos administrativos de revocacion de
  App/instalacion/webhook/OpenAI segun existieran. No inferir ausencias sin inventario.
- SHA y factory_digest de la fabrica nueva para la que se evaluo la retirada,
  fecha de verificacion, plazo de validez a decidir y condiciones de invalidacion.

Un hash solo detecta cambios: no prueba quien recogio la evidencia ni que el equipo
siga parado. La nueva fabrica necesitaria un verificador de procedencia separado,
con identidad del recolector autenticada, firma de acta y raiz de confianza aprobadas
fuera del contenido que se evalua. No existen hoy. Elegir operador, sistema de firma,
custodia y plazo es decision pendiente; no crear claves ni accesos por este plan.

### Comprobacion futura y sustitucion del bloqueo

1. Diseñar en una PR separada un verificador de retirada (sin modificar upstream/).
   Validar firma/procedencia, integridad, alcance completo, version exacta, vigencia
   y ausencia de revocacion del acta. Rechazar JSON hecho a mano o firmas desconocidas.
2. Exigir evidencia reciente de parada y prohibicion efectiva de relanzamiento.
   Proponer lectura autorizada del estado por un recolector independiente y una
   constancia de corta vigencia. Sin esa verificacion o si vence, bloquear. Un acta
   permanente de archivo no reemplaza una comprobacion reciente de seguridad.
3. Mantener un registro de revocacion de constancias: si se restaura la VM, se
   habilita un lanzador, aparece otra replica o se devuelve acceso a la original,
   invalidar la constancia y bloquear la nueva ANTES de reactivar la antigua.
   Sin monitor/acceso confiable no prometer deteccion inmediata; no operar en real.
4. Bajo el candado de un solo trabajador, comprobar esa constancia antes de recover
   y antes de cada llamada. Resolver la carrera entre comprobar y ejecutar con una
   exclusion mutua administrada en el punto de operacion y un protocolo de retorno:
   detener consumidores nuevos, esperar trabajos en curso, invalidar permiso y solo
   entonces habilitar la original. El simple archivo de bloqueo actual no coordina
   equipos distintos ni excluye acciones de un administrador.
5. Solo despues de implementar, revisar y probar ese mecanismo se podria sustituir
   ORIGINAL_COORDINATION_NOT_VERIFIED por un estado de retirada verificada. Cualquier
   dato faltante, alterado, caducado o contradictorio conserva un resultado BLOCKED.
6. Esta comprobacion no sustituye el resto de puertas: version/revision de Claude,
   dos aceptaciones, permisos ERP, presupuesto y autorizacion de operacion. Tampoco
   habilita publication_allowed, acceso al ERP ni modifica los interruptores false.

Pruebas futuras necesarias: acta correcta y autentica; copia falsa; firma desconocida;
SHA/instalacion distintos; base sin backup valido; trabajo incierto; App no revocada;
Windows activo; evidencia caducada; restauracion de la original; perdida del recolector;
y dos trabajadores simultaneos. Deben bloquear donde corresponda. Primero dobles
ficticios; despues una verificacion operativa autorizada, sin confundir ambos ensayos.

Deshacer este registro futuro: revocar la constancia, bloquear llamadas/recuperacion
y mantener parada la nueva. Conservar acta y auditoria como historicas, no editarlas
para fingir que nunca existieron. El retorno a la original sigue los pasos C y E y
necesita nueva decision, nunca es automatico por fallar el verificador.

## 7. Lista final para Fernando

No marcar "retirada completada" hasta tener:

- Inventario confirmado de Ubuntu, Windows y otros lanzadores, con versiones.
- Todas las PR de rdc y trabajos reconciliados; ninguna llamada/publicacion incierta.
- Servicio inactivo, autoarranque/desencadenantes retirados y Windows pausado.
- Codigo/historial/evidencias conservados y backup SQLite por API verificado.
- Decision de reglas de rdc aplicada y comprobada, o rdc deliberadamente sin nuevas
  integraciones; ninguna desproteccion temporal para completar la retirada.
- Credenciales exclusivas revocadas y dependencias compartidas resueltas, con recibos.
- Acta privada, custodio y limites documentados. Ningun secreto en informes publicos.

**Decisiones pendientes de Fernando:** opcion A/B/C para rdc; responsables y ventana
de trabajo; destino/custodia del archivo; tratamiento individual de PR/trabajos;
retirada de accesos compartidos; mecanismo de evidencia confiable y su vigencia.
No hace falta decidirlas para leer esta guia, pero si antes de ejecutar sus etapas.

Esta entrega solo reviso los archivos locales citados y la coherencia del documento.
No ejecuta codigo original ni comandos de este plan, no prueba backups reales, no
verifica estados remotos, permisos, pantallas, revocaciones ni reinicios. No se
cambia el bloqueo de la fabrica nueva ni se autoriza una llamada de pago.
