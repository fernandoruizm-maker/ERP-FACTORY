# Plan autorizado: segunda fábrica local

## Correcciones locales posteriores a la revision manual

Base comprobada: 0cb1882548fc141f4b764e82ff2e5154cfae2762. Clon separado
ERP-FACTORY-correcciones; factoria-2 intacta. Unico acceso de red: clon HTTPS
anonimo autorizado. origin push=DISABLED. Sin fetch, pull, push, PR remota,
workflows, proveedores ni nuevas dependencias.

Ramas por bloque: diagnostico/PARTIAL; aislamiento estatico; contrato y cobertura
por partes; condiciones operativas. Documentar dependencias sin integrar main.
Cada bloque entrega commits, docs/pr/bloque-N.md y suite local completa con
limites explicitos. Ninguno habilita ni prepara un nuevo intento de pago.

Bloque 1: implementado y probado; 60 Python + 5 JavaScript + 3 TypeScript.
Retencion y destinatarios de hallazgos: decision pendiente de Fernando.

Destino: `factoria-2/` en este espacio de trabajo. Fuente: ZIP verificado 53/53 con Ubuntu, SHA en ORIGEN.json.

1. Conservar 53 archivos en upstream sin alteraciones; no copiar configuración privada, colas ni evidencias históricas.
2. Implementar descubrimiento y comparación por evidencia. Sin acceso al ERP: matriz real pendiente; catálogo ficticio separado.
3. Proveedores separados: Codex produce propuestas; Claude revisa sin herramientas ni autoridad de aprobación. Llamadas deshabilitadas, permiso por contenido y presupuesto antes de transmitir.
4. Perfiles Python, JS y TS. Ejecutar solo el piloto confiable local; código generado requiere ejecutor Docker aislado y preparado, sin descargar imágenes automáticamente.
5. Piloto ficticio: 10 botellas, autorización por área y gerente/subgerente independiente, salida única, stock cero y comprobante.
6. Estado nuevo con transacciones, llamadas reservadas antes de transmitir y recuperación sin reintento de resultado incierto. Dos aceptaciones humanas de una misma versión, sin publicación.
7. Pruebas de dominio, acceso, límites, respuestas incompletas, aprobación desactualizada y recuperación. Documentar lo realmente ejecutado.

No forma parte de esta entrega activar consumidores de GitHub, instalar un servicio Ubuntu, abrir acceso al ERP, transmitir código a Anthropic o desplegar. El prototipo local queda desactivado. La identificación de personas y autenticación de las aprobaciones reales será un requisito de puesta en marcha: un registro local no acredita una firma humana.


## Actualizacion local: bloques 2 y 3

Fernando decidio que revisiones y artefactos vivan en un repositorio privado
separado; la carpeta ERP-FACTORY-revision/ es solo su propuesta local. Retencion
no validada limitada a los codigos/condiciones autorizados, documentada en bloque 2.
La base del bloque 3 incorpora b0da873 y f288441 (incluido a8cfa18), sin tocar main.
Bloque 3 implementa protocolo privado por partes, lineas y cobertura calculada,
con pruebas locales y dobles ficticios. No conecta la secuencia real a Actions.
Pendientes: bloque 4 y migracion/configuracion/ejecucion posterior expresamente
autorizada. No hay nuevo intento de pago preparado. Ver docs/pr/bloque-3.md.


## Bloque 4 en dos entregas locales

Rama fix/bloque-4-operacion rehecha desde ad91cb39609e589df72c8e0b01fc68c694fb4c83.
La referencia anterior (0cb1882, sin cambios propios) se conserva como
archive/bloque-4-base-anterior. Primera mitad: aceptaciones V2 con caducidad,
importador unico privado con integridad comprobada y autenticacion pendiente,
candado de trabajador/indicador solo simulado y permiso de comparacion por alcance.
Segunda mitad, despues de entregar la primera: orquestador, envoltorio Codex,
registro acumulado y topes, piloto y documentacion de migracion (puntos 5-9).
No construir el workflow multiparte ni activar integraciones en ninguna mitad.
Fernando declaro negocio fernandoruizm-maker ID 342326625 y tecnica FERRUMTJA
ID 352290329; no se autentican en local. Autorizo 11 llamadas por ejecucion;
gasto por ejecucion y gasto acumulado siguen null, sin valor por defecto.
Faltan origen GitHub autenticado y coordinacion real con la original: fallar
cerrado, no tratar fixtures o huellas locales como prueba de esas integraciones.
Verificar suites privada/raiz/JS/TS, registrar evidencia y entregar commit y
diffs contra ad91cb3 y 0cb1882 por cada mitad; no tocar main ni upstream/.


### Segunda mitad del bloque 4

Implementados localmente puntos 5-9 desde 84c5fe8: orquestador con pruebas de
confianza y dobles, rutas contra candidato, envoltorio Codex con entorno por
lista blanca, ledger persistente de reservas/topes, piloto y documentacion.
Suites finales 129 raiz + 87 privadas + 7 JS + 3 TS = 226, sin fallos/omitidas.
Primer ensayo raiz: 2 fallos por orden alfabetico de perfiles; corregido y
verificado con suites completas. Moneda y ambos topes monetarios siguen null.
No se construye el workflow multiparte ni se activa infraestructura real.

## Bloque 5 autorizado: workflow multiparte privado bloqueado

Base 8ffb8115843fcb0f05b8c6a7c28adc0ce87c3934; rama fix/bloque-5-multiparte.
Pasos fijos secuenciales, reserva/subida antes de llamar, validacion y subida
inmediata posterior. Contrato V2 existente, sin reintentos ni codigo publico
ejecutado. Tres bloqueos intactos; USD/11, importes null. Implementar solo comun
local de reserva/importacion de autorizaciones; opcion acumulada pendiente de
Fernando. Diseno y limites en docs/pr/bloque-5.md. Verificar suites completas,
entregar SHA/diffs frente a 8ffb811 y 0cb1882. Sin red/publicacion/activacion.

## Bloque 6: decision de revision manual

Base 55073009fc30c810c7c7ede8c1ff3352071a2fe0, rama fix/bloque-6-revision-manual.
Registro manual versionado por huella (archivo real local, sin alterar el SHA del
codigo), via alternativa con SHA exacto/dos roles vigentes, sin autenticacion
ni publicacion; V2 intacto. Roles business/accounting; technical rechazado.
Guias para personas no programadoras, ruleset local y plan de publicacion selectiva.
Riesgo aceptado: sin persona revisora tecnica; auditoria externa antes de datos
reales/ERP. Actions aparcado; registrar USD 1/12/13 y opcion manual sin activarla.
Ejecutar suites raiz/privada/JS/TS y entregar SHA/diffs frente a 5507300 y 0cb1882.
