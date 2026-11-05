"""Scoped local permission record; no real identity authentication or ERP access."""
from dataclasses import dataclass
import math
from pathlib import Path
import time

from .core import Blocked, contained, digest, relative_path


@dataclass(frozen=True)
class ComparisonPermit:
    authorized_by: str
    base: str
    root: str
    paths: tuple
    expires_at: float
    catalog_digest: str
    synthetic_only: bool


def permitted(permit, catalog, evidence_root):
    # Check all metadata before resolving any evidence path or reading a file.
    if (not isinstance(permit, ComparisonPermit) or not isinstance(catalog, dict)
            or permit.synthetic_only is not True or catalog.get('synthetic') is not True
            or not isinstance(permit.authorized_by, str) or not permit.authorized_by.strip()
            or not isinstance(permit.base, str) or not permit.base or permit.base != catalog.get('base')
            or type(permit.expires_at) not in (int, float) or not math.isfinite(permit.expires_at)
            or permit.expires_at <= time.time() or permit.catalog_digest != digest(catalog)
            or not isinstance(permit.paths, tuple) or not permit.paths
            or not all(isinstance(p, str) for p in permit.paths)
            or len(set(permit.paths)) != len(permit.paths)
            or not isinstance(permit.root, str) or not permit.root
            or evidence_root is None):
        return False
    try:
        if any(str(p).startswith(('\\\\', '//')) for p in (permit.root, evidence_root)):
            return False
        root = Path(evidence_root)
        for part in (root, *root.parents):
            if part.is_symlink() or (hasattr(part, 'is_junction') and part.is_junction()):
                return False
        if not Path(permit.root).is_absolute() or Path(permit.root) != root.resolve():
            return False
        for name in permit.paths:
            relative_path(name)
        for capability in catalog.get('capabilities', []):
            for evidence in capability.get('evidence', []):
                if evidence['path'] not in permit.paths:
                    return False
                contained(root, evidence['path'])
        return True
    except (OSError, KeyError, TypeError, Blocked):
        return False
