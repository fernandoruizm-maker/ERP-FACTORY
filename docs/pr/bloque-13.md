# Bloque 13: encargos generales ficticios

Titulo propuesto: Generalizar los encargos con pruebas fijas y compatibilidad del historial de botellas.

Rama `feat/bloque-13-encargos` desde `origin/main` en
`5bf2add46f6c22009875c6fe9f825cd8c02ab267`, comprobado con el unico fetch autorizado.
Trabajo local sin publicacion, activacion, proveedores, credenciales ni ERP.

## Que cambia

- Contrato estricto en factory2/encargos.py: requisitos.json, salida.json y pruebas
  fijas de cada encargo, con campos cerrados, volumen limitado y rutas seguras.
- PilotTrial, comprobacion previa y trial_command reciben el encargo, cuya huella
  incluye requisitos, perfil, interfaz, salida, numero esperado y todas las pruebas.
  La autorizacion ahora incluye encargo, ademas de attempt y las huellas anteriores.
- El constructor recibe una copia del contexto. Solo se admite exactamente la lista
  autorizada de src; se copian las pruebas de confianza y se comprueba el contenido.
  Se elige imagen Python o Node ya fijada por digest; se exige perfil, huella,
  exito y numero exacto de pruebas antes de continuar a revision manual.
- scripts/ensayo.ps1 sustituye ensayo-intento-1.ps1 y recibe -Encargo y -Intento.
  Su modo predeterminado sigue siendo Preparar: no ejecuta, no pide clave ni gasta.
  Check y Ejecutar conservan el mismo proceso con entorno reducido.
- Botellas pasa a encargos/botellas, copiando las siete pruebas existentes.
  fixtures/cliente.json y pilot-js se conservan para la regresion del piloto anterior.
  bottle_input queda como ayudante de compatibilidad que carga el encargo; no se
  usa como entrada fija del nuevo orquestador.
- Caja chica es un encargo Python con ocho pruebas: importes enteros, responsable
  independiente, tope diario por persona, revalidacion al pagar, duplicados y recibo.
  No hay una construccion real ni una llamada API de caja chica.

Las pruebas nuevas y el doble de referencia fueron preparados por Codex en esta
tarea para revision humana. No se atribuyen a una persona ni se afirma que esten
aprobados. El modelo constructor de un ensayo nunca escribe ni cambia esas pruebas.
Su aceptacion como contrato de negocio queda pendiente antes de un ensayo real.

## Compatibilidad y limites que permanecen

Los intentos nuevos son <nombre>-N. botellas-N reconoce bottles-N como alias
historico: no renombra filas, referencias ni carpetas; conserva revision,
aceptaciones y puerta. Se rechaza reutilizar el numero en cualquiera de las dos
formas, incluso si solo existe una referencia en otra tabla o un candidato local.
La coexistencia contradictoria de ambas formas bloquea. Autorizaciones antiguas
no habilitan una llamada nueva: se requiere una nueva con encargo y huellas actuales.

Para un nuevo intento se exigen los anteriores de ESE encargo como BLOCKED.
Otro encargo puede esperar revision sin impedir preparar uno distinto. El candado
sigue siendo global y el gasto tambien: no se reinicia el presupuesto al cambiar
de encargo. USD 1/12/13 y la liquidacion del bloque 12 permanecen intactos.
Ambos ejemplos siguen el nivel contable, con Fernando y FERRUMTJA.

config.json no cambia: enabled, external_calls_enabled, erp_access_enabled y
publication_enabled siguen false. No se abre Store sobre el registro real; su
huella de archivo antes/despues coincide. La correccion de bottles-2 sigue pendiente
de comparacion con facturacion real. state/, work/ y entregas-locales no entran en Git.
upstream/, runner.py y ERP-FACTORY-revision/ no cambian.

## Verificacion local

Comandos completos ejecutados, desde la raiz salvo indicacion:

```powershell
& "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -B ..\entregas-locales\ejecutar-suite-sin-red.py
# Desde ERP-FACTORY-revision:
& "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -B ..\..\entregas-locales\ejecutar-suite-sin-red.py
# Desde la raiz:
node --test --test-reporter=tap pilot-js/tests/bottles.test.mjs
node --experimental-strip-types --test --test-reporter=tap pilot-js/tests/bottles.test.ts
```

El envoltorio elimina credenciales heredadas, descubre toda la suite y bloquea red,
Docker y proveedores reales. Solo bases temporales y dobles ficticios. El constructor
de procesos PowerShell se analiza por AST y se comprueba su entorno sin ejecutarlo.

Resultados finales: raiz 278, privada 113, JavaScript 7, TypeScript 3.
Total de las suites: 401 pasadas; 0 fallos, 0 errores, 0 omitidas; cuatro salidas 0.
Las ejecuciones intermedias de raiz (252 y 275 pruebas) tambien terminaron en OK.
Logs externos: bloque-13-root-inicial.log, bloque-13-root-ampliada.log,
bloque-13-root-final.log, bloque-13-private.log, bloque-13-js.log y bloque-13-ts.log.

Ademas se ejecuto el lanzador real SOLO en modo Preparar, sin clave ni proveedor:

```powershell
$pythonPath = "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
pwsh -NoProfile -NonInteractive -File .\scripts\ensayo.ps1 -Modo Preparar -Encargo botellas -Intento 1 -Python $pythonPath
pwsh -NoProfile -NonInteractive -File .\scripts\ensayo.ps1 -Modo Preparar -Encargo caja-chica -Intento 1 -Python $pythonPath
```

Ambos devolvieron PREPARED_NOT_EXECUTED, execution_enabled=false,
attempt_consumed=false y publication_allowed=false. Botellas: 4661 bytes y
USD 0.329322 de peor caso; caja chica: 6433 bytes y USD 0.332866. Son calculos
con precios configurados, no gastos, facturas ni precios comprobados de nuevo.

Las pruebas de raiz incluyen ejecutar las ocho pruebas de caja chica con Python
local sobre el doble de referencia, y otra ejecucion sobre una variante que omite
el tope: el contrato detecta ese defecto y el ejecutor devuelve FAIL como se espera.
Ese fallo deliberado interno es una prueba negativa aprobada, no un fallo de suite.
El recorrido simulado verifica la imagen Python seleccionada; no ejecuta Docker.

Se comprueba ademas JSON duplicado/NaN, campos extra, origen ficticio declarado,
rutas, enlaces y junctions (dobles), pruebas ausentes/vacias, patrones de credencial
ficticios, salida ampliada, varios archivos de salida, cambio de huellas, nombre de
encargo incorrecto, numeracion independiente y gasto compartido. Una base temporal
con el formato historico bottles-N conserva revision, aceptaciones y puerta.

NO VERIFICADO: API real, autenticacion real, Docker real, aislamiento real de los
nuevos ejemplos, facturacion, GitHub Actions o uso de gh. TS sin comprobacion de tipos.
Las pruebas simuladas no acreditan integracion real. El revisor privado sigue
aparcado: su inventario historico debe revisarse antes de cualquier reactivacion;
este bloque no actualiza ni activa su workflow. Los auxiliares de entregas-locales
no se migran ni se firman: requieren revision separada antes de cualquier uso futuro.

## Publicacion futura

Se documenta la decision de Fernando: con autorizacion posterior para publicar
esta rama y su SHA, Codex subira y abrira la PR con gh como fernandocodex64-sudo;
nunca aprobara ni integrara. No se instala, configura ni usa gh en este bloque.
Reversion propuesta: revertir este commit tras revision, sin alterar filas ni
reservas del registro. Un rollback no autoriza repetir intentos ya consumidos.
