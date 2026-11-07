# Bloque 15: catálogo aprobado inicial

Base comprobada: 108e78fff958cd87083d7ceed7343881cf62d7f2.
Rama: feat/bloque-15-catalogo. Instrucción 11 del buzón, 7-11-2026.

El catálogo estaba vacío. Se registran las cinco bibliotecas y dos herramientas
autorizadas por Fernando, separando uso en productos y uso interno. No se instala
ninguna. Vitest sigue fuera. La validación estricta del esquema 2 impide que una
herramienta CLI o biblioteca interna se convierta en importación de un candidato.

Se prepara el adaptador de Acorn para una imagen inmutable sin red, montaje de
lectura y usuario sin privilegios. Sigue apagado y sin digest de imagen; continúa
el analizador conservador actual. Un fallo del adaptador activado bloquea, sin
fallback silencioso. El parser no evalúa el código. Se documentan las limitaciones
del análisis estático y las futuras descargas verificadas.

Se conserva como propuesta docs/propuestas/security-catalog.yml.txt (fuera de .github): solo manual, job con condición false, binarios
Gitleaks/OSV por versión y SHA-256, sin Action de Gitleaks ni secretos añadidos,
sin ejecución del proyecto ni publicación de hallazgos. Las bases OSV futuras
son datos actualizables, con huella registrada al descargarlas. El escaneo usa
--offline; no se afirma aislamiento de red del runner ni cobertura completa sin
lockfiles/SBOM. El workflow público previo de Claude y el revisor privado no cambian.

## Verificación ejecutada

Python usado: runtime local existente de Codex; ningún pip/npm install.
Desde la raíz, con TEMP/TMP apuntando al directorio local de pruebas:

```powershell
$env:TEMP=(Resolve-Path ..\entregas-locales\bloque-14-temp).Path
$env:TMP=$env:TEMP
& "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -B ..\entregas-locales\ejecutar-suite-sin-red.py
```

Resultado final: **312 pruebas, 0 fallos, 0 errores, 0 omitidas**.
El auxiliar descubre toda la suite raíz, reduce el entorno y prohíbe sockets y
subprocesos externos Docker/gh/curl/ssh/red de Git. Solo se usan dobles ficticios.

Desde ERP-FACTORY-revision, con TEMP/TMP al mismo directorio externo:

```powershell
& "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -B ..\..\entregas-locales\ejecutar-suite-sin-red.py
```

Resultado: **113 pruebas, 0 fallos, 0 errores, 0 omitidas**.

Desde la raíz:

```powershell
node --test --test-reporter=tap pilot-js/tests/bottles.test.mjs tools/acorn/analyze.test.mjs
node --experimental-strip-types --test --test-reporter=tap pilot-js/tests/bottles.test.ts
```

Resultados: **16 JS** (7 piloto + 9 AST ficticio), **3 TS**, cero fallos,
omitidas y canceladas. Total: **444 pruebas**. TS no comprueba tipos estáticamente.
git diff --check sin errores. La suite raíz anterior de 311 pruebas también pasó;
se repitió completa al añadir el caso del ID SHA-256 de imagen local.

Casos nuevos: separación product/internal/CLI, Vitest rechazado, fuentes oficiales,
duplicados y esquema, imagen ausente/etiqueta mutable, salida inválida/otra versión
o huella, timeout, aislamiento del comando, parser apagado sin subprocess,
AST con import/require/export, cargas ambiguas y límite de tamaño. Mutaciones del
YAML detectan activación, permisos de escritura, secretos, quitar offline o redacción,
Action no permitida y cambios de versión/hash. Es análisis estático acotado del YAML,
no un intérprete general ni una prueba de GitHub Actions.

## NO VERIFICADO y pendientes RESERVADOS

- Paquete Acorn real, imagen construida, entorno de Docker y parsing real. Los AST
  son hechos a mano; las respuestas Docker están simuladas. No prueban integración.
- Descarga/integridad de bytes y ejecución de Gitleaks/OSV; hashes solo cotejados
  con metadatos oficiales públicos. No se verificaron firmas de suministro.
- Workflow en GitHub, sintaxis y flags frente a esos binarios, cobertura efectiva
  de manifiestos, bases de vulnerabilidades, minutos y coste reales.
- Licencias transitivas, versiones instaladas de productos o ausencia absoluta
  de secretos/vulnerabilidades. No se escaneó el historial con estas herramientas.
- ERP, datos reales, revisión Claude de este commit y aprobaciones humanas.

Descargar/construir/probar Acorn, fijar su digest y habilitarlo; descargar/probar
los dos CLI y bases OSV; activar/ejecutar el workflow; instalar las otras bibliotecas:
todo requiere «buzón, autorizado» con alcance concreto. Comandos y fuentes exactas
en [HERRAMIENTAS-CATALOGO.md](../HERRAMIENTAS-CATALOGO.md). No se hace aquí.
No se modifican config.json, state/, upstream/, ERP ni la fábrica original.
La rama se publica para revisión; nadie aprueba ni integra en esta tarea.

## Ajuste del mensaje 14

El push anterior fue rechazado por el permiso workflow. Se conserva el contenido
exacto del YAML como propuesta de texto, sin ampliar permisos ni cambiar credenciales.
Las pruebas estáticas leen la propuesta; no se añade ningún workflow a GitHub.
No cambia ningún archivo bajo .github/ frente a origin/main. Su futura instalación
en .github/workflows/ y su activación necesitan autorización expresa y revisión.
Se crea un commit adicional: no se reescribe a36c617 ni el historial.

Verificación repetida después del traslado (mensaje 14): 312 raíz + 113 privada + 16 JS + 3 TS = 444, cero fallos/errores/omitidas/canceladas; mismos comandos completos documentados en docs/pr/bloque-15.md. Logs Python locales fuera de Git: bloque-15-m14-raiz.log y bloque-15-m14-privada.log. TS sin comprobación estática de tipos; ninguna integración de herramientas reales ni Actions. git diff origin/main -- .github vacío y git diff --check correcto.
