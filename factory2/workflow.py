"""Preparación de entregas locales. Ningún método publica o activa servicios."""
from datetime import datetime, timezone
import json
from pathlib import Path

from .core import Blocked, canonical, compare, contained, digest, discover, validate_edits


def prepare(brief, catalog=None, *, evidence_root=None, permit=None):
    return {"discovery": discover(brief),
            "comparison": compare(brief, catalog, evidence_root=evidence_root, permit=permit),
            "scope_approved": False, "next": "Revisar ficha, dudas y matriz antes de construir."}


def stage(work_root, brief, proposal):
    """Store a model proposal in a NEW candidate; no edits to source or old candidates."""
    validate_edits(proposal)
    record = {"brief_digest": digest(brief), "proposal": proposal}
    candidate_hash = digest(record)
    parent = Path(work_root).resolve()
    candidate = contained(parent, "candidates/" + candidate_hash)
    if candidate.exists():
        raise Blocked("El candidato ya existe; no se sobrescribe ni ejecuta otra vez.")
    candidate.mkdir(parents=True)
    for edit in proposal["edits"]:
        target = contained(candidate, edit["path"])
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(edit["content"], encoding="utf-8")
    manifest = {"artifact_digest": digest(proposal), "brief_digest": digest(brief),
                "candidate_digest": candidate_hash, "status": "UNTESTED", "publication_allowed": False}
    (candidate / "candidate.json").write_text(canonical(manifest) + "\n", encoding="utf-8")
    return manifest


def report(prepared, results, *, artifact_digest=None):
    return {"generated_at": datetime.now(timezone.utc).isoformat(),
            "installation": "rdc-factoria-2-local", "mode": "LOCAL_SYNTHETIC_ONLY",
            "prepared": prepared, "tests": results, "artifact_digest": artifact_digest,
            "claude_review": {"status": "NOT_RUN", "reason": "Sin autorización de transmisión, modelo ni credencial configurados."},
            "erp_comparison": {"status": "NOT_AUTHORIZED"},
            "human_approvals": {"status": "PENDING", "required": 2},
            "publication_allowed": False}


def markdown_report(data):
    lines = ["# Segunda fábrica · informe de ensayo", "",
             "Datos ficticios. No se utilizó el ERP ni se llamó a Claude o Codex desde la fábrica.", "",
             "## Resultado esperado", "",
             "Solicitar 10 botellas, autorizar con gerente o subgerente independiente de bodega, "
             "ejecutar una salida y comprobar saldo 0. Repetir la operación no genera otro descuento.", "",
             "## Pruebas ejecutadas", "", "| Perfil | Resultado | Pruebas |", "|---|---|---:|"]
    for r in data["tests"]:
        lines.append(f"| {r['profile']} | {r['status']} | {r['test_count']} |")
    lines += ["", "TypeScript: ejecución con eliminación de tipos; no se ejecutó un compilador de comprobación de tipos.",
              "", "## Cómo revisar el ejemplo", "",
              "1. Abrir `comprobante-ensayo.html`: debe mostrar 10 botellas y saldo 0.",
              "2. Consultar `piloto.json`: debe haber una sola salida y resultado repetido idéntico.",
              "3. Las pruebas negativas rechazan otra área, autoaprobación, falta de aprobación y stock insuficiente.",
              "4. La impresión consulta el documento existente; no genera movimientos.", "",
              "## Pendiente antes de uso real", "",
              "- Revisión real con Claude y construcción autónoma con Codex: no ejecutadas.",
              "- Comparación con el ERP: sin acceso autorizado; la matriz permanece pendiente.",
              "- Dos aceptaciones humanas autenticadas y vinculadas a una versión.",
              "- Ejecutor Docker para código no confiable y prueba de recuperación en el destino definitivo.",
              "- Modelo, autorización de transmisión, credenciales y presupuesto monetario de proveedores.",
              "- La nueva instalación está desactivada; no tiene consumidor de tareas ni capacidad de despliegue."]
    return "\n".join(lines) + "\n"
