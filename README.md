# ERP-FACTORY — revision manual, fabrica desactivada

Bloque 14: [armado local](docs/ARMADO-LOCAL.md) en state/armado.json, ligado al
encargo/intento y con vigencia máxima de 24 horas, sin cambiar config.json.
[Catálogo de dependencias](docs/CATALOGO-DEPENDENCIAS.md) con análisis estático
antes de construir el candidato. No hay paquetes externos aprobados ni ensayo armado.

Bloque 13: encargos ficticios en `encargos/<nombre>/`, con requisitos, pruebas
fijas y una lista cerrada de salida. Ejemplos: botellas (JavaScript) y caja chica
(Python). Preparacion local: `scripts/ensayo.ps1 -Encargo botellas -Intento 1`.
Esto no llama al proveedor ni consume un intento. Ver [guia de encargos](docs/ENCARGOS.md).
Todos los interruptores permanecen false; no se altera el historial del ensayo.

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
Sigue bloqueado: external_calls_enabled=false y los otros tres interruptores false.
En piloto/intento-1 se prepararon gpt-6.1-sol y precios estandar verificados
documentalmente, con USD 1.00/llamada, 12.00/ejecucion y 13.00/acumulado.
No se ejecuto el ensayo. Ver [preparacion del intento 1](docs/pr/intento-1.md). El ensayo permitiria solo
una llamada por intento expresamente autorizado, con calculo previo del peor coste
y registro numerico del uso. Cada nuevo numero necesita nueva autorizacion y
comparte el tope acumulado de USD 13. Las tarifas deben revalidarse antes de ejecutar;
una reserva local no garantiza el importe de la factura del proveedor.
Detalles y autorizaciones pendientes: [bloque-10.md](docs/pr/bloque-10.md).
El revisor automatico privado conserva su configuracion aparcada anterior.

Docker local: dos imagenes oficiales descargadas con autorizacion y piloto
ficticio comprobado sin red dentro de contenedores. Digests, resultados y limites
en [DOCKER.md](docs/DOCKER.md). No se activa la fabrica por probar su ejecutor.

Fuera de esas descargas autorizadas, trabajo local sin publicacion ni activacion. Main,
upstream/ y la fabrica original permanecen intactos. El repositorio es publico:
nunca subir datos de clientes, credenciales ni informacion del ERP, tampoco a ramas.
Hasta verificar la proteccion real de main, cada subida necesita autorizacion expresa.
