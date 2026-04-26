from __future__ import annotations

from api.models import DOMAIN_KEYS


def zero_advancement() -> dict:
    return {
        "points_available_earned": {domain: 0 for domain in DOMAIN_KEYS},
        "points_available_awarded": 0,
        "points_spent": 0,
        "points_earned_total": 0,
        "tag_advance_counters": {domain: 0 for domain in DOMAIN_KEYS},
    }