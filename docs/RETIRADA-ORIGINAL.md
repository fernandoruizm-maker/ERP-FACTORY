# Retirada de la fabrica original: registro de Fernando

Fecha declarada: **5 de noviembre de 2026**. Responsable: **Fernando**.
Fernando comunica la retirada completada. Codex registra su declaracion, sin
repetir consultas a VirtualBox, Ubuntu, GitHub ni proveedores en esta tarea.
Este registro sustituye la guia de pasos pendientes; la historia se conserva en Git.

## Acciones y decisiones comunicadas

| Elemento | Resultado registrado | Fuente |
|---|---|---|
| rdc | 0 PR abiertas y 25 cerradas; queda archivado; reglas sin cambios | Fernando |
| VM RDC-Piloto-Aislado | Exportada a OVA sin errores y despues eliminada de VirtualBox por decision de Fernando | Fernando |
| Archivo oficial | **SIN ARCHIVO**, por decision expresa de Fernando; el OVA no se conserva como respaldo oficial | Fernando |
| Windows | No se identificaron tareas ni servicios propios de la fabrica en el inventario anterior | Inventario acotado de Codex |
| pilot.pause | Se conserva | Fernando; su existencia se observo en el inventario anterior |
| GitHub App RDC Factory Fernando | Eliminada, junto con su clave y su instalacion en rdc; **App ID 5603415** | Fernando |
| OpenAI | **No existia** clave de OpenAI de la fabrica original; no corresponde revocacion | Confirmacion expresa de Fernando |

No se interpreta la eliminacion de VirtualBox como prueba de borrado de todos los
discos, instantaneas, copias o del OVA. No se verificaron esas ubicaciones. Tampoco
se afirma una auditoria de todos los procesos o componentes de Windows: el alcance
del inventario previo esta en el [anexo tecnico](RETIRADA-ORIGINAL-ANEXO-TECNICO.md).

## Decision expresa: retirada SIN ARCHIVO

La instruccion nueva sustituye el plan anterior de conservar una VM original y
un archivo oficial. Se registra la decision, sin crear una copia alternativa ni
borrar nada mas. No hay respaldo oficial disponible para prometer una restauracion.
No consta comprobacion de recuperacion del OVA ni archivo final de SQLite/trabajos.
El historial de rdc queda segun lo comunicado por Fernando; no se ha consultado.

No se usan las antiguas instrucciones de conservar/exportar la VM como tareas
pendientes ni como motivo para revertir esta decision. El anexo largo es historico.
La App original se declara retirada. Fernando confirma que no existia clave de
OpenAI de esta fabrica; ese punto ya no esta pendiente. No se hizo una auditoria
remota de credenciales ni se revoco ninguna clave en esta actualizacion.

## Registro implementado localmente en el bloque 8

[retirada-original.json](retirada-original.json) recoge esta declaracion sin
secretos ni firmas. `kind=DECLARACION_NO_AUTENTICADA` y
`provenance_authenticated=false`: comprobar su coherencia no autentica a Fernando
ni demuestra de nuevo el estado de VirtualBox, Windows o GitHub.

El Coordinator relee el registro antes de tomar el candado, despues de tomarlo
y antes de reservar cada llamada. Tambien lo comprueba antes de `recover()`.
Sustituye `ORIGINAL_COORDINATION_NOT_VERIFIED` por esta comprobacion: ausencia,
campos incompletos, datos invalidos o contradictorios mantienen BLOCKED.
`original_restored=true` bloquea con `ORIGINAL_RESTORED`.

Antes de restaurar/recrear la original o devolverle accesos, Fernando debe pedir
que se marque `original_restored=true`. El registro no detecta restauraciones
no comunicadas. Volver a `false` requiere comprobar y declarar otra vez la retirada;
no basta con borrar el aviso. No se exige archivo oficial ni sistema de firmas.

El candado sigue siendo obligatorio, situado junto al estado local de la fabrica.
Un resultado de una llamada ya reservada puede terminar de registrarse aunque
cambie la declaracion; no se autoriza una llamada nueva ni un reintento.
Se conservan revision, dos aceptaciones, presupuesto y permisos del ERP.
**La fabrica sigue desactivada; el registro no autoriza llamadas ni publicacion.**
Pruebas y limites del cambio local: [bloque-8.md](pr/bloque-8.md).
