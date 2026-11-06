"""Trusted offline container entry point. Writes source as data; never executes it."""
import json
from pathlib import Path, PurePosixPath
import re


def materialize(proposal, root):
    if not isinstance(proposal, dict) or set(proposal) != {'summary_es', 'edits'}:
        raise ValueError('INVALID_PROPOSAL')
    edits = proposal['edits']
    if not isinstance(edits, list) or not 1 <= len(edits) <= 10:
        raise ValueError('INVALID_EDITS')
    seen, total = set(), 0
    for item in edits:
        if not isinstance(item, dict) or set(item) != {'path', 'content'}:
            raise ValueError('INVALID_EDIT')
        name, content = item['path'], item['content']
        if (not isinstance(name, str) or not re.fullmatch(r'src/[A-Za-z0-9_./-]+', name)
                or any(p in ('', '.', '..') or p.startswith('.') for p in name.split('/'))
                or PurePosixPath(name).suffix not in ('.py', '.js', '.mjs', '.ts', '.tsx', '.css')
                or name.casefold() in seen or not isinstance(content, str)):
            raise ValueError('INVALID_PATH_OR_CONTENT')
        seen.add(name.casefold())
        total += len(content.encode('utf-8'))
        if total > 200000:
            raise ValueError('TOO_LARGE')
    for item in edits:
        target = root / item['path']
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('x', encoding='utf-8', newline='') as stream:
            stream.write(item['content'])


if __name__ == '__main__':
    try:
        raw = Path('/input/proposal.json').read_bytes()
        if len(raw) > 250000:
            raise ValueError('TOO_LARGE')
        materialize(json.loads(raw), Path('/candidate'))
        print('BUILT')
    except Exception:
        raise SystemExit('BUILD_BLOCKED') from None
