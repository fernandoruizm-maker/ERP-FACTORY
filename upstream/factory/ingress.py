"""Pure ingress primitives, not a public HTTP server."""
import hashlib
import hmac
import json


def verify_github(body: bytes, signature: str, secret: bytes):
    if not secret or not signature or not signature.isascii():
        raise ValueError("Missing or invalid signature/secret")
    expected = "sha256=" + hmac.new(secret, body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise ValueError("Invalid signature")


def receive_github(store, body, headers, secret, allowed_repos):
    """HTTP layer must enforce TLS, rate limits and secret selection."""
    if len(body) > 1_000_000:
        raise ValueError("Payload too large")
    headers = {k.lower(): v for k, v in headers.items()}
    verify_github(body, headers.get("x-hub-signature-256", ""), secret)
    if headers.get("x-github-event") != "issues":
        raise ValueError("Unsupported event")
    payload = json.loads(body)
    if payload.get("action") not in {"opened", "reopened"}:
        raise ValueError("Unsupported action")
    repo = payload["repository"]["full_name"]
    if repo not in allowed_repos:
        raise ValueError("Repository not authorized")
    event_id = headers.get("x-github-delivery", "")
    # Receipt only; production normalizer must separately save a scrubbed task.
    return store.accept("github", repo, event_id, body)
