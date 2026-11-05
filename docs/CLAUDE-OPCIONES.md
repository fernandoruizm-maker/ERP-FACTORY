# Claude: diseno privado y limites vigentes

Fernando eligio Claude Code en GitHub Actions y un repositorio privado separado
como lugar de ejecucion, no solo de almacenamiento. Nombre provisional:
`fernandoruizm-maker/ERP-FACTORY-revision`. Su contenido esta preparado localmente
en `ERP-FACTORY-revision/`; no se creo ni configuro el repositorio en esta tarea.

El archivo publico `.github/workflows/claude-factory-review.yml` existe y se
conserva como flujo historico. No se consulto su estado actual en GitHub ni se
ejecuto. La propuesta privada esta desactivada, con politica false y pin revisado
pendiente. El borrador `docs/actions/claude-factory-review.yml.disabled` es OBSOLETO.
Las antiguas autorizaciones de publicacion no autorizan publicar estas correcciones.

## Contrato y aislamiento

El codigo publico se tratara exclusivamente como dato. El workflow y validador
deben proceder del repositorio privado y de una referencia fija revisada. El
diseno de un unico trabajo confiable y sus limites estan en el README privado;
las pruebas estaticas no verifican aislamiento real en un runner de GitHub.

El protocolo V2 local usa partes de hasta 60.000 bytes de mensaje de usuario,
lineas numeradas y huellas de version/parte. El sistema contiene instrucciones
y esquema; el codigo va como JSON delimitado en el turno de usuario. El validador
calcula cobertura desde partes completas y validas; una declaracion del modelo
no suple partes ausentes. PARTIAL nunca permite aprobar ni publicar.

La pasada final recibe TODOS los resultados validados y el inventario, **no el
codigo fuente**. Puede omitir interacciones no reflejadas en esos resultados.
El calculo local de 0cb1882 produjo 10 partes: una revision completa supondria
11 llamadas, condicionada a validacion y limite del mensaje final. No se hizo
ninguna de esas llamadas ni se midio su coste.

Los artefactos y respuestas se conservaran solo en el repositorio privado,
con retencion prevista de 7 dias, aun sin verificar. Las respuestas no validadas
solo se conservan bajo la decision restringida del bloque 2; permanecen BLOCKED
y nunca se revalidan o reintentan automaticamente.

## Presupuesto e integracion pendientes

Existe un registro local de reservas por ejecucion y acumuladas. Guarda intentos
antes de transmitir, mantiene cargos conservadores ante incertidumbre o rechazo
y evita reusar un identificador. Las transacciones impiden sobrepasar el saldo
local disponible. No sustituye una garantia monetaria impuesta por el proveedor.

Fernando autorizo 11 llamadas por ejecucion. Los dos importes y la moneda siguen
null y bloquean. No hay presupuesto monetario por defecto. Las pruebas usan la
unidad ficticia TST; no selecciona una moneda real ni es gasto medido. Los ejemplos
de tarifas del documento anterior eran historicos y no se usan para elegir topes
o afirmar precios actuales; no se consultaron precios ni planes.

Antes de cualquier intento real es obligatorio construir y revisar un workflow
multiparte que llame en orden, guarde cada parte validada inmediatamente, preserve
las anteriores ante fallos, aplique topes de llamadas y gasto por ejecucion y
acumulado, y no reintente automaticamente. **No esta construido ni autorizado
para ejecucion.** El registro local esta disenado para ese futuro coordinador,
pero la integracion no se ha probado.

## Plan de retirada: etapa posterior autorizada

1. Crear/configurar el repositorio privado; revisar su codigo y fijar el validador
   por SHA. Aplicar protecciones de main y revision de .github/ y del validador.
2. Completar autenticacion de personas/procedencia, coordinacion con la original,
   workflow multiparte y presupuesto autorizado. Verificar artefactos y controles
   reales sin operar dos fabricas a la vez.
3. Configurar el secreto solo en el repositorio privado y retirar el publico,
   con autorizacion especifica. No se leen ni trasladan secretos aqui.
4. Cuando el revisor privado este activo y verificado, retirar
   factory2/actions_review.py y .github/workflows/claude-factory-review.yml del
   flujo publico. Adaptar/eliminar consumidores y contratos antiguos de
   factory2/core.py::validate_review y factory2/review_packet.py::validate_complete
   para revision de fabrica. El contrato de producto simulado no autentica la
   fabrica. No mantener dos validadores operativos en paralelo.

Nada de esta migracion se ejecuto. La puerta sigue BLOCKED incluso con fixtures
completos: las huellas locales no autentican un run de GitHub ni a una persona.
NO VERIFICADO: eventos reales error/errors de Claude Code, proveedores, identidad,
Docker, ERP, workflow real, visibilidad/retencion de artefactos y minutos consumidos.
