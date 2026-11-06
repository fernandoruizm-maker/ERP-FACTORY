# Paso 2: intento 1 preparado, NO ejecutado

Rama `piloto/intento-1`, desde `5dc2a61fb8794439fa706f535e1d8e7e5ef96199`.
Fecha de consulta: 6 de noviembre de 2026. Solo documentacion publica oficial,
sin sesion, claves ni peticiones a la API. No se hizo fetch, push ni PR.

## Compatibilidad comprobada en documentacion

| Elemento solicitado | Resultado documental |
|---|---|
| gpt-5.3-codex y Responses | La ficha incluye Responses y salidas estructuradas |
| json_schema strict | `text.format` admite `type=json_schema`, esquema y `strict=true` |
| Esquema local BUILD_SCHEMA | Objetos con `additionalProperties=false`, campos requeridos y tipos admitidos |
| tools=[]; tool_choice=none | Lista de herramientas opcional sin minimo indicado; none impide seleccion de herramientas |
| reasoning.effort=medium | Incluido entre los esfuerzos admitidos por este modelo |
| store=false | Booleano admitido; evita almacenamiento para recuperacion por Responses, no promete retencion cero universal |
| max_output_tokens=32000 | Dentro del maximo de 128000; incluye salida visible y razonamiento |

No se encontro incompatibilidad documental en esos parametros. Esto no es una
llamada de prueba ni certifica permisos de cuenta. La ficha marca el modelo como
obsoleto; la pagina de retiradas indica cierre el **1 de abril de 2027**. Se
conserva el modelo elegido; no se cambia el modelo permitido en el proyecto.

Tarifa **estandar**, por millon: entrada USD 1.75, salida USD 14.00. No se aplica
descuento por cache. Se agrega `service_tier=default` a la peticion para no heredar
un nivel distinto del proyecto mediante el valor automatico. La referencia lo
define como nivel de precio/rendimiento estandar. No se cambia el proyecto.

Fuentes exactas leidas:

1. Modelo y limites: https://developers.openai.com/api/docs/models/gpt-5.3-codex
2. Precios: https://developers.openai.com/api/docs/pricing
3. Contrato Responses, version Markdown publica:
   https://developers.openai.com/api/reference/resources/responses/methods/create.md
4. Salida estructurada y restricciones del esquema:
   https://developers.openai.com/api/docs/guides/structured-outputs
5. Retirada del modelo: https://developers.openai.com/api/docs/deprecations

Tambien se intentaron estas dos vistas HTML: el lector devolvio limite de tamano,
por lo que se leyo la version Markdown del punto 3, sin autenticacion:

- https://platform.openai.com/docs/api-reference/responses/create
- https://developers.openai.com/api/reference/resources/responses/methods/create

La copia de consulta de la referencia se guarda fuera del repositorio en
`../entregas-locales/openai-responses-create-2026-11-06.md`. No se copia esa
documentacion completa al repositorio publico.

## Configuracion preparada

`config.json`: modelo gpt-5.3-codex, esfuerzo medium, 32000 tokens de salida,
precios 1.75/14.00, max_call_usd=1.00 y topes USD 1.00/12.00/13.00.
`max_request_bytes=100000`. La configuracion general de 4096 tokens sigue siendo
la de los adaptadores antiguos; este ensayo usa exclusivamente el limite de
`pilot_cost_review.max_output_tokens=32000` y su prueba lo comprueba.

**Los cuatro interruptores siguen false**, incluido external_calls_enabled.
No se modifica upstream/, el revisor privado, los remotos o la fabrica original.
El envio sigue DISABLED. Ningun permiso de esta etapa autoriza gastar.

Fernando declara clave limitada a Responses, proyecto limitado a este modelo y
caducidad de 30 dias. No se leyo la clave ni se verificaron esas propiedades.
La fecha exacta de vencimiento sigue pendiente; no se infiere a partir de hoy.

## Calculo local reproducible

El mismo serializador del adaptador produjo **4682 bytes UTF-8**, incluyendo
instrucciones, requisitos ficticios, pruebas, esquema y parametros. Un byte se
cuenta conservadoramente como un token de entrada:

    (4682 * 1.75 + 32000 * 14.00) / 1000000 = 0.4561935 USD
    Redondeado hacia arriba al millonesimo: 0.456194 USD

Para el limite completo de entrada:

    (100000 * 1.75 + 32000 * 14.00) / 1000000 = 0.623000 USD

Ambos valores son inferiores al tope de una llamada de USD 1.00. La reserva del
intento seguira siendo USD 1.00; no es una factura ni una medicion de gasto.
Este calculo depende de las tarifas y del nivel estandar documentados; se debe
revalidar si cambia el modelo, la peticion, la tarifa o el nivel de servicio.
No se suman dos veces los tokens de razonamiento.

## Script y preparacion sin consumo

Desde la raiz, con el Python local ya instalado:

```powershell
.\scripts\ensayo-intento-1.ps1 -Modo Preparar
```

Es el modo por defecto. Genera un informe JSON en consola con la peticion
ficticia, huellas, coste y borrador de autorizacion **sin autor, SHA ni caducidad**.
No crea Store/SQLite, no reserva ni consume attempt=1, no pide claves y no llama
a Docker ni a un proveedor. El calculo usa una COPIA en memoria de config para
serializar la peticion hipotetica; no modifica ni activa config.json.

Se ejecuto solamente este modo. Salida: PREPARED_NOT_EXECUTED,
execution_enabled=false, attempt_consumed=false. Evidencia fuera del repositorio:
`../entregas-locales/intento-1-preparado.json`.

El modo futuro `Ejecutar` esta preparado pero **no se ejecuto**. Exige:

1. ConfirmoAutorizacionExpresa, archivo de autorizacion y SHA completo revisado.
2. Interruptor de llamadas encendido con permiso posterior; los otros tres false.
3. Checkout limpio en ese SHA, hashes coincidentes, attempt=1 y permiso vigente
   de Fernando. Cualquier cambio de config cambia su huella y requiere revision.
4. Registro compartido existente en `state/factory2.sqlite3`, revision manual de
   la fabrica para ese SHA, saldo suficiente y ausencia de estados inciertos.
   No crea un registro vacio para aparentar saldo ni sustituye registros previos.
5. Ausencia de una autorizacion/llamada/expediente anterior de bottles-1.

Solo despues de esas comprobaciones pediria la clave con entrada oculta, en una
terminal privada que abra Fernando. Requiere PowerShell 7 para ArgumentList.
La clave viajaria por stdin al proceso Python, nunca como argumento, archivo,
URL o variable global de Fernando. El hijo recibe un entorno por lista blanca;
solo dentro de ese hijo la clave se pone temporalmente en OPENAI_API_KEY.
El buffer BSTR se libera; esto no garantiza borrar todas las copias de memoria.
No usar transcripciones ni compartir/capturar esa terminal. No se imprime stderr.
El resultado mostrado se limita a estado, intento, uso numerico, coste y permiso
de publicacion. El script no apaga ni enciende interruptores automaticamente.

La autorizacion local es una declaracion, no autenticacion. El programa nunca
inventa una autorizacion nueva ni incrementa el numero para reintentar.

## Pendientes antes de autorizar la ejecucion

- **No existe** `state/factory2.sqlite3` en este clon. Fernando debe confirmar
  la ubicacion del registro acumulado permanente y su saldo, e indicar si hay
  uno previo que conservar. Inicializar uno nuevo requiere esa confirmacion;
  el script no lo hace. No se da por probado un gasto acumulado cero.
- Claude debe revisar el SHA entregado y cualquier posterior cambio de
  activacion. Su informe debe registrarse para el SHA exacto que se ejecutaria.
- Autorizar por escrito encender solo external_calls_enabled, la llamada unica,
  su cargo maximo y el expediente con attempt=1/caducidad. Preparar esta rama
  no concede esos permisos. Apagarlo al terminar tambien requiere la accion
  prevista; no queda automatizado aqui.
- Confirmar vencimiento de la clave, limites de cuenta y disponibilidad real.
  No se comprobo cuenta, factura, acceso al modelo ni permisos de la clave.

## Verificacion local

Pruebas focales: 40 pasadas, cero fallos/errores y cero omitidas.
Parser de PowerShell: cero errores. Script en modo Preparar: salida correcta,
sin crear el registro ni consumir el intento.

Comandos de suites completas (desde raiz salvo donde se indica):

```powershell
& "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -B -m unittest discover -s tests -v
# Mismo comando desde ERP-FACTORY-revision/ para la suite privada.
node --test --test-reporter=tap pilot-js/tests/bottles.test.mjs
node --experimental-strip-types --test --test-reporter=tap pilot-js/tests/bottles.test.ts
```

| Suite | Pruebas | Fallos/errores | Omitidas |
|---|---:|---:|---:|
| Raiz Python | 219 | 0 | 0 |
| Privada Python | 113 | 0 | 0 |
| JavaScript | 7 | 0 | 0 |
| TypeScript, sin comprobacion de tipos | 3 | 0 | 0 |
| Total | 342 | 0 | 0 |

Todas finalizaron con salida 0. Logs locales fuera del repositorio:
../entregas-locales/intento-1-root.log, intento-1-private.log,
intento-1-js.log e intento-1-ts.log; focales en intento-1-focused.log.
Python requirio permiso para los temporales locales, sin red ni proveedores.
El commit final y su diff --stat se entregan en el mensaje, para evitar que el
SHA se autorreferencie dentro del mismo commit.

NO VERIFICADO: Responses real, formato real de eventos/usage, facturacion real,
credencial, modelo accesible en la cuenta, Docker del nuevo constructor, ruta
Ejecutar de PowerShell y entrada privada en uso real, GitHub/ERP. Las pruebas
de ejecucion usan dobles y claves ficticias en temporales. TypeScript no comprueba
tipos. upstream/ no se prueba ni modifica. No se publico ni activo nada.
