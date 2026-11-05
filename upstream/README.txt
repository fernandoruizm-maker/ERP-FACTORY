AI SOFTWARE FACTORY — MVP ISSUE A PR
Actualizado: 3 de noviembre de 2026.

El servicio está en factory/mvp/. Guía: OPERACION-MVP.txt y ACTIVACION-APP.txt.
Puede consultar issues de GitHub periódicamente desde un PC, ejecutar agentes
reales mediante Codex CLI o Responses API, verificar RED/GREEN en Docker y
abrir un PR borrador. También conserva un receptor de webhook firmado opcional.
Todos los cambios Python del MVP requieren revisión humana; no integra ni despliega.

PILOTO SIN WEBHOOK
Configurar la GitHub App con config.app.example.json, fuera del repositorio.
Instalar requirements-app.txt para la firma RSA de la App.
  python -m unittest discover -s tests -q
  python -m factory.mvp --config RUTA_CONFIG_PRIVADA doctor
  python -m factory.mvp --config RUTA_CONFIG_PRIVADA pilot
El piloto consulta cada cinco minutos, usa sólo conexiones salientes y no abre
puertos. Crear la issue, terminar de editarla y aplicar al final ai-factory.
Ese acto debe hacerlo un humano autorizado con permiso de escritura.
La autorización se comprueba de nuevo antes de generar y antes de publicar.
Se registra cada evento de etiqueta para no duplicar tareas al reiniciar.

REQUISITOS
Python 3.11+, cryptography para GitHub App, Docker con imagen fijada por digest,
una sesión Codex autenticada o una clave API para Responses, y código Python
con pruebas de baseline que pasen. Protecciones de rama verificables y revisión
humana independiente. La operación autónoma requiere GitHub App y Rulesets
auditadas: el modo clásico heredado se bloquea. config.example.json se conserva
para fixtures y simulaciones; usar config.app.example.json para el piloto real.
En modo polling no se necesita secreto ni URL de webhook.

EVIDENCIA Y ESTADO
VERIFICATION.txt distingue pruebas automáticas, conexiones reales y simulaciones.
Primera issue real completada por polling: issue 3 -> PR 4 en rdc, 17 tests en
regresión y tres revisores PASS. El humano aprobó e integró los PR 2 y 4.
El PR 1 de infraestructura requiere su propia aprobación independiente.
Revisión previa a su integración: 90 tests del controlador y 17 del producto
pasan; ver REVIEW-PR1.md y VERIFICATION.txt. Las correcciones del PR 1 todavía
no sustituyen la versión que está ejecutándose en el PC.
examples/critical_backend.py ejecuta agentes y tests reales contra GitHub simulado.
La demo original demo.py sigue siendo una simulación offline del motor de políticas.
ARQUITECTURA.html describe el diseño objetivo; no todo su alcance está implementado.

LÍMITES
Un repositorio y un worker por directorio de estado. Producto Python/unittest,
sin Sentry, frontend visual, migraciones ejecutadas ni despliegue automático.
Las revisiones de modelos no garantizan ausencia de defectos. Los datos privados
del controlador deben permanecer fuera del repositorio y del contexto de agentes.
