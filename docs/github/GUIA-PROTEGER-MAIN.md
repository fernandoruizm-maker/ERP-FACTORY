# Proteger main desde la web de GitHub

Esta guia y ruleset-main.json son una propuesta LOCAL. No se ha consultado ni
modificado GitHub. No se ha comprobado el esquema con su API ni el nombre actual
de cada boton. Si su pantalla no coincide, detengase y muestre el paso a Claude
sin incluir secretos. Crear reglas es un cambio de configuracion: esta tarea
no lo ejecuta; Fernando debe autorizar esa etapa antes de realizarlo.

## Crear o importar la regla

1. Entre con la cuenta que administra **fernandoruizm-maker/ERP-FACTORY**.
   Compruebe el nombre: no es el repositorio privado, que no se va a crear ahora.
2. Abra **Settings** (configuracion) > **Rules** > **Rulesets**.
3. Para importar, use **New ruleset > Import a ruleset** si aparece y elija
   `ruleset-main.json`. Si esa opcion no existe, cree **New branch ruleset**
   y complete los campos siguientes manualmente. No cree las dos reglas a la vez.
4. Nombre: **main - dos aprobaciones sin excepciones**. Estado de aplicacion:
   **Active**, no Disabled ni Evaluate.
5. En las ramas incluidas, agregue exactamente **main**; no agregue exclusiones.
6. Deje **Bypass list** completamente vacia: sin administradores, equipos,
   personas ni aplicaciones, ni excepciones solo para PR.
7. Marque **Restrict deletions** y **Block force pushes**.
8. Marque **Require a pull request before merging** y exija **2 approvals**.
   Marque tambien invalidar aprobaciones cuando llegan cambios nuevos, exigir
   aprobacion del ultimo envio por otra persona y resolver conversaciones.
9. No agregue aprobaciones automaticas ni un workflow de Claude como requisito.
   No marque una restriccion de todas las actualizaciones que impida incluso
   las integraciones validas; este borrador no contiene esa regla.
10. Revise todos los valores y guarde. Vuelva a abrir la regla para confirmar
    que los valores quedaron guardados y que se aplica a main.

## Que debe verse al terminar

- Regla **Active**, rama **main**, ninguna rama excluida y lista de bypass vacia.
- PR obligatoria, **2** aprobaciones, conversaciones resueltas y aprobaciones
  anteriores invalidadas al subir cambios nuevos.
- Borrado y force push de main prohibidos.
- Una PR incompleta muestra que faltan aprobaciones o conversaciones por resolver.

## Verificar que funciona, antes del permiso habitual para Codex

Fernando autoriza una prueba reversible con una PR ficticia, sin integrar nada.
Codex solo la prepara/sube cuando reciba esa autorizacion. Claude comprueba en
lectura los valores de la regla y el estado de la PR: sin aprobaciones no se
puede integrar; con una sigue bloqueada; una conversacion abierta bloquea; un
cambio nuevo invalida aprobaciones anteriores. No intentar borrar main ni forzar
un push para probarlo. Para esas prohibiciones se inspecciona la regla efectiva.
Dejar escrito que fue comprobado por comportamiento y que solo se inspecciono.
Cerrar la PR de prueba sin integrarla, con la autorizacion correspondiente.

No afirmar que funciona por haber importado un JSON o por ver una captura de
configuracion. Claude debe identificar repositorio, regla, PR de prueba y evidencia.
Esa comprobacion en el chat no es autenticacion criptografica ni un gasto automatico.

## Limites que no resuelve este archivo

- La regla exige dos aprobaciones, pero no identifica por rol a Fernando y
  FERRUMTJA ni limita por si sola quien puede pulsar Merge. Hay que comprobar
  que solo las personas previstas tienen los permisos correspondientes y que
  ambas aprobaron. Cambiar esos permisos requiere otra autorizacion expresa.
- El autor no puede aprobar su propia PR. Con estas dos personas, falta decidir
  una identidad distinta que abra las PR; no eliminar la segunda aprobacion.
- Un administrador con permiso para editar las reglas puede cambiarlas. Lista
  de bypass vacia significa que no hay excepciones configuradas, no que la
  configuracion sea imposible de modificar. Todo cambio requiere autorizacion.
- Si GitHub rechaza la importacion o su plan no permite alguna regla, no aplicar
  una version mas debil: registrar el impedimento y decidir con Fernando.

Para deshacer un error de configuracion, Fernando autoriza una correccion puntual
y Claude vuelve a comprobarla. No desactivar toda la proteccion como atajo. Hasta
que esa verificacion termine, cada subida sigue necesitando autorizacion expresa.
