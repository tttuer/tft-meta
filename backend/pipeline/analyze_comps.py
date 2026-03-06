"""
Reads match_raw table, runs comp analysis, and upserts results into comps table.
Called by Airflow DAG after fetch_matches.
"""
import asyncio
import logging
import uuid
from datetime import datetime

from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models.comp import Comp
from app.models.match_raw import MatchRaw
from app.services.comp_analyzer import analyze_comps
from app.services.riot_api import get_latest_patch_version

logger = logging.getLogger(__name__)

TIER_THRESHOLDS = {
    "S": 0.20,
    "A": 0.14,
    "B": 0.08,
    "C": 0.0,
}


def _assign_tier(win_rate: float) -> str:
    for tier, threshold in TIER_THRESHOLDS.items():
        if win_rate >= threshold:
            return tier
    return "C"


async def run():
    patch_version = await get_latest_patch_version()
    logger.info("Analyzing patch: %s", patch_version)

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(MatchRaw).where(MatchRaw.patch_version == patch_version)
        )
        matches = [{"participants": m.participants} for m in result.scalars().all()]

    if not matches:
        logger.warning("No matches found for patch %s", patch_version)
        return

    logger.info("Analyzing %d matches...", len(matches))
    stats = analyze_comps(matches)

    async with AsyncSessionLocal() as session:
        for stat in stats:
            tier = _assign_tier(stat["win_rate"])
            comp = Comp(
                id=uuid.uuid4(),
                name=f"컴프 {stat['trait_signature'][:30]}",
                tier=tier,
                win_rate=stat["win_rate"],
                top4_rate=stat["top4_rate"],
                avg_placement=stat["avg_placement"],
                play_rate=0.0,
                sample_count=stat["sample_count"],
                core_units={},
                board_positions=[],
                recommended_augments={},
                entry_conditions=[],
                ai_summary=None,
                patch_version=patch_version,
                updated_at=datetime.utcnow(),
            )
            session.add(comp)
        await session.commit()

    logger.info("Upserted %d comps", len(stats))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run())
