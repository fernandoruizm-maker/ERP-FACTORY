# Publicacion vigente: aprobaciones por niveles

Decision posterior de Fernando: en **fernandoruizm-maker/ERP-FACTORY** basta
1 aprobacion de negocio de Fernando (fernandoruizm-maker, 342326625). Los productos
con impacto contable requieren 2: Fernando y FERRUMTJA (352290329), cada uno con
su cuenta. No es una autorizacion de publicacion ni de cambios remotos.

La puerta local distingue los niveles a partir del destino declarado en el
expediente y ligado a su version. No deduce que todo producto sea la fabrica.
Un destino ausente, incoherente o un nivel no decidido bloquea. El informe manual
de Claude sigue ligado al SHA exacto y nunca es una aprobacion humana autenticada.
Los registros locales tampoco autentican a las personas ni autorizan publicar.

Reglas que siguen vigentes:

1. La cuenta fernandocodex64-sudo NUNCA aprueba ni integra. No usar su nombre
   visible fenando-codex como si fuera otra persona aprobadora.
2. Nadie integra sin decision expresa de Fernando tras revision de Claude del
   SHA vigente y aprobaciones de su nivel. No integracion automatica ni bypass.
3. Cada subida requiere autorizacion expresa; destino unico ERP-FACTORY y envio
   de vuelta a DISABLED. Desde la decision del bloque 13, cuando Fernando autorice
   publicar una rama y su SHA, Codex la subira y abrira su PR con gh autenticado
   como fernandocodex64-sudo. Nunca aprobara ni integrara. Antes de publicar se
   comprobara la cuenta; si gh no esta preparado o la identidad difiere, detenerse.
   Esta decision no autoriza instalar, configurar credenciales ni publicar ahora.
4. Si cambia el contenido, destino o SHA: renovar revision, aceptaciones y decision.
5. Nunca publicar credenciales, datos de clientes o informacion del ERP. Activar
   fabrica/workflows, conectar ERP, cambiar permisos o gastar dinero requiere
   autorizacion especifica. Se mantiene la auditoria tecnica externa previa a
   datos reales o conexion ERP y el riesgo aceptado de no tener revisor tecnico humano.

**GitHub no se modifico.** La plantilla `docs/github/ruleset-main.json` conserva
el esquema anterior de 2 y no debe importarse como si reflejara esta decision.
Queda pendiente, con otra autorizacion: preparar/verificar la regla remota de
ERP-FACTORY con 1, manteniendo PR obligatoria, invalidacion tras nuevos cambios,
ultimo cambio aprobado por otra persona, conversaciones resueltas, prohibicion
de force push/borrado y sin bypass. En productos contables se necesitan 2 y
comprobar que las personas concretas son Fernando y FERRUMTJA: el contador de
GitHub por si solo no impone esos nombres. No se han consultado reglas remotas.

El bloque 9 continua en docs/bloque-9-docker. Tras el fetch autorizado del
6-11-2026 se incorpora origin/main 54b5bda8170a886755c768b1e2b7bfba5ac5eae4,
incluido el bloque 8. Se conservan Coordinator y roster(task); el unico conflicto
textual resuelto fue docs/ESTADO.md. Los resultados sobre el arbol combinado se
registran en pr/bloque-9.md. Claude reviso 6ce6af0 sin objeciones tecnicas segun
Fernando; la revision del nuevo SHA combinado queda pendiente. No hay autorizacion
de push. Docker no se repite: runner.py y el auxiliar siguen iguales al ensayo
documentado en DOCKER.md. Una futura subida exige permiso para su SHA concreto.

Para deshacer esta politica local, proponer una reversion revisada del commit;
volver al requisito anterior no cambia reglas remotas ni activa nada.

---

# Historia: PR unica para los bloques 1 a 7 (politica de dos aprobaciones anterior)

Los planes y cifras de aprobaciones siguientes son antecedentes, no instrucciones
para sustituir el esquema vigente de arriba ni permisos para ejecutar acciones.

Decision posterior de Fernando: este plan sustituye la publicacion selectiva y
la retirada separada. El plan anterior se conserva abajo como historia, NO como
instrucciones vigentes. No abrir ni integrar por separado revert/prueba-proteccion.
No se cierra ni modifica ninguna PR existente desde Codex.

## Contenido de la PR unica

- Rama: **publicacion/bloques-1-7**, creada desde origin/main actualizado mediante
  el unico fetch autorizado: **930528e2aad40aace0903311fc997c3d34024bd6**.
- Fuente completa: fix/bloque-7-cuenta-codex en
  **0ff127fd2a6fc65ec5d9064087c91b3bfcda6b91**, que ya contiene como ancestro
  fix/bloque-1-diagnostico en **b0da873b1dc3ff37bbafdf93eb6b8027d911885e**.
  Se conserva el contenido y el historial de los bloques 1 a 7. No volver a
  aplicar el bloque 1 encima del estado final ni restaurar versiones antiguas.
- Se elimina **docs/PRUEBA-PROTECCION.md** dentro de esta PR, sin integrar la rama
  de retirada separada. El merge 930528e permanece en el historial.
- **ERP-FACTORY-revision/ se incluye tal cual**, por decision expresa de Fernando.
  Sigue aparcado: condicion false, execution_enabled=false y pin del validador a
  ceros. Incluir su codigo no autoriza crear el repositorio privado, configurar
  secretos, ejecutar Actions ni hacer llamadas a proveedores. Las dependencias
  de pruebas V2 se conservan; ya no se necesita la separacion propuesta antes.
- No se cambia upstream/ ni la fabrica original. Los cambios nuevos de preparacion
  son esta aclaracion documental, las reglas de aprobacion y la retirada del aviso.
  El codigo operativo, pruebas, configuracion y carpeta privada coinciden con la
  fuente completa anterior; no se implementan funciones nuevas al publicar.

## Reglas obligatorias

1. **La cuenta fernandocodex64-sudo NUNCA aprueba ni integra.** Puede ser autora
   de la PR. Su nombre visible es fenando-codex, ID 353061596.
2. **Nadie integra sin decision expresa de Fernando tras la revision de Claude
   del SHA vigente.** Esto se mantiene aunque GitHub muestre el boton disponible
   o ya existan dos aprobaciones. No usar integracion automatica.
3. Fernando aprueba como fernandoruizm-maker (negocio); FERRUMTJA aprueba desde
   su propia cuenta (contabilidad/funcional). Solo una de estas dos personas puede
   integrar despues de la decision expresa. Codex no abre, aprueba ni integra la PR.
4. Las revisiones anteriores de bloques son antecedentes. No afirmar que Claude
   ya reviso el nuevo SHA combinado: debe comprobar la version final y los cambios
   de preparacion antes de la decision de Fernando. Una modificacion posterior
   exige repetir la comprobacion del SHA y renovar la decision correspondiente.

## Preparacion y entrega autorizadas

1. Combinar la fuente completa con main en la rama nueva; la combinacion realizada
   no produjo conflictos textuales. Eliminar solo el aviso de prueba y conservar
   los archivos revisados. No avanzar main ni otras ramas de los bloques.
2. Ejecutar suites completas con datos ficticios, sin red ni proveedores:

   ```powershell
   # Desde ERP-FACTORY-correcciones
   & "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -B -m unittest discover -s tests -v
   node --test --test-reporter=tap pilot-js/tests/bottles.test.mjs
   node --experimental-strip-types --test --test-reporter=tap pilot-js/tests/bottles.test.ts
   # Desde ERP-FACTORY-correcciones/ERP-FACTORY-revision
   & "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -B -m unittest discover -s tests -v
   ```

   Entregar numeros reales de aprobadas, fallos, errores y omitidas, SHA final,
   lista de commits y diff --stat contra origin/main. Los logs se conservan fuera
   del repositorio en entregas-locales; no publicar respuestas ni credenciales.
   TS se ejecuta sin typecheck. Dobles simulados no acreditan integracion real.
3. Solo con aprobacion de red para ese push: habilitar el destino unico
   https://github.com/fernandoruizm-maker/ERP-FACTORY.git, subir exclusivamente
   publicacion/bloques-1-7 y restaurar DISABLED. No token en URL ni nuevas
   solicitudes de credenciales; si la credencial guardada falla, detenerse.
4. Codex entrega enlace, titulo y texto. Fernando abre la PR desde la web con la
   sesion fernandocodex64-sudo y base main. No abrirla desde su cuenta aprobadora.
5. Claude revisa el SHA final; ambas personas aprueban; Fernando decide por escrito
   si integrar. Hasta entonces no integrar, activar ni conectar nada. No existe
   permiso permanente nuevo por esta autorizacion puntual de subida.

## Limites y recuperacion

GitHub muestra el codigo en un repositorio publico. La autorizacion de incluir
ERP-FACTORY-revision/ comprende su codigo revisado, no secretos, datos de clientes,
informes privados reales ni salidas de proveedores. No se anaden esos datos.
Los valores de presupuesto registrados no autorizan gastar dinero.

No verificados por pruebas locales: funcionamiento real de workflows, proveedores,
identidades y aprobaciones remotas, almacenamiento de artefactos, Docker, ERP,
costes ni auditoria tecnica externa. La fabrica sigue desactivada. Se conserva
la exigencia de auditoria tecnica externa antes de datos reales o conexion al ERP.

Antes de integrar, una decision de cancelar permite cerrar la PR, sin borrar
historial. Despues de una integracion autorizada, cualquier reversion sera otra
PR revisada y autorizada. No force push, no borrado de main ni reintentos de pago.

---

# Archivo historico: plan selectivo anterior, sustituido

Las instrucciones siguientes describen la decision anterior. Las exclusiones de
la carpeta privada y la retirada en PR separada NO rigen para la PR unica actual.
Se conservan como registro; no ejecutarlas en paralelo al plan vigente.

# Plan de publicacion tras la PR de prueba integrada

Este documento es un plan, no una autorizacion para ejecutar sus pasos futuros.
Solo se ha subido la rama de retirada indicada abajo. No se abrio, aprobo ni integro
ninguna PR desde Codex. El envio vuelve a DISABLED despues de cada subida autorizada.
El repositorio fernandoruizm-maker/ERP-FACTORY sigue siendo PUBLICO.

## Reglas obligatorias para todas las PR

1. **La cuenta fernandocodex64-sudo NUNCA aprueba ni integra.** ID 353061596;
   fenando-codex es solo su nombre visible. Puede ser autora de las PR.
2. **Nadie integra sin decision expresa de Fernando despues de la revision de
   Claude del SHA vigente, aunque GitHub muestre el boton disponible.** Las dos
   aprobaciones no sustituyen esa decision. No usar integracion automatica.
3. Solo Fernando (fernandoruizm-maker, negocio) y FERRUMTJA (contabilidad/funcional)
   aprueban con sus cuentas personales. Tras la decision de Fernando, solo una
   de esas dos personas realiza la integracion. Codex nunca lo hace.
4. Si cambia un archivo o el SHA, Claude debe revisar la version nueva y las
   personas deben comprobar de nuevo sus aprobaciones. Una PR de prueba marcada
   NO INTEGRAR se cierra sin integrar, incluso si parece lista.
5. Cada subida continua necesitando autorizacion expresa. El incidente no acredita
   que las reglas fallen tecnicamente, ni que el permiso permanente condicionado
   este cumplido: falta revisar evidencia de proteccion y la lista de excepciones.

No subir datos reales de clientes, credenciales, informacion del ERP ni informes
sensibles, tampoco a ramas. Revisar archivos e historial antes de cada envio.
No tocar el ERP, upstream/, la fabrica original, secretos, reglas o configuracion
remota. Activar workflows, gastar dinero, crear repositorios o cambiar permisos
requiere una autorizacion nueva y especifica. La fabrica sigue desactivada.

## Situacion verificada y evidencia comunicada

- Fernando informa que FERRUMTJA integro por error la PR #7 y abrio la #8 para
  revertirla; Fernando cerro la #8. No se consultaron esas PR por API o navegador.
- Un unico fetch HTTPS anonimo autorizado trajo origin/main a
  **930528e2aad40aace0903311fc997c3d34024bd6**. El commit es el merge de la PR #7,
  con padres 0cb1882548fc141f4b764e82ff2e5154cfae2762 y
  97940f524d077169579ddb0f47fb4f34f34a45d1.
- Frente a 0cb1882, su unico cambio es docs/PRUEBA-PROTECCION.md (cinco lineas).
- Rama creada y subida: **revert/prueba-proteccion**,
  **63c37154efb91de7152e10815f355a2fa7a018bf**, hija directa de 930528e.
  Solo elimina ese archivo; su arbol es identico al de 0cb1882. No borra el merge
  del historial. No se ha integrado esa retirada en main.
- El push autorizado termino con exito usando la credencial ya guardada, con
  interaccion deshabilitada. No se leyo ni mostro el token. Envio restaurado a DISABLED.
- Usuario correcto fernandocodex64-sudo; opciones de Git locales y wincredman.
  No afirmar que los scopes del token, el aislamiento de Windows o las reglas de
  GitHub quedaron certificados por conseguir subir una rama.
- Ruleset 26650549 activo segun Fernando, con las condiciones ya comunicadas por
  Claude. No se verifico su estado remoto en esta tarea. Bypass debe comprobarse
  en pantalla por Fernando; disponibilidad del boton no es permiso empresarial.

## PR inmediata: retirar el archivo de prueba

Fernando abre desde la web, con la sesion fernandocodex64-sudo, una PR nueva:
base main, rama revert/prueba-proteccion. No reabrir ni modificar la #8 aqui.

Titulo propuesto: **Retirar el archivo de prueba integrado por error**.

Texto propuesto:

> Elimina unicamente docs/PRUEBA-PROTECCION.md, incorporado por la PR #7
> (merge 930528e). No modifica codigo, configuracion ni workflows.
>
> Base revisada: 930528e2aad40aace0903311fc997c3d34024bd6.
> SHA propuesto: 63c37154efb91de7152e10815f355a2fa7a018bf.
> Comprobacion local: un archivo eliminado, cinco lineas; el arbol resultante
> coincide con 0cb1882. No se ejecutaron suites porque solo se retira un aviso.
>
> Claude debe revisar este SHA. Fernando y FERRUMTJA revisan con sus cuentas.
> Nadie integra sin decision expresa posterior de Fernando, aunque el boton
> este disponible. La cuenta fernandocodex64-sudo nunca aprueba ni integra.

Como deshacer: antes de integrar, cerrar la PR con autorizacion. Si despues se
necesitara restaurar el aviso, proponer otro commit y PR, nunca reescribir main.
No restaurarlo automaticamente al preparar bloques posteriores.

## Por que no subir las ramas de bloques directamente

Las ramas guardan desarrollo acumulado; sus nombres no delimitan el contenido
que llegaria a GitHub. La rama del bloque 7 incluye ancestros de los bloques 3 a 6,
y estos incluyen el revisor privado. Subirla publicaria tambien ese historial.

Hay una excepcion al apilado lineal: fix/bloque-2-aislamiento no contiene el commit
b0da873 de la rama final del bloque 1; conserva la version anterior 9109e05.
La base fa650d7 del bloque 3 combina el bloque 1 final y el bloque 2. No tratar
las siete ramas como siete PR independientes listas para integrar.

Referencias locales comprobadas (fuentes para seleccionar contenido, NO para push):

| Bloque | Rama fuente | SHA de referencia | Destino previsto |
|---|---|---|---|
| 1 | fix/bloque-1-diagnostico | b0da873 | PR publica 1 |
| 2 | fix/bloque-2-aislamiento | f288441 | Revisor privado aparcado |
| 3 | fix/bloque-3-cobertura | ad91cb3 | Revisor privado aparcado |
| 4 | fix/bloque-4-operacion | 8ffb811 | Seleccion operativa en PR publica 2 |
| 5 | fix/bloque-5-multiparte | 5507300 | Multiparte aparcado; revisar dependencia publica indicada abajo |
| 6 | fix/bloque-6-revision-manual | 31abe68 | Via manual/configuracion en PR publica 2 |
| 7 | fix/bloque-7-cuenta-codex | 7650098 mas este commit documental | Guias seleccionadas en PR publica 3 |

## Orden propuesto de PR de los bloques 1 a 7

Primero terminar la retirada anterior: revision de Claude, dos aprobaciones,
decision expresa de Fernando e integracion humana. Despues se obtiene, solo con
otra autorizacion de red, el main real resultante. No asumir que su SHA sera
63c3715: depende de como se integre la PR y de si hubo otros cambios.

No se han creado las ramas de publicacion propuestas en esta tabla. Cada una
nacera del main actualizado DESPUES de integrar la PR anterior, no de las ramas
apiladas. Todas tendran main como destino. Antes de cada push: permiso para la
rama y SHA concretos, destino unico ERP-FACTORY, y retorno a DISABLED.

| Orden | PR / rama nueva propuesta | Base y fuente | Contenido y exclusiones |
|---|---|---|---|
| 1 | Diagnostico seguro y revisiones parciales / publicar/bloque-1 | Main tras retirada; contenido del commit b0da873 | factory2/actions_review.py, tests/test_actions_review.py, docs/pr/bloque-1.md y registro acotado en docs/PLAN.md y docs/ESTADO.md. No carpeta privada ni cambios de workflows. |
| 2 | Operacion local y revision manual / publicar/bloques-4-6 | Main tras PR 1; seleccion de 8ffb811 y estado final publico de 31abe68 | factory2/ operativo del bloque 4 con correcciones del 6, config.json del modelo manual, pruebas raiz/JS/TS pertinentes, .gitignore para informes locales, README, LEEME, docs/CLAUDE-OPCIONES.md, docs/revisiones/, guias de aprobacion/proteccion y sus referencias. Sin ERP-FACTORY-revision/. No cambiar workflows activos; borrador .disabled solo marcado obsoleto. |
| 3 | Guias de cuenta, publicacion y reglas humanas / publicar/bloque-7 | Main tras PR 2; documentos vigentes de fix/bloque-7-cuenta-codex | docs/github/GUIA-CUENTA-CODEX.md, docs/github/CONFIG-LOCAL-CODEX.md, docs/PUBLICACION.md, actualizacion acotada de docs/ESTADO.md y reglas vigentes de docs/GUIA-APROBAR.md. Nunca .git/config, registros de credenciales ni datos de entregas-locales. |

### PR 1: preparacion y comprobacion futura

Codex prepara una rama nueva con el cambio aislado de b0da873, conservando el
estado actual de main. Un cherry-pick de ese commit puede servir si su diff e
historial siguen limitados a los cinco archivos indicados; no aplicar commits
adicionales de otras ramas. Registrar nuevo SHA y revisar el diff base/candidato.
Ejecutar la suite raiz Python y las pruebas JS/TS aplicables sobre esa seleccion,
con los comandos del bloque 1; no reutilizar como resultado los numeros historicos.
No ejecutar Actions ni proveedores. Un informe PARTIAL nunca aprueba ni publica.

Codex entrega SHA, pruebas reales, titulo y texto. Fernando abre la PR en la web
como fernandocodex64-sudo. Claude revisa solo ese diff y el SHA exacto. Las dos
personas aprueban con sus cuentas; Fernando decide expresamente si integrar.
Para deshacer: cerrar antes de integrar o una PR de reversion revisada despues.

### PR 2: dependencia que debe resolverse antes de publicar

No copiar factory2/ a ciegas ni hacer cherry-pick de los bloques completos.
El estado publico final de 31abe68 incluye un ajuste del bloque 5 en
factory2/review_import.py y tests/test_operation.py. Revisarlo como dependencia
V2 del bloque operativo; no es permiso para publicar el workflow multiparte.
Mantener el importador V2 bloqueado si no dispone de su contrato privado; no
sustituirlo por un informe aceptado ni rebajar comprobaciones.

Bloqueo concreto de la seleccion actual: factory2/review_import.py carga
ERP-FACTORY-revision/reviewer y tests/operation_fixtures.py construye artefactos
usando ese contrato. tests/test_operation.py y otras pruebas reutilizan esas
fixtures. Aunque la via manual tiene una prueba de independencia, la suite completa
seleccionada NO esta verificada sin esa carpeta. Antes de publicar hay que separar
las fixtures de la via manual y las pruebas privadas de contrato, conservando
pruebas publicas de rechazo cuando V2 no esta disponible. Esa adaptacion es trabajo
futuro con nuevo SHA y revision, NO se implementa en este plan.
No ocultar fallos omitiendo pruebas en silencio ni subir la carpeta privada para
hacerlas pasar. Si la separacion exige otro diseno, presentar la decision a Fernando.

Seleccionar las versiones finales de state/core/providers/runner/workflow, permisos,
candado, presupuesto, adaptador, orquestador, piloto y manual_review con sus pruebas.
Conservar los roles business/accounting, los interruptores desactivados y los
limites registrados, que no autorizan gasto. No editar upstream/. docs/ESTADO.md
y docs/PLAN.md se concilian por secciones: conservar incidentes de main y el bloque
1, y agregar evidencia del nuevo candidato; no sobrescribirlos con una version vieja.

Ejecutar suites completas de la seleccion: Python raiz, JS y TS (sin presentar la
ejecucion TS como typecheck). La suite privada queda en su rama local aparcada;
no afirmar que paso sobre una PR que no contiene esos archivos. Datos ficticios,
sin Docker/proveedores/ERP reales. Registrar fallos, omisiones y limites exactos.
Claude revisa diff y dependencias y, por ser entrega importante, toda la fabrica
en una conversacion nueva. Dos aprobaciones y decision de Fernando antes de integrar.
Para deshacer, PR de reversion; sin migraciones, activacion ni despliegue automatico.

### PR 3: documentacion y continuidad

Seleccionar solo las guias publicables desde la rama documental. Las dos reglas
humanas ya rigen desde esta decision: no esperar a publicar PR 3 para cumplirlas.
Incluirlas tambien en la GUIA-APROBAR de PR 2, evitando que se publique una guia
anterior que aun deja pendiente la cuenta autora. PR 3 no debe deshacerlas.
Conservar los resultados de PR 1 y 2 en ESTADO, distinguiendo historia de estado
actual. Revisar enlaces, nombres/ID, pasos de reversion y que ningun texto afirme
que Claude o GitHub verificaron algo no comprobado. Una guia no activa sus pasos.
Codex prepara texto; Fernando abre desde la web salvo autorizacion posterior para
gh. Revision de Claude, dos aprobaciones y decision expresa de Fernando.
Para deshacer, reversion documental por PR; nunca revertir permisos por automatismo.

## ERP-FACTORY-revision/: bloques 2, 3 y 5 aparcados

No hay PR publica para esos bloques ahora. Conservar codigo, tests y artefactos de
desarrollo en sus ramas locales. No subir esas ramas ni crear repositorio privado.
No copiar sus archivos en otra carpeta publica para evitar esta restriccion.
Tampoco publicar commits ancestros que los contengan aunque luego se borren.

Siguen los tres bloqueos: condicion false, execution_enabled=false y pin de ceros.
USD 1.00/llamada, 12.00/ejecucion, 13.00/acumulado y 11 llamadas son limites
registrados, no autorizacion. Si Fernando reactiva esta linea, sera otro plan y
otra autorizacion para repositorio privado, validacion, credenciales y gasto.
El workflow publico historico y factory2/actions_review.py no se retiran ahora;
la retirada coordinada se revisara cuando exista sustituto activo autorizado.

## Conflictos con main: resultado y limites

Analisis local sin cambiar ramas ni hacer merges: git merge-tree --write-tree
origin/main <rama> para las siete ramas fuente anteriores. Los siete terminaron
con codigo 0, sin conflictos textuales frente a 930528e. No se ejecutaron sus
arboles calculados ni se adoptaron como candidatos de publicacion.

La razon es que main solo anadio el archivo de prueba, que esas ramas no cambian.
Esto NO significa que convenga integrarlas: incluirian contenido aparcado. Ademas,
un merge directo conservaria el aviso de prueba mientras la retirada no se integre.
El arbol de 63c3715 coincide exactamente con 0cb1882, pero el historial ya avanzo.

Los conflictos futuros entre selecciones de documentos y dependencias de pruebas
no se han resuelto ni simulado. Especial cuidado con docs/ESTADO.md, docs/PLAN.md,
config.json y state.py: integrar el estado final deliberadamente, no elegir todo
"nuestro" o todo "suyo". Volver a calcular diff y pruebas si cambia main; un nuevo
SHA exige nueva revision. No inventar que las suites anteriores cubren la seleccion.

## Verificacion de esta entrega y limites

Ejecutado: un fetch de main, comparacion de arboles/nombres de archivos, commit de
retirada, un push de esa rama y restauracion DISABLED; siete analisis merge-tree,
inspeccion de dependencias, enlaces locales y git diff --check de documentos.
No suites de proyecto: retirada de un aviso y plan documental, sin codigo cambiado.
No se abrieron PR ni se inspeccionaron por red #7/#8; no se aprobaron ni integraron.
No se preparo ni publico ninguna rama de los bloques. No verificados reglas actuales,
identidad remota autenticada via API, selecciones finales, conflictos futuros,
suites sobre esas selecciones, workflows, coste, ERP, Docker ni auditoria externa.

La falta de revisor tecnico humano sigue siendo un riesgo aceptado: Claude no
esta autenticado como persona aprobadora. Se requiere auditoria tecnica externa
antes de usar datos reales de clientes o conectar el ERP.

GitHub CLI sigue fuera de esta tarea. Para su etapa futura ver
[CONFIG-LOCAL-CODEX.md](github/CONFIG-LOCAL-CODEX.md): directorio exclusivo, entrada
oculta por Fernando, no mostrar tokens y detenerse si public_repo no basta.
