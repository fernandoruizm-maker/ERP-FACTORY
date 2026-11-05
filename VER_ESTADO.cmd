@echo off
setlocal
pushd "%~dp0"
set "RDC2_PYTHON=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if not exist "%RDC2_PYTHON%" (
  echo Python de Codex no encontrado. No se instalara ni activara nada.
  popd
  exit /b 2
)
"%RDC2_PYTHON%" -B -m factory2 status
set "RDC2_RESULT=%ERRORLEVEL%"
popd
exit /b %RDC2_RESULT%
