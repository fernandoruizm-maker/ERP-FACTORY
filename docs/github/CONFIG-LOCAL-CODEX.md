# Configuracion local: resultado e instrucciones para Codex

**Pasos 1 a 10: ajustes locales aplicados y verificados, sin red ni token.**
Usuario/correo confirmados por Fernando. La verificacion de Claude sigue pendiente.
Los pasos 11 en adelante requieren otra autorizacion. Envio actual: DISABLED.
Fernando no debe editar archivos ni ejecutar comandos. Claude verificara en
lectura las opciones no secretas y los resultados de la prueba autorizada.

## Alcance exacto

- Clon: C:\Users\ferna\Documents\Codex\2026-11-05\task\ERP-FACTORY-correcciones.
- Usuario real: **fernandocodex64-sudo**, ID **353061596**. Nombre visible:
  **fenando-codex**; no usarlo como usuario de autenticacion.
- Repositorio: fernandoruizm-maker/ERP-FACTORY, publico.
- Identidad local: nombre fernandocodex64-sudo y correo
  353061596+fernandocodex64-sudo@users.noreply.github.com, proporcionado por Fernando.
  No reescribir autores de commits anteriores.
- Token clasico futuro, que solo creara Fernando: solo public_repo, 30 dias. Codex no lee,
  recibe, almacena en archivos ni imprime el token. No usar el de Fernando.
- No modificar configuracion global/sistema, otras carpetas, upstream/, ERP,
  fabrica original, sesiones globales ni credenciales personales.

## Antes de modificar

1. Obtener autorizacion especifica para la configuracion de este clon. Separar
   esa autorizacion de rehabilitar el envio, publicar y abrir la PR de prueba.
2. Comprobar ruta real del clon y estado de trabajo. Inspeccionar solo opciones
   no secretas relevantes, con su origen y ambito; nunca volcar configuracion
   completa, variables de entorno ni almacenes de credenciales.
3. Registrar, fuera del repositorio, los valores anteriores y su presencia/ausencia
   de identidad y opciones del gestor que se cambiaran, sin secretos. No copiar
   todo el archivo de configuracion. Servira para reponer exactamente esos valores.
4. Comprobar version local del gestor y compatibilidad con seleccion por cuenta,
   ruta y almacen seguro Windows. Si no se puede lograr sin tocar opciones globales,
   detenerse. No instalar ni actualizar herramientas sin autorizacion adicional.
5. Confirmar el correo noreply real de fernandocodex64-sudo y que el token aun no se haya
   compartido. No pedir su valor. Si se necesita consultar GitHub, solicitar primero
   autorizacion de lectura; no dar por verificada una identidad solo por su nombre.

## Aplicar solamente opciones locales autorizadas

6. Fijar user.name=fernandocodex64-sudo y user.email al noreply confirmado, solo en este
   clon. No ejecutar cambios con --global o --system ni cambiar GitHub Desktop.
7. Configurar Git Credential Manager para este clon: reinicio local de la lista
   heredada de helpers con entrada vacia y helper manager; useHttpPath=true;
   almacen Windows wincred y modo de token pat, si la version instalada los admite.
   Asociar el usuario fernandocodex64-sudo al destino HTTPS de ERP-FACTORY mediante una
   seccion de credenciales acotada a ese destino. No crear opciones para otros
   repositorios ni usar el helper store (texto plano).
8. Verificar los valores efectivos y su origen local antes de cualquier conexion.
   Una opcion escrita no acredita que el gestor la respete. No cambiar remotos ni
   DISABLED en esta fase. No poner el token en configuracion, argumentos, URLs,
   variables de entorno persistentes, archivos del repositorio ni logs.
9. Si hay una credencial previa de Fernando que pudiera reutilizarse, no recuperarla,
   sustituirla ni borrarla. Detenerse y resolver la separacion con autorizacion.

## Verificacion con Claude y prueba posterior

10. Comparar los valores globales no secretos relevantes antes/despues: sin cambios.
    Revisar que identidad, helper, ruta, cuenta y almacen efectivos proceden de
    este clon. Comparar el estado local anterior y confirmar que no se modificaron
    remotos ni otras opciones. Claude revisa esa evidencia, sin valores secretos.
11. Solo bajo la autorizacion de la PR ficticia: rehabilitar el envio hacia el unico
    destino autorizado, sin token en URL. Dejar a Fernando introducir el token en
    la ventana segura del gestor; suspender capturas, lectura de UI y trazas mientras
    lo introduce. Si se ofrece la identidad personal, cancelar; no continuar con ella.
12. Verificar sin recuperar contraseñas que la entrada del gestor distingue cuenta
    y destino. Si solo queda una entrada generica compartida, no declarar aislamiento
    logrado. No usar comandos que devuelvan credenciales, como credential fill/get.
13. Via intermedia elegida: Fernando abre la PR de prueba y la del bloque 1 en
    la web, con su perfil de navegador de fernandocodex64-sudo. Codex solo sube la rama
    cuando se autorice y prepara titulo y texto para que Fernando los pegue.
    El acceso Git no autentica esa sesion web. No extraer el token del gestor para
    abrir PR ni usar la sesion personal de Fernando. gh queda para otra etapa.
14. Claude comprueba autor de PR, identidad de los commits nuevos y reglas efectivas.
    La consulta anonima de un repositorio publico no demuestra quien se autentico.
    Cerrar la PR sin integrar. Registrar SHA y resultados, sin secretos.

La configuracion por clon evita alterar la identidad habitual de Fernando; no
encierra fisicamente el token en esa carpeta. public_repo tampoco selecciona un
repositorio unico: sus posibilidades cambian con los accesos de la cuenta. No
ampliar colaboraciones ni confundir la proteccion de main con una limitacion del
alcance del token. No acreditar aislamiento o permisos efectivos sin comprobarlos.

## Reversion, tambien con autorizacion concreta

1. Detener toda publicacion. Si hay exposicion, Fernando revoca el token clasico
   desde su cuenta de maquina; puede retirar a fernandocodex64-sudo del repositorio.
2. Reponer solo los valores locales modificados usando el registro no secreto
   previo. Si una opcion no existia, retirar solo esa opcion; conservar los demas
   valores y helpers locales. No reemplazar todo el archivo ni tocar lo global.
3. Eliminar solo la credencial de maquina/proyecto identificada sin duda, si esta
   accion fue autorizada. No leer su valor ni borrar entradas personales.
4. Si el envio fue rehabilitado durante la prueba, restaurar DISABLED con la
   autorizacion correspondiente. Revocar un token no restaura por si solo el remoto.
5. Verificar que la configuracion local volvio al estado anterior y que lo global
   sigue igual. La identidad heredada podria volver a ser Fernando: mantener
   detenido el trabajo, nunca seguir publicando accidentalmente con esa cuenta.
6. Cerrar PR o revertir publicaciones solo con permiso; no force push ni borrados
   de historial. Registrar que se revirtio y lo pendiente, sin datos de credenciales.

## Resultado local (2026-11-05)

Fernando corrigio la cuenta: usuario **fernandocodex64-sudo**, ID **353061596**;
**fenando-codex** es solo el nombre visible. Comunica que Claude verifico por API
publica el usuario/ID y su presencia como Collaborator en ERP-FACTORY. Codex no
repitio esa consulta de red. El noreply exacto fue proporcionado por Fernando.

Git Credential Manager: version previamente observada
**2.9.1+6760f0ef069c994aa2bb1d703fb374986ee82a3e**. La consulta de ayuda local
fallo: sh.exe no pudo crear un objeto de Windows (NtCreateDirectoryObject,
0xC0000022). No se repitio ni se uso otra via. Las rutas de documentacion local
supuestas no existian. Se configuro Git directamente dentro del alcance autorizado;
la aceptacion de estas opciones por el gestor en uso real sigue NO VERIFICADA.
GitHub CLI no localizado en PATH en la comprobacion anterior; sin instalacion ni uso.

| Opcion local | Antes | Despues |
|---|---|---|
| user.name | Sin definir | fernandocodex64-sudo |
| user.email | Sin definir | 353061596+fernandocodex64-sudo@users.noreply.github.com |
| credential.helper | Sin definir | Entrada vacia que reinicia herencia, seguida de manager |
| credential.useHttpPath | Sin definir | true |
| credential.credentialStore | Sin definir | wincred |
| credential.gitHubAuthModes | Sin definir | pat |
| credential.https://github.com/fernandoruizm-maker/ERP-FACTORY.git.username | Sin definir | fernandocodex64-sudo |
| remote.origin.pushurl | DISABLED | DISABLED |

Comprobaciones: lectura de valores locales, origen local de las opciones y valores
efectivos para la URL HTTPS exacta de ERP-FACTORY. No se ejecuto ningun comando
para obtener, guardar o borrar credenciales. No hubo token ni conexion.
Se compararon SHA-256 antes/despues del archivo de configuracion global identificado
por Git (una fuente) y los valores globales de identidad: identicos. No se publican
su contenido ni el correo personal. No se modificaron los remotos.

Registros no secretos fuera del repositorio, para verificacion y reversion:
- ../entregas-locales/bloque-7-config-usuario-real-before.json
- ../entregas-locales/bloque-7-config-usuario-real-after.json

El registro anterior bloque-7-config-before.json corresponde a la preparacion
historica, cuando aun faltaba el noreply. Para revertir esta aplicacion, usar el
registro usuario-real: todas las opciones modificadas estaban ausentes localmente.
No retirar valores globales ni cambiar DISABLED. La reversion requiere autorizacion.
Claude aun no verifico esta aplicacion. Git reconoce los ajustes; esto no acredita
que Windows almacene/aisle una credencial como se espera ni que GitHub autentique.

## Etapa futura de gh: documentada, NO autorizada ni ejecutada

La via actual para ambas PR es la web, con Fernando como operador de fernandocodex64-sudo.
No instalar, autenticar ni usar gh ahora. Si se autoriza mas adelante:

1. Comprobar instalacion/version y ayuda local de gh. Instalarlo, si hace falta,
   requiere permiso separado. Su compatibilidad con public_repo NO esta verificada.
2. Preparar un directorio de configuracion exclusivo fuera del repositorio, por
   ejemplo C:\Users\ferna\AppData\Local\ERP-FACTORY-Codex\gh. No crearlo ahora.
   En cada proceso autorizado de gh establecer GH_CONFIG_DIR a esa ruta, solo
   para ese proceso o terminal, nunca como variable global persistente. No usar
   el directorio habitual de gh de Fernando ni ejecutar cambios globales de Git.
3. No heredar GH_TOKEN, GITHUB_TOKEN, GH_ENTERPRISE_TOKEN ni GITHUB_ENTERPRISE_TOKEN
   al proceso reservado: omitirlas sin consultar ni imprimir sus valores. No
   ejecutar auth setup-git: el gestor Git del clon se configura por separado.
4. Fernando abre su propia terminal para autenticar fernandocodex64-sudo, fuera de la
   captura/control de los asistentes, sin transcripcion ni trazas. Un procedimiento
   revisado para la version instalada debe pedir el token con entrada OCULTA
   (por ejemplo Read-Host -AsSecureString) y pasarlo a gh auth login --with-token
   solo por entrada estandar; nunca como argumento, variable persistente, archivo
   temporal, historial o texto visible. El valor en memoria solo vive el tiempo
   imprescindible y se libera al terminar. No construir ni ejecutar ese proceso
   ahora; Codex no lo introduce ni recibe el token.
5. El token sigue siendo clasico con SOLO public_repo. gh puede exigir otros
   permisos durante su validacion de inicio de sesion (por ejemplo repo/read:org/gist).
   No afirmar que lo acepta: comprobarlo en esa etapa autorizada. Si lo rechaza,
   pide mas permisos o usa otro flujo de autorizacion mas amplio, DETENERSE y
   conservar la via web. No ampliar scopes, cambiar token ni eludir la validacion.
6. Verificar antes que gh puede almacenar de forma segura sin caer en texto plano;
   no usar --insecure-storage. GH_CONFIG_DIR separa archivos de configuracion,
   pero no garantiza por si solo que el almacen de credenciales del sistema quede
   separado. Si reutiliza o afecta una identidad personal, cancelar; no borrarla.
   No inspeccionar hosts.yml ni otros archivos que pudieran contener el token.
7. Tras una autenticacion autorizada, comprobar solo la identidad de la cuenta y
   el repositorio mediante una consulta no secreta autorizada. Un estado local
   no demuestra autenticacion real. Claude verifica la cuenta autora de la PR.
   Nunca usar **gh auth token**, auth status --show-token, volcados, logs de
   depuracion ni cualquier comando que muestre el token. Codex tampoco extrae
   el token del almacen para pasarlo a otra herramienta.
8. Reversion: Fernando revoca el token en Tokens (classic) de fernandocodex64-sudo.
   Con autorizacion, cerrar solo la sesion de esa cuenta en el GH_CONFIG_DIR
   exclusivo y retirar solo sus datos identificados, sin tocar la sesion de
   Fernando. Salir de gh no revoca el token en GitHub: la revocacion se hace alli.
   Eliminar la variable de esa terminal/cerrarla; no cambiar variables globales.
   Mantener las subidas detenidas; no reactivar autenticacion automaticamente.

NO VERIFICADO: instalacion/autenticacion de gh, aceptacion de public_repo, entrada
oculta del flujo futuro, aislamiento real de su almacen, comportamiento del gestor
al autenticar, conexion Git y PR de prueba. No se consulto
red ni se probaron credenciales. Los avances remotos proceden de Fernando.
