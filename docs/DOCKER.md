# Docker: ensayo real autorizado del bloque 9

Fernando arranco Docker Desktop y declaro cumplir los limites de licencia gratuita
(menos de 250 empleados y menos de USD 10 millones anuales). Se registra su
declaracion: no es auditoria de la empresa ni verificacion en linea de la licencia.
No se instalo, actualizo ni configuro Desktop/WSL. Solo se descargaron las dos
imagenes autorizadas; despues los ensayos usaron el motor local, sin red externa.

## Imagenes aprobadas y descargadas una vez

Ambas oficiales de Docker Hub, plataforma linux/amd64, variantes slim:

| Imagen descargada | Referencia inmutable utilizada por DockerRunner |
|---|---|
| docker.io/library/python:3.13-slim | `python@sha256:09a17cad02668ae61ece136b4fd36ac3849e14f670ebedb637ea3e15580525bc` |
| docker.io/library/node:24-slim | `node@sha256:01d566e8d94d8c619591d78652babfccd3c6992a3dffa9ed5ab39e11cf6c70e9` |

Se comprobaron esos RepoDigests mediante image inspect local. Tamanos informados:
Python 176201667 bytes; Node 330375508 bytes (no son bytes medidos de descarga).
No se consulto la red para resolver versiones adicionales ni vulnerabilidades.
Comandos ejecutados, cada pull una sola vez:

```powershell
docker --host npipe:////./pipe/dockerDesktopLinuxEngine pull --platform linux/amd64 docker.io/library/python:3.13-slim
docker --host npipe:////./pipe/dockerDesktopLinuxEngine pull --platform linux/amd64 docker.io/library/node:24-slim
```

## Resultado real del ensayo

Motor comprobado: **29.9.2, linux/amd64**. El entorno filtrado de DockerRunner
usa el canal local `npipe:////./pipe/docker_engine`; se comprobo que su ID coincide
con el de `dockerDesktopLinuxEngine`. No se cambio ningun contexto ni configuracion.

| Pruebas dentro de contenedores | Ejecutadas | Fallos | Omitidas |
|---|---:|---:|---:|
| Piloto Python | 13 | 0 | 0 |
| Piloto JavaScript | 7 | 0 | 0 |
| Aislamiento ficticio Python | 3 | 0 | 0 |

Se uso DockerRunner.run sin modificar factory2/runner.py: --pull=never,
--network=none, --read-only, --user=65534:65534, --cap-drop=ALL y
no-new-privileges. UID/GID 65534, capacidades efectivas cero y NoNewPrivs=1
comprobados dentro del contenedor. Se rechazaron crear/modificar archivos en
/workspace y crear archivos en la raiz; las huellas de todos los archivos
temporales del host coincidieron antes/despues. Solo existia la interfaz lo:
conectar a 192.0.2.1:9 (direccion ficticia TEST-NET-1) fallo con ENETUNREACH.
No se intento contactar un servicio real para probarlo.

Comprobacion de descargas: cada comando run llevaba --pull=never; la consulta
local de eventos de imagen pull durante el ensayo final devolvio **0 eventos**.
Las imagenes se inspeccionaron antes; ningun comando del ensayo hace pull/build.
Los tres contenedores de prueba se retiraron con comandos por su nombre unico.
No se tocaron otros contenedores ni se apago el motor iniciado por Fernando.

Comando ejecutado desde la raiz (no repetir sin autorizacion):

```powershell
& "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -B -m tests.docker_pilot_check --python-image python@sha256:09a17cad02668ae61ece136b4fd36ac3849e14f670ebedb637ea3e15580525bc --node-image node@sha256:01d566e8d94d8c619591d78652babfccd3c6992a3dffa9ed5ab39e11cf6c70e9 --output ..\entregas-locales\bloque-9-docker-real-3
```

El auxiliar es optativo; unittest discover no lo ejecuta. Prepara solo fixtures
temporales de codigo/pruebas, sin montar el repositorio ni credenciales. Guarda
evidence.json y commands-and-output.json fuera del repositorio; no invoca proveedores.
Usa Docker local y exige un directorio de salida nuevo para no sobrescribir evidencia.

Incidencias conservadas: el intento 1 no creo contenedores porque el auxiliar
exigia solo el nombre dockerDesktopLinuxEngine; se corrigio para admitir tambien
docker_engine despues de comprobar el mismo ID de motor. En el intento 2 pasaron
las 23 pruebas, pero fallo el formato `.ID` de la consulta de eventos. Se corrigio
solo esa lectura usando un marcador literal por evento. Intento 3: ensayo completo
PASS, incluida ausencia de pulls. No hubo nuevas descargas ni cambios al ejecutor.

Limites: se prueba este piloto y estas imagenes en este PC, no contencion de todo
codigo malicioso ni ausencia absoluta de vulnerabilidades. No Docker en GitHub,
ERP, proveedores, datos reales o TS dentro de Docker. El motor puede tener red;
la restriccion comprobada es la de los contenedores del ensayo. La politica de
licencia vigente sigue sin verificarse en linea. Configuracion de activacion intacta.

---

# Historia: inventario y opciones (fase 1, antes del arranque y las descargas)

Los estados detenido, digests pendientes y pruebas no ejecutadas que siguen
describen la fase anterior. Los resultados vigentes son los de arriba. Los pasos
futuros conservados no autorizan nuevas instalaciones, descargas ni configuraciones.

Solo preparacion documental. No se ha arrancado, instalado, actualizado ni
configurado Docker, WSL o Windows. Tampoco se han descargado imagenes, ejecutado
contenedores ni conectado proveedores. La fabrica sigue desactivada.

Rama: `docs/bloque-9-docker`. Base local de origin/main:
`877dd757f83f5fece05e2216ddfdea36843f0c4a`. No se hizo fetch en esta fase:
no se afirma que esta referencia coincida con GitHub ahora.

## Lo observado en este PC

Lectura del 6-11-2026 UTC (5-11-2026 segun el reloj local del equipo).

| Elemento | Resultado observado |
|---|---|
| Docker Desktop | Instalado para el usuario; version del ejecutable 4.98.0.245422 |
| Cliente docker | 29.9.2, compilacion a82e528; es la version del cliente, no del motor |
| Motor Linux de Desktop | No disponible en su canal local dockerDesktopLinuxEngine: archivo/canal no encontrado |
| Procesos Docker | No aparecieron Docker Desktop, com.docker.backend ni dockerd en la consulta |
| WSL | Instalado, version 3.0.3.0; kernel 6.18.54.1-1 |
| Distribuciones | Ubuntu-24.04: detenida, WSL 2; docker-desktop: detenida, WSL 2 |
| Predeterminada | Ubuntu-24.04; version predeterminada para distribuciones: WSL 2 |
| Windows | Microsoft Windows 11 Home, 64 bits; 10.0.26300, build 26300; WSL informa revision 26300.9711 |
| CPU y memoria | Intel Core i9-12900H (12.ª generacion); 15,7 GiB de memoria fisica |
| Virtualizacion | Windows informa HypervisorPresent=True, pero los tres indicadores CIM del procesador son False |
| Disco C: | 157,52 GiB libres; 381,44 GiB usados |
| Disco D: | 64,97 GiB libres; 325,66 GiB usados |

Conclusion: Desktop ya esta instalado y no se observo un motor local Linux
en marcha. La version del motor queda NO VERIFICADA. No se comprobo si hay
Docker Engine instalado dentro de Ubuntu: esta detenida y entrar en ella podria
arrancarla. No se buscaron contextos remotos ni se leyeron credenciales.

Hay un hipervisor activo, pero no se puede deducir de los indicadores CIM que
la virtualizacion del firmware este desactivada. La compatibilidad completa de
este build de Windows con esta version de Desktop queda NO VERIFICADA. Fernando
puede consultar, sin cambiar nada: clic derecho en Inicio > Administrador de
tareas > Rendimiento > CPU > Virtualizacion. Si la informacion no concuerda,
se investigara antes de tocar BIOS/UEFI; no se propone cambiarla ahora.

Las lecturas CIM y de estado WSL se denegaron inicialmente en el entorno
restringido. Se repitieron mediante la autorizacion formal del entorno, solo
lectura y sin red; funcionaron. Docker se consulto por una tuberia local de
Windows explicita, no por un servidor TCP. El espacio libre es una fotografia
del momento, no una reserva de capacidad.

## Opciones y recomendacion

| Opcion | Ventajas | Inconvenientes / condiciones |
|---|---|---|
| Aprovechar Docker Desktop instalado, con motor Linux sobre WSL 2 | Interfaz por clics; docker.exe ya disponible; encaja con el ejecutor de Windows de la fabrica | Licencia por comprobar; usa memoria y disco; compatibilidad y arranque aun no probados |
| Docker Engine dentro de Ubuntu-24.04 WSL 2 | Motor Linux sin depender de la suscripcion de Desktop; control de su mantenimiento | Instalacion y administracion Linux, actualizaciones y permisos; no ofrece el mismo flujo sencillo por clics; requiere adaptar o ejecutar el runner en WSL |

**Recomiendo comprobar y aprovechar Desktop ya instalado**, condicionado a
licencia y compatibilidad. No hace falta reinstalarlo por encontrar el motor
detenido. La alternativa WSL es posible en principio, pero no esta preparada:
el runner invoca `docker` desde Windows con rutas Windows. No basta con instalar
un motor en Ubuntu; habria que resolver esa integracion y probarla. No se propone
exponer un motor sin autenticacion por TCP ni operar dos motores en paralelo.

### Licencia: informacion conocida, NO VERIFICADA actualmente

Sin consultar la red, la politica de Docker Desktop conocida permite uso gratuito
personal, educativo, en proyectos de codigo abierto no comerciales y en pequenas
empresas con **menos de 250 empleados Y menos de USD 10 millones de ingresos
anuales**. El uso profesional fuera de esos limites y las entidades gubernamentales
requieren suscripcion de pago segun esa politica. No se ha comprobado la vigencia
actual, las excepciones contractuales ni si la empresa de Fernando cumple los
criterios. Tampoco se afirma que la instalacion tenga una licencia contratada.

Docker Engine es software de codigo abierto; sus licencias y las condiciones
de servicios como Docker Hub siguen siendo aplicables. No confundir Engine con
la licencia de Desktop. Antes de aceptar condiciones o contratar, Fernando debe
verificar la politica oficial vigente. Referencias para esa etapa autorizada,
**no consultadas en esta tarea**:
[licencia Desktop](https://docs.docker.com/subscription/desktop-license/),
[acuerdo de suscripcion](https://www.docker.com/legal/docker-subscription-service-agreement/),
[requisitos Windows](https://docs.docker.com/desktop/setup/install/windows-install/).

## Imagenes que necesitara el piloto

Dos imagenes Linux para arquitectura amd64: una de Python y una de Node.
Seleccion inicial a confirmar: Python 3.13 slim y Node 24 slim, distribuidas
como imagenes oficiales `docker.io/library/python` y `docker.io/library/node`.
Node debe admitir `--experimental-strip-types` y el ejecutor de pruebas TAP.
El piloto utiliza bibliotecas incluidas en Python/Node; no se propone pip ni npm
con red durante los ensayos. No se verificaron disponibilidad, vulnerabilidades,
tamano ni compatibilidad de una imagen concreta.

Los identificadores aprobados seran `nombre@sha256:DIGEST_REAL_DE_64_HEX`.
Esto es un ejemplo de formato, **no un digest utilizable**. Ambos digests estan
PENDIENTES. Se registraran version, plataforma, digest y fecha de aprobacion.
El digest fija contenido, pero no certifica que sea seguro.

Con autorizacion expresa para la descarga, se resolveran los digests y se
descargara una vez cada imagen aprobada. Se confirmara que estan en el motor
local elegido. Los ensayos posteriores usan `--pull=never`: si falta una imagen,
deben fallar, no descargarla. Si se borra la cache o se decide otra version,
cualquier nueva descarga necesita otra autorizacion.

## Pasos futuros para Fernando (NO realizados)

1. Autorizar primero la comprobacion de licencia y requisitos oficiales. Si se
   necesita pagar, decidirlo antes de aceptar una suscripcion.
2. Como Desktop ya esta instalado, no descargar otro instalador ni actualizarlo
   automaticamente. Autorizar su primer arranque de prueba; abrir Inicio >
   Docker Desktop. Si pide actualizar, instalar componentes o reiniciar, parar
   y decidir ese cambio por separado. Los nombres de menus no se verificaron.
3. Con autorizacion para configurarlo: Settings/Configuracion > General > usar
   motor WSL 2, si aparece esa opcion. Mantener desactivado el inicio al entrar
   en Windows. No habilitar Kubernetes, conexiones remotas ni integraciones
   WSL adicionales para el piloto. Cualquier boton Apply/Restart cambia estado.
4. Confirmar visualmente que el motor Linux esta listo. Codex comprobara, con
   permiso, la version del servidor y que docker usa el motor local correcto.
   El runner no fija un contexto Docker: ese destino debe verificarse antes.
5. Autorizar por separado la descarga de las dos imagenes fijadas por digest.
   Despues, autorizar el ensayo local descrito abajo. Nada requiere activar la
   fabrica, sus proveedores o sus workflows.
6. Si mas adelante hiciera falta reinstalar: verificar requisitos y licencia,
   descargar el instalador oficial con permiso, comprobar su firma, elegir WSL 2
   y completar el asistente. No reutilizar descargas de procedencia desconocida.
   Codex solo lo ejecutara con una autorizacion especifica para esa instalacion.

## Como comprobar DockerRunner despues

Este apartado es un plan, **NO una prueba Docker ejecutada**. Las pruebas previas
con dobles no acreditan contenedores reales. Codex preparara, con autorizacion,
una carpeta temporal nueva con solo codigo del piloto y pruebas de confianza,
sin .git, datos ERP, estado historico, credenciales ni archivos de entorno.

- Python: `factory2/__init__.py`, `factory2/core.py`, `factory2/pilot.py`,
  `tests/__init__.py` y `tests/test_pilot.py`, conservando su estructura.
- JS/TS: `src/bottles.mjs` y `tests/bottles.test.mjs`, `tests/bottles.test.ts`
  tomados de `pilot-js/`, en otra carpeta temporal. No montar el repositorio entero.
- Calcular la huella del material y llamar a `DockerRunner.run(directory, image,
  profile, tests, artifact_digest)` con cada perfil y sus archivos explicitos.
  No es necesario entrar por los adaptadores de Claude/Codex ni habilitar config.

El codigo actual exige imagen por digest y genera estas restricciones:

| Control | Comportamiento de runner.py |
|---|---|
| Red y descarga | `--network=none`, `--pull=never` |
| Archivos | Raiz del contenedor y montaje /workspace de solo lectura |
| Usuario | `65534:65534`, sin privilegios; `--cap-drop=ALL`, `no-new-privileges` |
| Recursos | 512 MB de memoria, 1 CPU, 64 procesos; limite de 60 s por prueba |
| Temporales | /tmp escribible, 64 MB, noexec y nosuid; Python no escribe bytecode |
| Limpieza | Contenedor de ensayo con nombre unico; se elimina al terminar |

Solo lectura se refiere al codigo montado y al sistema de archivos raiz del
contenedor: el motor crea contenedores y usa disco local; /tmp y los informes de
ensayo si se escriben. No es una operacion de inventario sin cambios. El usuario
no privilegiado dentro del contenedor no convierte al motor Docker en un servicio
sin privilegios; no se montara su socket ni se usara `--privileged`.

Comprobar con pruebas ficticias adicionales: UID distinto de cero, escritura
rechazada en /workspace y en la raiz, y conexion rechazada a un servidor ficticio
del host (sin consultar internet). Verificar tambien el comando generado y las
huellas de entrada/salida. No suponer aislamiento solo porque el piloto pase.
No cambiar las protecciones para hacer pasar una prueba: registrar cualquier fallo.

Resultado funcional esperado: pedir diez botellas, aprobar desde la misma area
con otra persona, descontar una sola vez, saldo cero y comprobante ficticio;
rechazar otra area, autoaprobacion y stock insuficiente. Registrar cantidades
reales de pruebas, fallos, omitidas, imagen/digest, version del motor y SHA del
codigo. TS no comprueba tipos estaticamente. Comprobar que no queda el contenedor
de ensayo y que config.json continua desactivado. No se prueban ERP ni proveedores.

## Como deshacerlo, si Fernando lo decide

Primero cerrar solo los ensayos autorizados. Para detener Desktop: icono de la
ballena junto al reloj > Quit/Salir. Esto detiene otros contenedores que pudiera
haber: comprobarlos antes. No apagar distribuciones WSL ajenas.

Para desinstalar: Inicio > Configuracion > Aplicaciones > Aplicaciones instaladas
> Docker Desktop > Desinstalar, y seguir el asistente. Puede borrar imagenes,
contenedores y volumenes: revisar y autorizar esa perdida antes; no usar limpieza
global ni Factory reset como primer paso. No borrar Ubuntu-24.04, sus datos ni
desregistrar distribuciones WSL automaticamente. Comprobar despues que Desktop
ya no figura y que los archivos de la fabrica siguen intactos.

Si se eligiera Engine en Ubuntu, Codex prepararia antes un inventario de sus
paquetes/datos y un procedimiento autorizado para detenerlo y retirar solo los
paquetes instalados para esta tarea. No se ofrece un comando de borrado masivo.
La desinstalacion real y la recuperacion de datos no se han probado.

## Verificacion de esta fase

Lecturas: versiones CLI/ejecutable, `wsl --version`, `wsl --status`,
`wsl --list --verbose`, consultas CIM limitadas, procesos por nombre, espacio
de discos y version del servidor por tuberia local explicita (fallo: no existe).
No se inicio ninguna distribucion para averiguar sus paquetes.

Se reviso el documento contra factory2/runner.py y las pruebas del piloto.
No se ejecutaron suites ni codigo del proyecto: el cambio es solo documental.
La licencia vigente, las pantallas, digests, motor real, aislamiento efectivo,
compatibilidad y desinstalacion permanecen NO VERIFICADOS.
