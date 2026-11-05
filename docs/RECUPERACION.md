# Recuperación y continuidad

## Estado inicial

`config.json` conserva todos los interruptores desactivados. `state/factory2.sqlite3` es nuevo y no contiene la cola original. Los ensayos usan bases temporales y el ejemplo de botellas usa memoria; sus informes quedan en outputs.

## Llamada interrumpida

La reserva de cada llamada se confirma en SQLite ANTES de transmitir. Una caída deja IN_FLIGHT; `python -B -m factory2 recover` lo cambia a UNKNOWN. La llamada mantiene su consumo de presupuesto. No se reenvía automáticamente ni se asume que no costó dinero. Un operador deberá contrastar el resultado con el proveedor antes de autorizar otro intento.

El comando no importa ni toca colas de Windows o Ubuntu. No modifica la configuración y no conecta proveedores.

## Cambios después de revisar

Un expediente incluye el hash del código. Cambiarlo invalida las aceptaciones. Actualizar el expediente elimina sus aceptaciones anteriores incluso si se vuelve al contenido previo. La revisión de Claude y las pruebas deben corresponder a ese código; la versión de la propia fábrica también necesita revisión.

## Recuperar una instalación futura

1. Mantenerla desactivada y detener de forma autorizada su único ejecutor antes de restaurar.
2. Conservar evidencia de la incidencia. Copiar SQLite mediante su API de backup en una futura operación autorizada; no copiar una base viva de manera improvisada.
3. Restaurar código, configuración no sensible y estado de una misma versión; comprobar huellas e integridad SQLite.
4. Marcar llamadas en curso como inciertas, sin repetirlas. Verificar que no haya otro consumidor activo.
5. Ejecutar pruebas locales, revisión de Claude y revisión humana antes de cualquier reactivación.

Esta entrega prueba reapertura de SQLite y recuperación de llamadas inciertas, además de restauración del estado ficticio de botellas. No se hizo una restauración completa en otra máquina. No hay procedimiento autorizado para modificar el ERP, GitHub o la primera fábrica.

## Volver al original

La primera fábrica permanece intacta. No encender ambas. La decisión futura de volver al original requiere reconciliar tareas y confirmar qué instancia tiene autorización para recibirlas; el código nuevo no ejecuta esa transición.
