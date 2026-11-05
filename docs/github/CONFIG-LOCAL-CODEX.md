# Configuracion local futura: instrucciones para Codex

**NO EJECUTADO. Requiere autorizacion expresa posterior.** Este documento no
habilita cambios, red, lectura de secretos ni publicacion. Envio actual: DISABLED.
Fernando no debe editar archivos ni ejecutar comandos. Claude verificara en
lectura las opciones no secretas y los resultados de la prueba autorizada.

## Alcance exacto

- Clon: C:\Users\ferna\Documents\Codex\2026-11-05\task\ERP-FACTORY-correcciones.
- Cuenta: **fenando-codex**, sin la primera r; no usar fernando-codex.
- Repositorio: fernandoruizm-maker/ERP-FACTORY, publico.
- Identidad de commits futuros: nombre fenando-codex y correo noreply real que
  GitHub asigne a esa cuenta (pendiente de obtener sin secretos). No inventar
  ID/correo ni reescribir autores de commits anteriores.
- Token clasico creado por Fernando: solo public_repo, 30 dias. Codex no lee,
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
5. Confirmar el correo noreply real de fenando-codex y que el token aun no se haya
   compartido. No pedir su valor. Si se necesita consultar GitHub, solicitar primero
   autorizacion de lectura; no dar por verificada una identidad solo por su nombre.

## Aplicar solamente opciones locales autorizadas

6. Fijar user.name=fenando-codex y user.email al noreply confirmado, solo en este
   clon. No ejecutar cambios con --global o --system ni cambiar GitHub Desktop.
7. Configurar Git Credential Manager para este clon: reinicio local de la lista
   heredada de helpers con entrada vacia y helper manager; useHttpPath=true;
   almacen Windows wincred y modo de token pat, si la version instalada los admite.
   Asociar el usuario fenando-codex al destino HTTPS de ERP-FACTORY mediante una
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
13. El acceso Git no autentica por si solo una herramienta de PR ni una sesion web.
    Para abrir la PR, usar solo un metodo autorizado que identifique fenando-codex;
    no extraer el token del gestor para pasarlo a otra herramienta ni cambiar una
    sesion global. Si no hay una via autorizada, detener esa parte y comunicarlo.
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
   desde su cuenta de maquina; puede retirar a fenando-codex del repositorio.
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

## Limites actuales

Ninguno de estos pasos se ejecuto en la actualizacion documental. No verificados
version/comportamiento del gestor, correo noreply, autenticacion, almacenamiento,
aislamiento efectivo ni PR de prueba. Los avances de cuenta y ruleset proceden
del informe de Fernando; Codex no accedio a red para confirmarlos.
