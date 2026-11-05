"""Durable inbox with atomic claims. One worker holds an OS-level process lock."""
import json
from pathlib import Path
import sqlite3
import time
from contextlib import contextmanager
from .common import Blocked, digest


class Queue:
    def __init__(self, path):
        self.path = str(path)
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with self.connection() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS jobs(
                    id TEXT PRIMARY KEY, payload TEXT NOT NULL, state TEXT NOT NULL,
                    checkpoint TEXT NOT NULL DEFAULT '{}', error TEXT, updated REAL NOT NULL);
                CREATE TABLE IF NOT EXISTS deliveries(
                    id TEXT PRIMARY KEY, digest TEXT NOT NULL, job_id TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS events(
                    seq INTEGER PRIMARY KEY, job_id TEXT NOT NULL, state TEXT NOT NULL, at REAL NOT NULL);
                CREATE TABLE IF NOT EXISTS metadata(key TEXT PRIMARY KEY, value TEXT NOT NULL);
            ''')

    def meta_get(self, key, default=None):
        with self.connection() as db:
            row = db.execute('SELECT value FROM metadata WHERE key=?', (key,)).fetchone()
            return json.loads(row['value']) if row else default

    def meta_set(self, key, value):
        with self.connection() as db:
            db.execute('INSERT INTO metadata VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value',
                       (key, json.dumps(value)))

    def delivery_job(self, delivery):
        with self.connection() as db:
            row = db.execute('SELECT job_id FROM deliveries WHERE id=?', (delivery,)).fetchone()
            return row['job_id'] if row else None

    @contextmanager
    def connection(self):
        db = sqlite3.connect(self.path, timeout=15)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA journal_mode=WAL")
        try:
            with db:
                yield db
        finally:
            db.close()

    def enqueue(self, delivery, payload):
        ident = digest(payload)
        # Same issue revision, requester and configuration request -> same durable job.
        with self.connection() as db:
            old = db.execute("SELECT * FROM deliveries WHERE id=?", (delivery,)).fetchone()
            if old and old["digest"] != ident:
                raise Blocked("Delivery ID collision")
            db.execute("INSERT OR IGNORE INTO jobs(id,payload,state,updated) VALUES (?,?,?,?)",
                       (ident, json.dumps(payload), "QUEUED", time.time()))
            db.execute("INSERT OR IGNORE INTO deliveries VALUES (?,?,?)", (delivery, ident, ident))
        return ident

    def claim(self):
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT * FROM jobs WHERE state='QUEUED' ORDER BY updated LIMIT 1").fetchone()
            if not row:
                return None
            db.execute("UPDATE jobs SET state='RUNNING',updated=? WHERE id=?", (time.time(), row["id"]))
            return dict(row)

    def set(self, job_id, state, checkpoint=None, error=None):
        with self.connection() as db:
            if checkpoint is None:
                db.execute("UPDATE jobs SET state=?,error=?,updated=? WHERE id=?",
                           (state, error, time.time(), job_id))
            else:
                db.execute("UPDATE jobs SET state=?,checkpoint=?,error=?,updated=? WHERE id=?",
                           (state, json.dumps(checkpoint), error, time.time(), job_id))
            db.execute("INSERT INTO events(job_id,state,at) VALUES (?,?,?)", (job_id, state, time.time()))

    def recover(self):
        # Only invoke after acquiring worker_lock: no live worker can still own these jobs.
        with self.connection() as db:
            db.execute("UPDATE jobs SET state='QUEUED' WHERE state IN ('RUNNING','PUBLISHING')")

    def get(self, job_id):
        with self.connection() as db:
            row = db.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
            return dict(row) if row else None

    def list(self):
        with self.connection() as db:
            return [dict(r) for r in db.execute("SELECT id,state,error,updated FROM jobs ORDER BY updated DESC")]


@contextmanager
def worker_lock(path):
    handle = open(path, "a+b")
    if handle.tell() == 0:
        handle.write(b"0")
        handle.flush()
    handle.seek(0)
    try:
        if __import__('os').name == 'nt':
            import msvcrt
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        handle.close()
        raise Blocked("Another worker is active") from None
    try:
        yield
    finally:
        handle.close()
