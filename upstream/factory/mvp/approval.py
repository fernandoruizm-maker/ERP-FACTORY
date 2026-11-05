from datetime import datetime, timezone, timedelta
import json
from .common import Blocked, digest
from ..memory import Brain


def resolve_approval(reviews, *, head, author, allowed, now, ttl_hours=24):
    latest = {}
    for review in sorted(reviews, key=lambda r: r["id"]):
        if review["state"] in {"APPROVED", "CHANGES_REQUESTED", "DISMISSED"}:
            latest[review["user"]["login"]] = review
    # An unresolved authorized request for changes vetoes an approval by another human.
    if any(r["state"] == "CHANGES_REQUESTED" for u, r in latest.items() if u in allowed):
        return None
    for login, review in latest.items():
        if login not in allowed or login == author or review["user"].get("type") != "User":
            continue
        if review["state"] != "APPROVED" or review.get("commit_id") != head:
            continue
        submitted = datetime.fromisoformat(review["submitted_at"].replace("Z", "+00:00"))
        if timedelta(0) <= now - submitted < timedelta(hours=ttl_hours):
            return login
    return None


def refresh(config, github, queue, job_id):
    if config.get('github_app') or config.get('approval_policy'):
        from .role_gate import refresh_roles
        return refresh_roles(config, github, queue, job_id)
    job = queue.get(job_id)
    if not job or job["state"] not in {"WAITING_APPROVAL", "APPROVED"}:
        raise Blocked("Job is not awaiting or holding an approval")
    saved = json.loads(job["checkpoint"])
    pr = github.get(f"/pulls/{saved['pr']['number']}")
    if pr.get('merged') is True:
        # Record an external outcome, not a new approval. The base naturally moves
        # after a merge; do not invalidate the completed commit's historical checks.
        same_candidate = (pr['state'] == 'closed' and pr['head']['sha'] == saved['pr']['head_sha']
                          and pr['base'].get('ref') == config['base_branch']
                          and pr['base'].get('repo', {}).get('full_name') == config['repository']
                          and isinstance(pr.get('merge_commit_sha'), str) and bool(pr['merge_commit_sha'])
                          and bool(pr.get('merged_at')))
        if not same_candidate:
            queue.set(job_id, 'BLOCKED', error='Merged PR differs from the tracked candidate or target')
            return 'BLOCKED'
        saved['integration'] = {'merge_commit_sha': pr['merge_commit_sha'], 'merged_at': pr['merged_at'],
                                'merged_by': (pr.get('merged_by') or {}).get('login'),
                                'observed_in_github': True}
        queue.set(job_id, 'MERGED', saved)
        return 'MERGED'
    def same_open_candidate(current):
        return (current['state'] == 'open' and not current.get('merged')
                and current['head']['sha'] == saved['pr']['head_sha']
                and current['base']['sha'] == saved['base_sha']
                and current['base'].get('ref') == config['base_branch']
                and current['base'].get('repo', {}).get('full_name') == config['repository'])

    def invalidate(current):
        github.status(current['head']['sha'], 'factory/quality', 'failure', 'Candidate changed; rerun the factory')
        github.status(current['head']['sha'], 'factory/human-approval', 'pending', 'Previous approval invalidated')
        queue.set(job_id, 'BLOCKED', error='Candidate changed')
        return 'BLOCKED'

    valid = (same_open_candidate(pr)
             and github.base(config["base_branch"]) == saved["base_sha"]
             and digest(config) == saved["config_sha"]
             and Brain.load(config["brain_dir"]).fingerprint == saved["brain_sha"])
    if not valid:
        return invalidate(pr)
    github.governance(config["base_branch"])
    reviewer = resolve_approval(github.reviews(pr["number"]), head=pr["head"]["sha"],
                               author=pr["user"]["login"], allowed=config["human_reviewers"],
                               now=datetime.now(timezone.utc))
    if reviewer and not github.can_write(reviewer):
        reviewer = None
    # Recheck after API reads. Native branch protections remain authoritative at merge.
    current = github.get(f"/pulls/{pr['number']}")
    if (not same_open_candidate(current)
            or github.base(config['base_branch']) != saved['base_sha']):
        if current.get('merged') is True:
            # Let the next cycle reconcile the external merge without rewriting history.
            raise Blocked('PR merged while checking approval; refresh to reconcile')
        return invalidate(current)
    state = "APPROVED" if reviewer else "WAITING_APPROVAL"
    github.status(pr["head"]["sha"], "factory/human-approval", "success" if reviewer else "pending",
                  "Approved by authorized human" if reviewer else "Waiting for independent human review")
    queue.set(job_id, state)
    # Remain draft; a human may mark ready and integrate through protected GitHub UI.
    # No merge or deployment capability exists in this service.
    return state
