"""
Comp analyzer: aggregates raw match data into comp statistics.
Called by the Airflow pipeline after match ingestion.
"""
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


def analyze_comps(matches: list[dict]) -> list[dict]:
    """
    Given a list of raw match participant records, compute comp win rates.
    Returns a list of comp stat dicts ready for DB upsert.
    """
    trait_buckets: dict[str, list] = defaultdict(list)

    for match in matches:
        for participant in match.get("participants", []):
            key = _trait_signature(participant.get("traits", []))
            trait_buckets[key].append(participant)

    results = []
    for sig, participants in trait_buckets.items():
        if len(participants) < 10:
            continue
        placements = [p.get("placement", 8) for p in participants]
        win_rate = sum(1 for p in placements if p == 1) / len(placements)
        top4_rate = sum(1 for p in placements if p <= 4) / len(placements)
        avg_placement = sum(placements) / len(placements)

        results.append(
            {
                "trait_signature": sig,
                "win_rate": win_rate,
                "top4_rate": top4_rate,
                "avg_placement": avg_placement,
                "sample_count": len(participants),
            }
        )

    results.sort(key=lambda x: x["win_rate"], reverse=True)
    return results


def _trait_signature(traits: list[dict]) -> str:
    active = sorted(
        [t["name"] for t in traits if t.get("tier_current", 0) > 0]
    )
    return "|".join(active)
