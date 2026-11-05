"""Conservative USD reservations. No billing API, credentials or implicit caps."""
from decimal import Decimal
import re

from .contract import Blocked, source_sha


def money(value):
    if not isinstance(value, str) or not re.fullmatch(r'[0-9]+(?:\.[0-9]{1,6})?', value):
        raise Blocked('SPEND_CAP_REQUIRED')
    units = Decimal(value) * 1_000_000
    if not 1 <= units <= 9_000_000_000_000_000:
        raise Blocked('SPEND_CAP_INVALID')
    return int(units)


def amount(units):
    return format(Decimal(units) / 1_000_000, 'f')


def execution_limits(policy, grant, commit):
    source_sha(commit)
    calls = policy.get('max_calls_per_execution')
    if policy.get('budget_currency') != 'USD' or type(calls) is not int or not 1 <= calls <= 11:
        raise Blocked('CALL_OR_CURRENCY_CAP_REQUIRED')
    run = money(policy.get('max_spend_per_execution'))
    per_call = money(policy.get('max_budget_usd_per_call'))
    if (not isinstance(grant, dict) or set(grant) != {'grant_id', 'source_sha', 'allowance_usd'}
            or not isinstance(grant['grant_id'], str)
            or not re.fullmatch('[A-Za-z0-9_-]{1,100}', grant['grant_id'])
            or grant['source_sha'] != commit):
        raise Blocked('LOCAL_ALLOWANCE_REQUIRED')
    return {'max_calls': calls, 'ceiling_units': min(run, money(grant['allowance_usd'])),
            'per_call_units': per_call, 'currency': 'USD', 'grant_id': grant['grant_id']}


def reserve(budget, limits, slot):
    if any(item['slot'] == slot for item in budget):
        raise Blocked('NO_AUTOMATIC_RETRY')
    if any(item['status'] in ('IN_FLIGHT', 'UNKNOWN', 'OVER_BUDGET') for item in budget):
        raise Blocked('UNCERTAIN_OR_OVER_BUDGET')
    if len(budget) >= limits['max_calls']:
        raise Blocked('CALL_LIMIT_REACHED')
    if sum(item['charged_units'] for item in budget) + limits['per_call_units'] > limits['ceiling_units']:
        raise Blocked('SPEND_LIMIT_REACHED')
    budget.append({'slot': slot, 'reserved_units': limits['per_call_units'],
                   'charged_units': limits['per_call_units'], 'status': 'IN_FLIGHT'})


def finish(budget, success, diagnostic):
    item = budget[-1]
    if item['status'] != 'IN_FLIGHT':
        raise Blocked('NO_AUTOMATIC_RETRY')
    item['status'] = 'COMPLETED' if success else 'UNKNOWN'
    reported = diagnostic.get('total_cost_usd')
    if type(reported) in (float, int) and 0 <= reported < 10**10:
        # Provider metadata is unverified. Never refund; a reported overrun stops.
        charged = int((Decimal(str(reported)) * 1_000_000).to_integral_value(rounding='ROUND_CEILING'))
        item['charged_units'] = max(item['charged_units'], charged)
        if charged > item['reserved_units']:
            item['status'] = 'OVER_BUDGET'
