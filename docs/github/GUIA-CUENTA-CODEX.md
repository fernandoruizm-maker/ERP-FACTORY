# Cuenta de GitHub aparte para Codex

Esta guia es solo documentacion local. No se ha creado cuenta, invitacion ni token;
no se han cambiado credenciales, identidad, remotos o configuracion de Git. El envio
sigue DISABLED. Fernando realizara los pasos desde su computadora en una etapa
posterior. No active Actions ni cree un repositorio privado.

Repositorio: **fernandoruizm-maker/ERP-FACTORY**, PUBLICO. Nombre provisional de la
cuenta: **fernando-codex**. Fernando elegira el definitivo; reemplace ese nombre en
la guia por el que realmente registre. La cuenta abre las PR, no las aprueba ni
las integra. Fernando y FERRUMTJA siguen siendo las dos personas aprobadoras.

No se consulto internet para esta guia. Los nombres de botones, disponibilidad del
token y comportamiento de Git Credential Manager NO se han verificado en este PC
ni con GitHub. Si una pantalla no coincide, detengase; no improvise permisos mayores.

## 1. Crear la cuenta y protegerla

1. Prepare un correo distinto del de su cuenta personal, bajo su control. No use
   un correo prestado. Compruebe las condiciones de GitHub aplicables a cuentas
   de maquina antes de continuar.
2. Abra un perfil separado del navegador para esta cuenta, para distinguirlo del
   perfil de Fernando. No cierre ni reconfigure su cuenta personal en otras aplicaciones.
3. En GitHub, elija **Sign up**. Registre el correo nuevo, una contraseña exclusiva
   y el nombre definitivo de la cuenta. Complete las verificaciones de GitHub y del correo.
4. Dentro de la cuenta nueva, abra la foto de perfil > **Settings** > **Password
   and authentication** > **Two-factor authentication** > **Enable**.
5. Configure una aplicacion de autenticacion o una llave de seguridad siguiendo
   las instrucciones. Confirme el codigo solicitado. No envie ese codigo a Codex.
6. Guarde los codigos de recuperacion en su gestor de contraseñas o lugar seguro
   fuera del repositorio. No los guarde en Documents/Codex ni en un chat o captura.
7. Vuelva a la pantalla de seguridad: debe indicar que la verificacion en dos pasos
   esta activada. No haga capturas de codigos, QR, contraseña o recuperacion.

## 2. Dar acceso solo a ERP-FACTORY

1. En el perfil de navegador de **Fernando**, abra fernandoruizm-maker/ERP-FACTORY.
2. Entre en **Settings** > **Collaborators** o **Manage access**. Confirme la contraseña
   o la verificacion adicional si GitHub se lo pide; hagalo usted, sin compartirla.
3. Pulse **Add people** / **Add collaborator**, busque el nombre definitivo de la
   cuenta nueva y compruebe que no esta eligiendo una persona de nombre parecido.
4. Si aparece un selector de rol, elija **Write**. Nunca **Admin** ni **Maintain**.
   En repositorios de una cuenta personal puede no existir selector de rol: la
   interfaz de colaboradores es diferente de la de organizaciones. Si no puede
   comprobar que el acceso resultante es de escritura sin administracion, detengase.
5. En el perfil de navegador de la **cuenta nueva**, abra la invitacion recibida
   y aceptela. Compruebe que menciona exactamente ERP-FACTORY y a su propietario.
6. Fernando vuelve a la lista de colaboradores y comprueba que la invitacion ya
   no esta pendiente. La cuenta no debe figurar como administradora ni propietaria.

Write no es un rol de "solo abrir PR": puede permitir otras acciones de escritura,
incluida integrar si la proteccion lo permite. Esta guia no afirma que el token o
el rol impidan por si solos integrar. Codex nunca integrara; hacen falta la regla
de main, las dos aprobaciones y la autorizacion expresa para la integracion humana.

## 3. Comprobar compatibilidad ANTES de crear el token

GitHub ha tenido una limitacion para tokens de grano fino de cuentas que solo son
colaboradoras de un repositorio perteneciente a otra cuenta personal. Aqui el
propietario es fernandoruizm-maker, no la nueva cuenta. **Tener Write no garantiza
que ERP-FACTORY aparezca en el selector del token.** No se verifico si esa limitacion
sigue afectando a esta combinacion concreta.

1. Desde la **cuenta nueva**, foto de perfil > **Settings** > **Developer settings**
   > **Personal access tokens** > **Fine-grained tokens** > **Generate new token**.
2. Revise **Resource owner** y **Repository access** antes de generar nada.
3. Debe poder elegir el propietario correcto y **Only select repositories**,
   seleccionando SOLO **fernandoruizm-maker/ERP-FACTORY**.
4. Si solo aparece la cuenta nueva como propietaria, si no aparece ERP-FACTORY,
   o si solo ofrece lectura de repositorios publicos: **DETENGASE**. Ese token
   no cumple el objetivo, aunque la cuenta sea colaboradora.

En ese caso no generar un token clasico, no elegir todos los repositorios, no usar
el token personal de Fernando, no trasladar el repositorio ni instalar una App
como solucion automatica. Informar solo del bloqueo y de las opciones visibles,
sin secretos. Fernando debera autorizar otro diseño compatible. Los pasos de token
y conexion siguientes son CONDICIONALES a superar esta comprobacion.

## 4. Crear el token de grano fino, si el paso anterior es compatible

1. Nombre sugerido: **Codex ERP-FACTORY - ramas y PR**.
2. Propietario y repositorio: los comprobados arriba; **Only select repositories**,
   con ERP-FACTORY como unica seleccion.
3. Caducidad propuesta: **30 dias**. Limita el tiempo de uso si se pierde el token
   y permite una primera revision mensual. Al vencer, el acceso debe fallar;
   no quitar la caducidad ni renovarlo automaticamente. Fernando decide cada renovacion.
4. En **Repository permissions**, configure unicamente:

   | Permiso | Nivel |
   |---|---|
   | Contents | Read and write |
   | Pull requests | Read and write |
   | Metadata | Read-only; puede aparecer concedido automaticamente |

5. **Workflows, Administration, Secrets y todos los demas permisos:** sin acceso.
   Ningun permiso adicional de cuenta ni acceso a otros repositorios.
6. Revise el resumen completo antes de **Generate token**. Si GitHub exige un
   permiso mayor, detengase: no aceptar un conjunto distinto para que funcione.
7. Copie el token solo al cuadro seguro de credenciales indicado en el paso 5,
   o temporalmente a un gestor de contraseñas de su confianza. No lo pegue en un
   comando de PowerShell, chat, URL remota, archivo del repositorio ni captura.
   No lo muestre a Codex. Si no dispone aun del cuadro seguro, puede cancelar y
   generar el token cuando vaya a configurarlo para no dejarlo expuesto.

Sin Workflows, una subida que cambie archivos de .github/workflows puede rechazarse.
Eso no se arregla ampliando el token: el contenido a publicar debe respetar el
alcance autorizado. La lectura publica de otros repositorios es posible para
cualquiera; "solo ERP-FACTORY" limita la concesion del token, no la lectura anonima.

## 5. Aislar la configuracion de este clon en Windows

**No se realiza ahora.** Estos cambios locales se haran por Fernando en la etapa
posterior. No use git config --global, no cambie la sesion global de GitHub Desktop
ni borre entradas existentes de Fernando en el administrador de credenciales.

La carpeta exacta es:

    C:\Users\ferna\Documents\Codex\2026-11-05\task\ERP-FACTORY-correcciones

### Preparar el gestor de credenciales

1. Abra esa carpeta en el Explorador y active **View > Show > Hidden items** si
   no ve .git. Compruebe dos veces el nombre: no es factoria-2 ni el ERP.
2. En una terminal de PowerShell abierta en esa carpeta, puede consultar:

       git credential-manager --version

   Esto debe mostrar una version local de Git Credential Manager. Si no existe,
   detengase. No descargar ni instalar otro gestor como parte de esta guia.
3. Anote para usted los valores actuales de identidad global, sin cambiarlos:

       git config --global --get user.name
       git config --global --get user.email

   Que no exista alguno es valido. No copiar ni mostrar toda la configuracion;
   otras entradas podrian contener informacion privada.

### Identidad y opciones locales, sin guardar el token en Git

4. Desde la cuenta nueva en GitHub, abra **Settings > Emails**. Verifique el correo
   nuevo. Para no publicar su direccion real, active la opcion de mantenerla privada
   y copie la direccion **noreply** que GitHub muestre. No invente su numero o formato.
5. Abra **solo** el archivo `.git\config` de esta carpeta con el Bloc de notas.
   No abra ni edite el archivo global `.gitconfig` de su carpeta de usuario.
6. Mantenga las secciones existentes, en especial los remotos y el envio DISABLED.
   Si ya hay secciones user o credential, ajuste sus valores locales sin duplicar
   opciones contradictorias. Si no sabe interpretarlas, detengase y solicite ayuda
   mostrando solo nombres de opciones, nunca secretos.
7. Las opciones locales que se necesitan son estas. Sustituya los dos marcadores
   de identidad antes de guardar. **No hay ningun lugar para el token en este texto.**

   ```ini
   [user]
       name = NOMBRE_DEFINITIVO_DE_LA_CUENTA
       email = DIRECCION_NOREPLY_COPIADA_DE_GITHUB
   [credential]
       helper =
       helper = manager
       useHttpPath = true
       credentialStore = wincred
       gitHubAuthModes = pat
   [credential "https://github.com"]
       username = NOMBRE_DEFINITIVO_DE_LA_CUENTA
   ```

   La primera linea helper vacia anula para este clon los gestores heredados;
   la siguiente selecciona Git Credential Manager. useHttpPath pide distinguir la
   ruta del repositorio; username selecciona la cuenta nueva; wincred solicita el
   almacen seguro de Windows y pat la entrada de token. La compatibilidad exacta
   de estas opciones debe comprobarse con la version instalada: si no se respetan,
   detenerse, no cambiar valores globales ni pasar a guardar contraseñas en texto.
8. Guarde el archivo. No cambie remote.origin.url ni remote.origin.pushurl.
   Tampoco escriba el token en .git/config: aunque no se suba normalmente, es texto plano.

### Introducir y comprobar la credencial sin exponerla

9. La autenticacion de escritura se comprobara **solo en la prueba autorizada del
   paso c de PUBLICACION.md**, despues de proteger main. El envio sigue DISABLED
   hasta esa autorizacion. No haga un push ahora "para probar el token".
10. En esa prueba, Git Credential Manager debe pedir la credencial de la cuenta
    nueva. Pegue el token exclusivamente en su cuadro de token/contraseña. Si ofrece
    entrar como Fernando o reutiliza su cuenta personal, cancele. No acepte cambiar
    la cuenta global como solucion. No active registros de depuracion de credenciales.
11. Abra en Windows **Control Panel > Credential Manager > Windows Credentials**
    y mire solo los nombres de las entradas, sin revelar contraseñas. La nueva
    entrada debe permitir distinguir la cuenta nueva y el destino de este proyecto.
    El nombre exacto depende del gestor. Si parece una credencial generica reutilizable
    para todos los repositorios, no considere verificado el aislamiento. No borre
    entradas personales existentes. Detengase para revisar el gestor.
12. En la carpeta correcta, compruebe el origen de las opciones no secretas:

       git config --show-origin --get user.name
       git config --show-origin --get user.email
       git config --show-origin --get credential.useHttpPath
       git config --show-origin --get-urlmatch credential.username https://github.com/fernandoruizm-maker/ERP-FACTORY.git
       git config --local --get-all credential.helper
       git config --local --get credential.credentialStore
       git config --local --get credential.gitHubAuthModes

    Nombre/correo y opciones locales deben proceder de .git/config de este clon;
    useHttpPath debe ser true, usuario el nuevo, gestor manager, almacen wincred,
    modo pat. Vuelva a consultar los dos valores globales del punto 3: deben ser
    los mismos. Esto comprueba configuracion, no que una autenticacion remota haya
    tenido exito ni que el gestor realmente haya almacenado la credencial como se pide.
13. En la PR de prueba, compruebe **quien la abrio**: debe ser la cuenta nueva.
    El nombre que figura en un commit no prueba quien se autentico. Un fetch de un
    repositorio publico tampoco lo demuestra, porque puede ser anonimo.

No usar `git credential fill`, `git credential-manager get`, volcados del entorno
ni comandos que impriman el token para verificarlo. No capturar la pantalla mientras
se muestra un secreto. Borre el portapapeles y su entrada del historial de portapapeles
si se guardo alli, despues de almacenarlo de forma segura.

**Limite del aislamiento:** la configuracion es local al clon; el secreto se guarda
en el almacen protegido de Windows, no dentro de la carpeta. Eso no crea una barrera
fisica que impida a otro proceso de su misma sesion usar una credencial accesible.
El limite al repositorio debe imponerlo tambien GitHub mediante el token. No afirmar
que una credencial solo puede usarse desde una carpeta por tener opciones locales.

## 6. Nombre y correo de los commits de Codex

Para los commits FUTUROS de esta carpeta: nombre publico de la cuenta de maquina
(por ejemplo, fernando-codex si ese es el definitivo) y el noreply de esa cuenta.
El correo debe ser el que GitHub le asigne; no usar el de Fernando ni FERRUMTJA.
No reescribir los commits locales anteriores para cambiar su autor. Esta tarea
documental conserva la identidad local de trabajo ya utilizada, no suplanta una
cuenta nueva que todavia no existe. Identidad del commit y cuenta que abre una PR
son cosas diferentes; hay que comprobar ambas cuando se autorice la prueba.

## 7. Revocar acceso si algo va mal

1. Detenga nuevas subidas. Si el token se expuso, no lo pruebe ni lo pegue para que
   alguien confirme si funciona: desde la cuenta nueva vaya a Settings > Developer
   settings > Personal access tokens > Fine-grained tokens y elimine/revoque ese token.
2. Desde la cuenta de Fernando, ERP-FACTORY > Settings > Collaborators/Manage access:
   quite la cuenta nueva del repositorio. Confirme que ya no aparece con acceso.
3. Solo si puede identificarla sin duda, quite del Administrador de credenciales de
   Windows la entrada de ESTA cuenta/proyecto. No borre credenciales de Fernando.
4. Fernando puede retirar las opciones user/credential que agrego en el .git/config
   de este clon, sin modificar otros apartados ni el archivo global. Dejar de tener
   una identidad local explicita puede volver a heredar la de Fernando: mantenga el
   trabajo de publicacion detenido, no continue con esa identidad accidentalmente.
5. Restablecer el envio DISABLED, cerrar las PR abiertas o revertir cambios requiere
   la autorizacion correspondiente; se prepara una reversion por PR, nunca force push.
   Quitar una cuenta o token no deshace automaticamente commits ya enviados.
6. Revise con Claude los cambios efectuados durante el incidente sin mostrar secretos.
   Generar un reemplazo, cambiar permisos o volver a habilitar acceso requiere una
   nueva autorizacion; no se renueva ni se amplian permisos automaticamente.

## Antes de seguir

La cuenta definitiva, compatibilidad del token para este propietario, funcionamiento
del gestor local y proteccion real de main siguen SIN VERIFICAR. Si no se puede
cumplir exactamente el alcance del token o el aislamiento, no continuar con la subida.
