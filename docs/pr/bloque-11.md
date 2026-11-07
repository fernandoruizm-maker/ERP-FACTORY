# Bloque 11: mejoras del ensayo real y fabrica desarmada

Titulo propuesto: Incorporar las mejoras del ensayo de botellas, con llamadas desactivadas.

Rama feat/bloque-11-ensayo, creada desde piloto/intento-1 en
aa6fcb15f24b361cf6df7652496675f114f6d1c3. El unico fetch autorizado confirmo
origin/main en f7d973c6f9ca841d818204c12793d1c488fd6f80.
Este bloque se prepara localmente: no se sube, abre PR ni integra en main.

## Resultado REAL del ensayo

El piloto usa exclusivamente un caso ficticio de botellas; no accede al ERP.

| Aspecto | Resultado observado |
|---|---|
| Intento 1 | Bloqueado antes de llamar al proveedor; sin gasto. |
| Diagnostico del intento 1 | El candado state/worker.lock ensuciaba Git antes de comprobar el SHA. Se reprodujo y corrigio. |
| Intento 2 | Construccion y pruebas completadas; llego a WAITING_FOR_MANUAL_REVIEW. |
| Modelo | gpt-6.1-sol |
| Tokens de entrada / salida | 1153 / 1364 |
| Coste calculado | USD 0.015946; no es una factura verificada. |
| Pruebas del candidato | 7 de 7 aprobadas en Docker. |
| Revision del candidato por Claude | SIN OBJECIONES TECNICAS, declarada en chat y no autenticada. |
| Aceptacion de negocio | Fernando, declaracion local no autenticada. |
| Aceptacion contable y funcional | FERRUMTJA, declaracion local no autenticada comunicada por Fernando. |
| Puerta tras las aceptaciones | READY_FOR_MANUAL_REVIEW, reasons=[], sin bloqueos. |
| Publicacion | publication_allowed=false; no se publico ni desplego. |

Calculo con las tarifas configuradas: (1153 x 2.00 + 1364 x 10.00) / 1000000
= USD 0.015946. No se identifica ese importe con el cargo conservador reservado
por el presupuesto ni con una factura del proveedor.

Hallazgo minimo conservado: quien aprueba tambien puede despachar. Antes de usar
el producto con clientes reales hay que decidir si separar esas funciones.
Las aceptaciones se registraron con caducidad de siete dias; la puerta refleja
su evaluacion en ese momento, no una autorizacion permanente de publicacion.

Este resumen contiene solo los resultados autorizados del ensayo. No incorpora
SQLite, filas del registro privado, autorizaciones firmadas, identificadores de
revisiones privadas, candidatos locales, respuestas del proveedor ni claves.

## Cambios que aporta la rama

- Preparacion del ensayo con modelo, formato y limites de coste comprobados.
- Comprobaciones previas compartidas entre check y ejecucion, mismo entorno
  reducido, candado excluido especificamente de Git y codigos cerrados de fallo.
- Numero de intento explicito en Python y PowerShell; rechazo de reutilizacion
  y exigencia de que los intentos anteriores esten BLOCKED. Sin reintentos.
- Copias temporales de configuracion para las pruebas de comportamiento.
- Desarmado tras completar el intento 2: enabled, external_calls_enabled,
  erp_access_enabled y publication_enabled permanecen false.

La prueba de configuracion real se ajusta a este estado final: exige los cuatro
interruptores false. Antes exigia external_calls_enabled=true para preparar
el ensayo. No se cambia codigo productivo ni configuracion en este bloque;
el desarmado ya pertenece a aa6fcb1. Las pruebas de llamadas usan solo dobles.

## Verificacion y limites

Comandos de las suites completas (raiz salvo donde se indica):

```powershell
& "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -B ..\entregas-locales\ejecutar-suite-sin-red.py
# Desde ERP-FACTORY-revision:
& "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -B ..\..\entregas-locales\ejecutar-suite-sin-red.py
# Desde la raiz:
node --test --test-reporter=tap pilot-js/tests/bottles.test.mjs
node --experimental-strip-types --test --test-reporter=tap pilot-js/tests/bottles.test.ts
```

Resultados reales: raiz 242, privada 113, JavaScript 7, TypeScript 3.
Total: 365 pasadas; 0 fallos, 0 errores, 0 omitidas. Las cuatro salidas son 0.
Logs externos: bloque-11-root.log, bloque-11-private.log, bloque-11-js.log y
bloque-11-ts.log. Estas suites se ejecutaron en la rama desarmada del bloque 11.

El envoltorio Python ejecuta las suites completas sin heredar credenciales y
bloquea red, Docker real y proveedores. Estas pruebas locales no repiten ni
acreditan otra ejecucion real. TS ejecuta pruebas sin comprobacion de tipos.
NO VERIFICADO en este bloque: factura del proveedor, GitHub Actions, integracion
en main, despliegue, acceso al ERP o autenticacion de personas. No se repite el
ensayo, no se usa clave y no se cambia el registro privado.

Antes del commit se comprueba que state/, work/ y entregas-locales/ no contienen
archivos seguidos, preparados ni introducidos por los commits de esta rama.
Los documentos de revision *.local.md permanecen excluidos. Los logs locales
estan fuera del repositorio. El envio sigue DISABLED.
Comprobado: cero rutas de esas carpetas en el indice y en los commits nuevos
respecto a origin/main. Revision de patrones sobre los archivos seguidos y el
documento nuevo: una coincidencia, una cabecera PEM aislada sin cuerpo de clave
en una prueba negativa que ya existe en origin/main. No se muestran valores de
credenciales. La revision de patrones es limitada y no certifica ausencia absoluta.
