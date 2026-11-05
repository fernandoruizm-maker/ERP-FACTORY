# ERP-FACTORY

Segunda fabrica RDC de desarrollo local, **desactivada**. La original se conserva.
Las correcciones estan en ramas locales; no se publican ni activan desde esta tarea.

Existe un workflow publico historico en `.github/workflows/claude-factory-review.yml`.
Se conserva hasta una migracion autorizada. Su estado actual en GitHub no se ha
consultado. `ERP-FACTORY-revision/` contiene la propuesta de repositorio PRIVADO
para ejecutar revisiones; su workflow esta bloqueado y su referencia revisada
pendiente. No basta publicar esa carpeta para ponerla en marcha.

Codex y Claude se prueban aqui con dobles ficticios. El flujo local monta el
candidato junto con pruebas de confianza y recorre construir -> probar -> revisar
sin ejecutar propuestas de modelos en el equipo. Esto no acredita integracion
real con proveedores ni Docker. Las revisiones simuladas nunca aprueban la fabrica.

## Uso y evidencia

- [Guia local](LEEME.md)
- [Estado actual e historial de pruebas](docs/ESTADO.md)
- [Diseno de revision privada y requisitos pendientes](docs/CLAUDE-OPCIONES.md)
- [Entrega del bloque 4 y sus dos mitades](docs/pr/bloque-4.md)
- [Recuperacion historica](docs/RECUPERACION.md): la recuperacion actual exige
  candado y coordinacion; la via real permanece bloqueada.

Con Python y Node ya disponibles, los comandos del piloto confiable son:

```text
python -B -m factory2 status
python -B -m factory2 discover fixtures/cliente.json
python -B -m factory2 pilot
python -B -m unittest discover -s tests -v
```

El piloto usa datos ficticios. No instala herramientas ni conecta al ERP.
Los informes reales deberan permanecer privados. No publicar archivos de estado,
respuestas del proveedor ni artefactos privados en este repositorio publico.

## Bloqueos vigentes

Faltan autenticacion de las personas, procedencia autenticada de GitHub,
coordinacion real con la original, importes maximos y moneda autorizados.
Fernando indico 11 llamadas por ejecucion; ambos topes de gasto siguen vacios.
El registro local conserva reservas e intentos inciertos, pero no mide facturas
ni garantiza un limite impuesto por el proveedor. Ninguna funcion publica o activa.

`upstream/` es referencia intacta: no ejecutar su piloto. El adaptador de Codex se
envuelve desde factory2/ con una lista blanca de entorno; su ejecucion real sigue
sin conectar. El borrador `docs/actions/*.disabled` es **OBSOLETO** y no debe activarse.
El workflow multiparte con guardado de cada resultado, topes y sin reintentos
sigue siendo un requisito obligatorio pendiente, no una funcionalidad entregada.
