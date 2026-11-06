# Segunda fábrica RDC

- Instalación local de desarrollo, desactivada. No activar el original ni esta copia automáticamente.
- No acceder al ERP, credenciales, GitHub o servicios externos sin autorización específica.
- `upstream/` es la referencia verificada de 53 archivos: no editarla ni ejecutar su piloto.
- La nueva implementación vive en `factory2/`. Nunca importar tareas de `estado/` del ZIP.
- Usar datos ficticios. Las pruebas de adaptadores simulados no acreditan llamadas reales.
- Conservar revisión Claude y aceptaciones por nivel, vinculadas al contenido exacto: ERP-FACTORY requiere Fernando; productos con impacto contable requieren Fernando y FERRUMTJA. Destino no clasificado: bloquear. No cambiar reglas remotas sin autorización.
- No hay capacidad de integrar o desplegar. Un informe listo para revisión no autoriza publicación.
- Pruebas: Python unittest y Node test runner. TS se ejecuta sin comprobación estática de tipos.
- Registrar verificación y limitaciones en `docs/ESTADO.md`.
