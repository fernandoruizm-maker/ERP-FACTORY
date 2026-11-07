# Dependencias permitidas en un candidato

catalogo-aprobado.json empieza con packages vacío. La fábrica permite un conjunto
explícito de módulos estándar de Python y Node, definido en factory2/dependencies.py.
No considera estándar todo lo que esté instalado en este PC. Si falta un módulo
estándar en esa lista, se bloquea hasta revisar y ampliar la lista.

Una entrada externa exige package, version exacta, license, use (internal o
product) y profile (javascript o python). Ejemplo FICTICIO, no aprobado:

```json
{"package":"ejemplo","version":"1.2.3","license":"MIT","use":"product","profile":"python"}
```

package es el nombre usado al importar. En Python puede ser diferente del nombre
de distribución: antes de aprobarlo hay que verificar esa correspondencia. En
JavaScript un submódulo se vincula al paquete raíz, incluidos @scope/paquete.
Solo use=product permite que un candidato lo importe. Internal no lo autoriza.
No se admiten rangos, latest, filas duplicadas ni licencia vacía. Registrar la
licencia es una declaración pendiente de revisión, no un análisis legal.

Antes de la llamada se comprueba el formato del catálogo. Tras recibir la propuesta,
se analiza cada archivo src/ antes de materializar o ejecutar el candidato:

- Python: AST para import/from; módulos relativos deben existir en la salida.
- JavaScript: análisis léxico conservador de import, export-from y require.
  Importación dinámica solo con nombre literal; módulos relativos deben existir.
- Se rechazan cargadores dinámicos conocidos, nombres no resolubles, rutas externas
  y construcciones ambiguas. No se ejecuta el candidato para descubrir dependencias.

Limitaciones explícitas: el analizador JS no es un parser completo. Rechaza, entre
otras construcciones, expresiones en plantillas, identificadores escapados y `/`
fuera de cadenas/comentarios (incluye expresiones regulares y división). Así evita
confundir una expresión regular con una cadena y pasar por alto un import. Puede
rechazar código legítimo: debe corregirse o ampliarse el parser con pruebas, nunca
desactivar la puerta para ese candidato. Python bloquea cargadores como __import__,
eval/exec/getattr. Este inventario estático no demuestra ausencia de toda carga
indirecta posible ni sustituye el aislamiento de Docker o la revisión técnica.

No instala paquetes ni verifica su versión instalada. La versión del catálogo es
una aprobación exacta, no un lockfile ni evidencia de suministro. Para usar paquetes
externos de verdad faltará preparar imágenes fijadas y comprobar versiones/licencias
con autorización separada. Las imágenes actuales no se descargan ni modifican aquí.
Una respuesta con uso válido puede consumir presupuesto aunque su código sea
rechazado después por dependencias; no se reembolsa ni se reintenta automáticamente.
