# Segunda fábrica RDC · instalación local desactivada

Creada el 5 de noviembre de 2026, separada de Ubuntu y del ERP. No tiene tareas heredadas, credenciales, conexión a GitHub, servicio de fondo ni publicación automática. La primera fábrica no se ha modificado.

## Qué puedes revisar ahora

- `outputs/INFORME-PILOTO.md`: resultados y pasos comprensibles del ensayo.
- `outputs/comprobante-ensayo.html`: documento ficticio imprimible de diez botellas, saldo cero.
- `fixtures/cliente.json`: ejemplo de objetivos, funciones, áreas y reglas.
- `docs/CLAUDE-OPCIONES.md`: API o GitHub Actions, costos orientativos, permisos y decisiones pendientes.
- `outputs/revision-claude/manifest.json`: referencia del código preparado para que Claude revise la propia fábrica. NOT_RUN significa que todavía no lo revisó.

## Uso local

Abrir `VER_ESTADO.cmd` consulta el estado. `PROBAR_PILOTO.cmd` repite solo el ejemplo ficticio y actualiza sus informes. No encienden la fábrica ni conectan proveedores. Necesitan el Python local que ya usa Codex y Node instalado; no instalan herramientas.

Comandos equivalentes desde esta carpeta con Python disponible:

```text
python -B -m factory2 status
python -B -m factory2 discover fixtures/cliente.json
python -B -m factory2 pilot
python -B -m factory2 prepare-factory-review
python -B -m unittest discover -s tests -v
```

No usar `upstream/factory/mvp` para iniciar el piloto antiguo. `upstream/` conserva los 53 archivos verificados para comparación y reutilización del adaptador Codex, sin la configuración ni la cola originales.

## Qué está implementado

1. Ficha de descubrimiento con dudas y criterios de aceptación; no aprueba el alcance automáticamente.
2. Comparador de catálogo por requisito, ruta y huella, con autorización explícita de la base. El ERP real sigue sin acceso: su matriz queda PENDIENTE. Solo se probó un catálogo ficticio temporal.
3. Constructor Codex que propone archivos nuevos dentro de `src/`, sin tocar pruebas o reglas. Se reutiliza el adaptador del código verificado. No se ejecutó una llamada real de esta fábrica a Codex.
4. Adaptador Claude con límite de respuesta, tiempo, permiso vinculado al contenido, rechazo de herramientas y respuestas incompletas, y sin redirección de credenciales. Probado con transporte simulado; ninguna llamada real.
5. Perfiles de pruebas Python, JavaScript y TypeScript. Código generado requiere Docker con imagen aprobada por digest y ya instalada. No se probó Docker en esta entrega. El piloto propio se ejecutó localmente.
6. SQLite propio, reservas de llamadas transaccionales, límites por tarea y recuperación que marca llamadas inciertas sin reenviar.
7. Dos aceptaciones locales distintas vinculadas al expediente y código; revisión del producto y de la propia fábrica. Son registros preparatorios: falta autenticación real de personas y de resultados remotos antes de producción.
8. Informe de ensayo y comprobante consultable sin nuevos movimientos.

## Límites que impiden activar producción

Esta versión es una base local funcional de desarrollo, no un servicio operativo autónomo. No hay comando de activación. El estado permanece vacío: el piloto no crea trabajos en la cola real de esta instalación.

Faltan elegir e integrar Claude (API o Actions), autorizar transmisión y costos, configurar credenciales nuevas de forma segura, comprobar Codex CLI real y Docker, autenticar aprobaciones, revisar la fábrica con Claude, y decidir el destino de despliegue. TypeScript se probó ejecutando código con eliminación de tipos; no equivale a `tsc` o al build completo de React.

El escenario supone que un gerente O subgerente de la misma área, distinto del solicitante, puede aprobar. Es una regla de ensayo que debe confirmarse para cada cliente. La doble aceptación humana de la fábrica es un control distinto.

## Cambio futuro de fábrica

No operar ambas simultáneamente. Una futura transición debe primero impedir que la original reciba trabajos nuevos y reconciliar trabajos en curso; después activar solamente la segunda, con estado propio y autorizaciones nuevas. Ese cambio no se realiza desde estos comandos ni se ha autorizado en esta entrega.

Ver recuperación y verificación en `docs/RECUPERACION.md` y `docs/ESTADO.md`.
