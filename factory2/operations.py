"""One OS worker lock; real cross-factory coordination remains unconfigured.

No marker is created/changed by this module. Simulation never grants permission
for a real transport. The original factory does not yet participate in this lock.
"""
from contextlib import contextmanager
import json
import math
import os
from pathlib import Path
import threading
import time

from .core import Blocked


@contextmanager
def worker_lock(path):
    path = Path(path)
    if path.is_symlink() or (hasattr(path, 'is_junction') and path.is_junction()):
        raise Blocked('WORKER_LOCK_UNSAFE')
    handle = path.open('a+b')
    try:
        if handle.tell() == 0:
            handle.write(b'0')
            handle.flush()
        handle.seek(0)
        try:
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            raise Blocked('WORKER_ALREADY_ACTIVE') from None
        yield
    finally:
        handle.close()


class Coordinator:
    """Explicit fixture coordinator, not evidence of the original's live state."""
    def __init__(self, directory, *, simulation=False):
        self.directory = Path(directory) if directory is not None else None
        self.simulation = simulation
        self._owner = threading.local()

    def check_active(self):
        if not self.simulation:
            # No offline JSON can establish that Ubuntu/Windows is stopped.
            raise Blocked('ORIGINAL_COORDINATION_NOT_VERIFIED')
        if self.directory is None or not self.directory.is_dir():
            raise Blocked('ACTIVE_FACTORY_NOT_CONFIGURED')
        for path in (self.directory, *self.directory.parents):
            if path.is_symlink() or (hasattr(path, 'is_junction') and path.is_junction()):
                raise Blocked('COORDINATION_PATH_UNSAFE')
        path = self.directory / 'active-factory.json'
        try:
            if path.is_symlink() or path.stat().st_size > 4096:
                raise Blocked('ACTIVE_FACTORY_INVALID')
            marker = json.loads(path.read_text(encoding='utf-8'))
            if (set(marker) != {'mode', 'active_factory', 'original_stopped', 'expires_at'}
                    or marker['mode'] != 'SIMULATED_ONLY'
                    or marker['active_factory'] != 'factory2'
                    or marker['original_stopped'] is not True
                    or type(marker['expires_at']) not in (int, float)
                    or not math.isfinite(marker['expires_at']) or marker['expires_at'] <= time.time()):
                raise Blocked('ACTIVE_FACTORY_INVALID')
        except (OSError, ValueError, TypeError, KeyError):
            raise Blocked('ACTIVE_FACTORY_INVALID') from None

    @contextmanager
    def worker(self):
        self.check_active()
        if getattr(self._owner, 'held', False):
            raise Blocked('WORKER_ALREADY_ACTIVE')
        with worker_lock(self.directory / 'worker.lock'):
            self.check_active()
            self._owner.held = os.getpid()
            try:
                yield
            finally:
                self._owner.held = False

    def require_worker(self, *, check_active=True):
        if getattr(self._owner, 'held', None) != os.getpid():
            raise Blocked('WORKER_LOCK_REQUIRED')
        if check_active:
            self.check_active()
