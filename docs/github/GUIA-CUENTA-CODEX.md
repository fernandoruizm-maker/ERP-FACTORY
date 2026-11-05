# Cuenta de GitHub de Codex: fernandocodex64-sudo

Guia para Fernando. Usuario real: **fernandocodex64-sudo**, ID **353061596**.
Nombre visible del perfil: **fenando-codex**; no usarlo como usuario de autenticacion.
Repositorio PUBLICO: **fernandoruizm-maker/ERP-FACTORY**.
Actualizacion: configuracion local de Git aplicada con autorizacion, sin token
ni acceso a credenciales. El envio sigue DISABLED y no se autoriza ninguna subida.

## 1. Cuenta creada y protegida

Segun Fernando, la cuenta fernandocodex64-sudo ya esta creada y tiene verificacion en dos
pasos activada. No hay que crearla otra vez. Mantenga un perfil de navegador
separado para distinguir esta cuenta de la cuenta personal de Fernando.
Conserve los codigos de recuperacion fuera del repositorio; no los envie en chats
ni en capturas. La cuenta abre PR; no las aprueba ni las integra.

## 2. Invitacion aceptada y proteccion de main

Fernando informa que Claude verifico por API publica el usuario y su ID, y que
figura como Collaborator en ERP-FACTORY. Invitacion aceptada segun Fernando.
Codex registra esta evidencia comunicada; no consulto la red para confirmarla. No ampliar su acceso a Admin ni Maintain ni a otros repositorios.
Fernando y FERRUMTJA siguen siendo las dos personas aprobadoras.

Fernando informa que el ruleset **main - dos aprobaciones sin excepciones**,
ID **26650549**, esta activo. Segun su comunicacion, Claude verifico en lectura
por la API publica: PR obligatoria, dos aprobaciones, invalidacion de aprobaciones
antiguas, aprobacion del ultimo cambio por otra persona, conversaciones resueltas,
prohibicion de borrar y de force push. La lista de excepciones (bypass) no fue
visible sin credenciales: Fernando debe comprobar en pantalla que esta vacia.
No se da esa comprobacion por hecha ni se ha ejecutado aun la PR de prueba.
Codex no ha consultado GitHub en esta tarea.

## 3. Por que se usara un token clasico

Fernando comunica que Claude comprobo la documentacion oficial de GitHub: los
tokens de grano fino no sirven para este colaborador de un repositorio de otra
cuenta personal. Para este caso se elige **token clasico**, con un unico permiso:
**public_repo**. Esta decision sustituye la propuesta anterior de grano fino.
Codex registra esa comprobacion comunicada; no la repite por red en esta tarea.

El token clasico **no tiene un selector para limitarlo a ERP-FACTORY**. Puede usar
los permisos que fernandocodex64-sudo tenga sobre repositorios publicos. Segun Fernando,
esta cuenta solo es colaboradora de ERP-FACTORY: por eso su escritura actual como
colaboradora de repositorios ajenos queda acotada a ese proyecto. No puede escribir
en cualquier repositorio ajeno solo porque sea publico.

No es una restriccion permanente del token a un solo repositorio: si la cuenta
crea otros repositorios publicos o recibe mas accesos, el token puede abarcarlos.
No darle otros accesos ni usarla para otros proyectos sin revisar esta decision.
La proteccion de main limita los cambios a esa rama; no reduce el alcance del
token ni impide todas las demas acciones de escritura. Codex no integrara PR.
La regla y las dos aprobaciones deben seguir vigentes, sin excepciones.

## 4. Fernando crea el token justo antes de la configuracion autorizada

**Todavia no esta creado.** Espere a que se vaya a realizar la configuracion local
y la prueba autorizada. No lo genere dias antes para dejarlo sin uso.

1. Abra el perfil de navegador de **fernandocodex64-sudo** y confirme ese nombre en el
   menu de la foto. No cree el token desde fernandoruizm-maker.
2. Foto de perfil > **Settings** > **Developer settings** > **Personal access
   tokens** > **Tokens (classic)** > **Generate new token (classic)**.
3. Si GitHub solicita contraseña o verificacion adicional, completela usted.
4. En **Note**, escriba: **Codex ERP-FACTORY - ramas y PR**.
5. En **Expiration**, elija **30 days** (30 dias). Al vencer se detiene el acceso;
   no renovar automaticamente ni quitar la caducidad.
6. En permisos, marque **solo public_repo**. Puede estar dentro del grupo repo:
   no marque el permiso amplio **repo** ni sus otros permisos. Deje sin marcar
   **workflow**, **admin:** (todos), **delete_repo**, **gist** y cualquier otro.
7. Revise la seleccion completa y pulse **Generate token**. Si no puede dejar
   solamente public_repo, detengase; no ampliar permisos para continuar.
8. Mantenga la pantalla privada. Durante la prueba autorizada, escriba o pegue
   el token **unicamente en la ventana segura de credenciales de Windows** que
   aparezca para fernandocodex64-sudo. Codex y Claude no deben ver ni leer ese cuadro.
   No lo pegue en chat, terminal, archivo, URL ni captura. Si no aparece el cuadro
   correcto, detengase: no entregue el token a los asistentes como alternativa.
9. Si uso el portapapeles, borre su contenido y su entrada del historial al terminar.
   Si cancela el proceso y no va a usar el token, revoquelo desde GitHub.

Las etiquetas de pantalla no se han comprobado en esta tarea sin red. Si difieren,
pida ayuda indicando solo los nombres de las opciones, nunca mostrando el token.
Sin workflow, una subida que cambie workflows puede rechazarse: no ampliar el
permiso para resolverlo automaticamente.

## 5. Configuracion local aplicada por Codex, sin conexion

Fernando **no tiene que editar archivos ni ejecutar comandos**.
Codex configuro solamente ERP-FACTORY-correcciones: nombre fernandocodex64-sudo,
correo 353061596+fernandocodex64-sudo@users.noreply.github.com y opciones del gestor.
El nombre correcto del almacen de Windows es **wincredman**; queda configurado
solo en este clon. Este ajuste no guarda ningun token por si mismo.
No cambio configuracion global ni leyo credenciales. Claude queda pendiente de
verificar esta evidencia no secreta. Los resultados y limites estan descritos en
[CONFIG-LOCAL-CODEX.md](CONFIG-LOCAL-CODEX.md).

A Fernando le corresponde crear el token y introducirlo personalmente en la
ventana de credenciales cuando llegue la prueba autorizada. Puede consultar su
correo noreply en Settings > Emails; no es una contraseña. Fernando ya proporciono el noreply exacto; no se uso su correo personal. No se cambian autores de commits
anteriores.

El ajuste del gestor es local al clon; el secreto se guarda en el almacen seguro
de Windows. Esto no crea una barrera contra otros procesos de la misma sesion.
La configuracion y el uso real deben verificarse; no se presume aislamiento absoluto.

## 6. Prueba y publicacion, siempre en el orden acordado

[PUBLICACION.md](../PUBLICACION.md) establece: token, configuracion local,
PR ficticia autorizada con fernandocodex64-sudo y, despues de comprobar los bloqueos,
publicacion del bloque 1 con autorizacion expresa. La PR de prueba se cierra
**sin integrarla**. No se habilita el envio solo por seguir esta guia.
El nombre de autor de un commit no demuestra que la PR la abrio esa cuenta:
Claude comprobara tambien la cuenta autora de la PR y las reglas efectivas.

## 7. Revocar el token y retirar la cuenta

1. Detenga las subidas. Desde **fernandocodex64-sudo**: Settings > Developer settings >
   Personal access tokens > **Tokens (classic)**. Localice el token por su nota
   y pulse **Delete** / revocar. Confirme. No hace falta mostrar su valor.
2. Desde **fernandoruizm-maker**: ERP-FACTORY > Settings > Collaborators / Manage
   access. Seleccione **fernandocodex64-sudo**, retire el acceso y confirme que desaparece.
3. Pida a Codex la reversion local descrita en CONFIG-LOCAL-CODEX.md, con autorizacion
   concreta. No borre credenciales personales de Fernando ni edite archivos usted.
4. Quitar el token o la cuenta no deshace lo publicado. Cerrar PR o revertir cambios
   requiere la autorizacion correspondiente; no reescribir main ni usar force push.
5. No crear otro token, renovar o ampliar permisos automaticamente. Si el token se
   expuso, revoquelo sin enviarlo a nadie para que compruebe si funciona.

Pendientes: token, verificacion de Claude de los ajustes, confirmacion de bypass
vacio por Fernando y prueba funcional de la proteccion. Estos documentos no acreditan esas acciones.
