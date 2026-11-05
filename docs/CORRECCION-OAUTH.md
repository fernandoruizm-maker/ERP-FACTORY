# Correccion de la incompatibilidad OAuth

El tercer intento autorizado, tras actualizar el secreto, volvio a clasificar
el error como AUTHENTICATION. No produjo revision. Run:
https://github.com/fernandoruizm-maker/ERP-FACTORY/actions/runs/41994371843
Commit: `4c307c4d5a53a08f1c9b35cb217e84a46dfcc506`.
El CLI registro un turno, 56 ms y costo estimado 0, sin acreditar facturacion.

La investigacion posterior identifico un defecto en nuestra configuracion:
`--bare` hace que Claude Code ignore `CLAUDE_CODE_OAUTH_TOKEN`. Esto esta
documentado por Anthropic en https://code.claude.com/docs/en/authentication.
Por tanto, los intentos anteriores no prueban que el token proporcionado por
Fernando estuviera mal copiado, vencido o fuera invalido. Pedir su reemplazo
antes de comprobar esta compatibilidad fue prematuro.

Se sustituye unicamente `--bare` por `--safe-mode`, cuya documentacion confirma
que conserva autenticacion y permisos mientras desactiva las personalizaciones
(hooks, plugins, MCP, CLAUDE.md y memoria, entre otras). Se mantiene la denegacion
explicita de herramientas, el token GitHub de lectura, la entrada por SHA exacto,
dos turnos, diez minutos y la validacion de informe. No se cambian credenciales,
permisos de GitHub, configuracion del ERP ni la fabrica original.

Fuente de los modos: https://code.claude.com/docs/en/cli-reference.

Verificacion: la prueba de preparacion del workflow fallo antes del arreglo al
detectar --bare. Las nueve pruebas de revision pasan tras el cambio. La llamada
real con safe-mode sigue pendiente; corregir la incompatibilidad no acredita
todavia que OAuth, el modelo y la respuesta estructurada funcionen de extremo
a extremo. No se inicio un cuarto intento automaticamente.
