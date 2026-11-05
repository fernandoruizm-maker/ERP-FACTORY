# Claude: revisión del producto y de la propia fábrica

Decisión de Fernando, 5 de noviembre de 2026: usar **Claude Code en GitHub Actions**. Ninguna integración está activada. No se ha enviado código a Anthropic. La publicación pública del código en GitHub está autorizada. La API local queda como alternativa no seleccionada.

## Dos opciones

| Opción | Encaje en esta instalación | Pendiente |
|---|---|---|
| API de Claude desde el controlador | Adaptador local preparado; paquete explícito, sin herramientas, resultado JSON ligado a huella. | Elegir modelo, autorizar contenido/costo, credencial nueva en entorno autorizado, validar llamada real. |
| Claude Code en GitHub Actions | Revisión visible dentro del flujo de PR, desacoplada del constructor local. | Repositorio de destino, autenticación, permisos, workflow revisado y prueba real. No hay workflow activo en esta entrega. |

La Action oficial puede revisar PR, pero también modificar código según configuración. Admite API y OAuth de suscripción; las ejecuciones tienen consumo de GitHub y del proveedor. El ejemplo de revisión puede omitir PR borrador, triviales o ya comentados: una omisión no sirve como PASS de nuestra fábrica. La App oficial solicita permisos amplios; reducir `GITHUB_TOKEN` no reduce necesariamente los de otro token de App. Estas condiciones deben revisarse antes de instalar. [Documentación Anthropic](https://code.claude.com/docs/en/github-actions)

## Diseño seleccionado: Actions (no instalado)

- Primera activación manual y solo en un repositorio autorizado. Versiones de acciones fijadas por commit revisado; no seguir una etiqueta móvil sin evaluación.
- Checkout del commit exacto a revisar, sin credenciales persistidas. No ejecutar código o scripts del PR con secretos disponibles. No usar pull_request_target para ejecutar contenido no confiable.
- Proceso de revisión con permisos de lectura; sin herramientas de edición, terminal libre, merge o administración. Si publicar comentarios exige escritura, separar esa operación del modelo y validar el informe antes de usar un token limitado.
- No aceptar comentarios libres como aprobación. Importar resultado estructurado con repositorio, PR, head SHA, versión de la fábrica, modelo, pruebas y hallazgos. Cambiar head invalida el resultado anterior.
- Resultado ausente, omitido, cancelado o incompleto bloquea. Mantener los checks existentes y dos aprobaciones humanas; la Action no sustituye ninguna de ellas ni recibe bypass.
- No habilitar todos los bots o usuarios externos. La fábrica puede crear PR como bot: decidir quién solicita la revisión y verificar eventos antes de activar.
- Limitar concurrencia, tiempo y turnos; impedir ciclos de comentarios. Publicar solo un informe en español, no cambios automáticos.
- Revisar aparte cambios del controlador, políticas y workflow. El código evaluado no puede alterar su propio criterio de aprobación ni acceder a secretos del revisor.

## Costos verificables, no presupuesto contratado

Con API: costo = tokens de entrada / 1.000.000 × tarifa de entrada + tokens de salida / 1.000.000 × tarifa de salida, más caché u otras funciones usadas. Como ejemplo consultado el 5-11-2026, Sonnet 5.5 figura en USD 2/MTok de entrada y USD 10/MTok de salida: 50.000 de entrada + 5.000 de salida serían USD 0,15, sin caché ni herramientas adicionales. Es un ejemplo, no consumo medido ni elección de modelo. [Tarifas oficiales](https://platform.claude.com/docs/en/about-claude/pricing)

Actions añade cómputo y almacenamiento conforme al plan de GitHub; no se verificó el plan ni saldo de Fernando. No asumir gratuidad por disponer de Claude ni estimar ahorro sin medir uso. [Facturación GitHub Actions](https://docs.github.com/en/billing/concepts/product-billing/github-actions)

Los límites locales implementados son llamadas por tarea, tamaño de entrada, tiempo y salida de Claude. No hay aún límite monetario contractual. El adaptador Codex heredado limita tiempo y tamaño de propuesta, pero no acredita un límite de tokens facturados. Definir gasto máximo y alertas antes de habilitar cualquier proveedor.

## Revisión de la propia fábrica

`prepare-factory-review` genera paquetes locales con archivos, huellas y criterios de revisión. No los envía. Incluye código heredado, nuevo controlador, pruebas, piloto y documentación de controles. El manifiesto queda NOT_RUN; todas las partes y la interacción entre componentes necesitan revisión.

Claude debe identificar defectos, alcance, evidencia y pendientes en español. Ningún PASS parcial acredita la totalidad. Debe revisar especialmente límites de permisos, inyección de instrucciones, doble aceptación, contenido desactualizado, ejecución aislada, presupuesto y recuperación.

La puerta de entrega bloquea si falta la revisión de la versión de la fábrica. Los registros locales son preparación de evidencia, no autenticación de personas o certificación. Antes de producción se requiere conexión autenticada del resultado de Claude y aprobaciones humanas verificables.

Destino elegido y localizado: `fernandoruizm-maker/ERP-FACTORY`. Fernando autorizó mantenerlo público y publicar el código. Autenticación elegida: suscripción de Claude, condicionada a verificar el plan, que aún desconoce. Pendientes: confirmar plan, generar/configurar OAuth mediante el flujo autorizado, modelo, contenido autorizado para Anthropic, presupuesto y personas responsables. Publicar el código en GitHub no equivale a habilitar llamadas o conceder acceso persistente a Claude.

## Borrador concreto de primera revisión

`docs/actions/claude-factory-review.yml.disabled` prepara una revisión manual de los paquetes de la propia fábrica en una rama de confianza. Está fuera de `.github/workflows`, con trabajo deshabilitado y referencias pendientes de fijar a commits revisados. No es un workflow desplegado o probado en GitHub.

No instala la App oficial: el borrador pasa explícitamente el token efímero de GitHub con permisos de lectura. La compatibilidad real de la Action con ese token y el método de autenticación seleccionado debe validarse antes de activarla. No utilizar un PAT más amplio para solventar un fallo sin revisar la causa.

Primero se revisará la fábrica; después se adaptará el flujo de productos a PR y head SHA concretos. La recepción autenticada del resultado, la cobertura de las siete partes y la conclusión entre componentes siguen siendo requisitos de integración. Un job verde por sí solo no autoriza entregar, aprobar o publicar.
