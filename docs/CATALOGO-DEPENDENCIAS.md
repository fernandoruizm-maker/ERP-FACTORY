# Dependencias permitidas en un candidato

catalogo-aprobado.json usa ahora schema_version=2, con cinco bibliotecas y una
sección herramientas separada. El catálogo inicial autorizado por Fernando es:

| Nombre | Versión | Licencia | Uso | Perfil |
|---|---|---|---|---|
| acorn | 8.19.0 | MIT | internal | javascript |
| zod | 4.6.7 | MIT | product | javascript |
| drizzle-orm | 0.45.4 | Apache-2.0 | product | javascript |
| @playwright/test | 1.65.0 | Apache-2.0 | internal | javascript |
| pytest | 9.2.0 | MIT | internal | python |
| Gitleaks CLI | v8.30.1 | MIT | internal | herramienta |
| OSV-Scanner CLI | v2.7.0 | Apache-2.0 | internal | herramienta |

Vitest no está aprobado. Playwright y pytest sirven para pruebas de confianza,
no para que el modelo cree pruebas o introduzca importaciones en src/.
Las herramientas CLI no se consideran bibliotecas importables. Sus fuentes son
https://github.com/gitleaks/gitleaks y https://github.com/google/osv-scanner.
La validación exige name, version, license, use=internal y source oficial exacto;
rechaza duplicados, campos extra, otros orígenes y versiones no fijadas.
El esquema anterior vacío queda sustituido; no se convierte silenciosamente.

La fábrica permite un conjunto
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
- JavaScript: por ahora análisis léxico conservador de import, export-from y require.
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

El adaptador Acorn preparado en tools/acorn/ conserva enabled=false e image=null.
No se busca ni descarga una imagen automáticamente. Los cambios futuros y las
descargas requieren autorización; ver [preparación de herramientas](HERRAMIENTAS-CATALOGO.md).
Una política activada con imagen ausente, salida inválida o fallo bloquea; no vuelve
silenciosamente al analizador anterior para aceptar ese mismo código.
