# Guia de la fabrica local

La segunda fabrica sigue desactivada. La original se conserva sin cambios y no
se operan ambas a la vez. Las pruebas usan ejemplos ficticios, no el ERP real.

## Como trabajaremos

1. Fernando explica el objetivo y confirma las reglas de negocio.
2. Codex prepara los cambios y las pruebas locales en una rama.
3. Claude revisa en el chat solo los cambios de la propuesta, indicando el SHA
   completo y sus hallazgos. Antes de una entrega importante, revisa toda la
   fabrica en una conversacion nueva. No se trata de una aprobacion humana.
4. Codex conserva la revision recibida en docs/revisiones/ usando la plantilla.
   Un registro *.local.md no se agrega al commit evaluado: cambiarlo cambiaria el SHA.
5. En ERP-FACTORY aprueba Fernando como negocio (business). En productos con
   impacto contable tambien aprueba FERRUMTJA como contable y funcional (accounting).
   El antiguo rol technical ya no sirve. Se comprueba la version vigente y su
   destino; si este no esta clasificado, se bloquea. Ver docs/GUIA-APROBAR.md.
6. Publicar o integrar solo sigue las condiciones de docs/PUBLICACION.md. Estar
   listo para revision manual nunca significa publicar o activar automaticamente.

Si Claude concluye CORREGIR, el SHA no coincide, falta una aceptacion o vencio,
la puerta queda bloqueada. Aunque los documentos sean coherentes, siguen sin
estar autenticados: la verificacion de personas y de GitHub no se simula como real.

## Que se puede comprobar localmente

El bloque 10 prepara UN ensayo futuro de las botellas con modelo Codex por API.
No se ha ejecutado: el interruptor sigue apagado y los tres importes de gasto,
el modelo y su revision de coste siguen null. Construccion y pruebas serian en
Docker sin red; solo la peticion al proveedor saldria del host con autorizacion.
Despues se detiene para Claude en el chat y las aceptaciones del producto.
La lista de permisos y limites reales esta en docs/pr/bloque-10.md.

Con Python y Node ya disponibles, Codex puede ejecutar las suites y el piloto
ficticio autorizado. No instala programas ni llama a proveedores para hacerlo.
Las pruebas con dobles verifican reglas locales, no una integracion real.
Los informes de cada bloque en docs/pr/ indican comandos, resultados y limites.

Para quien aprueba, las instrucciones estan en docs/GUIA-APROBAR.md. No hace falta
leer codigo: comparar el SHA completo y comprobar las demostraciones y resultados.
No aprobar algo cuyo efecto no se comprende.

## Automatizacion aparcada

GitHub Actions no se activa. No se crea el repositorio privado. Sus tres bloqueos
se mantienen y el envio remoto sigue deshabilitado. USD 1.00 por llamada, 12.00 por
ejecucion, 13.00 acumulado y opcion 1 quedan anotados solo para una reactivacion
expresamente autorizada. No hay permiso actual de gasto ni adaptador conectado.

## Riesgo aceptado y limites

Fernando y FERRUMTJA no programan. No hay persona revisora tecnica; Claude puede
omitir errores y su autoria no esta autenticada. Fernando acepta ese riesgo para
el trabajo local con datos ficticios. Antes de usar datos reales de clientes o
conectar el ERP se requiere una auditoria tecnica externa y autorizacion expresa.
No publicar datos reales, claves o informacion del ERP en ninguna parte del
repositorio publico. No usar recover() en modo real sin coordinacion verificable
con la fabrica original. Nada de eso se habilita con esta entrega.
