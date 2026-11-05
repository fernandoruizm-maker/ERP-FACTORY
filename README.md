# ERP-FACTORY

Segunda fábrica RDC, preparada localmente y **desactivada**.

Codex propone código; Claude revisará mediante GitHub Actions tanto los productos como la propia fábrica. La integración real de Claude está pendiente. No hay workflows activos, credenciales, colas históricas ni conexiones al ERP.

## Empezar

- [Guía de uso](LEEME.md)
- [Estado y pruebas ejecutadas](docs/ESTADO.md)
- [Integración elegida: GitHub Actions](docs/CLAUDE-OPCIONES.md)
- [Recuperación](docs/RECUPERACION.md)

Con Python y Node disponibles:

```text
python -B -m factory2 status
python -B -m factory2 discover fixtures/cliente.json
python -B -m factory2 pilot
python -B -m unittest discover -s tests -v
python -B -m factory2 prepare-factory-review
```

Los informes y paquetes de revisión se generan localmente en `outputs/`; no se publican resultados simulados como revisiones reales de Claude. El piloto usa únicamente datos ficticios.

`upstream/` conserva los 53 archivos de referencia verificados. No ejecutar su piloto ni copiar credenciales del original. El borrador en `docs/actions/*.disabled` contiene marcadores pendientes, no está listo para activar y no se encuentra en `.github/workflows`.

La puesta en marcha necesita autenticación OAuth compatible, modelo, presupuesto, autorización de transmisión, validación real del workflow y dos aprobaciones humanas verificables. Esta versión no integra ni despliega automáticamente.
