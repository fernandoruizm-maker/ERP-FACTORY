# Herramientas preparadas, ninguna instalada por el bloque 15

La aprobación del catálogo permite registrar estas versiones. No autoriza
descargas, instalaciones, ejecución de workflows ni llamadas pagadas.
config.json y los controles de revisión humana no cambian.

## Acorn: preparación local pendiente de autorización RESERVADA

tools/acorn/policy.json mantiene enabled=false e image=null. factory2/js_analysis.py
usa por defecto el analizador conservador anterior. El nuevo adaptador solo admite
una referencia inmutable: nombre@sha256 del manifiesto de registro, o sha256 del
ID de configuración de una imagen local. Son huellas distintas, no intercambiables.
El segundo formato permite construir localmente sin publicar una imagen en un registro.
Una etiqueta como latest o 8.19.0 nunca basta para ejecutar el analizador.

Descarga futura única del paquete:
https://registry.npmjs.org/acorn/-/acorn-8.19.0.tgz

Integridad publicada en [metadatos oficiales de npm](https://registry.npmjs.org/acorn/8.19.0):
`sha512-oJlA3XiRm7Cyk6qFD2Jn8ak9B7jSy0qy00ADO3+8dpT0LSjFihQYv4C02LFCSYJV3Q37xYwwRy5m+IpIiUzqWw==`.
Metadatos leídos el 7-11-2026. No se descargó el paquete ni se comprobaron firmas
del registro. Comparar la huella de los bytes sigue pendiente.

Estos son comandos FUTUROS de PowerShell, no ejecutados. Fernando autorizará un
directorio de trabajo vacío fuera del repositorio, representado por $AcornBuild.
No guardar el tarball ni la imagen en Git. Copiar allí únicamente Dockerfile,
cli.mjs y analyze.mjs de tools/acorn/ del commit revisado.

```powershell
# Solo después de autorización de descarga e instalación/construcción:
Invoke-WebRequest -Uri 'https://registry.npmjs.org/acorn/-/acorn-8.19.0.tgz' -OutFile "$AcornBuild/acorn-8.19.0.tgz"
docker image inspect node@sha256:01d566e8d94d8c619591d78652babfccd3c6992a3dffa9ed5ab39e11cf6c70e9
# Si falta esa base local, detenerse: no hacer pull sin autorización nueva.
docker build --network=none --pull=false --tag rdc2-acorn:8.19.0 "$AcornBuild"
docker image inspect rdc2-acorn:8.19.0 --format '{{.Id}}'
```

El Dockerfile verifica SHA-512 ANTES de extraer el tarball; un desacuerdo detiene
la construcción. No usa npm install ni scripts de instalación. La base Node está
fijada al digest ya registrado en docs/DOCKER.md. La etiqueta solo sirve para
obtener el ID; copiar el sha256 resultante a la política requiere revisión y
autorización separadas. No inventamos una huella de imagen todavía inexistente.

Antes de habilitar: probar el parser real, salida y tiempos, inspeccionar las capas,
licencia/versiones y el comportamiento de Docker en este PC con entorno reducido.
La CLI comprueba Acorn 8.19.0 y parsea ECMAScript 2025 como módulo; CommonJS con
return de nivel superior, TypeScript y otras construcciones no admitidas bloquean.
El recorrido del AST rechaza cargas dinámicas no literales, alias require,
propiedades computadas, eval/Function, import.meta y cargadores conocidos.
Es un inventario conservador, no una prueba de ausencia de toda carga indirecta.

La ejecución usa docker run --pull=never --network=none --read-only,
usuario 65534:65534, sin capacidades, no-new-privileges, límites de memoria,
CPU, procesos y 15 s. Solo monta un directorio temporal con el JSON del archivo
analizado, en lectura. No monta el repositorio, credenciales ni el socket Docker.
La salida debe vincular versión y SHA-256 del código; el candidato nunca se evalúa.
Un error, advertencia que contamine JSON, imagen ausente o límite bloquea.
Se intenta retirar solo el contenedor propio de nombre único, también ante fallo.
Hoy se probaron dobles de proceso y AST hechos a mano: NO el paquete Acorn real.

## Gitleaks y OSV: workflow manual apagado

.github/workflows/security-catalog.yml solo tiene workflow_dispatch y condición
literal false. No se ejecuta al subir esta rama ni al abrir su PR. No contiene
secretos de repositorio, no usa la Action de Gitleaks, no instala el proyecto ni
ejecuta sus pruebas. Checkout usa el permiso mínimo contents:read, token efímero
de GitHub y persist-credentials:false. No se crean ni se configuran credenciales.

Descargas futuras en un runner Linux amd64 efímero:

| Ejecutable | Archivo oficial | SHA-256 obligatorio antes de ejecutarlo |
|---|---|---|
| Gitleaks v8.30.1 | [gitleaks_8.30.1_linux_x64.tar.gz](https://github.com/gitleaks/gitleaks/releases/download/v8.30.1/gitleaks_8.30.1_linux_x64.tar.gz) | 551f6fc83ea457d62a0d98237cbad105af8d557003051f41f3e7ca7b3f2470eb |
| OSV v2.7.0 | [osv-scanner_linux_amd64](https://github.com/google/osv-scanner/releases/download/v2.7.0/osv-scanner_linux_amd64) | 160c6253e2922e9e0a6a9771c5c4c40a4b3c6090b34a3cdd5e80c96cc2e4218b |

Huellas obtenidas del campo digest de los metadatos públicos de releases de
[Gitleaks](https://api.github.com/repos/gitleaks/gitleaks/releases/tags/v8.30.1) y
[OSV](https://api.github.com/repos/google/osv-scanner/releases/tags/v2.7.0), el
7-11-2026. No se descargaron ejecutables: integridad de bytes y funcionamiento
de esos binarios NO VERIFICADOS. El YAML contiene las URL y comandos exactos;
curl solo admite HTTPS, no reintenta, y sha256sum bloquea antes de usar un binario.

El mismo paso futuro descargará estas dos bases públicas de vulnerabilidades:
https://osv-vulnerabilities.storage.googleapis.com/npm/all.zip y
https://osv-vulnerabilities.storage.googleapis.com/PyPI/all.zip.
Son datos actualizables, no binarios fijados: se registrará su SHA-256 al descargarlas.
No se afirma reproducibilidad entre fechas de la base ni autenticación adicional
a HTTPS. El escaneo posterior usa --offline y no consulta la API con dependencias
del proyecto, según la [guía oficial de OSV](https://google.github.io/osv-scanner/usage/offline-mode/).
Los análisis de llamadas Go/Rust se deshabilitan para evitar compilación del proyecto.
El runner sí necesita red para checkout y descargas iniciales; no es una máquina
aislada de red. Los flags offline no equivalen a un cortafuegos del sistema.

Gitleaks examina el historial descargado, con reglas predeterminadas explícitas,
sin exclusiones del repositorio ni comentarios allow, y redacción al 100%.
OSV examina manifiestos, lockfiles y SBOM reconocidos; catalogo-aprobado.json por sí
solo NO es un lockfile/SBOM. No demuestra que siete herramientas estén instaladas,
ni cubre dependencias transitivas sin inventario. Si no encuentra paquetes o falla,
se conserva el fallo: no se convierte en éxito. Antes de activarlo hay que revisar
qué archivos reconoce y su cobertura real. Véase [escaneo de fuentes](https://google.github.io/osv-scanner/usage/scan-source).

No se publican hallazgos como artefactos ni como texto de consola; solo códigos
de resultado. Se descarta la salida de los analizadores, incluida stderr. Esto
limita el diagnóstico; una investigación posterior necesita permiso y canal seguro.
La prueba estática del YAML no acredita ejecución ni protección contra todo cambio
futuro. Cualquier cambio del workflow requiere otra revisión.

## Minutos y acciones pendientes

El workflow apagado no inicia trabajos. Si se autoriza, hay un trabajo Ubuntu
estándar con límite de 15 minutos, cuatro descargas de hasta 120 s cada una y dos
escaneos de hasta 180 s. Es un límite, NO una duración medida. Para repositorios
públicos los runners estándar son gratuitos según [GitHub](https://docs.github.com/en/billing/concepts/product-billing/github-actions);
otros tipos de runner/visibilidad pueden cambiar la facturación. No se midió coste.

Requieren «buzón, autorizado» de Fernando y alcance preciso:
1. Descargar el tarball de Acorn y construir la imagen local; no descargar otras
   bibliotecas por considerar aprobado el catálogo.
2. Ejecutar la validación real de esa imagen y, tras revisión, habilitar su política
   con el digest obtenido; no activar la fábrica ni proveedores por ese motivo.
3. Descargar los dos ejecutables y las bases OSV, probarlos y revisar su cobertura.
4. Activar/ejecutar el workflow revisado y aceptar sus minutos; sin cambios de reglas
   de main, secretos ni publicación automática de hallazgos.
5. Instalar cualquiera de las demás bibliotecas en imágenes de productos: versión,
   dependencias transitivas, licencia y huellas requieren preparación separada.

Nada de lo anterior se realizó en este bloque. Publicar la rama y abrir su PR
está permitido por el buzón; aprobar e integrar siguen fuera de esta tarea.
