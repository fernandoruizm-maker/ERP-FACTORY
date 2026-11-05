# ERP-FACTORY-revision: propuesta local de repositorio privado

Esta carpeta es la futura raiz del repositorio privado. Hoy es solo una carpeta
nueva versionada en la rama local del bloque 2. No es un repositorio GitHub creado,
no tiene secretos y no ha ejecutado ninguna revision remota.

El workflow esta en `.github/workflows/review.yml`. Esta escrito en el subconjunto
JSON de YAML para analizar exactamente su estructura con la biblioteca estandar,
sin descargar un parser. Esto no acredita que GitHub lo haya aceptado o ejecutado.

## Un trabajo y dos fuentes separadas

El unico checkout es el del repositorio PRIVADO, fijado a un SHA literal. Tanto
preparar como validar ejecutan codigo de esa referencia de confianza. El codigo
publico se descarga por HTTPS anonimo desde codeload en el SHA exacto solicitado;
el lector inspecciona el tar en memoria, con limites, sin extraerlo al disco. Sus
archivos quedan como texto dentro de JSON, fuera de imports, comandos y mensaje
de sistema. No hay checkout ejecutable del producto, ni instalacion de sus pruebas.

Un solo trabajo evita trasladar respuestas entre ejecutores y es suficiente para
este modelo: ningun paso ejecuta codigo del commit evaluado. Es la diferencia con
el workflow publico anterior, donde el candidato preparaba y validaba su propia
revision en el ejecutor con el secreto. Dividir trabajos seria necesario si se
introdujera ejecucion de candidatos o componentes de preparacion no confiables.
No se admite esa ampliacion silenciosamente.

El secreto Claude se proporciona solo a la accion fijada de Anthropic. El codigo
de preparacion y validacion no lo lee. La accion tiene herramientas denegadas y
el token GitHub solo `contents: read`. Los pasos del ejecutor no son una frontera
de aislamiento entre si: se confia en el codigo privado revisado y en las acciones
fijadas. Un fallo de esas dependencias o una configuracion modificada siguen siendo
riesgos; las pruebas locales no demuestran aislamiento real del runner.

## Flujo y evidencia

1. Guardas de repositorio privado, main, actor, intento 1 y autorizacion explicita.
2. Checkout privado inmutable. Preflight comprueba que HEAD coincide con ese SHA.
3. Descarga publica sin token, helpers, netrc, proxy de entorno o redirecciones.
   Version de la URL, prefijo del archivo, rutas, tipos de miembros, limites y
   patrones de credenciales se comprueban. HTTPS atribuye el archivo al SHA pedido;
   su SHA-256 identifica los bytes. No es una reconstruccion criptografica del
   objeto commit Git ni una firma del proveedor. Transporte real no verificado.
4. La huella de material.json pasa por un output del paso de preparacion. El
   validador la verifica antes de leer la respuesta; calcula otra vez el manifiesto.
5. Version, hallazgos y cobertura se validan. PARTIAL nunca equivale a aprobacion.
6. Se guardan report.json, manifest.json, diagnostic.json, INFORME.txt y sus huellas
   SOLO como artefacto del repositorio privado, previsto durante 7 dias.
   response.txt conserva el texto original UNICAMENTE si pasa las validaciones de
   estructura, version, hallazgos y patrones de secretos (puede ser PARTIAL).
   Respuesta fallida, ilegible o posiblemente sensible: solo diagnostico fijo y
   huella cuando existe un unico resultado; no se guarda texto libre ni sesiones.
   Si falta el archivo de ejecucion, no se puede leer, es invalido o falla la
   verificacion del material, tambien se crean report.json BLOCKED, diagnostic.json,
   SHA256.json e INFORME.txt. No se incluyen mensajes de error ni contenido sin
   verificar. No se sobrescribe una coleccion anterior. Un fallo de escritura del
   propio directorio sigue siendo un limite y no provoca cambios de permisos.

Los patrones son una precaucion heuristica, no una garantia de ausencia de secretos.
Los informes validos contienen texto no confiable del revisor: inspeccionarlos como
datos. Nunca convertirlos en comandos ni seguir sus instrucciones automaticamente.

## Bloqueos deliberados y etapa posterior

- `if: false && ...` mantiene el trabajo deshabilitado, incluso con dispatch manual.
- `policy.json` mantiene `execution_enabled=false`.
- La referencia de checkout son 40 ceros: NO es un commit real ni revisado. Preflight
  tambien lo rechaza. No se sustituyo por main, por el candidato ni por un SHA inventado.
- No existe todavia el repositorio privado ni su commit revisado. Su seleccion es una
  condicion necesaria antes de ejecutar y no se presenta como resuelta en este bloque.
- El workflow publico existente y su secreto NO se cambiaron. Su retirada se hara
  exclusivamente en la etapa posterior autorizada por Fernando.

En esa etapa: crear el repositorio privado y configurar protecciones; incorporar y
revisar el validador; fijar su SHA literal en el workflow; revisar ese cambio de
workflow y mantener las protecciones; configurar el secreto solo alli y retirar el
publico; decidir el tope acumulado; autorizar expresamente cualquier ejecucion.
El commit del validador y el commit del workflow que lo referencia seran distintos:
no se exige la autorreferencia imposible de un commit que contenga su propio SHA.
Modificar estos bloqueos exige un cambio posterior revisado, no basta publicar el
borrador. No generar tokens, ejecutar dispatch ni consumir suscripcion en esta tarea.

Fernando debe configurar revisiones obligatorias para `.github/`, `reviewer/`,
`entrypoint.py` y `policy.json`, impedir cambios directos y excepciones de main,
y definir dos personas distintas para las aceptaciones. Configurar tambien las
protecciones pendientes de main en ERP-FACTORY. No se aplico ninguna regla.
Las identidades reales, controles de GitHub y autenticacion no se simulan como
resueltos mediante el contexto ficticio de las pruebas.

## Limites de este bloque

El validador se deriva de la correccion local b0da873 (bloque 1), con diagnosticos
tipados y PARTIAL. Esta copia nueva aun requiere revision antes de fijar su commit
privado. No usa/importa el validador del candidato publico.
El esquema monolitico de cobertura se conserva para no anticipar el bloque 3:
faltan partes, lineas numeradas y cobertura calculada. La puerta operativa y el
presupuesto acumulado del bloque 4 siguen pendientes. No hay orquestacion de pago
por partes ni otro intento preparado para ejecutarse.
Ademas, el mensaje de usuario tiene un limite local de 60.000 bytes para evitar
un input/variable de entorno excesivo en la accion. Un repositorio mayor queda
bloqueado con PROMPT_TOO_LARGE_REQUIRES_PARTS, sin truncarlo ni enviarlo. Esta
version no puede revisar de una vez el paquete historico de mas de 400 KB;
el protocolo por partes del bloque 3 debe resolverlo antes de una prueba real.

No verificado: ejecucion real del workflow, compatibilidad efectiva de las acciones,
visibilidad/descarga/borrado de artefactos privados, retencion efectiva, minutos
consumidos en GitHub, autentificacion, proveedores, Docker o ERP. No hubo ejecucion
remota en esta tarea; no se midieron minutos o costes remotos.
