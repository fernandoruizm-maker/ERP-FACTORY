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
