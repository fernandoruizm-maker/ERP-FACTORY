"""Paquetes locales para revisión de la propia fábrica; nunca se transmiten aquí."""
import json
from pathlib import Path
from .core import Blocked, canonical, contained, digest, file_digest


CHECKS = [
    "Aislamiento: no acceso al ERP, secretos, red o publicación sin autorización.",
    "Codex no modifica sus pruebas, permisos ni reglas de aprobación.",
    "Claude no aprueba ni publica; falla bloqueando ante respuestas incompletas.",
    "Revisiones y dos aceptaciones independientes ligadas a contenido exacto.",
    "Presupuesto, expiración, concurrencia y resultados remotos inciertos sin reintentos.",
    "Recuperación transaccional y estado inicial vacío; nunca importar colas históricas.",
    "Rutas, enlaces, salida de procesos, pruebas vacías, omitidas y fallidas.",
    "Limitaciones reales: autenticación humana, tipos TS, contenedores y conexión no verificados.",
]


def packet(root, limit=60000):
    root = Path(root).resolve()
    files = {}
    for directory in ("factory2", "tests", "upstream", "pilot-js", "fixtures", "docs"):
        for path in sorted((root / directory).rglob("*")):
            if path.is_file() and path.suffix in (".py", ".mjs", ".ts", ".md", ".txt", ".json", ".disabled"):
                name = path.relative_to(root).as_posix()
                safe = contained(root, name)
                files[name] = safe.read_text(encoding="utf-8-sig")
    for name in ("config.json", "ORIGEN.json", "AGENTS.md", "README.md", "LEEME.md", "VER_ESTADO.cmd", "PROBAR_PILOTO.cmd"):
        path = contained(root, name)
        if path.is_file():
            files[name] = path.read_text(encoding="utf-8-sig")
    hashes = {name: file_digest(contained(root,name)) for name in files}
    factory_hash = digest(hashes)
    chunks, current = [], {}
    for name, body in files.items():
        if len(canonical({name:body}).encode()) > limit:
            raise Blocked("Archivo demasiado grande para un paquete; dividir la revisión explícitamente.")
        if current and len(canonical({**current,name:body}).encode()) > limit:
            chunks.append(current); current = {}
        current[name] = body
    if current: chunks.append(current)
    packets = [{"scope":"FACTORY_SELF_REVIEW", "factory_digest":factory_hash,
                "part":i+1,"total_parts":len(chunks),"checklist":CHECKS,"files":chunk}
               for i,chunk in enumerate(chunks)]
    manifest = {"factory_digest":factory_hash,"files":hashes,
                "packets":[{"part":i+1,"artifact_digest":digest(p)} for i,p in enumerate(packets)],
                "review_status":"NOT_RUN", "transmission_authorized":False,
                "note":"Todas las partes y su interacción requieren revisión antes de una conclusión global."}
    return manifest, packets


def validate_complete(manifest, reviews):
    from .core import validate_review
    expected = {p['artifact_digest'] for p in manifest['packets']}
    if len(reviews) != len(expected) or {r.get('artifact_digest') for r in reviews} != expected:
        raise Blocked('Revisión parcial: no acredita revisión de toda la fábrica.')
    for review in reviews:
        validate_review(review,review['artifact_digest'])
        if review['verdict'] != 'PASS':
            raise Blocked('Una parte de la fábrica tiene hallazgos bloqueantes.')
    return {"parts_complete":True,"factory_digest":manifest['factory_digest'],
            "status":"NEEDS_CROSS_COMPONENT_REVIEW", "publication_allowed":False}
