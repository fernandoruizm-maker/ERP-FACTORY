"""Estado propio; no importa la cola de la primera fábrica."""
import json
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path

from .core import Blocked, canonical, digest, validate_review


class Store:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.executescript("""
            CREATE TABLE IF NOT EXISTS tasks(id TEXT PRIMARY KEY, version TEXT NOT NULL,
                brief TEXT NOT NULL, status TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS calls(id TEXT PRIMARY KEY, task TEXT NOT NULL,
                provider TEXT NOT NULL, payload TEXT NOT NULL, status TEXT NOT NULL,
                output_limit INTEGER NOT NULL, created REAL NOT NULL);
            CREATE TABLE IF NOT EXISTS acceptances(task TEXT, version TEXT, person TEXT,
                role TEXT, PRIMARY KEY(task,version,role));
            """)

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=5)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    def put_task(self, task, brief):
        version = digest(brief)
        with self.connect() as db:
            db.execute("INSERT INTO tasks VALUES(?,?,?,?) ON CONFLICT(id) DO UPDATE SET "
                       "version=excluded.version,brief=excluded.brief,status=excluded.status",
                       (task, version, canonical(brief), "DRAFT"))
            # All acceptances are discarded even if a previous version is restored.
            db.execute("DELETE FROM acceptances WHERE task=?", (task,))
        return version

    def reserve_call(self, call_id, task, provider, payload_hash, *, max_calls, output_limit):
        if not 1 <= max_calls <= 10 or not 1 <= output_limit <= 4096:
            raise Blocked("Límite de llamadas o salida inválido.")
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            if not db.execute("SELECT 1 FROM tasks WHERE id=?", (task,)).fetchone():
                raise Blocked("Tarea desconocida.")
            if db.execute("SELECT 1 FROM calls WHERE id=?", (call_id,)).fetchone():
                raise Blocked("Llamada ya reservada: no se reintenta automáticamente.")
            if db.execute("SELECT count(*) FROM calls WHERE task=?", (task,)).fetchone()[0] >= max_calls:
                raise Blocked("Presupuesto de llamadas agotado.")
            db.execute("INSERT INTO calls VALUES(?,?,?,?,?,?,?)",
                       (call_id, task, provider, payload_hash, "IN_FLIGHT", output_limit, time.time()))

    def finish_call(self, call_id, status):
        if status not in ("COMPLETED", "UNKNOWN", "REJECTED"):
            raise Blocked("Estado de llamada inválido.")
        with self.connect() as db:
            updated = db.execute("UPDATE calls SET status=? WHERE id=? AND status='IN_FLIGHT'", (status, call_id))
            if updated.rowcount != 1:
                raise Blocked("La llamada no estaba en curso.")

    def recover(self):
        with self.connect() as db:
            count = db.execute("UPDATE calls SET status='UNKNOWN' WHERE status='IN_FLIGHT'").rowcount
        return {"uncertain_calls": count, "retried": 0,
                "action": "Reconciliar manualmente; no reenviar ni liberar presupuesto automáticamente."}

    def accept(self, task, version, person, role):
        # Local operator records only. Not identity authentication or a GitHub approval.
        if role not in ("business", "technical") or not isinstance(person, str) or not person.strip():
            raise Blocked("Se requiere identidad y función de revisión.")
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT version FROM tasks WHERE id=?", (task,)).fetchone()
            if row is None or row[0] != version:
                raise Blocked("Aceptación desactualizada.")
            if db.execute("SELECT 1 FROM acceptances WHERE task=? AND version=? AND person=? AND role<>?",
                          (task, version, person.casefold(), role)).fetchone():
                raise Blocked("Las dos revisiones deben corresponder a personas distintas.")
            db.execute("INSERT OR REPLACE INTO acceptances VALUES(?,?,?,?)",
                       (task, version, person.casefold(), role))

    def gate(self, task, version, artifact_digest, review, tests, *, factory_review=None, factory_digest=None):
        reasons = []
        with self.connect() as db:
            row = db.execute("SELECT version,brief FROM tasks WHERE id=?", (task,)).fetchone()
            roles = {r[0] for r in db.execute("SELECT role FROM acceptances WHERE task=? AND version=?", (task, version))}
        if row is None or row[0] != version:
            reasons.append("La versión de requisitos cambió.")
        if row is None or json.loads(row[1]).get("artifact_digest") != artifact_digest:
            reasons.append("El código no corresponde al expediente aceptado.")
        if roles != {"business", "technical"}:
            reasons.append("Faltan las dos aceptaciones humanas locales.")
        try:
            validate_review(review, artifact_digest)
            if review["verdict"] != "PASS":
                reasons.append("Claude bloqueó la entrega.")
        except (Blocked, TypeError):
            reasons.append("Revisión ausente, incompleta o de otra versión.")
        try:
            if not factory_digest:
                raise Blocked("Sin versión de fábrica.")
            validate_review(factory_review, factory_digest)
            if factory_review["verdict"] != "PASS":
                reasons.append("La revisión de la propia fábrica está bloqueada.")
        except (Blocked, TypeError):
            reasons.append("Falta revisión de Claude de esta versión de la propia fábrica.")
        if not tests or any(t.get("status") != "PASS" or t.get("test_count", 0) < 1 or t.get("artifact_digest") != artifact_digest for t in tests):
            reasons.append("Pruebas ausentes, fallidas o de otra versión.")
        return {"status": "BLOCKED" if reasons else "READY_FOR_MANUAL_REVIEW",
                "reasons": reasons, "publication_allowed": False,
                "note": "Los registros locales no autentican personas ni autorizan despliegues."}

    def summary(self):
        with self.connect() as db:
            return {"tasks": db.execute("SELECT count(*) FROM tasks").fetchone()[0],
                    "calls": db.execute("SELECT count(*) FROM calls").fetchone()[0],
                    "uncertain": db.execute("SELECT count(*) FROM calls WHERE status='UNKNOWN'").fetchone()[0]}
