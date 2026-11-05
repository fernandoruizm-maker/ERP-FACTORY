# Revisiones manuales: como conservar la evidencia

Claude revisa los cambios de cada PR en el chat. Antes de una entrega importante,
Fernando abre una conversacion nueva y pide revisar la fabrica completa. Este
trabajo no acredita que Claude ya haya revisado el bloque 6.

Codex registra una revision recibida usando PLANTILLA.md. La copia se guarda como
PR-N-SHA.local.md en docs/revisiones/; .gitignore la excluye de los commits normales.
Asi guardar el informe no cambia el SHA revisado ni crea un ciclo interminable de
revisar el commit que agrega su propia revision. No forzar su inclusion con git add -f.
Estos archivos locales deben conservarse junto con el expediente de la entrega;
no se crea aqui un respaldo externo ni una transmision automatica.

La puerta local importa el documento con Store.import_manual_review(path). Guarda
sus bytes y una huella, exige reviewed_sha exacto y enlaza las aceptaciones a esa
revision, version de requisitos, SHA y huella de fabrica. No autentica a Claude ni
a las personas, no comprueba por si sola que el diff declarado sea exhaustivo, ni
convierte una prueba simulada en integracion real. Un cambio del documento crea
otra revision; requiere aceptaciones nuevas. No hay sustituciones silenciosas.

La plantilla, esta guia y las pruebas se versionan; los informes reales no se
publican automaticamente. Si se decide archivar un informe en Git mas adelante,
debe ser en una revision documental separada que indique claramente el SHA anterior
al que corresponde. No usar ese registro como evidencia de un nuevo SHA.

CORREGIR bloquea. SIN OBJECIONES TÉCNICAS solo permite continuar la revision humana.
Las dos personas son business (negocio) y accounting (contable/funcional). Claude
no ocupa ninguna de esas plazas. No hay revisor tecnico humano; se requiere una
auditoria tecnica externa antes de datos reales de clientes o conexion al ERP.
