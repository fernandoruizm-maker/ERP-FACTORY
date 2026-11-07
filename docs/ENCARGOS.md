# Encargos ficticios, sin activar la fabrica

Un encargo es una carpeta `encargos/<nombre>/` con tres elementos:

- `requisitos.json`: version 1, declaracion `synthetic: true` y ficha `brief`
  con cliente ficticio, objetivo, usuarios, areas, requisitos, exclusiones y supuestos.
- `tests/`: pruebas fijas controladas por quienes preparan y revisan el encargo.
  Nunca son archivos que el modelo constructor pueda entregar o cambiar.
- `salida.json`: version 1, lista exacta `files` bajo `src/`, `profile` javascript
  o python, numero entero `expected_tests` e instrucciones de interfaz `interface`.

La declaracion de datos ficticios no autentica su origen. No incluir datos reales,
ERP ni credenciales. Los ejemplos y pruebas nuevas de este bloque fueron preparados
por Codex para revision humana: no se atribuyen a una persona ni se consideran
aprobados. Fernando y quien redacte las pruebas deben revisar y asumir el contrato
antes de autorizar un ensayo. El modelo que construye durante un ensayo no escribe
las pruebas; solo propone la lista autorizada de archivos `src/`.

Ejemplos incluidos:

| Encargo | Perfil | Salida | Pruebas esperadas |
|---|---|---|---:|
| botellas | javascript | src/bottles.mjs | 7 |
| caja-chica | python | src/caja_chica.py | 8 |

Botellas conserva las siete pruebas del piloto anterior. Caja chica usa centavos
ficticios: tope diario por persona, aprobador responsable independiente, comprobante
e idempotencia. No implementa contabilidad real, autenticacion ni conexion a un ERP.
Su implementacion de referencia en tests/fixtures es SOLO un doble para probar la
fabrica; no es un producto generado ni una entrega del proveedor.

## Preparar sin gastar

En PowerShell 7, desde la carpeta del repositorio:

```powershell
.\scripts\ensayo.ps1 -Modo Preparar -Encargo botellas -Intento 1
.\scripts\ensayo.ps1 -Modo Preparar -Encargo caja-chica -Intento 1
```

Preparar calcula material, huellas y peor caso; no lee una clave, no abre el
registro SQLite y no consume un intento. Preparar botellas-1 no autoriza repetir
el antiguo bottles-1: la comprobacion previa de una ejecucion lo rechaza.
El comando Python equivalente requiere `--encargo <nombre>` y `--attempt N`.
El script anterior ensayo-intento-1.ps1 se sustituye; los auxiliares locales
fuera de Git no se actualizan automaticamente y deben revisarse antes de usarlos.

Una autorizacion nueva incluye `encargo`, `attempt`, SHA exacto de la fabrica,
huella de configuracion y `context_digest` (nombre, ficha, perfil, salida, numero
de pruebas y contenido completo de las pruebas), revision, responsable y caducidad.
Cualquier cambio invalida esas huellas. Los borradores no son autorizaciones.

## Validaciones y recorrido

Se rechazan campos extra o ausentes, JSON duplicado o invalido, nombres inseguros,
enlaces o junctions, archivos no clasificados, requisitos vacios, perfiles distintos,
rutas repetidas o fuera de src y pruebas vacias o de otro perfil. Tamano total del
contexto limitado a 100 KB; hasta 10 salidas y 30 archivos de pruebas.
Las pruebas son archivos planos tests/*.test.mjs o tests/test_*.py; no se admiten
dependencias, subcarpetas auxiliares ni descargas. El numero esperado no puede ser
cero, booleano o fraccionario. La salida del ejecutor debe coincidir exactamente.

Se usa una copia del contexto para el constructor y otra conservada como contrato.
El modelo no puede ampliar la salida ni sustituir pruebas. Se materializan los src,
se copian las pruebas fijas y se verifica la huella de todos los archivos antes y
despues del ensayo. Pruebas Python y JavaScript eligen sus imagenes ya fijadas por
digest, con red deshabilitada, solo lectura y --pull=never. No se ejecutan aqui.
El resultado se detiene para revision manual y las aceptaciones correspondientes.
Ambos ejemplos se clasifican conservadoramente como producto contable: Fernando
y FERRUMTJA. No se decide otro nivel ni se publica automaticamente.

## Numeracion e historial

Cada encargo empieza en 1: botellas-N y caja-chica-N. Solo se permite un nuevo
numero cuando los anteriores de ese encargo existen y estan BLOCKED. Los trabajos
de otro encargo no bloquean por estar esperando revision, pero conservan su gasto;
siguen vigentes el candado unico y la conciliacion de llamadas inciertas.

Para botellas se reconoce tambien bottles-N. Se busca en todas las tablas y
referencias para evitar reutilizar un numero antiguo, y en ambos directorios de
candidato. Un registro antiguo se carga con su ID y ruta originales; revisar,
aceptar y consultar la puerta siguen usando esas referencias. Si coexisten ambas
formas para un numero, se bloquea. No se renombra ni reescribe el historial real.

El presupuesto sigue siendo uno: USD 1 por llamada, 12 por ejecucion y 13 en total,
no por encargo. El bloque 12 mantiene reservas inciertas y liquida uso valido.
La correccion de bottles-2 sigue pendiente de comparar con facturacion real.
Los cuatro interruptores permanecen apagados. Ningun ejemplo autoriza una llamada.
