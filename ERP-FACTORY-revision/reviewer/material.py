"""Read a public source archive in memory. No extraction, imports, or execution."""
import io
import gzip
import json
from pathlib import Path, PurePosixPath
import re
import tarfile
import urllib.request

from .contract import Blocked, canonical, digest, safe_material, sha256, source_sha

PUBLIC_REPOSITORY = 'fernandoruizm-maker/ERP-FACTORY'
MAX_ARCHIVE = 8_000_000
MAX_SOURCE = 600_000
MAX_MEMBERS = 4096
MAX_TAR_BYTES = 4_000_000


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise Blocked('ARCHIVE_REDIRECT_REFUSED')


def download_archive(commit):
    """Future runtime only; no token, credential helper, netrc or environment proxy."""
    source_sha(commit)
    url = 'https://codeload.github.com/' + PUBLIC_REPOSITORY + '/tar.gz/' + commit
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    request = urllib.request.Request(url, headers={'User-Agent': 'ERP-FACTORY-private-review'})
    with opener.open(request, timeout=30) as response:
        raw = response.read(MAX_ARCHIVE + 1)
    if len(raw) > MAX_ARCHIVE:
        raise Blocked('ARCHIVE_TOO_LARGE')
    return raw


def archive_material(raw, commit):
    source_sha(commit)
    if not isinstance(raw, bytes) or len(raw) > MAX_ARCHIVE:
        raise Blocked('ARCHIVE_TOO_LARGE')
    prefix = 'ERP-FACTORY-' + commit
    files = {}
    used = 0
    try:
        # Bound decompression before tarfile parses extended headers or names.
        with gzip.GzipFile(fileobj=io.BytesIO(raw), mode='rb') as compressed:
            unpacked = compressed.read(MAX_TAR_BYTES + 1)
        if len(unpacked) > MAX_TAR_BYTES:
            raise Blocked('DECOMPRESSED_ARCHIVE_TOO_LARGE')
        with tarfile.open(fileobj=io.BytesIO(unpacked), mode='r:') as archive:
            for count, member in enumerate(archive, 1):
                if count > MAX_MEMBERS:
                    raise Blocked('TOO_MANY_MEMBERS')
                pieces = member.name.rstrip('/').split('/')
                if (pieces[0] != prefix or any(p in ('', '.', '..') for p in pieces)
                        or not re.fullmatch(r'[A-Za-z0-9_./-]+', member.name)):
                    raise Blocked('ARCHIVE_PATH_INVALID')
                if member.isdir():
                    continue
                if (not member.isfile() or len(pieces) < 2
                        or set(member.pax_headers) - {'comment', 'mtime', 'atime', 'ctime'}):
                    raise Blocked('ARCHIVE_MEMBER_UNSAFE')
                if 'comment' in member.pax_headers and member.pax_headers['comment'] != commit:
                    raise Blocked('ARCHIVE_COMMIT_COMMENT_MISMATCH')
                name = '/'.join(pieces[1:])
                if (name in files or any(p in ('.git', '.ssh', '.aws') for p in pieces)
                        or any(p.startswith('.env') for p in pieces)
                        or PurePosixPath(name).suffix.lower() in ('.pem', '.key', '.p12', '.pfx')):
                    raise Blocked('ARCHIVE_PATH_REFUSED')
                used += member.size
                if member.size < 0 or used > MAX_SOURCE:
                    raise Blocked('SOURCE_TOO_LARGE')
                body = archive.extractfile(member).read(member.size + 1)
                if len(body) != member.size:
                    raise Blocked('ARCHIVE_MEMBER_SIZE')
                text = body.decode('utf-8-sig')
                safe_material(text)
                files[name] = {'sha256': sha256(body), 'text': text}
    except (tarfile.TarError, UnicodeError, EOFError, gzip.BadGzipFile):
        raise Blocked('ARCHIVE_FORMAT_INVALID') from None
    if not files:
        raise Blocked('EMPTY_SOURCE')
    files = dict(sorted(files.items()))
    return {'repository': PUBLIC_REPOSITORY, 'source_sha': commit,
            'archive_sha256': sha256(raw), 'files': files,
            'factory_digest': digest({name: data['sha256'] for name, data in files.items()})}


def manifest_for(material):
    return {'repository': material['repository'], 'source_sha': material['source_sha'],
            'factory_digest': material['factory_digest'], 'archive_sha256': material['archive_sha256'],
            'files': {name: item['sha256'] for name, item in material['files'].items()},
            'file_lines': {name: max(1, len(item['text'].splitlines()))
                           for name, item in material['files'].items()}}


def write_material(destination, raw, commit):
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=False)
    material = archive_material(raw, commit)
    body = canonical(material).encode('utf-8')
    (destination / 'material.json').write_bytes(body)
    return material, sha256(body)


def verified_material(destination, expected_hash, expected_commit):
    source_sha(expected_commit)
    path = Path(destination) / 'material.json'
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 4 * MAX_SOURCE:
        raise Blocked('MATERIAL_FILE_INVALID')
    raw = path.read_bytes()
    if not re.fullmatch('[0-9a-f]{64}', expected_hash) or sha256(raw) != expected_hash:
        raise Blocked('MATERIAL_HASH_MISMATCH')
    material = json.loads(raw)
    if material['repository'] != PUBLIC_REPOSITORY or material['source_sha'] != expected_commit:
        raise Blocked('SOURCE_VERSION_MISMATCH')
    return material
