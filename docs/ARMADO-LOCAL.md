# Preparar un ensayo sin cambiar el código

Los cuatro interruptores de config.json permanecen en false. No hay que hacer
un commit para armar o desarmar un ensayo. Este bloque no arma ninguno.

1. Preparar el encargo con scripts/ensayo.ps1, modo Preparar. Devuelve los
   borradores de autorización y de armado; no llama al proveedor ni pide claves.
2. Obtener la revisión de Claude del SHA exacto y la autorización expresa de
   Fernando para el encargo, número de intento y gasto. Importar la revisión y
   completar la autorización mediante el procedimiento revisado por separado.
   La autorización firmada/declarada localmente sigue siendo obligatoria; no es
   una autenticación criptográfica de Fernando.
3. Solo entonces, preparar state/armado.json para ese encargo e intento. Usar
   config_digest del modo Preparar, issued_at con la hora de emisión y expires_at
   con el vencimiento (segundos UTC desde época Unix). Vigencia máxima: 86.400
   segundos, y nunca más allá del permiso de Fernando. No usar la fecha de ejemplo.
4. Ejecutar la comprobación previa habitual. Tanto check como el inicio real leen
   el mismo armado. Un archivo ausente, incompleto, caducado, con otra huella o de
   otro intento bloquea antes de la clave o la llamada. Se vuelve a comprobar
   dentro del candado y justo antes de contactar con el proveedor.
5. El número consumido no se puede repetir. Una llamada incierta no se reintenta.
   Para desarmar, dejar vencer el archivo o, con autorización, cambiar su
   expires_at a 0. Esto bloquea llamadas nuevas y permite revisar el candidato
   ya construido. El registro de gasto y el historial no se alteran.

Esquema del borrador (NO válido para ejecutar):

```json
{
  "encargo": "botellas",
  "attempt": 1,
  "issued_at": null,
  "expires_at": null,
  "config_digest": null
}
```

state/armado.json está excluido por .gitignore. No contiene claves y nunca debe
subirse. No sustituye la revisión, la autorización, el presupuesto, la coordinación
ni las aceptaciones humanas. La configuración efectiva con llamadas habilitadas
solo se construye en memoria después de las comprobaciones del ensayo; config.json
no se modifica. Preparar usa una copia exclusivamente para calcular la petición y
siempre informa execution_enabled=false; no acredita que se pueda ejecutar.

Los auxiliares anteriores de entregas-locales no se han actualizado ni validado
en este bloque. Antes de otro ensayo habrá que adaptarlos y revisarlos: no reutilizar
instrucciones históricas que exigían cambiar el interruptor y hacer un commit.
