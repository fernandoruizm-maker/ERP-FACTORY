# Bloque 12: gasto calculado para llamadas completadas

Titulo propuesto: Liquidar las llamadas completadas con uso valido sin modificar el historial.

Rama `fix/bloque-12-gasto-real`, desde `origin/main` comprobado mediante el unico
fetch autorizado en `f745cde657c18fb7cefcacf4e2c05ea96a5527ba`.
Trabajo local: sin subida, PR, activacion ni llamadas a proveedores.

## Cambio y controles

Antes, una llamada completada seguia consumiendo toda su reserva aunque el uso
validado permitiera calcular un coste menor. Ahora `charged_units=actual_units`
solo al finalizar como COMPLETED, con uso validado y coste dentro de la reserva.
`reserved_units` conserva el importe original. Las cantidades son enteros de
millesimas de milesima de USD (1 USD = 1.000.000 unidades), sin coma flotante.
Es coste calculado con los precios configurados, no una factura comprobada:
`billing_verified=false` permanece.

`usage_validated` es una senal interna del llamador, no una autenticacion. Su
valor predeterminado es false: los adaptadores antiguos no liberan reservas.
PilotTrial la establece solo tras validar el uso, la respuesta y el alcance,
y comprobar los limites autorizados de tokens ANTES de liquidar la llamada.
Los cambios de `calls` y `paid_attempts` siguen dentro de una misma transaccion.
Que las pruebas posteriores del candidato fallen no anula un uso ya completado.

Uso ausente, invalido, no validado o resultado UNKNOWN/REJECTED: reserva completa.
Un importe mal formado se rechaza sin modificar la fila ni liberar la reserva.
Si el importe supera la reserva, queda OVER_BUDGET, cargo igual a la reserva y
`actual_units=null`: no se acepta ni se recorta silenciosamente como coste valido.
Se bloquean nuevas llamadas para conciliacion; en el piloto se conserva el
importe calculado anomalo en su evidencia de uso, sin texto del proveedor.

Los limites no cambian: USD 1 por llamada, 12 por ejecucion, 13 acumulados;
11 llamadas por ejecucion como limite general y una por intento del piloto.
La admision suma cargos liquidados y reservas pendientes, mas la nueva reserva.
Los cuatro interruptores siguen false, sin cambios en config.json. Candados,
revision, aceptaciones y prohibicion de reintentos permanecen.

## Historial y propuesta separada para bottles-2

No hay migracion ni recalculo automatico. Solo se liquidan filas IN_FLIGHT;
reabrir el registro no cambia filas terminadas. No se ha abierto mediante Store
ni modificado el registro real; su huella de archivo antes y despues coincide.

Propuesta PENDIENTE de autorizacion expresa de Fernando, no implementada:

- Conciliar exclusivamente bottles-2 contra su uso guardado y COMPLETED valido.
- Conservar reserva original USD 1.000000, cargo anterior USD 1.000000 y coste
  calculado USD 0.015946; cargo corregido propuesto USD 0.015946, diferencia
  liberada USD 0.984054. No representar esto como devolucion del proveedor.
- Crear evidencia de ajuste que conserve ambos valores, motivo, responsable,
  fecha y referencia a la autorizacion y a la evidencia de uso.
- Aplicar el ajuste y su evidencia en una sola transaccion, tras verificar los
  valores originales exactos; rechazar una segunda aplicacion. Si hay duda o
  discrepancia, detenerse. Nunca cambiar el tope acumulado de USD 13.

Hasta esa autorizacion y su implementacion separada, bottles-2 conserva su cargo
de USD 1.000000. El bloque no incorpora filas, autorizaciones ni datos privados.

## Pruebas y limites

Comandos ejecutados (raiz salvo indicacion):

```powershell
& "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -B ..\entregas-locales\ejecutar-suite-sin-red.py
# Desde ERP-FACTORY-revision:
& "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -B ..\..\entregas-locales\ejecutar-suite-sin-red.py
# Desde la raiz:
node --test --test-reporter=tap pilot-js/tests/bottles.test.mjs
node --experimental-strip-types --test --test-reporter=tap pilot-js/tests/bottles.test.ts
```

El envoltorio Python descubre toda la suite, elimina el entorno heredado salvo
variables de sistema permitidas y bloquea red y procesos de servicios externos.
Solo se usan bases temporales y dobles ficticios para API y Docker.

Resultados finales: raiz 252, privada 113, JavaScript 7, TypeScript 3.
Total 375 pasadas; 0 fallos, 0 errores y 0 omitidas, salidas de las suites 0.
Primera ejecucion de raiz: 252 pruebas, 2 fallos en expectativas de codigo de
error de las pruebas nuevas; el adaptador envuelve el uso invalido/ausente en
CODEX_RESPONSE_INVALID_OR_UNCERTAIN. Corregidas esas expectativas sin cambiar
el adaptador ni las aserciones de reserva completa y bloqueo; se repitio toda
la suite raiz, con el resultado final anterior. Las otras suites no fallaron.
Logs Python externos: bloque-12-root.log, bloque-12-root-final.log y
bloque-12-private.log. Las salidas de Node constan en la ejecucion local.

Cobertura nueva: liquidacion exacta, coste cero y coste igual a reserva, uso
ausente/invalido/incierto, exceso de tokens aunque el coste sea menor a la
reserva, sobrecoste bloqueado, conservacion del historial y limites por ejecucion
y acumulados con cargos reales. El ensayo simulado acredita 17 cargos de USD
0.75 = 12.75 y rechaza la siguiente reserva de USD 1 frente al tope de USD 13.

NO VERIFICADO: facturacion del proveedor, nuevas llamadas reales, Docker real,
GitHub Actions, publicacion o autenticacion de personas. TS se ejecuta sin
comprobacion estatica de tipos. `upstream/` y el revisor privado no se modifican.
