# Retirar y archivar la fabrica original: guia corta

Solo es una guia: aun no se ha realizado ningun cambio operativo.
Decision: rdc no seguira desarrollandose; cerrar PR sin integrar y conservar sus reglas.
Inventario: RDC-Piloto-Aislado esta APAGADA, autostart desactivado y tiene una instantanea.
No la encienda solo para seguir estos pasos. La fabrica nueva sigue desactivada.

## 1. Cerrar las PR de rdc en la web
1. Fernando entra en GitHub con su cuenta personal y abre el repositorio rdc correcto.
2. Pulse Pull requests > Open; revise todas, incluidas las que estan en borrador.
3. En cada PR, guarde su numero/enlace y cierre con Close pull request, SIN integrar.
4. Conserve ramas, comentarios e historial. No cambie rulesets ni pulse Merge.
5. Anote cuantas habia y que no quede ninguna abierta. No confundir rdc con ERP-FACTORY.

## 2. Pausar, solo si estuviera funcionando
1. Si la VM sigue apagada, no hay nada que pausar: mantengala asi.
2. Si estuviera encendida y la fabrica ofrece un boton de pausa conocido, uselo.
3. Si no existe ese boton, Codex comprobara y solicitara la pausa con autorizacion
   especifica; Fernando no ejecuta comandos de Linux. Pausar VirtualBox congela la
   VM, pero no equivale a pausar de forma segura un trabajo o una llamada externa.

## 3. Confirmar que no quede trabajo en curso
1. Si hay una tarea visible en marcha, espere a que termine; no reinicie para probar.
2. La VM apagada no ejecuta tareas dentro, pero puede haber trabajos previos inciertos.
3. Codex, con autorizacion de lectura, reconciliara esos pendientes y los posibles
   procesos de Windows; no repetira trabajos ni encendera la fabrica automaticamente.
4. Si no puede confirmarse el fin del trabajo, detener la retirada y pedir ayuda.

## 4. Apagar y evitar el arranque automatico
1. Abra VirtualBox y seleccione RDC-Piloto-Aislado. Si dice Apagada, no haga nada mas.
2. Si estuviera encendida, use el apagado normal del menu del Ubuntu invitado o
   Maquina > Cerrar > Enviar señal de apagado. Espere a que aparezca Apagada.
3. No elija Guardar estado ni Apagar la maquina de forma forzada; si no responde,
   detengase y pida ayuda. No borre la VM ni sus discos o instantaneas.
4. El autostart de esta VM ya figura desactivado. Si cambia, Codex lo quitara solo
   con autorizacion, sin pedirle a Fernando que use comandos.
5. No se hallaron tareas Windows propias de la fabrica. Si despues se identifican,
   Codex las deshabilitara con autorizacion. No tocar Autopilot, Copilot ni VBoxSDS:
   son coincidencias del filtro, no workers confirmados de la fabrica.

## 5. Exportar la VM completa, sin borrar la original
1. Fernando elige un disco/carpeta privada y protegida, con espacio suficiente.
2. En VirtualBox: Archivo > Exportar servicio virtualizado; seleccione
   RDC-Piloto-Aislado y el destino elegido; exporte como archivo OVA.
3. Espere a que termine sin errores y anote ruta, fecha y tamaño. No marque opciones
   para enviar a la nube. No suba el OVA a GitHub ni lo adjunte a un chat.
4. El OVA puede contener datos y claves antiguas: mantengalo protegido. Conserva el
   estado actual, no el historial de instantaneas; por eso NO se borra la VM original.
5. Si falla, conserve la original y no marque la copia como valida. Una futura
   prueba de restauracion sera aparte, aislada y sin arrancar ambas fabricas.

## 6. Retirar credenciales, despues de apagar y comprobar la exportacion
1. En GitHub, cuenta propietaria de la App original: Settings > Developer settings >
   GitHub Apps > App correcta > Private keys. Identifique y revoque su clave privada
   sin mostrarla. Si afecta a otro sistema, detengase antes de revocar.
2. Cuenta/organizacion de rdc: Settings > Applications / Installed GitHub Apps >
   App original > Configure > Uninstall. Confirme la App y su alcance antes de quitarla.
3. No elimine la cuenta fernandocodex64-sudo ni sus credenciales; son de la nueva.
4. Si existia una clave OpenAI exclusiva: consola de OpenAI > proyecto correcto >
   API keys > clave identificada > Revoke/Delete. Si no sabe cual es o es compartida,
   pida ayuda y no borre otra. No muestre claves en capturas ni mensajes.
5. Si quedo un webhook independiente de la App, Codex explicara su baja por clics
   con autorizacion; no tocar integraciones ajenas. Guarde solo fecha y confirmacion.
6. No cambiar reglas de rdc: sus checks antiguos pueden quedar pendientes y eso es
   aceptable porque no habra nuevas integraciones. Los menus pueden variar; si duda, pare.

## 7. Dejar un registro sencillo en la fabrica nueva
1. Fernando comunica fecha, quien comprobo y resultado de los pasos 4, 5 y 6:
   VM apagada/autostart desactivado; archivo OVA terminado; App/clave/OpenAI retiradas
   o pendientes/no aplicables, con motivo. La ubicacion detallada queda en registro privado.
2. Codex lo anota, con autorizacion, sin claves ni firmas. Hoy este registro es solo
   documental: NO cambia ORIGINAL_COORDINATION_NOT_VERIFIED ni activa la fabrica nueva.
3. Si falta algo, registrar Pendiente. No afirmar retirada completa ni reactivar nada.
4. Para deshacer: conservar la VM y el archivo; pedir autorizacion antes de restaurar
   o arrancar. Las claves revocadas necesitan reemplazo, no se recuperan automaticamente.

Inventario y limites en [anexo tecnico](RETIRADA-ORIGINAL-ANEXO-TECNICO.md).
