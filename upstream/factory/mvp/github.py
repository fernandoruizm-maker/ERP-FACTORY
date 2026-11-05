"""GitHub.com REST adapter; no credentials stored in URLs, files or prompts."""
import base64
import json
import os
import time
from urllib.error import HTTPError
from urllib.parse import quote, urlencode
from urllib.request import Request, build_opener
from .auth import InstallationToken, NoRedirect
from .governance import no_bypass_verified
from .common import Blocked, check_rate_limit, safe_path


class GitHub:
    def __init__(self, repository, token=None, *, app=None, governance_mode='classic',
                 ruleset_attestations=None):
        self.repository = repository
        self.auth = InstallationToken(repository, **app) if app else None
        self.app_id = self.auth.app_id if self.auth else None
        self.governance_mode = governance_mode
        self.ruleset_attestations = ruleset_attestations or {}
        if governance_mode not in {'classic', 'rulesets'}:
            raise Blocked('Unknown governance mode')
        self.token = None if self.auth else (token or os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN"))
        if not self.token and not self.auth:
            raise Blocked("Set GITHUB_TOKEN for the autonomous service; chat connector auth is separate")
        self.prefix = "/repos/" + repository
        self.opener = build_opener(NoRedirect())

    @classmethod
    def from_config(cls, config):
        return cls(config['repository'], app=config.get('github_app'),
                   governance_mode=config.get('governance_mode', 'classic'),
                   ruleset_attestations=config.get('ruleset_attestations'))

    def request(self, method, path, data=None):
        return self._response(method, path, data)[0]

    def _response(self, method, path, data=None, etag=None):
        if not path.startswith(self.prefix + "/"):
            raise Blocked("Cross-repository request denied")
        request = Request("https://api.github.com" + path, method=method,
            data=None if data is None else json.dumps(data).encode(), headers={
                "Authorization": "Bearer " + (self.auth.get_token() if self.auth else self.token),
                "Accept": "application/vnd.github+json", "Content-Type": "application/json",
                "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "ai-factory-mvp"})
        if etag:
            request.add_header('If-None-Match', etag)
        try:
            with self.opener.open(request, timeout=30) as response:
                headers = {k.lower(): v for k, v in response.headers.items()}
                if str(headers.get('x-poll-interval', '')).isdigit():
                    self.poll_interval = max(getattr(self, 'poll_interval', 0), int(headers['x-poll-interval']))
                return json.load(response), headers
        except HTTPError as exc:
            exc.close()
            headers = {k.lower(): v for k, v in exc.headers.items()}
            if str(headers.get('x-poll-interval', '')).isdigit():
                self.poll_interval = max(getattr(self, 'poll_interval', 0), int(headers['x-poll-interval']))
            if exc.code == 304 and etag:
                return None, {'not_modified': True}
            check_rate_limit(exc.code, headers, time.time())
            # Never echo response bodies that might contain tokens or private content.
            raise Blocked(f"GitHub {method} returned HTTP {exc.code}") from None

    def conditional_get(self, path, cache):
        key = f'http:{self.repository}:{self.app_id}:{path}'
        previous = cache.meta_get(key, {})
        data, headers = self._response('GET', self.prefix + path, etag=previous.get('etag'))
        if headers.get('not_modified'):
            if 'data' not in previous:
                raise Blocked('304 response without a persisted cache entry')
            return previous['data']
        cache.meta_set(key, {'etag': headers.get('etag'), 'data': data})
        return data

    def open_issues(self, label, cache):
        results = []
        for page in range(1, 6):
            path = '/issues?' + urlencode({'state': 'open', 'labels': label, 'sort': 'created',
                                            'direction': 'asc', 'per_page': 100, 'page': page})
            batch = self.conditional_get(path, cache)
            if not isinstance(batch, list):
                raise Blocked('Invalid issue list')
            results += [i for i in batch if 'pull_request' not in i]
            if len(results) > 20:
                raise Blocked('Pilot supports at most 20 open opted-in issues')
            if len(batch) < 100:
                return results
        raise Blocked('Issue list exceeds pagination limit')

    def issue_events(self, number):
        results = []
        for page in range(1, 11):
            batch = self.get(f'/issues/{int(number)}/events?per_page=100&page={page}')
            if not isinstance(batch, list):
                raise Blocked('Invalid issue event list')
            results += batch
            if len(batch) < 100:
                return results
        raise Blocked('Issue event list exceeds pagination limit')

    def get(self, path):
        return self.request("GET", self.prefix + path)

    def post(self, path, data):
        return self.request("POST", self.prefix + path, data)

    def issue(self, number):
        issue = self.get(f"/issues/{int(number)}")
        if "pull_request" in issue or issue.get("state") != "open":
            raise Blocked("Expected an open issue")
        return issue

    def can_write(self, login):
        p = self.get("/collaborators/" + quote(login, safe="") + "/permission")
        return p.get("permission") in {"admin", "maintain", "write"}

    def base(self, branch):
        return self.get("/commits/" + quote(branch, safe=""))["sha"]

    def governance(self, branch):
        if getattr(self, 'governance_mode', 'classic') == 'rulesets':
            return self.ruleset_governance(branch)
        # The old classic gate verified names, not trusted producers or bypass actors.
        # Autonomous writes require the fully audited App/Rulesets path.
        raise Blocked('Autonomous operation requires a GitHub App and audited rulesets; use config.app.example.json')

    def ruleset_governance(self, branch):
        if not getattr(self, 'app_id', None):
            raise Blocked('Ruleset mode requires GitHub App identity for trusted status sources')
        rules = []
        for page in range(1, 11):
            batch = self.get('/rules/branches/' + quote(branch, safe='') + f'?per_page=100&page={page}')
            if not isinstance(batch, list):
                raise Blocked('Invalid ruleset response')
            rules += batch
            if len(batch) < 100:
                break
        else:
            raise Blocked('Too many effective rules')
        details = {}
        for rule in rules:
            rid = rule.get('ruleset_id')
            if (type(rid) is not int or rule.get('ruleset_source_type') != 'Repository'
                    or rule.get('ruleset_source', '').casefold() != self.repository.casefold()):
                raise Blocked('MVP supports repository-local rulesets only')
            if rid not in details:
                details[rid] = self.get(f'/rulesets/{rid}')
            detail = details[rid]
            if (detail.get('id') != rid or detail.get('enforcement') != 'active'
                    or detail.get('target') != 'branch' or detail.get('source_type') != 'Repository'
                    or detail.get('source', '').casefold() != self.repository.casefold()
                    or not no_bypass_verified(detail, getattr(self, 'ruleset_attestations', {}))):
                raise Blocked('Ruleset bypass verification missing or stale; repeat the administrator audit')
            # Detect settings changing between the effective-rule and detail reads.
            compact = {k: v for k, v in rule.items() if k in {'type', 'parameters'}}
            if compact not in detail.get('rules', []):
                raise Blocked('Ruleset changed while verifying; retry after settings stabilize')
        kinds = {r['type'] for r in rules}
        review_ok = False
        checks = set()
        for rule in rules:
            p = rule.get('parameters', {})
            if rule['type'] == 'pull_request':
                review_ok |= (p.get('required_approving_review_count', 0) >= 1
                              and bool(p.get('dismiss_stale_reviews_on_push'))
                              and bool(p.get('require_last_push_approval'))
                              and bool(p.get('required_review_thread_resolution')))
            if rule['type'] == 'required_status_checks' and p.get('strict_required_status_checks_policy'):
                for check in p.get('required_status_checks', []):
                    if check.get('integration_id') == self.app_id:
                        checks.add(check.get('context'))
        if not review_ok or not {'deletion', 'non_fast_forward'}.issubset(kinds):
            raise Blocked('Ruleset must require fresh review, resolved conversations and block deletion/force pushes')
        if not {'factory/quality', 'factory/human-approval'}.issubset(checks):
            raise Blocked('Ruleset must require strict factory/quality and factory/human-approval checks from this GitHub App')

    def snapshot(self, base_sha, prefixes):
        commit = self.get("/git/commits/" + base_sha)
        tree = self.get("/git/trees/" + commit["tree"]["sha"] + "?recursive=1")
        if tree.get("truncated"):
            raise Blocked("Repository tree truncated")
        files, size = {}, 0
        for entry in tree["tree"]:
            path = safe_path(entry["path"])
            selected = path == "README.md" or any(path.startswith(p) for p in prefixes)
            if not selected or entry["type"] == "tree":
                continue
            if entry.get("mode") not in {"100644", "100755"}:
                raise Blocked("Symlinks/submodules in selected context are unsupported")
            if (path.rsplit("/", 1)[-1].startswith(".")
                    or path.lower().endswith((".pem", ".key", ".p12", ".env"))):
                raise Blocked("Potential secret file in selected context")
            if entry.get("size", 0) > 100_000 or len(files) >= 150:
                raise Blocked("Context budget exceeded; narrow repository scope")
            blob = self.get("/git/blobs/" + entry["sha"])
            content = base64.b64decode(blob["content"]).decode("utf-8")
            size += len(content.encode())
            if size > 400_000 or "\x00" in content:
                raise Blocked("Context too large or binary")
            if path.casefold() in {p.casefold() for p in files}:
                raise Blocked("Case-colliding repository paths")
            files[path] = content
        return files

    def publish(self, *, base_sha, base_branch, branch, changes, title, body):
        """Reconcile immutable branch/PR after uncertain network outcomes; never force push."""
        base = self.get("/git/commits/" + base_sha)
        tree = self.post("/git/trees", {"base_tree": base["tree"]["sha"], "tree": [
            {"path": safe_path(p), "mode": "100644", "type": "blob", "content": value}
            for p, value in sorted(changes.items())]})
        refs = self.get("/git/matching-refs/heads/" + quote(branch, safe="/"))
        existing = next((r for r in refs if r["ref"] == "refs/heads/" + branch), None)
        if existing:
            head = existing["object"]["sha"]
            commit = self.get("/git/commits/" + head)
            if commit["tree"]["sha"] != tree["sha"] or [p["sha"] for p in commit["parents"]] != [base_sha]:
                raise Blocked("Existing factory branch differs; refusing to overwrite")
        else:
            head = self.post("/git/commits", {"message": title, "tree": tree["sha"],
                                             "parents": [base_sha]})["sha"]
            self.post("/git/refs", {"ref": "refs/heads/" + branch, "sha": head})
        query = urlencode({"head": self.repository.split('/')[0] + ":" + branch,
                           "base": base_branch, "state": "all"})
        prs = self.get("/pulls?" + query)
        body = body.replace('{{FACTORY_HEAD}}', head)
        if prs:
            if len(prs) != 1 or prs[0]["state"] != "open":
                raise Blocked("Factory PR already closed or ambiguous")
            pr = prs[0]
        else:
            # All MVP PRs are draft: no premature integration while statuses are written.
            pr = self.post("/pulls", {"title": title[:240], "head": branch,
                                      "base": base_branch, "body": body, "draft": True})
        if pr["head"]["sha"] != head:
            raise Blocked("PR head changed during publication")
        return {"number": pr["number"], "url": pr["html_url"], "head_sha": head,
                "author_login": pr.get("user", {}).get("login", "")}

    def request_reviewers(self, number, reviewers):
        return self.post(f"/pulls/{number}/requested_reviewers", {"reviewers": reviewers})

    def status(self, sha, context, state, description):
        return self.post("/statuses/" + sha, {"context": context, "state": state,
                                               "description": description[:140]})

    def reviews(self, number):
        results = []
        for page in range(1, 11):
            batch = self.get(f"/pulls/{number}/reviews?per_page=100&page={page}")
            results += batch
            if len(batch) < 100:
                return results
        raise Blocked("Too many reviews to safely resolve approval state")

    def changed_paths(self, number):
        paths = set()
        for page in range(1, 31):
            batch = self.get(f'/pulls/{int(number)}/files?per_page=100&page={page}')
            if not isinstance(batch,list):
                raise Blocked('Lista de archivos no verificable')
            for entry in batch:
                paths.add(safe_path(entry['filename']))
                if entry.get('previous_filename'):
                    paths.add(safe_path(entry['previous_filename']))
            if len(batch)<100:
                return sorted(paths)
        raise Blocked('Demasiados archivos; revisión no verificable')

    def quality_passed(self, sha, producer):
        for page in range(1, 11):
            statuses=self.get(f'/statuses/{sha}?per_page=100&page={page}')
            for status in statuses:
                if status['context']=='factory/quality':
                    return (status['state']=='success'
                            and status.get('creator',{}).get('login','').casefold()==producer.casefold())
            if len(statuses)<100:
                return False
        raise Blocked('Historial de checks demasiado grande')
