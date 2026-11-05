"""Contratos, descubrimiento y comparación basados en evidencia explícita."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path, PurePosixPath


class Blocked(ValueError):
    pass


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest(value):
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def file_digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def text(value, field):
    if not isinstance(value, str) or not value.strip() or len(value) > 10000:
        raise Blocked(f"Completar {field} con texto breve.")
    return value.strip()


def relative_path(name):
    if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z0-9_./-]+", name):
        raise Blocked("Ruta no permitida.")
    p = PurePosixPath(name)
    if p.is_absolute() or any(x in (".", "..") for x in name.split("/")) or "//" in name:
        raise Blocked("Ruta fuera del alcance.")
    if any(x.startswith(".") for x in p.parts):
        raise Blocked("Archivos privados fuera del alcance.")
    return p


def contained(root, name):
    p = relative_path(name)
    root = Path(root).resolve()
    target = root.joinpath(*p.parts)
    # Reject junctions/symlinks at every existing level, including broken symlinks.
    for part in (target, *target.parents):
        if part == root:
            break
        if part.is_symlink() or (hasattr(part, "is_junction") and part.is_junction()):
            raise Blocked("No se siguen enlaces del sistema de archivos.")
    if not target.resolve().is_relative_to(root):
        raise Blocked("Ruta fuera del alcance.")
    return target


QUESTIONS = {
    "client": "¿Para qué cliente o proyecto se prepara el sistema?",
    "objective": "¿Qué resultado quiere lograr el cliente?",
    "users": "¿Quién lo utilizará y qué puede hacer cada función?",
    "areas": "¿En qué áreas trabajará cada usuario?",
    "requirements": "¿Qué operaciones y resultados deben comprobarse?",
    "exclusions": "¿Qué queda fuera de esta primera entrega?",
}


def discover(brief):
    if not isinstance(brief, dict):
        raise Blocked("La ficha debe ser un objeto.")
    questions = [q for k, q in QUESTIONS.items() if not brief.get(k)]
    requirements = brief.get("requirements", [])
    if not isinstance(requirements, list):
        raise Blocked("Los requisitos deben ser una lista.")
    ids = set()
    for r in requirements:
        if not isinstance(r, dict):
            raise Blocked("Requisito inválido.")
        rid = text(r.get("id"), "identificador")
        if rid in ids:
            raise Blocked("Identificador de requisito repetido.")
        ids.add(rid)
        for field in ("goal", "acceptance", "document"):
            if not r.get(field):
                questions.append(f"{rid}: completar {field}.")
            else:
                text(r[field], field)
    return {"status": "NEEDS_INPUT" if questions else "READY_FOR_SCOPE_REVIEW",
            "brief_digest": digest(brief), "questions": questions,
            "requirements": requirements, "approved": False}


def compare(brief, catalog=None, *, evidence_root=None, permit=None):
    from .comparison_permit import permitted
    authorized = permitted(permit, catalog, evidence_root)
    discovery = discover(brief)
    rows = []
    for req in discovery["requirements"]:
        row = {"requirement": req["id"], "decision": "PENDIENTE",
               "reason": "No hay catálogo autorizado y comprobado.", "evidence": []}
        if catalog is not None and authorized and evidence_root is not None:
            capabilities = catalog.get("capabilities", [])
            matches = [c for c in capabilities if c.get("requirement") == req["id"]]
            if len(matches) == 1:
                cap = matches[0]
                decision = cap.get("decision")
                valid = decision in ("REUTILIZAR", "ADAPTAR", "CREAR") and bool(cap.get("evidence"))
                proofs = []
                for item in cap.get("evidence", []):
                    try:
                        path = contained(evidence_root, item["path"])
                        valid = valid and path.is_file() and file_digest(path) == item["sha256"]
                        valid = valid and bool(item.get("supports"))
                        proofs.append({"path": item["path"], "sha256": item["sha256"],
                                       "supports": item.get("supports", "")})
                    except (KeyError, OSError, Blocked):
                        valid = False
                # Absence of a file never establishes absence of a capability.
                if decision == "CREAR" and not cap.get("coverage_review"):
                    valid = False
                if valid:
                    row.update(decision=decision, reason=text(cap.get("reason"), "justificación"), evidence=proofs)
                else:
                    row["reason"] = "Evidencia incompleta, modificada o fuera de alcance. Revisar manualmente."
        rows.append(row)
    return {"brief_digest": discovery["brief_digest"], "rows": rows,
            "base": catalog.get("base", "No identificada") if authorized and catalog else "No autorizada",
            "synthetic": bool(catalog and catalog.get("synthetic")),
            "limitations": "Las huellas verifican archivos; la equivalencia funcional requiere revisión humana."}


def validate_edits(proposal):
    if not isinstance(proposal, dict) or set(proposal) != {"summary_es", "edits"}:
        raise Blocked("Propuesta de construcción inválida.")
    text(proposal["summary_es"], "resumen")
    edits = proposal["edits"]
    if not isinstance(edits, list) or not 1 <= len(edits) <= 10:
        raise Blocked("La propuesta debe contener de 1 a 10 archivos.")
    seen = set()
    total = 0
    for edit in edits:
        if not isinstance(edit, dict) or set(edit) != {"path", "content"}:
            raise Blocked("Edición inválida.")
        p = relative_path(edit["path"])
        if p.parts[0] != "src" or p.suffix not in (".py", ".js", ".mjs", ".ts", ".tsx", ".css"):
            raise Blocked("El constructor solo propone código dentro de src/. No modifica controles o pruebas.")
        key = str(p).casefold()
        if key in seen:
            raise Blocked("Archivo repetido.")
        seen.add(key)
        if not isinstance(edit["content"], str):
            raise Blocked("Contenido inválido.")
        total += len(edit["content"].encode("utf-8"))
    if total > 200000:
        raise Blocked("Propuesta demasiado grande.")
    return proposal


def validate_review(review, artifact_digest):
    if not isinstance(review, dict) or set(review) != {"artifact_digest", "verdict", "summary_es", "findings"}:
        raise Blocked("Revisión incompleta: no se acepta como aprobada.")
    if review["artifact_digest"] != artifact_digest or review["verdict"] not in ("PASS", "BLOCK"):
        raise Blocked("Revisión de otra versión o conclusión inválida.")
    text(review["summary_es"], "resumen de revisión")
    if not isinstance(review["findings"], list):
        raise Blocked("Hallazgos inválidos.")
    for finding in review["findings"]:
        if not isinstance(finding, dict) or set(finding) != {"severity", "detail_es"}:
            raise Blocked("Hallazgo incompleto.")
        if finding["severity"] not in ("low", "medium", "high", "critical"):
            raise Blocked("Gravedad inválida.")
        text(finding["detail_es"], "hallazgo")
    if review["verdict"] == "PASS" and any(f["severity"] in ("high", "critical") for f in review["findings"]):
        raise Blocked("La conclusión contradice un hallazgo bloqueante.")
    return review
