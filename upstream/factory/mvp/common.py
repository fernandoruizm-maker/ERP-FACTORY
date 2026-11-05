from pathlib import Path, PurePosixPath
import hashlib
import json
import re


class Blocked(RuntimeError):
    pass


class RateLimited(Blocked):
    def __init__(self, retry_at):
        self.retry_at = float(retry_at)
        super().__init__('GitHub API rate limit; waiting for the permitted retry time')


def check_rate_limit(code, headers, now):
    if code == 429 or (code == 403 and
            ('retry-after' in headers or headers.get('x-ratelimit-remaining') == '0')):
        retry = now + 300
        if str(headers.get('retry-after', '')).isdigit():
            retry = max(retry, now + int(headers['retry-after']))
        if str(headers.get('x-ratelimit-reset', '')).isdigit():
            retry = max(retry, int(headers['x-ratelimit-reset']) + 1)
        raise RateLimited(retry)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     separators=(",", ":")).encode()).hexdigest()


def safe_path(value):
    if not isinstance(value, str) or not value or len(value) > 240:
        raise Blocked("Invalid repository path")
    if (value.startswith("/") or "\\" in value or ":" in value
            or any(p in {"", ".", ".."} for p in value.split("/"))
            or any(ord(c) < 32 for c in value)):
        raise Blocked("Unsafe repository path")
    # Portable path semantics, including Windows device names and trailing dots.
    for part in value.split("/"):
        if part.endswith((" ", ".")) or re.fullmatch(r"(?i)(con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\..*)?", part):
            raise Blocked("Non-portable path")
    return value


def checked_edits(edits, original, *, phase, allowed_prefixes):
    if not isinstance(edits, list) or not 1 <= len(edits) <= 12:
        raise Blocked("Expected 1..12 edits")
    out = {}
    for edit in edits:
        path = safe_path(edit["path"])
        text = edit["content"]
        if path.casefold() in {p.casefold() for p in out}:
            raise Blocked("Duplicate edit path")
        if any(p.casefold() == path.casefold() and p != path for p in original):
            raise Blocked("Edit path collides with existing file on case-insensitive filesystems")
        if not isinstance(text, str) or len(text.encode()) > 100_000 or "\x00" in text:
            raise Blocked("Invalid content")
        if phase == "test":
            if (not re.fullmatch(r"tests/test_factory_[a-z0-9_]+\.py", path)
                    or path in original):
                raise Blocked("RED phase can only add a new test file")
        elif (not any(path.startswith(p) for p in allowed_prefixes)
              or path.startswith(("tests/", "brain/", ".", "factory/"))
              or any(p.startswith(".") for p in path.split("/"))
              or PurePosixPath(path).suffix not in {".py", ".txt", ".md"}):
            raise Blocked("Builder edit outside permitted product paths")
        out[path] = text
    if sum(len(v.encode()) for v in out.values()) > 200_000:
        raise Blocked("Edit budget exceeded")
    return out


def validate_schema(value, schema):
    kind = schema.get("type")
    types = {"object": dict, "array": list, "string": str, "boolean": bool, "integer": int}
    if kind in types and type(value) is not types[kind]:
        raise Blocked("Agent response has invalid type")
    if "enum" in schema and value not in schema["enum"]:
        raise Blocked("Agent response has invalid enum")
    if kind == "object":
        props = schema["properties"]
        if set(value) != set(schema["required"]) or set(value) - set(props):
            raise Blocked("Agent response has invalid fields")
        for key, child in value.items():
            validate_schema(child, props[key])
    if kind == "array":
        if len(value) > 100:
            raise Blocked("Agent array exceeds limit")
        for child in value:
            validate_schema(child, schema["items"])


def object_schema(properties):
    return {"type": "object", "properties": properties,
            "required": list(properties), "additionalProperties": False}


STRING = {"type": "string"}
STRINGS = {"type": "array", "items": STRING}
SPEC_SCHEMA = object_schema({"title": STRING, "problem": STRING,
                            "acceptance": STRINGS, "design": STRING,
                            "test_plan": STRING, "open_questions": STRINGS})
EDITS_SCHEMA = object_schema({"explanation": STRING, "edits": {
    "type": "array", "items": object_schema({"path": STRING, "content": STRING})}})
REVIEW_SCHEMA = object_schema({"verdict": {"type": "string", "enum": ["PASS", "BLOCK"]},
                              "findings": {**STRINGS, "description": "Blocking defects only. PASS requires an empty array. Put positive observations and non-applicability in rationale."},
                              "rationale": STRING})


def load_config(path):
    path = Path(path).resolve()
    config = json.loads(path.read_text(encoding="utf-8"))
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", config["repository"]):
        raise Blocked("Configure an explicit owner/repository")
    if not config.get("allowed_requesters") or not config.get("human_reviewers"):
        raise Blocked("Requester and reviewer allowlists must be explicit")
    for p in config["product_prefixes"]:
        safe_path(p.rstrip("/"))
        if not p.endswith("/") or p.startswith(("tests/", "brain/", ".", "factory/")):
            raise Blocked("Unsafe product prefix")
    for key in ("state_dir", "brain_dir"):
        config[key] = str((path.parent / config[key]).resolve())
    if config.get('github_app'):
        app = config['github_app']
        app['private_key_file'] = str((path.parent / app['private_key_file']).resolve())
    if config.get('webhook_secret_file'):
        config['webhook_secret_file'] = str((path.parent / config['webhook_secret_file']).resolve())
    if config.get('pilot_status_file'):
        config['pilot_status_file'] = str((path.parent / config['pilot_status_file']).resolve())
    return config
