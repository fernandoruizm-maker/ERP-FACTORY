"""Each callback must invoke an independent, read-only review session."""
import asyncio
from .contracts import Review
from .policy import ROLES


async def parallel_reviews(candidate, reviewers, timeout=30.0):
    if set(reviewers) != ROLES:
        raise ValueError("Three independent reviewers are mandatory")

    async def invoke(role):
        try:
            result = await asyncio.wait_for(reviewers[role](candidate), timeout)
            if not isinstance(result, Review) or result.role != role:
                raise ValueError("Malformed review")
            if result.candidate_id != candidate.fingerprint:
                raise ValueError("Stale review")
            return result
        except Exception as exc:
            return Review(role, candidate.fingerprint, "ERROR", (type(exc).__name__,))

    return tuple(await asyncio.gather(*(invoke(role) for role in sorted(ROLES))))
