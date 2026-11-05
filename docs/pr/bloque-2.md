# Propuesta de PR: revisar ERP-FACTORY desde un repositorio privado de confianza

## Problema y resultado

El workflow publico anterior ejecuta preparacion y validacion del propio candidato
en el trabajo que usa la credencial Claude (A2). Este bloque entrega una carpeta
nueva `ERP-FACTORY-revision/`, futura raiz de un repositorio privado separado:
workflow, lector anonimo de codigo publico, validador independiente y pruebas.
No se creo ningun repositorio GitHub ni se modifico su configuracion o sus secretos.

Un solo trabajo basta para este diseño: ejecuta exclusivamente codigo privado
fijado; el candidato publico nunca se ejecuta, instala ni importa. Se descarga un
tar del SHA exacto, inspeccionado en memoria sin extraer archivos. El candidato
solo aporta datos JSON. No hay proceso del candidato que pueda sobrevivir hasta
el paso con el secreto. Esto no aisla entre si los pasos confiables: quedan como
frontera de confianza el codigo privado revisado, las acciones fijadas y GitHub.

La credencial Claude solo se referencia en su paso y en el futuro repositorio
privado. El token GitHub tiene solo contents: read. Conserva dispatch manual,
actor, intento 1, concurrencia, limites y acciones fijadas por los SHA que ya
constaban localmente. El SHA publico se valida como 40 hexadecimales exactos y
se usa en la URL y en la validacion; no se compara con github.sha porque ese SHA
ahora pertenece al repositorio privado, no al codigo publico.

No hay intercambio entre trabajos. Entre preparar y validar se conserva una huella
en el output del paso, y el consumidor la verifica antes de usar el material. Los
artefactos finales tienen SHA256.json. Respuesta validada, hallazgos e informes van
solo a artefactos privados con retencion propuesta de 7 dias. Respuestas invalidas
o posiblemente sensibles no conservan texto libre: solo codigos y huella disponible.
Nunca se suben estos datos al repositorio publico. Las pruebas usan solo ficticios.

## Bloqueos y dependencias expresos

Se entregan tres bloqueos deliberados: guardia false del workflow,
execution_enabled=false y pin de 40 ceros rechazado en preflight. Ese pin NO es una
referencia real revisada. Seleccionar el commit privado revisado es pendiente,
porque el repositorio privado aun no existe. El analisis estatico devuelve
structural_checks=PASS y operational_readiness=BLOCKED; no se llama listo para operar.

El README del repositorio propuesto detalla la etapa posterior: repositorio privado,
revision y SHA inmutable del validador, revision del workflow que fija ese SHA,
protecciones de main en ambos repositorios, revision obligatoria de .github/ y del
validador, dos identidades humanas, configurar alli el secreto y retirar el publico.
No se ejecuto ninguno de esos pasos. No se ha elegido un tope acumulado de gasto.
El prompt de usuario se limita a 60.000 bytes; paquetes mayores quedan bloqueados
sin truncar ni enviar. El paquete historico de mas de 400 KB requiere el protocolo
por partes del bloque 3 antes de una prueba real. La prueba adicional de este
limite paso al repetir la suite privada completa: 23/23, sin fallos ni omitidas.
No basta publicar este borrador para ejecutar: cualquier cambio de bloqueos y
cualquier intento Claude requieren autorizacion posterior expresa.

## Procedencia y ramas

Rama local: fix/bloque-2-aislamiento, creada directamente desde
0cb1882548fc141f4b764e82ff2e5154cfae2762. No integra main ni fusiona el bloque 1.
El validador privado toma funciones de validacion del commit LOCAL
b0da873b1dc3ff37bbafdf93eb6b8027d911885e, adaptadas a un paquete independiente,
sin importar factory2 ni otro codigo del candidato. Su copia aun necesita revision
antes de escoger el pin privado. La suite raiz es la de la base (49 Python);
las 23 nuevas pruebas cubren el diseño privado. No se confunden con las 60 de la
rama independiente del bloque 1 ni se afirma que aquel bloque desaparecio.

## Verificacion ejecutada

Desde ERP-FACTORY-correcciones/ERP-FACTORY-revision:

```powershell
& "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -B -m unittest discover -s tests -v
```

Resultado real: 23 pruebas, 0 fallos, 0 errores, 0 omitidas. Incluye lectura de tar
malicioso, enlaces/rutas/tamaños, fuente no ejecutada, version exacta, controles de
contexto, bloqueo antes de red, transporte SOLO simulado, datos fuera del system
prompt, huellas alteradas, PARTIAL, respuestas invalidas y mutaciones del YAML.
El workflow usa el subconjunto JSON de YAML; se analiza con json de Python, sin
instalar dependencias. Estos controles no equivalen a validar Actions en GitHub.

Desde ERP-FACTORY-correcciones:

```powershell
& "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -B -m unittest discover -s tests -v
node --test --test-reporter=tap pilot-js/tests/bottles.test.mjs
node --experimental-strip-types --test --test-reporter=tap pilot-js/tests/bottles.test.ts
```

Resultados reales: 49 Python, 5 JavaScript y 3 TypeScript, todos aprobados; 0 fallos,
0 errores y 0 omitidas. TypeScript sin comprobacion estatica de tipos. Total: 80
casos entre la suite nueva del revisor privado y la suite completa de la fabrica
base documentada. upstream/ permanece intacto y su suite heredada no se ejecuto.
Las pruebas Python se ejecutaron con la via autorizada del ejecutor para temporales;
no se cambiaron permisos del sistema, credenciales ni configuracion de red.

## No verificado y hallazgos pendientes

- Ejecucion real del workflow: NO VERIFICADA; el workflow esta bloqueado.
- Visibilidad, descarga, retencion efectiva y borrado de artefactos: NO VERIFICADOS.
- Minutos consumidos en GitHub: NO VERIFICADOS; no se ejecuto Actions ni se consulto
  facturacion. No se calculo un coste simulado como si fuera gasto real.
- GitHub, reglas de rama, autenticacion e identidades, compatibilidad de acciones,
  transporte real HTTPS, Claude y otros proveedores, Docker, ERP y despliegue:
  NO VERIFICADOS. Los dobles no acreditan integracion real.
- A2 se aborda mediante el diseño local; su despliegue, referencia privada revisada
  y protecciones quedan pendientes. El workflow y secreto publicos no se tocaron.
- A1 se reutiliza en el validador privado (diagnosticos/PARTIAL). No sustituye los
  cambios de la rama del bloque 1 en el repositorio publico.
- M1 se aborda para este nuevo flujo al separar datos e instrucciones. B6 tiene
  destino privado decidido; la privacidad efectiva aun no se comprobo.
- El bloque 3 (partes, lineas y cobertura calculada) y bloque 4 (aceptaciones,
  procedencia operativa, candado, permisos ERP, orquestador, entorno, presupuesto
  y piloto) siguen pendientes. La documentacion antigua del repositorio publico
  requiere su actualizacion del bloque 4; este bloque solo documenta el diseño nuevo.

## Entrega y publicacion futura

Commit y diff --stat respecto a 0cb1882 se entregan junto a este documento, fuera
del propio commit para no crear una autorreferencia. Sin push, PR remota ni uso
de gh/API. origin conserva push=DISABLED. Ninguna operacion de red en este bloque.
Antes de publicar un bloque con autorizacion escrita se verificara que el SHA
coincide exactamente con el entregado; si difiere, detenerse y avisar.
