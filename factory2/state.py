"""Estado propio; no importa la cola de la primera fábrica."""
import json
import math
import sqlite3
import time
import unicodedata
from contextlib import contextmanager
from pathlib import Path

from .core import Blocked, canonical, digest, validate_review
from .operations import Coordinator
from .review_import import import_artifacts, verify_stored
from .budget import BudgetLedger
from .manual_review import read_document, metadata as manual_metadata, CLEAR, hex_value


def identity(value):
    if not isinstance(value, str):
        raise Blocked('IDENTITY_REQUIRED')
    normalized = ''.join(unicodedata.normalize('NFKC', value).split()).casefold()
    if not normalized or len(normalized) > 100:
        raise Blocked('IDENTITY_REQUIRED')
    return normalized


class Store:
    def __init__(self, path, *, config_path=None, coordinator=None, reviews_directory=None):
        self.path = Path(path)
        self.config_path = Path(config_path) if config_path else Path(__file__).resolve().parent.parent / 'config.json'
        self.coordinator = coordinator or Coordinator(self.path.parent)
        self.reviews_directory = (Path(reviews_directory) if reviews_directory else
                                  Path(__file__).resolve().parent.parent / 'docs/revisiones')
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
            CREATE TABLE IF NOT EXISTS private_reviews(id TEXT PRIMARY KEY,
                receipt TEXT NOT NULL, report BLOB NOT NULL, manifest BLOB NOT NULL,
                hash_index BLOB NOT NULL);
            CREATE TABLE IF NOT EXISTS manual_reviews(id TEXT PRIMARY KEY, document BLOB NOT NULL);
            CREATE TABLE IF NOT EXISTS acceptances_v2(task TEXT, version TEXT, person TEXT,
                person_id TEXT, role TEXT, source_sha TEXT, factory_digest TEXT,
                review_id TEXT, expires_at REAL, created REAL,
                PRIMARY KEY(task,version,role), UNIQUE(task,version,person),
                UNIQUE(task,version,person_id));
            """)
        self.budget = BudgetLedger(self.path)

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
            db.execute('DELETE FROM acceptances_v2 WHERE task=?', (task,))
        return version

    def config(self):
        try:
            config = json.loads(self.config_path.read_text(encoding='utf-8-sig'))
            if not isinstance(config, dict):
                raise ValueError
            return config
        except (OSError, ValueError):
            raise Blocked('OPERATION_CONFIG_INVALID') from None

    def roster(self):
        config = self.config()
        required = config.get('human_approvals_required')
        people = config.get('human_approvers')
        if (type(required) is not int or required < 2 or not isinstance(people, dict)
                or len(people) != required or not {'business', 'accounting'} <= set(people)
                or 'technical' in people):
            raise Blocked('HUMAN_APPROVERS_PENDING')
        seen_names, seen_ids = set(), set()
        normalized = {}
        for role, person in people.items():
            if not isinstance(person, dict) or set(person) != {'login', 'id'}:
                raise Blocked('HUMAN_APPROVERS_PENDING')
            name = identity(person['login'])
            number = person['id']
            if (not isinstance(number, str) or not number.isdigit() or not int(number)
                    or name in seen_names or number in seen_ids):
                raise Blocked('HUMAN_APPROVERS_INVALID')
            seen_names.add(name)
            seen_ids.add(number)
            normalized[role] = {'login': name, 'id': number}
        return required, normalized

    def import_factory_review(self, directory, receipt):
        metadata, report, manifest, hashes = import_artifacts(
            directory, receipt, self.config().get('private_review_trust'))
        try:
            with self.connect() as db:
                db.execute('INSERT INTO private_reviews VALUES(?,?,?,?,?)',
                           (metadata['review_id'], canonical(receipt), report, manifest, hashes))
        except sqlite3.IntegrityError:
            raise Blocked('REVIEW_ALREADY_IMPORTED') from None
        return metadata

    def factory_review(self, review_id):
        if not isinstance(review_id, str):
            raise Blocked('IMPORTED_REVIEW_ID_REQUIRED')
        with self.connect() as db:
            row = db.execute('SELECT * FROM private_reviews WHERE id=?', (review_id,)).fetchone()
        if row is None:
            raise Blocked('IMPORTED_REVIEW_NOT_FOUND')
        return verify_stored(row, self.config().get('private_review_trust'))

    def worker(self):
        return self.coordinator.worker()

    def import_manual_review(self, path):
        raw = read_document(path, self.reviews_directory)
        review = manual_metadata(raw)
        try:
            with self.connect() as db:
                db.execute('INSERT INTO manual_reviews VALUES(?,?)', (review['review_id'],raw))
        except sqlite3.IntegrityError:
            raise Blocked('MANUAL_REVIEW_ALREADY_IMPORTED') from None
        return review

    def manual_review(self, review_id):
        if not isinstance(review_id,str) or not review_id.startswith('manual:'):
            raise Blocked('MANUAL_REVIEW_ID_REQUIRED')
        with self.connect() as db:
            row = db.execute('SELECT document FROM manual_reviews WHERE id=?',(review_id,)).fetchone()
        if row is None:
            raise Blocked('MANUAL_REVIEW_NOT_FOUND')
        review = manual_metadata(row[0])
        if review['review_id'] != review_id:
            raise Blocked('MANUAL_REVIEW_CHANGED')
        return review

    def reserve_call(self, call_id, task, provider, payload_hash, *, max_calls, output_limit):
        self.coordinator.require_worker()
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
        # Persist an already-started result under the same lock even if the
        # active marker expired meanwhile. Expiry still prevents the NEXT call.
        self.coordinator.require_worker(check_active=False)
        if status not in ("COMPLETED", "UNKNOWN", "REJECTED"):
            raise Blocked("Estado de llamada inválido.")
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            if db.execute('SELECT 1 FROM paid_attempts WHERE id=?', (call_id,)).fetchone():
                self.budget.finish_in(db, call_id, status)
            updated = db.execute("UPDATE calls SET status=? WHERE id=? AND status='IN_FLIGHT'", (status, call_id))
            if updated.rowcount != 1:
                raise Blocked("La llamada no estaba en curso.")

    def recover(self):
        with self.worker():
            with self.connect() as db:
                db.execute('BEGIN IMMEDIATE')
                paid = db.execute("UPDATE paid_attempts SET status='UNKNOWN' WHERE status='IN_FLIGHT'").rowcount
                count = db.execute("UPDATE calls SET status='UNKNOWN' WHERE status='IN_FLIGHT'").rowcount
        return {"uncertain_calls": count, "uncertain_paid_attempts": paid, "retried": 0,
                "action": "Reconciliar manualmente; no reenviar ni liberar presupuesto automáticamente."}

    def reserve_paid_call(self, call_id, task, provider, payload_hash, *, execution_id,
                          source_sha, max_cost, output_limit):
        self.coordinator.require_worker()
        if type(output_limit) is not int or not 1 <= output_limit <= 4096:
            raise Blocked('OUTPUT_LIMIT_INVALID')
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            if not db.execute('SELECT 1 FROM tasks WHERE id=?', (task,)).fetchone():
                raise Blocked('TASK_NOT_FOUND')
            if db.execute('SELECT 1 FROM calls WHERE id=?', (call_id,)).fetchone():
                raise Blocked('CALL_ALREADY_RECORDED')
            self.budget.reserve_in(db, call_id, execution_id, provider, payload_hash,
                                   source_sha, max_cost, self.config())
            db.execute('INSERT INTO calls VALUES(?,?,?,?,?,?,?)',
                       (call_id, task, provider, payload_hash, 'IN_FLIGHT', output_limit, time.time()))

    def accept(self, task, version, person, role, *, source_sha=None,
               factory_digest=None, review_id=None, expires_at=None, manual_review_id=None):
        # A local declaration only. Authentication is explicitly not implemented.
        _, people = self.roster()
        name = identity(person)
        if role not in people or name != people[role]['login']:
            raise Blocked('ACCEPTANT_NOT_CONFIGURED')
        if manual_review_id is not None:
            if review_id is not None:
                raise Blocked('REVIEW_PATH_AMBIGUOUS')
            review = self.manual_review(manual_review_id)
            if review['source_sha'] != source_sha or not hex_value(factory_digest,64):
                raise Blocked('ACCEPTANCE_REVIEW_VERSION_MISMATCH')
            if review['conclusion'] != CLEAR:
                raise Blocked('MANUAL_REVIEW_REQUIRES_CORRECTION')
            review_id = manual_review_id
        else:
            review = self.factory_review(review_id)
            if review['source_sha'] != source_sha or review['factory_digest'] != factory_digest:
                raise Blocked('ACCEPTANCE_REVIEW_VERSION_MISMATCH')
        if type(expires_at) not in (int, float) or not math.isfinite(expires_at) or expires_at <= time.time():
            raise Blocked('ACCEPTANCE_EXPIRY_REQUIRED')
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT version FROM tasks WHERE id=?", (task,)).fetchone()
            if row is None or row[0] != version:
                raise Blocked("Aceptación desactualizada.")
            try:
                db.execute('INSERT INTO acceptances_v2 VALUES(?,?,?,?,?,?,?,?,?,?)',
                           (task, version, name, people[role]['id'], role, source_sha,
                            factory_digest, review_id, expires_at, time.time()))
            except sqlite3.IntegrityError:
                raise Blocked('ACCEPTANCE_ALREADY_RECORDED') from None
        return {'recorded': True, 'identity_authenticated': False, 'publication_allowed': False}

    def gate(self, task, version, artifact_digest, review, tests, *, factory_review=None,
             factory_digest=None, source_sha=None, manual_review_id=None):
        reasons = []
        manual = manual_review_id is not None
        selected_review = manual_review_id if manual else factory_review
        if manual and factory_review is not None:
            reasons.append('REVIEW_PATH_AMBIGUOUS')
        with self.connect() as db:
            row = db.execute("SELECT version,brief FROM tasks WHERE id=?", (task,)).fetchone()
            acceptances = list(db.execute('SELECT * FROM acceptances_v2 WHERE task=? AND version=?', (task, version)))
        if row is None or row[0] != version:
            reasons.append("La versión de requisitos cambió.")
        if row is None or json.loads(row[1]).get("artifact_digest") != artifact_digest:
            reasons.append("El código no corresponde al expediente aceptado.")
        try:
            required, people = self.roster()
            valid = [r for r in acceptances if r['role'] in people
                     and r['person'] == people[r['role']]['login'] and r['person_id'] == people[r['role']]['id']
                     and r['source_sha'] == source_sha and r['factory_digest'] == factory_digest
                    and r['review_id'] == selected_review and r['expires_at'] > time.time()]
            if (len(valid) != required or len({r['person_id'] for r in valid}) != required
                    or len({r['person'] for r in valid}) != required):
                reasons.append('HUMAN_ACCEPTANCES_MISSING_STALE_OR_EXPIRED')
        except Blocked:
            reasons.append('HUMAN_APPROVERS_PENDING_OR_INVALID')
        if not manual:
            reasons.append('HUMAN_AUTHENTICATION_PENDING')
        try:
            validate_review(review, artifact_digest)
            if review["verdict"] != "PASS":
                reasons.append("Claude bloqueó la entrega.")
        except (Blocked, TypeError):
            reasons.append("Revisión ausente, incompleta o de otra versión.")
        if manual:
            try:
                imported = self.manual_review(manual_review_id)
                if imported['source_sha'] != source_sha or not hex_value(factory_digest,64):
                    raise Blocked('MANUAL_REVIEW_SHA_MISMATCH')
                if imported['conclusion'] != CLEAR:
                    raise Blocked('MANUAL_REVIEW_REQUIRES_CORRECTION')
            except (Blocked, TypeError):
                reasons.append('MANUAL_FACTORY_REVIEW_INVALID_OR_REQUIRES_CORRECTION')
        else:
            try:
                imported = self.factory_review(factory_review)
                if imported['factory_digest'] != factory_digest or imported['source_sha'] != source_sha:
                    raise Blocked('FACTORY_REVIEW_VERSION_MISMATCH')
                if imported['provenance_authenticated'] is not True:
                    reasons.append('PRIVATE_REVIEW_AUTHENTICATION_PENDING')
            except (Blocked, TypeError):
                reasons.append('PRIVATE_FACTORY_REVIEW_INVALID')
        if not tests or any(t.get("status") != "PASS" or t.get("test_count", 0) < 1 or t.get("artifact_digest") != artifact_digest for t in tests):
            reasons.append("Pruebas ausentes, fallidas o de otra versión.")
        return {"status": "BLOCKED" if reasons else "READY_FOR_MANUAL_REVIEW",
                "reasons": reasons, "publication_allowed": False,
                "provenance_authenticated": False, "human_acceptances_authenticated": False,
                "review_mode": "MANUAL_CHAT" if manual else "PRIVATE_V2",
                "note": "Los registros locales no autentican personas ni autorizan despliegues."}

    def summary(self):
        with self.connect() as db:
            return {"tasks": db.execute("SELECT count(*) FROM tasks").fetchone()[0],
                    "calls": db.execute("SELECT count(*) FROM calls").fetchone()[0],
                    "uncertain": db.execute("SELECT count(*) FROM calls WHERE status='UNKNOWN'").fetchone()[0]}
