# Bloque 14: armado local y catálogo de dependencias

Base comprobada por fetch: 3988ce4fca1ca61d9d70a73a345b166d9b2454ea.
Rama: feat/bloque-14-armado-local. Encargo: mensaje 4 PERMITIDO del buzón,
7-11-2026. El mensaje 5 de corrección de gasto queda reservado, sin ejecutar.

## Qué cambia

Armar un ensayo ya no requiere cambiar config.json ni generar un commit: se lee
state/armado.json, ignorado por Git, con encargo, intento, issued_at, expires_at
y huella de configuración. Vigencia máxima 24 horas; los cuatro interruptores
de Git deben seguir false. Ausencia, caducidad o discrepancia bloquean. Preparar
solo emite un borrador; check y start comparten la comprobación. El inicio vuelve
a comprobarla dentro del candado y antes de la llamada. Revisión, autorización
expresa de Fernando, numeración, presupuesto y aceptaciones siguen obligatorios.
No se crea ningún armado real ni se actualiza el auxiliar fuera del repositorio.

catalogo-aprobado.json comienza vacío para paquetes externos. Cada entrada futura
exige paquete, versión exacta, licencia, uso interno/producto y perfil. La salida
se analiza estáticamente antes de materializar: Python AST y análisis léxico JS.
Solo el uso producto habilita un import externo; no se instala ni ejecuta código
para descubrir dependencias. Se registra la huella del catálogo usado. Un rechazo
del candidato no elimina el gasto de una respuesta válida ya recibida.

La guía de gh registra la configuración por defecto de Windows y la única cuenta
permitida, fernandocodex64-sudo, con auth status previo sin tokens. Buzón excluido
solo con .git/info/exclude. No cambia la configuración global ni credenciales.

## Verificación ejecutada

Desde la raíz, con Python y Node ya instalados. El directorio temporal se fija
solo para cada proceso; no modifica variables globales ni permisos:

```powershell
$env:TEMP=(Resolve-Path ..\entregas-locales\bloque-14-temp).Path
$env:TMP=$env:TEMP
& "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -B ..\entregas-locales\ejecutar-suite-sin-red.py
node --test --test-reporter=tap pilot-js/tests/bottles.test.mjs
node --experimental-strip-types --test --test-reporter=tap pilot-js/tests/bottles.test.ts
```

Desde ERP-FACTORY-revision:

```powershell
$env:TEMP=(Resolve-Path ..\..\entregas-locales\bloque-14-temp).Path
$env:TMP=$env:TEMP
& "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -B ..\..\entregas-locales\ejecutar-suite-sin-red.py
```

Resultados finales: raíz **300**, privada **113**, JS **7**, TS **3**:
**423 pruebas aprobadas, 0 fallos, 0 errores, 0 omitidas**, cuatro salidas 0.
Logs externos: bloque-14-root-final.log, bloque-14-private.log, bloque-14-js.log,
bloque-14-ts.log. El envoltorio bloquea conexiones y procesos externos reales;
las pruebas usan bases temporales y dobles, sin tocar el registro real.

Cobertura nueva: armado correcto/ausente/caducado/futuro/mayor de 24 h, encargo,
intento y huella incorrectos, esquema estricto, enlaces, exclusión Git, autorización
obligatoria, expiración entre comprobación y llamada, flujo simulado con config
intacta, importaciones estándar/locales/externas, uso interno rechazado, cargadores
dinámicos ambiguos y catálogo inválido. Se mantienen los escenarios históricos
adaptando solamente sus fixtures temporales de armado y configuración.

La primera ejecución tuvo 457 errores de entorno sobre 278 pruebas: Windows negó
acceso al temporal del sandbox. Se cambió TEMP/TMP al workspace autorizado, sin
cambiar permisos. Después, 300 pruebas detectaron 9 fallos y 1 error: un código
de rechazo capturado como ValueError y dos fixtures del encargo equivocado. Ambos
defectos se corrigieron; las dos ejecuciones posteriores de raíz pasaron 300/300.
No se ocultan esas ejecuciones iniciales ni se consideran evidencia aprobada.

## Límites y pendientes

- NO VERIFICADO: integración real con proveedor o Docker, coste y facturación,
  autenticación de revisiones/autorizaciones, ni nuevo ensayo real. TS se ejecuta
  sin comprobación estática de tipos. GitHub Actions sigue aparcado.
- JS admite un subconjunto conservador: rechaza plantillas con expresiones,
  identificadores escapados y slash fuera de cadenas/comentarios, incluidas
  división y expresiones regulares. Puede bloquear código legítimo; ver
  docs/CATALOGO-DEPENDENCIAS.md. No es un sandbox ni prueba ausencia de todas las
  cargas indirectas. La revisión técnica y Docker siguen siendo necesarios.
- El catálogo registra versión y licencia, pero no acredita paquetes instalados,
  licencias verificadas ni dependencias transitivas. No hay paquetes externos
  aprobados. Su uso futuro requiere imágenes y comprobaciones adicionales.
- Auxiliares de entregas-locales: pendientes de adaptación y revisión antes de
  otro ensayo; no se reutilizan las instrucciones antiguas de armar por commit.
- Mensaje 5: NO ejecutado. No hay ajuste ni copia de la base real ni gasto nuevo.

config.json, upstream/, runner.py y ERP-FACTORY-revision/ conservan su contenido.
No se aprueba ni integra esta PR. Reversión futura: revertir este bloque con
autorización, sin reescribir historial ni repetir números de intento.
