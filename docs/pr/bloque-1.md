# Diagnostico seguro y revisiones parciales sin aprobacion

## Cambios y hallazgos corregidos

Corrige A1 y el resto de pruebas B7 del informe manual. Las siete causas de
cobertura tienen codigos tipados independientes del mensaje de excepcion;
se registran todas las aplicables. Guarda conteos, nombres faltantes del
manifiesto, declaraciones normalizadas y SHA-256 del texto original UTF-8
antes de parsearlo. Valores de tipo incorrecto se representan como INVALID
o null; no copia nombres sobrantes ni mensajes libres al diagnostico.

Version incorrecta, estructura o hallazgos invalidos siguen bloqueados.
Cobertura insuficiente con el resto valido produce PARTIAL y conserva los
hallazgos. PARTIAL no produce NEEDS_HUMAN_REVIEW ni satisface la puerta local;
publication_allowed=false y human_approvals=0 siempre.

## Conservacion: decision pendiente de Fernando

No se eligio servicio, destinatario ni retencion definitivos. Alternativas
para decidir: carpeta local de acceso restringido, almacen privado de Fernando
o artefactos en un repositorio privado. Faltan personas autorizadas y plazo.
No publicar automaticamente hallazgos detallados en el repositorio publico.

Mientras tanto, review.pending.json es solo la salida provisional local del
procesamiento y no sobrescribe otra anterior. NO figura en la lista explicita
de subida del workflow. report.json e INFORME.txt solo contienen estado y
diagnostico seguro, tanto para revisiones parciales como completas. No se ha
subido ningun informe. En un ejecutor efimero la salida provisional se perderia
al finalizar: no constituye retencion aprobada ni habilita otro intento.
Los siete dias del workflow existente no garantizan privacidad; su acceso real
en GitHub no se verifico en esta tarea.

## Pruebas ejecutadas

Directorio: C:\Users\ferna\Documents\Codex\2026-11-05\task\ERP-FACTORY-correcciones

```powershell
& "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -B -m unittest discover -s tests -v
node --test --test-reporter=tap pilot-js/tests/bottles.test.mjs
node --experimental-strip-types --test --test-reporter=tap pilot-js/tests/bottles.test.ts
```

- Suite completa Python de la nueva fabrica (tests/): 60 pruebas, 0 fallos,
  0 errores, 0 omitidas; incluye 25 de Actions.
- JavaScript: 5 pruebas, 0 fallos, 0 omitidas, 0 canceladas.
- TypeScript: 3 pruebas, 0 fallos, 0 omitidas, 0 canceladas; sin comprobacion
  estatica de tipos. Total correcto: 68 casos.
- Primera ejecucion Python aislada: 60 pruebas y 47 errores de acceso a
  temporales/SQLite, 0 fallos de asercion. No se presenta como validacion.
  Se repitio con autorizacion del ejecutor, sin modificar permisos del sistema
  ni borrar manualmente las rutas denegadas.

La prueba real reconstruye los archivos con git archive del objeto LOCAL
0cb1882548fc141f4b764e82ff2e5154cfae2762 y genera packet(): exactamente 91
archivos. Omitir tests/__init__.py produce un faltante exacto. No descarga,
hace checkout ni ejecuta codigo archivado. Hay una prueba por codigo,
causas simultaneas, contenido malformado, hallazgos invalidos, huella original,
privacidad del resumen y rechazo de PARTIAL por la puerta.

## No verificado y pendiente

No verificados: proveedores reales, GitHub Actions, accesibilidad de artefactos,
Docker, identidades humanas, ERP y despliegues. Los dobles ficticios no acreditan
integracion real. upstream/ es referencia intacta: no se ejecuto su piloto ni
su suite heredada. Suite completa aqui significa tests/ y ambos perfiles de
pilot-js/ de la nueva implementacion, conforme a los comandos del proyecto.

Pendientes en los bloques siguientes: A2/A3, M1-M7, B1-B6 y mejoras del piloto;
no se presentan corregidos por este bloque. No cambia upstream/, config.json
ni el workflow. La preparacion por partes y el aislamiento requieren trabajo
posterior; este bloque no habilita ni prepara otro intento de pago.

## Entrega local

Rama fix/bloque-1-diagnostico, base 0cb1882. Sin integrar main ni publicar.
El SHA final y diff --stat se entregan aparte para evitar una autorreferencia
imposible del commit dentro de su propio texto. Publicacion posterior solo con
autorizacion escrita para el bloque y SHA entregado; si difiere, detener y avisar.
