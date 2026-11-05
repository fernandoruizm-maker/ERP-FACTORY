# Estado de la segunda fábrica · 5 de noviembre de 2026

## Entrega

Instalación local en `C:\Users\ferna\Documents\Codex\2026-11-05\task\factoria-2`.
No es un servicio Ubuntu instalado o habilitado. No existe consumidor nuevo de GitHub ni despliegue.

Referencia de origen: ZIP SHA-256 `9924878c35d6ffa23e15ef2d619d6ece1b8bed936f966b5a69eaa5cc65b53ba2`, previamente cotejado 53/53 con Ubuntu. Solo se extrajo `codigo/` a `upstream/`; no se copiaron configuración operativa, estado histórico o credenciales. La fábrica original, pausa Windows, doble aprobación y protecciones GitHub no se modificaron.

## Verificación ejecutada

- 35 pruebas Python de la nueva implementación: PASS, cero fallos, errores u omisiones. Registro: `outputs/test-factory.txt`.
- Piloto: 7 pruebas de dominio Python, incluidas en las 35 anteriores; 5 JavaScript y 3 TypeScript adicionales: PASS. Total de casos distintos ejecutados: 43.
- Piloto: stock inicial 10, final 0, un movimiento; repetir devuelve el mismo comprobante. Reapertura del estado ficticio conserva saldo e identidad de salida. Impresión no altera estado.
- Controles ensayados: otra área, autoaprobación, falta de aprobación, cantidades inválidas, saldo insuficiente, duplicados, rutas fuera de alcance, catálogo sin autorización o huella válida, presupuesto concurrente, permiso vencido o de otro contenido, ausencia de credencial, respuesta truncada, timeout incierto, revisión de otra versión, aceptación desactualizada, falta de revisión de la fábrica y revisión parcial.
- Las pruebas de proveedores usan dobles simulados y una cadena ficticia de prueba. No acreditan integración real con Anthropic o Codex CLI.
- Estado local observado: desactivado; 0 tareas, 0 llamadas, 0 llamadas inciertas. Sin conexiones externas.
- Runtime usado: Python proporcionado por Codex, Node v24.22.1. TypeScript ejecutado con `--experimental-strip-types`, sin comprobación estática de tipos.

## Incidencias resueltas durante las pruebas

El aislamiento del ejecutor denegó escrituras en sus temporales. Se solicitó y obtuvo ejecución autorizada de las pruebas, sin cambiar permisos o desactivar permanentemente el aislamiento. No se intentó limpiar manualmente las rutas denegadas.

La ejecución autorizada reveló conexiones SQLite que no se cerraban explícitamente, causando WinError 32 al retirar temporales. Se corrigió el gestor de conexiones para confirmar/revertir y cerrar en todos los casos. Las pruebas completas posteriores pasan. El primer ensayo del piloto, antes de crear su módulo, falló por módulo ausente; no se presenta como prueba de detección de un defecto de negocio.

## Pendientes y límites

1. Claude NO ha revisado todavía ni el producto ni la fábrica. Los paquetes locales de `outputs/revision-claude/` están preparados para revisión, con estado NOT_RUN, y no se transmitieron.
2. Fernando eligió GitHub Actions, el repositorio `fernandoruizm-maker/ERP-FACTORY` y su suscripción de Claude si es compatible. Se comprobó que el repositorio existe y es público. Fernando autorizó mantenerlo público y publicar el código. Pendientes: plan de Claude, credencial OAuth, modelo, contenido autorizado para Anthropic y presupuesto. Hay un borrador desactivado en docs/actions; no hay workflow instalado, App nueva, secreto generado ni integración activada.
3. No se accedió al ERP. La comparación real permanece pendiente; se comprobó solo el comparador con evidencia ficticia.
4. No se ejecutó el adaptador Docker ni se descargaron imágenes. Se probaron sus restricciones de comando; falta validarlas en un motor e imagen aprobados. No ejecutar propuestas de modelos en el host.
5. No se ejecutaron los tests del código `upstream` ni se certificó la fábrica heredada completa. Se preserva como referencia verificada y se incluye en los paquetes de revisión.
6. Los registros de aceptaciones locales no autentican a personas; falta vincular identidades y evidencia del proveedor en un entorno operativo. Ninguna puerta de esta entrega concede permiso de publicar.
7. El comprobante HTML se generó y su contenido se comprobó mediante pruebas; no se hizo revisión visual de paginación ni prueba de impresora.
8. Límites por llamadas, tamaño y tiempo no equivalen a un límite monetario contractual. No se midió consumo de proveedores porque no hubo llamadas.
9. La restauración completa en otra máquina y el cambio de fábrica activa requieren una etapa posterior autorizada. Nunca activar las dos fábricas a la vez.

## Continuidad

La implementación local y sus pruebas están entregadas. La conexión elegida es GitHub Actions, empezando por una revisión de la propia fábrica en ERP-FACTORY mediante suscripción Claude. La publicación pública está autorizada; falta completar autenticación. No se necesita tocar el ERP para esa revisión. Cualquier autorización futura debe delimitar los archivos enviados, proveedor/modelo, costo y destino; los paquetes permiten revisar el alcance antes de transmitir.
