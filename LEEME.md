# Segunda fabrica RDC: guia local

La fabrica esta desactivada. No se modifico la original ni se accedio al ERP.
Esta rama contiene correcciones locales y pruebas con datos ficticios.

Existe un archivo de workflow publico historico. El nuevo diseno ejecutara las
revisiones en un repositorio privado separado, cuyo contenido propuesto esta en
`ERP-FACTORY-revision/`. No se creo ese repositorio ni se probo su ejecucion real.
No se han consultado ni movido credenciales en estas correcciones.

## Que esta disponible

1. Ficha de necesidades y comparacion por evidencia, con permiso de autorizante,
   base, rutas y caducidad. Solo se prueba con una base ficticia; el ERP real
   permanece PENDIENTE.
2. Flujo construir -> montar pruebas de confianza -> probar -> revisar con dobles
   ficticios. Comprueba huellas y conserva resultados previos si una etapa falla.
   No ejecuta codigo generado, Docker ni llamadas reales.
3. Importacion local del contrato V2 privado con hashes y procedencia declarada.
   Las huellas no autentican GitHub; el resultado sigue bloqueado para operar.
4. Aceptaciones con identidad normalizada, version, revision y caducidad, sin
   reemplazo silencioso. Los nombres configurados no autentican a las personas.
5. Candado local de un trabajador y recuperacion sin reintento. La coordinacion
   con la original no esta conectada y por eso bloquea la via real.
6. Reservas de presupuesto por ejecucion y acumuladas. Los intentos inciertos
   conservan su reserva; un importe reportado mayor congela nuevos intentos hasta
   conciliacion. No son importes facturados ni certificacion del proveedor.
7. Piloto de diez botellas y restauracion que verifica solicitudes, movimientos,
   aprobadores y saldos. La huella no firma ni autentica el estado.

## Probar el ejemplo confiable

`VER_ESTADO.cmd` consulta el estado y `PROBAR_PILOTO.cmd` ejecuta el piloto local.
Necesitan Python y Node disponibles; no instalan nada ni encienden servicios.

```text
python -B -m factory2 status
python -B -m factory2 discover fixtures/cliente.json
python -B -m factory2 pilot
python -B -m unittest discover -s tests -v
```

Los informes del piloto se generan en outputs/. El comprobante dice
**SIN VALIDEZ FISCAL**. TypeScript se ejecuta sin comprobar tipos estaticamente.
No ejecutar propuestas de modelos en el host: su ejecucion real requiere un
entorno aislado y una autorizacion futura.

El comando historico `prepare-factory-review` conserva el formato anterior;
no genera una revision V2 aceptable y no debe usarse para habilitar otro intento.
Los contratos antiguos y el workflow publico se retiraran solo en la migracion
autorizada al revisor privado. El borrador `.disabled` esta marcado OBSOLETO.

## Decisiones y puesta en marcha pendientes

Fernando indico negocio fernandoruizm-maker (342326625) y tecnica FERRUMTJA
(352290329), sin que esta tarea autentique esas cuentas. Indico 11 llamadas por
ejecucion; gasto por ejecucion, gasto acumulado y moneda siguen sin definir.
Los valores ausentes bloquean un intento pagado; no hay importes por defecto.
Se conservan ademas los bloqueos de coordinacion y acceso.

Antes de cualquier intento real faltan un workflow multiparte revisado, guardado
inmediato de cada parte validada, topes efectivos, ausencia de reintentos,
procedencia autenticada, identidades reales y autorizacion expresa nueva.
La pasada de interacciones recibe resultados e inventario, no el codigo completo.
No operar las dos fabricas simultaneamente. No se autoriza aqui su transicion.

Ver [estado](docs/ESTADO.md), [diseno privado](docs/CLAUDE-OPCIONES.md)
y [entrega por mitades](docs/pr/bloque-4.md).
