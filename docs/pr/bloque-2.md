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
solo a artefactos privados con retencion propuesta de 7 dias. Los rechazos de
formato, version o evidencia pueden conservar texto original solo bajo la decision
restringida de Fernando que se detalla abajo. Errores de ejecucion, respuestas
posiblemente sensibles o demasiado grandes conservan solo codigos y huella disponible.
Nunca se suben estos datos al repositorio publico. Las pruebas usan solo ficticios.

El commit adicional conserva evidencia tambien ante fallos tempranos: archivo de
ejecucion ausente, enlace/directorio/tamaño invalido, error de lectura, JSON o
estructura invalida, o material ausente/alterado/de otra version. En esos casos
artifacts/ contiene report.json BLOCKED, diagnostic.json, SHA256.json e INFORME.txt,
sin texto libre del proveedor, rutas ni excepciones. reason_code pertenece a un
conjunto fijo; nunca se obtiene comparando mensajes de excepcion.
El archivo de ejecucion se comprueba primero; si es valido, se verifica el material
antes de validar sus hallazgos. Ninguna de estas salidas puede producir aprobacion.
No se sobrescribe evidencia previa. Si el propio directorio de salida no permite
escritura, no se promete producir archivos: se falla sin cambiar sus permisos.

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
las 57 pruebas actuales cubren el diseño privado. No se confunden con las 60 de la
rama independiente del bloque 1 ni se afirma que aquel bloque desaparecio.

## Verificacion ejecutada

Desde ERP-FACTORY-correcciones/ERP-FACTORY-revision:

```powershell
& "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -B -m unittest discover -s tests -v
```

Resultado final real de esta entrega: 57 pruebas, 0 fallos, 0 errores, 0 omitidas. Incluye lectura de tar
malicioso, enlaces/rutas/tamaños, fuente no ejecutada, version exacta, controles de
contexto, bloqueo antes de red, transporte SOLO simulado, datos fuera del system
prompt, huellas alteradas, PARTIAL, respuestas invalidas y mutaciones del YAML.
El workflow usa el subconjunto JSON de YAML; se analiza con json de Python, sin
instalar dependencias. Estos controles no equivalen a validar Actions en GitHub.
Ocho pruebas nuevas comprueban salidas bloqueadas con sus huellas, errores de
lectura simulados, material invalido, la ruta completa del CLI sin archivo,
rechazo de reason_code libre, conservacion de evidencia previa y la ruta valida.

Registro historico del ajuste a8cfa18: su primera ejecucion tuvo 31 pruebas, 1 fallo y 22 errores
(incluidos subcasos), sin omitidas, por un operador ausente al concatenar el texto
del informe. Se corrigio y se repitio la suite privada completa: 31/31. El resultado
fallido no se presenta como validacion. Las suites de base y Node pasaron y sus
archivos no cambiaron despues; no se ejecutaron proveedores para estas pruebas.

Desde ERP-FACTORY-correcciones:

```powershell
& "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -B -m unittest discover -s tests -v
node --test --test-reporter=tap pilot-js/tests/bottles.test.mjs
node --experimental-strip-types --test --test-reporter=tap pilot-js/tests/bottles.test.ts
```

Resultados reales: 49 Python, 5 JavaScript y 3 TypeScript, todos aprobados; 0 fallos,
0 errores y 0 omitidas. TypeScript sin comprobacion estatica de tipos. Total: 114
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

## Destino de publicacion y orden propuesto (NO ejecutado)

Publicar el bloque 2 significa CREAR EL REPOSITORIO PRIVADO con el CONTENIDO de
ERP-FACTORY-revision/ como su raiz. No significa integrar esta rama completa en
ERP-FACTORY ni alojar alli el workflow del revisor. Los documentos docs/pr/ y
docs/ESTADO.md de esta rama son evidencia de la entrega local, no una orden de
fusionar la carpeta privada en el repositorio publico.

Orden propuesto, sujeto a autorizacion posterior por destino y bloque:

1. Bloque 1 en ERP-FACTORY, solo si Fernando autoriza esa correccion transitoria
   del diagnostico publico; mantener la fabrica y cualquier nuevo intento apagados.
2. Bloque 2 actualizado: publicar exclusivamente el contenido de la carpeta nueva
   en ERP-FACTORY-revision PRIVADO. Revisar y fijar alli el commit del validador.
3. Bloque 3: por la ultima decision de Fernando, su rama local debe contener el
   contenido de b0da873 (bloque 1) y TODO fix/bloque-2-aislamiento actualizado,
   incluido a8cfa18 y la conservacion restringida. Resolver el registro compartido
   y ejecutar todas las suites antes de añadir codigo. Desarrollar partes, lineas
   y cobertura exclusivamente en el revisor privado; publicar solo su subarbol
   privado, sin trasladar alli el validador publico. La integracion local conjunta
   no autoriza fusionar la rama completa en ERP-FACTORY ni publicar nada.
4. Bloque 4: integrar las condiciones operativas de la fabrica en ERP-FACTORY,
   con el importador vinculado a la evidencia del revisor privado. Resolver y
   revisar sus dependencias expresamente; no trasladar secretos o informes alli.
5. Cuando el revisor privado este verificado y autorizado para operar, retirar
   factory2/actions_review.py y .github/workflows/claude-factory-review.yml del
   repositorio publico, junto con sus referencias/pruebas obsoletas. Retirar su
   secreto publico en esa misma migracion autorizada. Deshabilitar la via publica
   antes de permitir la privada: no mantener dos validadores operativos ni dos
   rutas de ejecucion. Estos retiros NO se han realizado en esta entrega.

El choque de docs/ESTADO.md con el bloque 1 se resuelve conservando ambas secciones:
primero el registro del bloque 1 y despues el del bloque 2 como revision PRIVADA.
No usar una sustitucion global de un lado por el otro ni borrar resultados previos.
Conservar la distincion entre las 60 pruebas de la rama 1 y las 49 de la base de la
rama 2, mas las 57 privadas actuales. Como el bloque 2 no se fusiona entero en ERP-FACTORY,
esa reconciliacion documental solo se aplica si se autoriza trasladar el registro;
no es necesario fusionar codigo privado para resolverla. Reejecutar las pruebas
pertinentes si la futura integracion modifica codigo, y entregar su nuevo SHA.

La rama provisional del bloque 3 creada antes de esta aclaracion no tiene cambios
propios de codigo; solo copias locales de los commits 1 y 2. No se publicara ni se
usara como base. Se conservara como referencia local y la rama de trabajo del
bloque 3 partira del bloque 2 actualizado e incorporara el bloque 1 conforme a la
ultima decision. Ningun codigo nuevo del bloque 3 se añade antes de verificarlo.

## Decision adicional: conservar texto no validado exclusivamente en privado

Fernando autoriza response.unvalidated.txt SOLO para un unico evento result
exitoso (subtype success, is_error=false, 1-2 turnos, sin denegaciones ni otros
eventos de error), texto UTF-8 de hasta 100.000 bytes y sin coincidencia del texto
ORIGINAL completo con SECRET_PATTERN. Se comprueba antes de parsear o guardar.

Lista cerrada: INVALID_JSON (incluido JSON envuelto en Markdown), REPORT_STRUCTURE,
VERSION_MISMATCH, COVERAGE_STRUCTURE, INVALID_VERDICT, MISSING_LIMITATIONS,
INVALID_FINDINGS, FINDING_STRUCTURE, INVALID_FINDING_EVIDENCE, CONTRADICTORY_PASS.

Nunca se conserva para POSSIBLE_SECRET, OUTPUT_SAFETY_OR_SIZE,
RESULT_MISSING_OR_TOO_LARGE, RESULT_EXECUTION_INVALID, ACTION_FAILED, eventos de
error del proveedor o fallos tempranos de archivo, material o procedencia.
Un codigo nuevo/no reconocido tampoco concede conservacion.

El archivo guarda el texto original exacto, sin reserializarlo. Su SHA-256 coincide
con response_sha256 de report.json y con su entrada en SHA256.json. report.json
añade unvalidated_response_saved=true y conserva BLOCKED y reason_code, sin texto
libre. INFORME.txt incluye la frase exacta solicitada:
"Respuesta NO VALIDADA conservada solo para diagnóstico privado; no es una revisión aceptada."
No hay revalidacion, reintento, aprobacion ni paso a PARTIAL/NEEDS_HUMAN_REVIEW
automaticos. Ningun lector de este flujo consume response.unvalidated.txt.

Pruebas nuevas: 26, todas con datos ficticios. Hay una prueba por cada uno de los
10 codigos que conserva; se comprueban bytes, huellas, bandera y estado BLOCKED.
Se comprueban los codigos excluidos, errores previos aun con resultado final
exitoso, turnos/denegaciones, fallos tempranos (tambien cubiertos por la suite
anterior), un token ficticio en JSON invalido, token escapado detectado al validar,
el limite exacto y el exceso de 100.000 bytes, Markdown/Unicode/CRLF, ausencia de
texto en report.json/INFORME.txt/diagnostic.json y consola, y como maximo una
validacion sin reintento. Suite privada 57/57; raiz 49/49; JS 5/5; TS 3/3.
No hubo fallos, errores u omitidas en esta nueva entrega de conservacion.

Referencia anterior: a8cfa18680e238dbae3ba2f6283e82589e6eb5dd. El nuevo SHA se
entrega al confirmar el commit y se registra en la nota de integracion de la rama
3. Puede consultarse localmente con `git rev-parse fix/bloque-2-aislamiento`.
No se incluye un SHA autorreferente imposible dentro de su propio commit.

## Entrega y comprobacion futura

Commit y diff --stat respecto a 0cb1882 se entregan junto a este documento, fuera
del propio commit para no crear una autorreferencia. Sin push, PR remota ni uso
de gh/API. origin conserva push=DISABLED. Ninguna operacion de red en este bloque.
Antes de publicar un bloque con autorizacion escrita se verificara que el SHA
coincide exactamente con el entregado; si difiere, detenerse y avisar. Para crear
el repositorio privado se exportara exactamente el subarbol ERP-FACTORY-revision/
de ese SHA, sin cambios de codigo adicionales. El nuevo commit del repositorio
privado tendra otra historia y puede tener otro SHA: cotejar los archivos y el
arbol exportado con la referencia local entregada, no afirmar que ambos commits
son el mismo. La creacion, configuracion y conexion siguen fuera de esta tarea.
