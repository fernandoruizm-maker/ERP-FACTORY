# Guia para Fernando y FERRUMTJA

Una PR es una propuesta de cambios. Aprobar una propuesta no activa la fabrica
ni autoriza usar datos reales. Claude revisa la parte tecnica en el chat; Fernando
y FERRUMTJA comprueban que el resultado sirve para el negocio y la contabilidad.

## Aprobaciones por niveles: decision vigente de Fernando

| Propuesta | Aprobacion necesaria |
|---|---|
| Cambios de la propia fabrica en fernandoruizm-maker/ERP-FACTORY | Fernando, como negocio: 1 |
| Producto con impacto contable | Fernando y FERRUMTJA, negocio y contabilidad: 2 personas distintas |

Antes de revisar, comprobar en la propuesta a que repositorio/producto pertenece
y si afecta asientos, saldos, stock valorado, impuestos, cobros o comprobantes.
Un producto no se convierte en cambio de la fabrica por usarla para construirse.
Si el destino o el impacto no estan claros, no aprobar: pedir su clasificacion.
Para productos declarados sin impacto contable no se ha decidido otro nivel;
la puerta local los mantiene bloqueados, sin suponer una excepcion.

Este cambio modifica la puerta local. **No cambia las reglas de GitHub.** La
regla y plantilla anteriores exigen 2; no se han consultado ni modificado en esta
tarea. Si GitHub pide 2 para ERP-FACTORY, detener la integracion y pedir a Fernando
autorizar una actualizacion de esa regla, sin excepciones ni integracion forzada.

## Dos reglas que nunca se saltan

- **La cuenta fernandocodex64-sudo NUNCA aprueba ni integra.** Puede abrir las PR.
  fenando-codex es su nombre visible; no es la cuenta personal de Fernando.
- **Nadie integra sin decision expresa de Fernando despues de la revision de
  Claude del SHA vigente, aunque GitHub muestre el boton disponible.** Las
  aprobaciones del nivel correspondiente no sustituyen esa decision. No activar integracion automatica.

Si una propuesta dice NO INTEGRAR, se cierra sin integrar. La prueba de proteccion
no es una entrega del producto. Ante una duda, no pulse el boton de integrar.
Fernando decide con su cuenta personal; FERRUMTJA no integra por iniciativa propia.

## Antecedente: PR unica de bloques 1 a 7

La entrega propuesta agrupa los siete bloques, incluye el revisor automatico
aparcado sin activarlo y elimina el aviso de prueba dentro de la misma PR.
No integrar por separado la retirada anterior. Las revisiones previas de Claude
no prueban que ya reviso el nuevo SHA combinado: comparar el informe de revision
final con el SHA exacto propuesto. Fernando decide expresamente despues de esa
revision y de las aprobaciones entonces exigidas. Para cambios nuevos se aplica
el esquema por niveles de arriba; que el boton este disponible no basta.

## Fernando: revision de negocio

- La propuesta explica que problema resuelve y que cambia para el usuario.
- Lo mostrado coincide con lo que pidio el cliente; no agrega acciones inesperadas.
- Los ejemplos son ficticios y permiten ver el resultado, incluidos los errores.
- Se entiende quien puede solicitar, aprobar y consultar cada operacion.
- Estan explicados los limites, lo que falta probar y como volver atras.
- Claude no dejo la conclusion CORREGIR y reviso exactamente la version propuesta.

## FERRUMTJA: revision contable y funcional

- Asientos: cuentas, fechas, debe y haber correctos; una operacion no se registra dos veces.
- Saldos: saldo inicial + entradas - salidas = saldo final; el detalle coincide con el total.
- Cuadres: libros, reportes y movimientos coinciden. Las diferencias quedan visibles.
- Documentos: comprobante identificable, datos coherentes y relacion con la operacion.
  Los comprobantes de ensayo se distinguen de documentos reales; no se afirma validez fiscal.
- Correcciones: una anulacion o devolucion conserva la historia y ajusta saldos correctamente.
- Permisos por area: una persona solo puede ver y aprobar lo que le corresponde;
  no puede aprobar su propia solicitud cuando la regla del negocio lo prohibe.
- Casos de error: falta de stock, duplicados, fechas incorrectas y datos incompletos
  se rechazan sin alterar saldos. Solicitar demostraciones ficticias cuando haya dudas.

## Comprobar que Claude vio la misma version

El SHA es el identificador de una version: una cadena de 40 letras y numeros.
No hace falta programar para compararlo. No basta comparar solo los primeros siete.

1. Abra la PR y entre en la pestaña **Commits** (cambios guardados).
2. Abra el ultimo cambio de la rama propuesta. Use el boton para copiar su SHA
   completo; si solo ve un identificador corto, abra el detalle del cambio.
3. Compare los 40 caracteres con **SHA revisado / reviewed_sha** del informe de Claude.
   Si no logra ver el completo, pida a Codex que lo muestre; no adivine ni apruebe.
4. Compruebe tambien que el informe identifica esa PR y sus archivos. Revise
   **Files changed** (archivos cambiados) para reconocer que el alcance coincide.
5. Si se subio un cambio despues de la revision, pida a Claude revisar el nuevo SHA
   y vuelva a comprobarlo. Un cambio solo de documentacion tambien cambia el SHA.

Los nombres y botones de GitHub no se han contrastado en linea en esta tarea.
La revision automatica esta aparcada: no espere un informe automatico nuevo.

## Cuando NO aprobar

- Claude concluyo CORREGIR, el SHA no coincide o la revision no cubre la propuesta.
- Faltan resultados de pruebas o se presentan simulaciones como pruebas reales.
- Hay diferencias contables, permisos incorrectos o datos reales de clientes/ERP.
- Le piden saltarse una regla, ignorar una conversacion abierta o aprobar sin comprender el efecto.
- Se pretende conectar el ERP o usar datos reales sin auditoria tecnica externa previa.

Cuando todo este claro, cada persona usa su propia cuenta: **Files changed >
Review changes > Approve**. No comparta cuentas ni contraseñas. Si falta algo,
seleccione **Request changes** o deje la propuesta pendiente. Nadie aprueba por Claude.

El autor de una PR no puede ser uno de sus propios aprobadores. Para las PR de
esta via, Fernando abre la propuesta desde la web con **fernandocodex64-sudo**.
Para revisar y aprobar cambia a su cuenta personal **fernandoruizm-maker**;
FERRUMTJA usa la suya. No aprobar ni integrar desde la sesion de la cuenta de maquina.
En ERP-FACTORY debe figurar Fernando; en productos contables deben figurar Fernando
y FERRUMTJA. Dos aprobaciones cualquiera no prueban que sean negocio y contabilidad.
No crear excepciones para saltarse la regla configurada en GitHub.

Antes de integrar, Fernando debe dejar una decision expresa para esa PR y su SHA
completo, despues de la revision de Claude y con las aprobaciones de su nivel vigentes.
Solo entonces Fernando o FERRUMTJA, desde su cuenta personal, puede integrar.
Si cambia el SHA, detenerse: nueva revision y nueva decision. Codex nunca integra.
La disponibilidad del boton de GitHub no es una instruccion ni una autorizacion.
