import asyncio
import logging
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

REGION_ROUTING = {
    "kr": "asia",
    "na1": "americas",
    "euw1": "europe",
}

BASE_URLS = {
    "kr": "https://kr.api.riotgames.com",
    "na1": "https://na1.api.riotgames.com",
    "euw1": "https://euw1.api.riotgames.com",
    "asia": "https://asia.api.riotgames.com",
    "americas": "https://americas.api.riotgames.com",
    "europe": "https://europe.api.riotgames.com",
}

_semaphore = asyncio.Semaphore(10)
_latest_patch: str | None = None  # 프로세스 내 캐시


async def get_latest_patch_version() -> str:
    """Data Dragon에서 현재 최신 TFT 패치 버전을 반환한다. 프로세스당 1회 fetch 후 캐싱."""
    global _latest_patch
    if _latest_patch:
        return _latest_patch

    url = "https://ddragon.leagueoflegends.com/api/versions.json"
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        versions: list[str] = resp.json()

    _latest_patch = versions[0]  # 첫 번째 항목이 최신
    logger.info("Latest patch version: %s", _latest_patch)
    return _latest_patch


async def _request(url: str, retries: int = 3) -> Any:
    headers = {"X-Riot-Token": settings.riot_api_key}
    delay = 1.0

    async with _semaphore:
        for attempt in range(retries):
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url, headers=headers)

            if resp.status_code == 200:
                return resp.json()

            if resp.status_code == 429:
                retry_after = int(resp.headers.get("Retry-After", delay * 2))
                logger.warning("Rate limited. Sleeping %ss (attempt %d)", retry_after, attempt + 1)
                await asyncio.sleep(retry_after)
                delay *= 2
                continue

            resp.raise_for_status()

    raise RuntimeError(f"Failed after {retries} retries: {url}")


async def get_challenger_summoners(region: str = "kr") -> list[dict]:
    base = BASE_URLS[region]
    url = f"{base}/tft/league/v1/challenger?queue=RANKED_TFT"
    data = await _request(url)
    return data.get("entries", [])


async def get_grandmaster_summoners(region: str = "kr") -> list[dict]:
    base = BASE_URLS[region]
    url = f"{base}/tft/league/v1/grandmaster?queue=RANKED_TFT"
    data = await _request(url)
    return data.get("entries", [])


async def get_master_summoners(region: str = "kr") -> list[dict]:
    base = BASE_URLS[region]
    url = f"{base}/tft/league/v1/master?queue=RANKED_TFT"
    data = await _request(url)
    return data.get("entries", [])


async def get_match_ids(puuid: str, region: str = "kr", count: int = 20) -> list[str]:
    routing = REGION_ROUTING.get(region, "asia")
    base = BASE_URLS[routing]
    url = f"{base}/tft/match/v1/matches/by-puuid/{puuid}/ids?count={count}"
    return await _request(url)


async def get_match_detail(match_id: str, region: str = "kr") -> dict:
    routing = REGION_ROUTING.get(region, "asia")
    base = BASE_URLS[routing]
    url = f"{base}/tft/match/v1/matches/{match_id}"
    return await _request(url)
