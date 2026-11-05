# Propuesta de PR: workflow privado V2 multiparte, preparado y bloqueado

Rama fix/bloque-5-multiparte. SHA de partida comprobado e informado antes de editar:
8ffb8115843fcb0f05b8c6a7c28adc0ce87c3934. Solo trabajo local y datos ficticios.
No se inicia otra revision real ni se crea/configura GitHub. No se toca upstream/,
la fabrica original, secretos, el workflow publico ni config.json de la fabrica.

## Diseno elegido y alternativas

Se eligen **pasos fijos**, en un unico trabajo privado, para un maximo de 11 llamadas.
Base 0cb1882 tiene 10 partes; si otra base tiene menos, la siguiente posicion es
cross y el resto se omite. Mas de 10 partes bloquea antes de llamar. Cada posicion:

1. Codigo PRIVADO fijado verifica la huella del estado recibido, prepara el mensaje
   y reserva todo el maximo por llamada antes de comunicar ready=true.
2. Sube el checkpoint de reserva a artefactos PRIVADOS (IN_FLIGHT, gasto reservado).
3. La Action de Claude fijada por commit llama, con secreto solo en ese paso,
   herramientas denegadas, max-turns 2, max-budget-usd obtenido de la reserva.
4. Un paso always() sin secreto recoge el archivo de ejecucion, valida contrato V2
   y guarda un checkpoint inmutable en cuanto recibe el resultado.
5. Otro paso always() sube ese checkpoint. No se llama al siguiente proveedor si
   fallo la subida anterior. No se reintenta una llamada ni una validacion.

Los pasos fijos son mas auditables aqui que una matriz paralela o un bucle CLI que
mantenga el secreto mientras prepara/valida todo. La Action ya esta fijada y sus
argumentos son los conocidos en este repositorio. Un CLI directo exigiria verificar
instalacion, version, autenticacion, eventos y ciclo de vida de otro proceso, todo
pendiente. No se asegura que la Action real no deje rastros de su credencial en el
runner: eso NO VERIFICADO forma parte de la revision previa a activar. Un solo job
conserva estado local y evita transportar source/estado entre runners; solo ejecuta
el validador privado fijado y nunca codigo publico. Sin credenciales persistentes
del checkout, permisos contents:read, una concurrencia global, manual/actor/SHA/
primer intento sin cambios. No hay matrix, continue-on-error ni wrapper de reintento.

workflow_spec.py define un esquema cerrado. workflow_audit.py exige igualdad de la
estructura completa y de la politica entregada; rechaza incluso campos adicionales,
orden/guardas alterados, pasos desconocidos, secretos fuera de Claude, topes omitidos,
timeouts ampliados, rutas amplias de artefactos y referencias dinamicas. Esta auditoria
tambien debe cambiar mediante revision expresa al autorizar una futura configuracion.
No es una aprobacion independiente del codigo que vive en la referencia privada.

## Material, contrato y checkpoints

El protocolo de partes/lineas, rangos, huellas, cobertura y cross es el V2 existente.
El sistema solo contiene instrucciones y esquema; los datos son JSON delimitado en
el turno de usuario. Cross recibe resultados validados e inventario, no codigo fuente.
Mantiene el limite de 60.000 bytes por mensaje y 100.000 por respuesta. La declaracion
del modelo no crea cobertura. NEEDS_HUMAN_REVIEW exige todas las partes y cross de
la misma version; nunca concede aprobacion, publicacion ni activacion.

La preparacion futura descarga solo un tar anonimo por URL/SHA fijo, valida rutas,
tamano, tipos y patrones de secretos en memoria, sin extraerlo. archive_packets
crea un indice Git aislado de nombres validados con blobs vacios y usa git ls-files
para clasificar todo el alcance; no ejecuta ni importa codigo publico. Los bytes
revisados y sus huellas proceden del tar. Se registra explicitamente
git_commit_object_verified=false: esto no equivale a verificar un objeto commit
remoto. packet() sobre el clon local si verifica el objeto Git. La descarga real y
su correspondencia con GitHub NO se han probado. No hay red en estas pruebas.

Estado local inmutable por fase, enlazado mediante SHA-256 en outputs. Partes y
rangos se vuelven a validar al leerlo. Se borra SOLO el archivo de salida conocido
de la Action antes de cada llamada futura para evitar reutilizar una respuesta vieja.
La ruta y formato reales de esa salida aun NO VERIFICADOS con la Action fijada.
Los prompts en outputs y sus limites reales en GitHub tampoco se han contrastado.

Cada artefacto contiene report.json, diagnostic.json, INFORME.txt, manifest.json,
budget.json e indice SHA256.json; response.txt solo tras validacion. La retencion
de respuesta no validada reutiliza las condiciones exactas del bloque 2, en
response.unvalidated.txt, con huella, aviso y estado BLOCKED, nunca en logs ni
diagnosticos. No se incluyen eventos brutos, entorno o sesiones. El importador de
factory2 admite budget.json solo como adjunto con huella, sin convertirlo en prueba
de facturacion ni en autenticacion; la puerta continua bloqueada.

## Fallos, tiempo y conservacion

- Primer fallo de proveedor, accion, evento incierto, salida ausente/invalida,
  permiso denegado o tope: parar, conservar evidencias, no mas llamadas ni reintentos.
- Una parte valida pero PARTIAL se conserva y detiene la secuencia; no hay cross.
  Un hallazgo BLOCK con cobertura completa sigue siendo evidencia valida y no se
  convierte en PASS por una pasada posterior.
- Si cross no cabe, o faltan partes completas, resultado PARTIAL y cero llamada final.
- Reservas inciertas permanecen cargadas por completo. Un coste reportado mayor
  que la reserva bloquea nuevas llamadas; no se presenta como factura comprobada.
- Cada subida tiene nombre unico por run/intento/fase. Se sube tambien la reserva
  ANTES de Claude: un corte abrupto deja evidencia de resultado desconocido.
- No existe garantia de ejecutar always() o subir archivos despues de que GitHub
  mate el runner, ni de exito de red de upload. Solo se pueden conservar remotamente
  checkpoints que ya se subieron. Un resultado aun no subido puede perderse; la
  reserva anterior permite conciliarlo sin repetir. Esto NO se oculta como garantia.

Timeout del paso Claude: 6 min = 360 s, unos 80 s por encima de los ~280 s previos
aportados por Fernando. Incluye arranque/instalacion de la Action y puede resultar
insuficiente; NO medido. Job: 120 min. Calculo conservador: 11 x (6 min llamada +
1 seleccion + 1 validacion + 1 subida previa + 1 posterior) = 110 min; checkout 2,
preflight 1, preparacion 3, subida inicial 1 = 117 min; quedan 3 min de margen.
No son duraciones observadas ni estimacion monetaria. Como maximo 23 artefactos,
retencion 7 dias; no se han medido minutos ni almacenamiento facturado.

## Presupuesto: lo implementado y decision pendiente de Fernando

USD, max_calls_per_execution=11. max_spend_per_execution=null y
max_budget_usd_per_call=null en politica privada; topes de gasto de config.json
siguen null. No hay valores monetarios por defecto. Un tope ausente impide arrancar.
Cada llamada reserva su techo completo, sin devolver diferencia automatica. El
techo efectivo por run es el menor entre el autorizado por ejecucion y el saldo
de una autorizacion local. No es garantia de que el proveedor respete el techo.

Opciones SIN nuevas credenciales de escritura (ninguna elegida/instalada):

1. **Autorizacion manual por ejecucion.** Fernando reserva en su PC el saldo que
   permite gastar y suministra una autorizacion unica ligada al SHA. GitHub limita
   esa ejecucion al saldo; luego Fernando descarga/importa los checkpoints. Reservar
   antes evita reutilizar dinero cuando una ejecucion queda incierta. El saldo no
   es un secreto ni una firma. GitHub desconectado NO puede detectar por si solo que
   el mismo ticket se usase en otro run; exige disciplina de uso unico/serializacion
   y una solucion revisada para aprovisionarlo. Menor infraestructura, mas operacion
   manual. No hay inputs ni adaptador de aprovisionamiento habilitados para elegir
   esta opcion implicitamente.
2. **Runner dedicado en el PC con coordinador local.** El job consulta/reserva en el
   mismo registro local bajo candado y transaccion; GitHub no escribe al registro
   por API. Evita la desconexion, pero exige instalar/aislar un runner, disponibilidad
   del PC, acceso minimo al registro y revisar su coexistencia con la fabrica original.
   No requiere un nuevo token de escritura del repositorio; si GitHub exige un token
   de registro del runner, su gestion/permiso queda para autorizacion posterior.

Comun implementado: LocalAllowances reserva atomicamente autorizaciones hasta un
tope explicito y conserva su importe entero incluso si no llegan resultados. Importa
checkpoints por huella, de forma idempotente, sin autenticar GitHub ni liberar saldo.
Detecta uso de un ticket en distintos runs al importar, suma sus cargos y bloquea
nuevas reservas hasta conciliacion. Esto NO impide el segundo uso remoto antes de
importar. El registro de autorizaciones es un componente local separado: falta
integrarlo con el ledger de intentos del bloque 4 y establecer un saldo inicial
que incluya gastos/reservas anteriores, sin duplicarlos ni olvidarlos. No se lee ni
migra ningun estado real aqui.

cumulative_strategy=null bloquea la ejecucion. La CLI futura espera authorization.json
con el contrato comun; **ningun paso lo aprovisiona** porque la opcion esta pendiente.
No se crea saldo a partir del modelo, del repo publico ni de una respuesta de Claude.
Configurar solo los tres bloqueos no bastara: hacen falta importes, adaptador revisado,
referencia privada revisada y nueva autorizacion expresa de intento real.

## Pruebas y entrega

Primera tanda focal: 23 pruebas multiparte aprobadas, cero fallos/errores/omitidas.
Se agregaron despues comprobaciones del paso CLI, checkpoint de estado corrupto,
opcion acumulada pendiente y compatibilidad del adjunto presupuestario en la puerta.

Comando focal ejecutado desde ERP-FACTORY-revision:

```powershell
& "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -B -m unittest discover -s tests -p test_multipart.py -v
```

Suites finales completas, despues de esos cambios:

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
| Raiz Python | 131 | 0 | 0 | 0 |
| Privada Python | 113 | 0 | 0 | 0 |
| JavaScript | 7 | 0 | 0 | 0 |
| TypeScript (sin comprobacion estatica de tipos) | 3 | 0 | 0 | 0 |
| Total | 254 | 0 | 0 | 0 |

Ambas ejecuciones Python usaron la via autorizada del entorno para temporales.
No hubo ensayos fallidos del bloque 5. La prueba sobre el commit local REAL
0cb1882548fc141f4b764e82ff2e5154cfae2762 inventario 91 archivos, genero 10 partes y
recorrio 11 llamadas FICTICIAS; no acredita que Claude haya leido esos archivos.
Las mutaciones del YAML verifican orden, secreto, tiempos, topes, subida, ausencia
de paralelismo/reintentos y prohibicion de ejecutar codigo publico.

Un solo commit previsto para este bloque: `Add blocked private multipart workflow and local allowance primitives`.
Su SHA final y el git diff --stat frente a 8ffb811 y 0cb1882 se entregan despues del
commit en la respuesta y en ../entregas-locales/bloque-5-entrega.txt. Un commit no
puede contener su propio SHA literal sin cambiarlo. El acta externa lo coteja con
la rama limpia y enumera todos los commits de este bloque. No se crea otro ZIP.

NO VERIFICADO: ejecucion/aceptacion del YAML en GitHub, visibilidad/retencion real de
artefactos, comportamiento de always() al cancelar, instalacion/limpieza/timeout de
la Action, ubicacion y formato de eventos reales de Claude Code (incluidos error/errors),
limites efectivos de gasto, costes y duracion reales, importacion autenticada desde
GitHub, identidades, Docker, ERP o coordinacion real con la fabrica original.
recover() real sigue bloqueado. Las llamadas/subidas ficticias no prueban integracion.

Sin red, push, PR, workflows, proveedores, activacion ni cambios en main. El bloque 5
requiere revision posterior antes de cualquier conexion; esta entrega no la autoriza.
