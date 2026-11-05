"""Common LOCAL reservation/import primitives, not a selected GitHub mechanism.

No refund from unverified remote metadata. A grant is not a credential/signature
and cannot prevent reuse on a disconnected runner. Production remains blocked.
"""
from contextlib import contextmanager
import json
from pathlib import Path
import re
import sqlite3

from .contract import Blocked, canonical, sha256, source_sha
from .execution_budget import money


class LocalAllowances:
    def __init__(self, path):
        self.path = str(path)
        with self.connect() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS grants(id TEXT PRIMARY KEY, source_sha TEXT NOT NULL,
                    reserved_units INTEGER NOT NULL, charged_units INTEGER NOT NULL);
                CREATE TABLE IF NOT EXISTS receipts(grant_id TEXT, receipt_sha TEXT,
                    PRIMARY KEY(grant_id, receipt_sha));
                CREATE TABLE IF NOT EXISTS grant_runs(grant_id TEXT, run_id TEXT,
                    charged_units INTEGER NOT NULL, PRIMARY KEY(grant_id,run_id));
            ''')

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=5)
        try:
            with db:
                yield db
        finally:
            db.close()

    def reserve(self, grant_id, commit, allowance_usd, total_cap_usd):
        source_sha(commit)
        if not isinstance(grant_id, str) or not re.fullmatch('[A-Za-z0-9_-]{1,100}', grant_id):
            raise Blocked('GRANT_ID_INVALID')
        cost, cap = money(allowance_usd), money(total_cap_usd)
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            if (db.execute('SELECT 1 FROM grants WHERE charged_units>reserved_units').fetchone()
                    or db.execute('SELECT grant_id FROM grant_runs GROUP BY grant_id HAVING count(*)>1').fetchone()):
                raise Blocked('ALLOWANCE_RECONCILIATION_REQUIRED')
            used = db.execute('SELECT coalesce(sum(charged_units),0) FROM grants').fetchone()[0]
            if used + cost > cap:
                raise Blocked('ACCUMULATED_CAP_REACHED')
            try:
                db.execute('INSERT INTO grants VALUES(?,?,?,?)', (grant_id, commit, cost, cost))
            except sqlite3.IntegrityError:
                raise Blocked('GRANT_ALREADY_RESERVED') from None
        return {'grant_id': grant_id, 'source_sha': commit, 'allowance_usd': allowance_usd}

    def import_checkpoint(self, folder, expected_index_sha256):
        """Record hash-consistent evidence only, NOT authenticated GitHub billing."""
        folder = Path(folder)
        index = (folder / 'SHA256.json').read_bytes()
        if sha256(index) != expected_index_sha256:
            raise Blocked('RECEIPT_HASH_MISMATCH')
        hashes = json.loads(index)
        allowed = {'budget.json', 'report.json', 'manifest.json', 'diagnostic.json', 'INFORME.txt',
                   'response.txt', 'response.unvalidated.txt'}
        if not isinstance(hashes, dict) or not {'budget.json', 'report.json'} <= set(hashes) <= allowed:
            raise Blocked('RECEIPT_STRUCTURE')
        raw_budget = None
        for name, expected in hashes.items():
            path = folder / name
            if path.is_symlink() or not path.is_file() or path.stat().st_size > 8_000_000:
                raise Blocked('RECEIPT_STRUCTURE')
            raw = path.read_bytes()
            if sha256(raw) != expected:
                raise Blocked('RECEIPT_HASH_MISMATCH')
            if name == 'budget.json':
                raw_budget = raw
        budget = json.loads(raw_budget)
        if budget.get('schema') != 'private-budget-v1' or budget.get('billing_verified') is not False:
            raise Blocked('RECEIPT_STRUCTURE')
        attempts = budget.get('attempts')
        if (not isinstance(attempts, list) or len(attempts) > 11
                or any(not isinstance(a, dict) or type(a.get('charged_units')) is not int
                       or a['charged_units'] < 0 for a in attempts)):
            raise Blocked('RECEIPT_STRUCTURE')
        charged = sum(a['charged_units'] for a in attempts)
        grant = budget['limits']['grant_id']
        provenance = budget.get('provenance', {})
        run_id = provenance.get('run_id')
        if (not isinstance(run_id, str) or not run_id.isdigit()
                or provenance.get('repository') != 'fernandoruizm-maker/ERP-FACTORY-revision'
                or provenance.get('source_sha') != budget['source_sha']
                or provenance.get('run_attempt') != 1):
            raise Blocked('RECEIPT_PROVENANCE_INVALID')
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT source_sha,charged_units FROM grants WHERE id=?', (grant,)).fetchone()
            if row is None or row[0] != budget['source_sha']:
                raise Blocked('GRANT_VERSION_MISMATCH')
            duplicate = db.execute('SELECT 1 FROM receipts WHERE grant_id=? AND receipt_sha=?',
                                   (grant, expected_index_sha256)).fetchone() is not None
            if not duplicate:
                db.execute('INSERT INTO receipts VALUES(?,?)', (grant, expected_index_sha256))
                db.execute('INSERT INTO grant_runs VALUES(?,?,?) ON CONFLICT(grant_id,run_id) DO UPDATE SET '
                           'charged_units=max(charged_units,excluded.charged_units)', (grant,run_id,charged))
                total = db.execute('SELECT coalesce(sum(charged_units),0) FROM grant_runs WHERE grant_id=?',
                                   (grant,)).fetchone()[0]
                db.execute('UPDATE grants SET charged_units=? WHERE id=?', (max(row[1], total), grant))
            reused = db.execute('SELECT count(*) FROM grant_runs WHERE grant_id=?',(grant,)).fetchone()[0] > 1
        return {'recorded': not duplicate, 'duplicate': duplicate, 'authenticated': False,
                'billing_verified': False, 'refunded_units': 0, 'publication_allowed': False,
                'grant_reused': reused}

    def summary(self):
        with self.connect() as db:
            count, charged = db.execute('SELECT count(*),coalesce(sum(charged_units),0) FROM grants').fetchone()
        return {'grants': count, 'charged_units': charged, 'currency': 'USD', 'billing_verified': False}
