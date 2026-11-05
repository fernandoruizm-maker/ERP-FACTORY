# Guia para Fernando y FERRUMTJA

Una PR es una propuesta de cambios. Aprobar una propuesta no activa la fabrica
ni autoriza usar datos reales. Claude revisa la parte tecnica en el chat; Fernando
y FERRUMTJA comprueban que el resultado sirve para el negocio y la contabilidad.

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

Importante: el autor de una PR no puede contar como uno de sus propios aprobadores.
Si la abre Fernando con su cuenta, faltara su aprobacion valida para llegar a dos.
No reduzca el numero ni cree una excepcion. Antes de publicar el flujo habitual
debe decidirse un autor distinto de ambas personas; no se crea aqui una cuenta
ni una aplicacion para resolverlo. Ademas, dos aprobaciones cualquiera no prueban
por si solas que sean estas dos personas: compruebe los nombres en la PR.

Integrar en main es un paso separado: siempre necesita autorizacion expresa de
Fernando y solo lo realiza una de las dos personas aprobadoras, nunca Codex.
