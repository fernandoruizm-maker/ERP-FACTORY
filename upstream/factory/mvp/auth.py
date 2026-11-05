"""GitHub App authentication. Private keys stay local; installation tokens stay in memory."""
import base64
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import threading
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, build_opener, HTTPRedirectHandler
from .common import Blocked, check_rate_limit


PERMISSIONS = {'administration': 'read', 'contents': 'write', 'issues': 'read',
               'pull_requests': 'write', 'statuses': 'write', 'metadata': 'read'}


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class InstallationToken:
    def __init__(self, repository, app_id, installation_id, private_key_file, *,
                 client_id=None, clock=time.time):
        if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repository):
            raise Blocked('Invalid App repository')
        if not str(app_id).isdigit() or int(app_id) <= 0:
            raise Blocked('Invalid App ID')
        if not str(installation_id).isdigit() or int(installation_id) <= 0:
            raise Blocked('Invalid installation ID')
        self.repository = repository
        self.app_id, self.installation_id = int(app_id), int(installation_id)
        self.issuer = str(client_id or app_id)
        self.private_key_file = Path(private_key_file)
        self.clock, self._lock = clock, threading.Lock()
        self._token, self._expires = None, 0
        self.opener = build_opener(NoRedirect())

    def jwt(self):
        try:
            from cryptography.hazmat.primitives import hashes, serialization
            from cryptography.hazmat.primitives.asymmetric import padding, rsa
        except ImportError:
            raise Blocked('Install requirements-app.txt for GitHub App authentication') from None
        try:
            if self.private_key_file.stat().st_size > 20_000:
                raise ValueError('Key too large')
            key = serialization.load_pem_private_key(self.private_key_file.read_bytes(), password=None)
            if not isinstance(key, rsa.RSAPrivateKey) or key.key_size < 2048:
                raise ValueError('Expected RSA key of at least 2048 bits')
        except (OSError, ValueError, TypeError):
            raise Blocked('Cannot load the configured GitHub App RSA private key') from None
        encode = lambda b: base64.urlsafe_b64encode(b).rstrip(b'=')
        now = int(self.clock())
        header = encode(json.dumps({'alg': 'RS256', 'typ': 'JWT'}, separators=(',', ':')).encode())
        payload = encode(json.dumps({'iss': self.issuer, 'iat': now - 60, 'exp': now + 540},
                                    separators=(',', ':')).encode())
        message = header + b'.' + payload
        signature = key.sign(message, padding.PKCS1v15(), hashes.SHA256())
        return (message + b'.' + encode(signature)).decode('ascii')

    def app_request(self, method, path, data=None):
        allowed = {('GET', '/app'), ('GET', '/app/hook/config'),
                   ('GET', '/repos/' + self.repository + '/installation'),
                   ('POST', f'/app/installations/{self.installation_id}/access_tokens')}
        if (method, path) not in allowed:
            raise Blocked('App authentication endpoint not allowed')
        request = Request('https://api.github.com' + path, method=method,
            data=None if data is None else json.dumps(data).encode(), headers={
                'Authorization': 'Bearer ' + self.jwt(), 'Accept': 'application/vnd.github+json',
                'Content-Type': 'application/json', 'X-GitHub-Api-Version': '2022-11-28',
                'User-Agent': 'ai-factory-mvp'})
        try:
            with self.opener.open(request, timeout=30) as response:
                body = response.read(1_000_001)
                if len(body) > 1_000_000:
                    raise Blocked('GitHub App response exceeds limit')
                return json.loads(body)
        except HTTPError as exc:
            exc.close()
            check_rate_limit(exc.code, {k.lower(): v for k, v in exc.headers.items()}, self.clock())
            raise Blocked(f'GitHub App authentication returned HTTP {exc.code}') from None
        except (URLError, ValueError):
            raise Blocked('GitHub App authentication transport failed') from None

    def verify_installation(self):
        app = self.app_request('GET', '/app')
        info = self.app_request('GET', '/repos/' + self.repository + '/installation')
        if (app.get('id') != self.app_id or info.get('app_id') != self.app_id
                or info.get('id') != self.installation_id or info.get('suspended_at')
                or info.get('repository_selection') != 'selected'
                or info.get('account', {}).get('login', '').casefold() != self.repository.split('/')[0].casefold()):
            raise Blocked('App installation does not match the selected repository/account')
        grants = info.get('permissions', {})
        for name, permission in PERMISSIONS.items():
            if grants.get(name) not in ({'read', 'write'} if permission == 'read' else {'write'}):
                raise Blocked('GitHub App is missing permission: ' + name)
        return {'app_id': self.app_id, 'installation_id': self.installation_id,
                'slug': app.get('slug'), 'repository': self.repository,
                'repository_selection': info['repository_selection'], 'permissions': grants}

    def get_token(self):
        with self._lock:
            if self._token and self.clock() < self._expires - 300:
                return self._token
            result = self.app_request('POST', f'/app/installations/{self.installation_id}/access_tokens',
                {'repositories': [self.repository.split('/')[1]], 'permissions': PERMISSIONS})
            try:
                expiry = datetime.fromisoformat(result['expires_at'].replace('Z', '+00:00'))
                if expiry.tzinfo is None:
                    raise ValueError('Timezone required')
                expires = expiry.astimezone(timezone.utc).timestamp()
                token = result['token']
                if (not isinstance(token, str) or not token or len(token) > 20_000
                        or expires <= self.clock() + 300 or expires > self.clock() + 3700):
                    raise ValueError('Invalid installation token')
            except (KeyError, ValueError, TypeError, AttributeError):
                raise Blocked('Invalid or expired GitHub installation token response') from None
            self._token, self._expires = token, expires
            return token
