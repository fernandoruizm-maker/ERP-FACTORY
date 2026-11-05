# Estado de la segunda fábrica · 5 de noviembre de 2026

## Actualizacion: conexion mediante Actions preparada

Nota posterior: en el clon ERP-FACTORY-correcciones se trabaja sobre la base
0cb1882, exclusivamente en ramas locales y con push deshabilitado. Bloque 1:
diagnostico tipado, SHA-256 y PARTIAL sin aprobacion; 60 pruebas Python, 5 JS
y 3 TS correctas, sin omitidas. GitHub y proveedores reales no verificados.
Ver docs/pr/bloque-1.md. Las entradas historicas siguientes no describen una
activacion actual ni autorizan conexiones. Factoria original y factoria-2 intactas.

Fernando confirma que guardo `CLAUDE_CODE_OAUTH_TOKEN` en GitHub. Su valor no se
leyo. Se preparo un workflow manual con referencias fijas, autorizacion por SHA,
revision estatica sin herramientas y validador de cobertura/informe. Las 42
pruebas Python actuales pasan, incluidas siete nuevas de la integracion.
No se ejecuto Claude ni se probo aun la autenticacion real. Ver
[pasos y limites](ACTIVAR-CLAUDE.md). La consulta a GitHub muestra `main` del
repositorio nuevo sin proteccion; no se modifico. La doble aprobacion operativa
en ese repositorio todavia no esta acreditada. El estado anterior se conserva
abajo como registro de la entrega inicial; el secreto ya no esta pendiente
segun la confirmacion de Fernando.

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
## Actualizacion: cuarto intento y correccion de entrega del informe

OAuth ya funciono en el run 41995251713. Claude proceso la solicitud pero termino
por limite de turnos, sin informe aceptable. No existe aun revision completa
acreditada. Registro: 3 turnos frente a 2 configurados, una denegacion y costo
estimado USD 1.039741. No se afirma que ese importe fuera facturado.

Se preparo una correccion que recibe JSON textual y conserva todas las
herramientas denegadas. Las 12 pruebas locales del modulo Actions pasan.
No se ejecuto un quinto intento. Ver [evidencia y limites](CORRECCION-INFORME.md).
Las entradas anteriores son historicas y no sustituyen esta actualizacion.

## Actualizacion: quinto intento autorizado

Se integro PR #4 y termino el run 41996918613: Claude completo la llamada en un
turno, sin denegaciones, con USD 1.0870979 estimados. El validador rechazo el
resultado, por lo que no hay informe de revision aceptado. El diagnostico
generico no permite conocer la regla exacta que fallo.

Se preparo una correccion local del diagnostico, sin relajar la validacion.
Las 14 pruebas del modulo Actions pasan; no se hizo un sexto intento.
Ver [evidencia, integridad del artefacto y limites](QUINTO-INTENTO.md).



## Bloque 2: borrador privado local, sin ejecucion remota

Carpeta nueva ERP-FACTORY-revision/, en rama local independiente desde 0cb1882.
Un trabajo confiable privado; candidato publico leido como tar/JSON sin ejecutar.
Workflow bloqueado, politica desactivada y pin privado revisado pendiente.
23 pruebas privadas + 49 Python de base + 5 JS + 3 TS aprobadas (80, sin fallos ni
omitidas). Ver comandos y limites en docs/pr/bloque-2.md. No verificados Actions,
visibilidad de artefactos, minutos consumidos, proveedores o identidades. No se
creo repositorio, no se movieron secretos, no se publico ni se activo la fabrica.

### Ajuste adicional del bloque 2

Los fallos tempranos de archivo de ejecucion o verificacion del material producen
ahora artefactos BLOCKED con codigos fijos y huellas, sin texto del proveedor.
Resultado final: 31 pruebas privadas + 49 Python de base + 5 JS + 3 TS = 88,
sin fallos ni omitidas. El primer ensayo del cambio detecto una concatenacion
incorrecta, corregida y comprobada al repetir la suite privada completa.
Publicacion futura: exportar solo ERP-FACTORY-revision/ al repositorio PRIVADO;
no fusionar esta rama en ERP-FACTORY. Bloque 3 partira de la rama 2 actualizada.
El retiro del validador/workflow publico y secreto se reserva para la migracion
autorizada al revisor privado. Ver orden y reconciliacion documental en la PR local.

### Conservacion restringida autorizada por Fernando

Respuestas no validadas solo para los codigos de formato/version/evidencia
autorizados, tras comprobar evento exitoso, tamaño y SECRET_PATTERN del original.
Se guardan exactamente en response.unvalidated.txt privado con huella; el informe
sigue BLOCKED y no incluye el texto. Sin revalidacion ni reintento automaticos.
57 pruebas privadas + 49 Python de base + 5 JS + 3 TS = 114 aprobadas, sin fallos
ni omitidas. La futura base local del bloque 3 debe contener tambien el bloque 1
y pasar sus suites completas antes de añadir funcionalidad de revision por partes.

### Base combinada verificada para iniciar el bloque 3

Bloque 1: b0da873b1dc3ff37bbafdf93eb6b8027d911885e.
Bloque 2 completo: f28844123d62cf0a491875c713cdc3fc8fce3d05, incluido a8cfa18.
Integracion solo local en fix/bloque-3-cobertura, conservando ambos registros de
estado. Sin cambios nuevos de codigo: suites completas 57 privadas + 60 raiz +
5 JS + 3 TS = 125 aprobadas, sin fallos, errores u omitidas. No hubo red,
proveedores, publicacion o activacion. La implementacion del bloque 3 sigue pendiente.


## Bloque 3: protocolo privado local por partes

Base combinada: fa650d7322e136093e445b6801b90bd37d93fd4c, con bloque 1 y bloque 2
completo. Inventario Git exacto y clasificacion expresa; lineas numeradas, huellas
por parte y pasada final ligada a todos los resultados. Contrato privado unico
y cobertura calculada desde rangos/partes validados, sin aprobacion ni publicacion.
La secuencia se prueba con dobles ficticios; prepare bloquea la antigua llamada
monolitica. El workflow y la politica siguen desactivados.

Resultado final: 86 privadas + 60 raiz + 5 JS + 3 TS = 154 pruebas, cero fallos,
errores u omitidas. El primer ensayo privado tuvo un error de sintaxis en una
prueba, corregido antes de repetir la suite completa. Ver comandos, incidencia
y limites en docs/pr/bloque-3.md. Las entradas anteriores son historicas.
No verificados integracion real, GitHub, privacidad/retencion de artefactos,
minutos, Docker, identidades ni ERP. No se ejecuto upstream/. Sin red, secretos,
proveedores, publicacion o activacion; original y factoria-2 intactas.
