# ERP-FACTORY — revision manual, fabrica desactivada

Claude revisa en el chat los cambios de cada PR. Antes de una entrega importante,
revisa toda la fabrica en una conversacion nueva. Sus informes se registran en
`docs/revisiones/`, como revision tecnica **no autenticada y nunca aprobacion humana**.
No se afirma que Claude ya haya revisado esta version.

Las personas declaradas para los distintos niveles son:

- **Negocio (business):** fernandoruizm-maker, ID 342326625.
- **Contable y funcional (accounting):** FERRUMTJA, ID 352290329, contador con experiencia en ERP.

Ninguna programa. Fernando acepta el riesgo de no tener una persona revisora
tecnica. **Antes de usar datos reales de clientes o conectar el ERP se requiere
una auditoria tecnica externa.** El contador y Claude no sustituyen esa auditoria.

ERP-FACTORY requiere 1 aceptacion de Fernando; productos con impacto contable,
2 (Fernando y FERRUMTJA). Un destino sin clasificar queda bloqueado; no se ha
decidido otro nivel para productos sin impacto contable. Las reglas remotas de
GitHub no se modifican con esta politica local.

La puerta manual exige el SHA exacto de la revision y las aceptaciones de su nivel,
ligadas a la revision, version y huella evaluadas. Su resultado puede quedar listo
para revision manual, pero siempre declara provenance_authenticated=false y
publication_allowed=false. Los registros locales no autentican personas.
La via V2 privada se conserva, con sus controles, sin usarla como sustituto de la manual.

## Guias y evidencia

- [Como aprobar negocio y contabilidad](docs/GUIA-APROBAR.md)
- [Plantilla de revision](docs/revisiones/PLANTILLA.md) y [como registrar sin cambiar el SHA](docs/revisiones/README.md)
- [Proteccion de main](docs/github/GUIA-PROTEGER-MAIN.md)
- [Plan y permisos de publicacion](docs/PUBLICACION.md)
- [Estado y pruebas](docs/ESTADO.md)
- [Entrega del bloque 6](docs/pr/bloque-6.md)
- [Guia local](LEEME.md)

La revision automatica en GitHub esta **APARCADA**. ERP-FACTORY-revision/ se conserva
localmente: no crear un repositorio privado ahora. Siguen if false,
execution_enabled=false y el pin de ceros. El workflow publico historico tampoco
se modifica ni ejecuta aqui. No se ha comprobado su estado remoto.

Bloque 10: un ensayo ficticio preparado con modelo Codex por API, una llamada
desde el host y construccion/pruebas Docker sin red, seguido de revision manual.
Sigue bloqueado: external_calls_enabled=false, modelo/revision de coste null y
los tres importes de config.json **null**. USD 1.00/llamada, 12.00/ejecucion y
13.00/acumulado son valores propuestos, no activados. El ensayo permitiria solo
una llamada; una reserva local no garantiza el importe de la factura del proveedor.
Detalles y autorizaciones pendientes: [bloque-10.md](docs/pr/bloque-10.md).
El revisor automatico privado conserva su configuracion aparcada anterior.

Docker local: dos imagenes oficiales descargadas con autorizacion y piloto
ficticio comprobado sin red dentro de contenedores. Digests, resultados y limites
en [DOCKER.md](docs/DOCKER.md). No se activa la fabrica por probar su ejecutor.

Fuera de esas descargas autorizadas, trabajo local sin publicacion ni activacion. Main,
upstream/ y la fabrica original permanecen intactos. El repositorio es publico:
nunca subir datos de clientes, credenciales ni informacion del ERP, tampoco a ramas.
Hasta verificar la proteccion real de main, cada subida necesita autorizacion expresa.
