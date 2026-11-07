"""Read-only, local trial arm. Never creates an authorization or enables config."""
import math
from pathlib import Path
import time

from .core import Blocked, digest
from .encargos import _json, _plain_path, attempt_ids

FLAGS = ('enabled', 'external_calls_enabled', 'erp_access_enabled', 'publication_enabled')


def validate_arm(path, config, encargo, attempt, *, now=None):
    if any(config.get(flag) is not False for flag in FLAGS):
        raise Blocked('PILOT_CONFIG_MUST_REMAIN_DISARMED')
    attempt_ids(encargo, attempt)
    now = time.time() if now is None else now
    path = Path(path).absolute()
    try:
        _plain_path(path)
        if not path.exists():
            raise Blocked('PILOT_SWITCH_OFF')
        if not path.is_file() or path.stat().st_size > 4096:
            raise ValueError
        arm = _json(path)
        if (not isinstance(arm, dict) or set(arm) !=
                {'encargo', 'attempt', 'issued_at', 'expires_at', 'config_digest'}
                or arm['encargo'] != encargo or type(arm['attempt']) is not int
                or arm['attempt'] != attempt or arm['config_digest'] != digest(config)
                or any(type(arm[k]) not in (int, float) or not math.isfinite(arm[k])
                       for k in ('issued_at', 'expires_at'))
                or not arm['issued_at'] <= now < arm['expires_at']
                or not 0 < arm['expires_at'] - arm['issued_at'] <= 86400):
            raise ValueError
        return arm
    except Blocked as exc:
        if str(exc) == 'PILOT_SWITCH_OFF':
            raise
        raise Blocked('PILOT_ARM_INVALID') from None
    except (ValueError, OSError, UnicodeError):
        raise Blocked('PILOT_ARM_INVALID') from None
