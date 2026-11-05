"""Single-process durable inbox and audit log for this reference kernel."""
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import sqlite3
import time
import uuid


@dataclass(frozen=True)
class Brain:
    fingerprint: str
    documents: tuple[tuple[str, str], ...]

    @classmethod
    def load(cls, root):
        root = Path(root).resolve()
        names = ("stack.md", "conventions.md", "decisions/0001-control-plane.md")
        # Keep the original ordering/fingerprint when only the required files exist.
        # Every additional Markdown decision is also part of the versioned context.
        extra = sorted(p.relative_to(root).as_posix() for p in root.rglob('*.md')
                       if p.relative_to(root).as_posix() not in names)
        names += tuple(extra)
        documents = []
        for name in names:
            path = (root / name).resolve()
            if not path.is_relative_to(root):
                raise ValueError("Brain path escapes root")
            text = path.read_text(encoding="utf-8")
            if not text.strip():
                raise ValueError("Required context is empty")
            documents.append((name, text))
        payload = json.dumps(documents, ensure_ascii=False, separators=(",", ":"))
        return cls(hashlib.sha256(payload.encode()).hexdigest(), tuple(documents))


class Store:
    def __init__(self, path):
        self.db = sqlite3.connect(path)
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY, source TEXT NOT NULL, repo TEXT NOT NULL,
                event_id TEXT NOT NULL, payload_hash TEXT NOT NULL,
                state TEXT NOT NULL, created_at REAL NOT NULL,
                UNIQUE(source, repo, event_id));
            CREATE TABLE IF NOT EXISTS audit (
                seq INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT NOT NULL REFERENCES tasks(id),
                at REAL NOT NULL, event TEXT NOT NULL, data TEXT NOT NULL);
        """)

    def accept(self, source, repo, event_id, body):
        if not all((source, repo, event_id)):
            raise ValueError("Missing event identity")
        digest = hashlib.sha256(body).hexdigest()
        task_id = str(uuid.uuid4())
        with self.db:
            inserted = self.db.execute(
                "INSERT OR IGNORE INTO tasks VALUES (?, ?, ?, ?, ?, ?, ?)",
                (task_id, source, repo, event_id, digest, "RECEIVED", time.time())
            ).rowcount
            row = self.db.execute(
                "SELECT id, payload_hash FROM tasks WHERE source=? AND repo=? AND event_id=?",
                (source, repo, event_id)).fetchone()
            if row[1] != digest:
                raise ValueError("Event identity reused with different payload")
            if inserted:
                self._audit(task_id, "RECEIVED", {"payload_hash": digest})
        return row[0], bool(inserted)

    def _audit(self, task_id, event, data):
        self.db.execute("INSERT INTO audit(task_id, at, event, data) VALUES (?, ?, ?, ?)",
                        (task_id, time.time(), event, json.dumps(data, sort_keys=True)))

    def transition(self, task_id, expected, target, data):
        allowed = {
            "RECEIVED": {"REVIEWING"},
            "REVIEWING": {"BLOCKED", "WAITING_APPROVAL", "READY_FAST_TRACK", "READY_APPROVED"},
            "WAITING_APPROVAL": {"READY_APPROVED", "BLOCKED"},
        }
        if target not in allowed.get(expected, set()):
            raise ValueError("Illegal transition")
        with self.db:
            updated = self.db.execute("UPDATE tasks SET state=? WHERE id=? AND state=?",
                                      (target, task_id, expected)).rowcount
            if updated != 1:
                raise ValueError("Stale state or missing task")
            self._audit(task_id, target, data)

    def close(self):
        self.db.close()
