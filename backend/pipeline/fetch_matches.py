"""
Fetches match data from Riot API and stores raw JSON in match_raw table.
Called by Airflow DAG.
"""
import asyncio
import logging
from datetime import datetime

from app.database import AsyncSessionLocal
from app.models.match_raw import MatchRaw
from app.services.riot_api import (
    get_challenger_summoners,
    get_latest_patch_version,
    get_master_summoners,
    get_match_detail,
    get_match_ids,
)

logger = logging.getLogger(__name__)

REGIONS = ["kr", "na1", "euw1"]
MATCH_COUNT_PER_SUMMONER = 10
MAX_SUMMONERS = 50


async def fetch_and_store(region: str, patch_version: str) -> int:
    challengers = await get_challenger_summoners(region)
    masters = await get_master_summoners(region)
    summoners = (challengers + masters)[:MAX_SUMMONERS]
    logger.info("[%s] Processing %d summoners", region, len(summoners))

    stored = 0
    async with AsyncSessionLocal() as session:
        for summoner in summoners:
            puuid = summoner.get("puuid")
            if not puuid:
                continue
            try:
                match_ids = await get_match_ids(puuid, region=region, count=MATCH_COUNT_PER_SUMMONER)
            except Exception as e:
                logger.warning("Failed to fetch match IDs for %s: %s", puuid[:12], e)
                continue

            for match_id in match_ids:
                existing = await session.get(MatchRaw, match_id)
                if existing:
                    continue
                try:
                    detail = await get_match_detail(match_id, region=region)
                    participants = detail.get("info", {}).get("participants", [])
                    raw = MatchRaw(
                        match_id=match_id,
                        region=region,
                        participants=participants,
                        patch_version=patch_version,
                        collected_at=datetime.utcnow(),
                    )
                    session.add(raw)
                    stored += 1
                except Exception as e:
                    logger.warning("Failed match %s: %s", match_id, e)

        await session.commit()

    logger.info("[%s] Stored %d new matches", region, stored)
    return stored


async def run():
    patch_version = await get_latest_patch_version()
    logger.info("Running fetch for patch: %s", patch_version)
    total = 0
    for region in REGIONS:
        total += await fetch_and_store(region, patch_version)
    logger.info("Total new matches stored: %d", total)
    return total


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run())
