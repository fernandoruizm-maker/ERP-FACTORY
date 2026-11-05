# Registro de revision tecnica manual — PLANTILLA, NO ES UNA REVISION

Codex transcribe aqui la revision REAL que Fernando facilite; no inventa hallazgos
ni una conclusion. Guardar la copia completada como PR-N-SHA.local.md en esta carpeta.
Los valores REEMPLAZAR hacen que esta plantilla no sea un registro valido.
Una PR aun local puede identificarse como LOCAL:fix/nombre; actualizar su referencia
si corresponde sin atribuir una revision a un SHA que Claude no haya leido.

```json
{
  "schema_version": 1,
  "pr": "REEMPLAZAR: enlace de PR o LOCAL:rama",
  "base_sha": "REEMPLAZAR_SHA_COMPLETO_DE_40_CARACTERES",
  "reviewed_sha": "REEMPLAZAR_SHA_COMPLETO_DE_40_CARACTERES",
  "scope": {
    "mode": "CAMBIOS_PR",
    "files": ["REEMPLAZAR/ruta-del-archivo.py"],
    "diff": "REEMPLAZAR: comparacion exacta base..revisado, archivos/lineas revisados y exclusiones"
  },
  "reviewer": "Claude, chat, no autenticado",
  "findings": [],
  "conclusion": "REEMPLAZAR: CORREGIR o SIN OBJECIONES TÉCNICAS",
  "date": "AAAA-MM-DD"
}
```

Para revisar toda la fabrica, usar FABRICA_COMPLETA, indicar todos los archivos
realmente leidos y anotar el inventario y las diferencias relevantes en scope.diff.
Para cada hallazgo, agregar un objeto a findings con este formato (no es un hallazgo real):

    {"severity":"high", "file":"ruta.py", "line":123,
     "description":"hecho, evidencia e impacto", "recommendation":"correccion propuesta"}

Gravedad: critical, high, medium o low. Archivo y linea deben identificar evidencia.
No usar SIN OBJECIONES TÉCNICAS si quedan hallazgos critical/high sin resolver.
La fecha es la de la revision, no la fecha en que Codex copia el texto.

NUNCA significa aprobacion humana, permiso de publicar, integrar, activar o gastar.
El revisor no esta autenticado; la cobertura declarada de una lectura manual no
se comprueba automaticamente. No incluir claves, datos de clientes ni del ERP.
