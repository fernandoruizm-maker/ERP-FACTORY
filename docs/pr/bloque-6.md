# Propuesta de PR: revision manual y aprobacion de negocio/contabilidad

Rama local fix/bloque-6-revision-manual. Base comprobada e informada:
55073009fc30c810c7c7ede8c1ff3352071a2fe0. No hay push ni PR abierta.

## Cambio de modelo decidido por Fernando

Claude revisa en el chat cada PR (solo cambios); antes de entregas importantes,
revisa toda la fabrica en una conversacion nueva. Su revision tecnica no esta
autenticada y NO es aprobacion humana. Las personas son business (Fernando,
342326625) y accounting (FERRUMTJA, 352290329, contador con experiencia en ERP).
Ninguna programa. Riesgo aceptado documentado en ESTADO: no hay persona revisora
tecnica; auditoria tecnica externa obligatoria antes de datos reales o conexion ERP.

Actions queda APARCADO. Se registran USD, "1.00" por llamada, "12.00" por ejecucion,
"13.00" acumulado, 11 llamadas y opcion 1 (autorizacion manual). Esos valores no
autorizan gasto ni conectan el adaptador. if false, execution_enabled=false y
pin cero permanecen. No se crea repositorio privado, no se leen secretos y no se
cambia el YAML del workflow. El auditor local reconoce la nueva politica aparcada.

## Registro y puerta alternativa

Plantilla en docs/revisiones/PLANTILLA.md: PR, SHA base/revisado completos, modo,
archivos/diff, revisor fijo, hallazgos con gravedad/archivo/linea, conclusion y fecha.
No hay un informe real inventado en esta entrega. Las pruebas son ficticias.
Los informes reales se guardan como *.local.md, ignorados por Git por defecto:
agregar el informe al propio commit cambiaria el SHA y lo dejaria sin revision.
La plantilla y las guias si se versionan. El archivo local necesita conservarse;
no se ha creado un almacenamiento o respaldo externo automatico.

manual_review.py importa solo documentos Markdown acotados de docs/revisiones/,
con un unico bloque JSON y esquema cerrado. Rechaza plantilla, rutas fuera de
alcance, enlaces, patrones de credenciales y conclusiones inconsistentes. La
huella vincula el texto importado, no prueba su autor ni la exhaustividad del diff.
El detector de patrones es heuristico: no garantiza ausencia absoluta de secretos.

Store.import_manual_review guarda bytes/huella en una tabla separada. accept recibe
manual_review_id explicitamente: no se mezcla con review_id de V2. Las declaraciones
humanas mantienen version, source_sha, factory_digest, revision exacta y caducidad,
sin sustitucion silenciosa. El rol technical antiguo se rechaza, no se renombra
automaticamente en registros previos. Cambios de tarea/revision/rol requieren
nuevas aceptaciones. Los fixtures V2 se adaptan a accounting; su validador no cambia.

gate permite READY_FOR_MANUAL_REVIEW por esta via si la revision declara SIN
OBJECIONES TÉCNICAS, el SHA coincide y estan las dos aceptaciones vigentes; mantiene
las comprobaciones existentes de tarea, producto y pruebas. Devuelve siempre
provenance_authenticated=false, human_acceptances_authenticated=false y
publication_allowed=false. No devuelve APPROVED, no publica ni activa nada.
La falta de autenticacion no se trata como prueba de identidad ni como permiso;
es el limite aceptado expresamente para esta via documental local. La via privada
V2 conserva sus requisitos y sus motivos de bloqueo de autenticacion. Un identificador
manual no sirve para pasar por la via V2.

## Guias, proteccion y publicacion

GUIA-APROBAR.md separa negocio de contabilidad/funcionamiento y explica comparar
los 40 caracteres del SHA, comprobar resultados y cuando NO aprobar.
docs/github/ruleset-main.json propone main/Active, PR obligatoria, dos aprobaciones,
invalidacion tras cambios, ultimo envio aprobado por otra persona, conversaciones
resueltas, prohibicion de borrado/force push y bypass vacio. Guia clic a clic incluida.
El JSON es una propuesta local: no validado con GitHub ni aplicado. No se uso red.

Limites expresos: la regla por si sola no exige esos dos nombres ni restringe
Merge a ellos; revisar permisos y nombres es requisito posterior autorizado.
El autor no puede aprobar su propia PR: con solo estas dos personas queda pendiente
una identidad de autoria distinta. No se rebaja la regla para resolverlo. Nadie ha
verificado aun la proteccion efectiva, asi que no rige aun el permiso permanente.

PUBLICACION.md establece autorizacion por subida hasta esa verificacion; despues,
permiso permanente solo para ramas/PR de ERP-FACTORY. Integrar (solo las personas),
configuracion/permisos/protecciones, repositorios, secretos, gasto/activacion y todo
ERP/original siempre necesitan autorizacion expresa. Prohibicion de datos reales
incluso en ramas/comentarios/historial. Orden: bloque 1, luego factory2 del bloque 4
y bloque 6; no publicar ERP-FACTORY-revision/ ni la historia completa de estas ramas.
Cada paso indica Fernando/Codex/Claude y reversion sin force push.

Antes de esa publicacion selectiva hay que resolver dependencias de pruebas V2 con
la carpeta privada. Se demuestra que la puerta manual no llama al validador privado,
pero eso no prueba que toda la suite de una futura seleccion funcione sin la carpeta.
No se presenta esta rama completa como paquete ya listo para publicar esa seleccion.

## Verificacion

Focal ejecutada desde ERP-FACTORY-correcciones:

```powershell
& "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -B -m unittest tests.test_manual_review -v
```

Resultado: 18 pruebas, cero fallos, errores u omitidas. Incluye otro SHA, CORREGIR,
aceptacion faltante/caducada, rol antiguo, dos vias ambiguas, documento modificado,
version de tarea/fabrica, ausencia de autenticacion/publicacion y contenido del ruleset.
Suites completas ejecutadas despues de los cambios:

```powershell
# Desde ERP-FACTORY-correcciones
& "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -B -m unittest discover -s tests -v
node --test --test-reporter=tap pilot-js/tests/bottles.test.mjs
node --experimental-strip-types --test --test-reporter=tap pilot-js/tests/bottles.test.ts
# Desde ERP-FACTORY-correcciones/ERP-FACTORY-revision
& "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -B -m unittest discover -s tests -v
```

| Suite | Pruebas | Fallos | Errores | Omitidas |
|---|---:|---:|---:|---:|
| Raiz Python | 149 | 0 | 0 | 0 |
| Privada Python | 113 | 0 | 0 | 0 |
| JavaScript | 7 | 0 | 0 | 0 |
| TypeScript, sin comprobacion estatica de tipos | 3 | 0 | 0 | 0 |
| Total | 272 | 0 | 0 | 0 |

Python uso la via autorizada del entorno para temporales. No hubo ensayos fallidos
en este bloque. Comprobado con git check-ignore que PR-PRUEBA.local.md queda ignorado
sin crear un informe real. Los archivos de workflow y el validador V2 no tienen diff
respecto a 5507300. La prueba positiva manual impide invocar el contrato privado
mediante un doble que fallaria si se usara, sin simular una identidad autenticada.

NO VERIFICADO: revision real de Claude de este bloque, identidades/autoria de chat,
aprobaciones GitHub, esquema/importacion/menus/efectividad real del ruleset, permisos
de integracion por persona, ejecucion de workflows, coste/duracion, ERP/Docker/datos
reales, auditoria tecnica externa, ni la futura publicacion selectiva. Las pruebas
estaticas del JSON no acreditan configuracion de GitHub. No se instala nada.

Un commit previsto: `Add unauthenticated manual review path and business accounting approval guides`.
SHA final, todos los commits creados y diffs frente a 5507300 y 0cb1882 se entregan
en la respuesta y en ../entregas-locales/bloque-6-entrega.txt, fuera del commit para
no exigir su autorreferencia imposible. Sin nuevo ZIP. Esperar instrucciones al terminar.
