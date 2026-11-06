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

## Propuesta breve para la fabrica nueva (NO implementada)

1. En una futura PR autorizada, admitir un registro simple de retiro declarado:
   fecha, responsable, VM eliminada, App ID 5603415 retirada, inventario Windows,
   estado OpenAI confirmado y archivo=NO_POR_DECISION_DE_FERNANDO. No exigir archivo
   ni firmas; identificar la evidencia como declaracion, no como autenticacion tecnica.
2. Sustituir el bloqueo de coordinacion solo cuando ese registro este completo y
   Fernando autorice expresamente el cambio. Datos pendientes o contradictorios
   mantienen BLOCKED. Probar esos casos; no convertir la declaracion en prueba remota.
3. Si se restaura/recrea la original o se le devuelven accesos, invalidar el registro
   y bloquear la nueva antes de permitir cualquier operacion paralela.
4. Conservar candado, revision, dos aceptaciones, presupuesto y permisos restantes:
   resolver la coordinacion no activa fabrica, proveedores, publicaciones ni ERP.

**Hoy ORIGINAL_COORDINATION_NOT_VERIFIED permanece intacto.** No se cambia codigo,
configuracion ni comportamiento. La fabrica nueva sigue desactivada. Esta tarea
solo actualiza documentos locales; no consulta red, no revoca nada y no publica.
