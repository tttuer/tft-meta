"""
매치 수집 워커: Riot API → match_raw 테이블

지원 리전: kr, na1, euw1
수집 대상: 마스터+ (챌린저 + 마스터 + 그랜드마스터) 소환사
소환사당 최근 10경기 수집.
이미 저장된 match_id는 스킵.
목표: 리전당 5,000~10,000 매치/일.
동시 요청: asyncio.Semaphore(10)

CLI:
  python fetch_matches.py --region kr
  python fetch_matches.py --region kr --dry-run
"""
import argparse
import asyncio
import logging
import sys
from datetime import datetime

from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models.match_raw import MatchRaw
from app.services.riot_api import (
    get_challenger_summoners,
    get_grandmaster_summoners,
    get_latest_patch_version,
    get_master_summoners,
    get_match_detail,
    get_match_ids,
)

logger = logging.getLogger(__name__)

MATCH_COUNT_PER_SUMMONER = 10
_fetch_semaphore = asyncio.Semaphore(10)


# ---------------------------------------------------------------------------
# 내부 유틸
# ---------------------------------------------------------------------------

async def _get_existing_match_ids(session, match_ids: list[str]) -> set[str]:
    """DB에 이미 존재하는 match_id 집합 반환."""
    result = await session.execute(
        select(MatchRaw.match_id).where(MatchRaw.match_id.in_(match_ids))
    )
    return {row[0] for row in result.fetchall()}


async def _fetch_match_safe(match_id: str, region: str) -> dict | None:
    """단일 매치 상세 조회. 실패 시 None 반환."""
    async with _fetch_semaphore:
        try:
            return await get_match_detail(match_id, region=region)
        except Exception as exc:
            logger.warning("[%s] 매치 상세 조회 실패 %s: %s", region, match_id, exc)
            return None


async def _collect_summoners(region: str) -> list[dict]:
    """챌린저 + 그랜드마스터 + 마스터 소환사 목록 통합."""
    results: list[list[dict]] = await asyncio.gather(
        get_challenger_summoners(region),
        get_grandmaster_summoners(region),
        get_master_summoners(region),
        return_exceptions=True,
    )
    combined: list[dict] = []
    for r in results:
        if isinstance(r, Exception):
            logger.warning("[%s] 소환사 목록 조회 실패: %s", region, r)
            continue
        combined.extend(r)

    # puuid 중복 제거
    seen: set[str] = set()
    unique: list[dict] = []
    for s in combined:
        puuid = s.get("puuid")
        if puuid and puuid not in seen:
            seen.add(puuid)
            unique.append(s)

    logger.info("[%s] 마스터+ 소환사 수: %d", region, len(unique))
    return unique


# ---------------------------------------------------------------------------
# 메인 로직
# ---------------------------------------------------------------------------

async def fetch_and_store_region(
    region: str,
    patch_version: str,
    dry_run: bool = False,
) -> dict:
    """
    한 리전의 마스터+ 소환사 매치 데이터를 수집·저장.

    Returns:
        dict: {"region": str, "stored": int, "skipped": int, "errors": int}
    """
    stats = {"region": region, "stored": 0, "skipped": 0, "errors": 0}

    summoners = await _collect_summoners(region)
    if not summoners:
        logger.warning("[%s] 소환사 목록이 비어 있습니다.", region)
        return stats

    # 각 소환사의 매치 ID 수집 (Semaphore로 동시성 제어)
    async def _get_ids_for_summoner(summoner: dict) -> list[str]:
        puuid = summoner.get("puuid")
        if not puuid:
            return []
        async with _fetch_semaphore:
            try:
                return await get_match_ids(puuid, region=region, count=MATCH_COUNT_PER_SUMMONER)
            except Exception as exc:
                logger.warning("[%s] 매치 ID 조회 실패 puuid=%s: %s", region, puuid[:12], exc)
                stats["errors"] += 1
                return []

    id_lists = await asyncio.gather(*[_get_ids_for_summoner(s) for s in summoners])
    all_match_ids: list[str] = list({mid for ids in id_lists for mid in ids})
    logger.info("[%s] 수집된 고유 매치 ID: %d", region, len(all_match_ids))

    if dry_run:
        logger.info("[%s] DRY-RUN 모드: 저장 없이 종료 (ID 수: %d)", region, len(all_match_ids))
        stats["stored"] = len(all_match_ids)
        return stats

    # DB에서 기존 match_id 조회
    async with AsyncSessionLocal() as session:
        existing_ids = await _get_existing_match_ids(session, all_match_ids)

    new_ids = [mid for mid in all_match_ids if mid not in existing_ids]
    stats["skipped"] = len(existing_ids)
    logger.info(
        "[%s] 신규: %d / 스킵(중복): %d",
        region, len(new_ids), stats["skipped"],
    )

    # 신규 매치 상세 수집 및 저장 (배치 처리)
    BATCH_SIZE = 100
    for batch_start in range(0, len(new_ids), BATCH_SIZE):
        batch = new_ids[batch_start : batch_start + BATCH_SIZE]
        details = await asyncio.gather(*[_fetch_match_safe(mid, region) for mid in batch])

        async with AsyncSessionLocal() as session:
            for match_id, detail in zip(batch, details):
                if detail is None:
                    stats["errors"] += 1
                    continue
                participants = detail.get("info", {}).get("participants", [])
                row = MatchRaw(
                    match_id=match_id,
                    region=region,
                    participants=participants,
                    patch_version=patch_version,
                    collected_at=datetime.utcnow(),
                )
                session.add(row)
                stats["stored"] += 1
            await session.commit()

        logger.info(
            "[%s] 배치 저장 완료 (%d/%d)", region, min(batch_start + BATCH_SIZE, len(new_ids)), len(new_ids)
        )

    logger.info(
        "[%s] 완료 — 저장: %d / 스킵: %d / 에러: %d",
        region, stats["stored"], stats["skipped"], stats["errors"],
    )
    return stats


async def run(regions: list[str] | None = None, dry_run: bool = False) -> int:
    """
    Airflow DAG에서 호출하는 진입점.

    Args:
        regions: 수집할 리전 목록. None이면 ["kr", "na1", "euw1"] 전체 실행.
        dry_run: True이면 실제 DB 저장 없이 카운트만 출력.

    Returns:
        총 저장된 매치 수.
    """
    if regions is None:
        regions = ["kr", "na1", "euw1"]

    patch_version = await get_latest_patch_version()
    logger.info("패치 버전: %s / 대상 리전: %s", patch_version, regions)

    region_stats = await asyncio.gather(
        *[fetch_and_store_region(r, patch_version, dry_run=dry_run) for r in regions]
    )

    total_stored = 0
    for stat in region_stats:
        logger.info(
            "리전 요약 [%s] 저장=%d 스킵=%d 에러=%d",
            stat["region"], stat["stored"], stat["skipped"], stat["errors"],
        )
        total_stored += stat["stored"]

    logger.info("전체 수집 완료: 총 %d 매치 저장", total_stored)
    return total_stored


async def parse_raw_matches(run_date: str) -> int:
    """
    Airflow parse_matches 태스크에서 호출.
    match_raw 테이블에서 해당 날짜(collected_at)의 레코드를 읽어 참가자 수를 집계.

    Returns:
        파싱된 참가자 레코드 총 수.
    """
    from datetime import date
    from sqlalchemy import func, cast
    from sqlalchemy.types import Date

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(MatchRaw).where(
                cast(MatchRaw.collected_at, Date) == date.fromisoformat(run_date)
            )
        )
        matches = result.scalars().all()

    total_participants = sum(len(m.participants) for m in matches)
    logger.info(
        "[parse_raw_matches] run_date=%s, 매치=%d, 참가자=%d",
        run_date, len(matches), total_participants,
    )
    return total_participants


# ---------------------------------------------------------------------------
# CLI 지원
# ---------------------------------------------------------------------------

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="TFT 매치 수집 워커")
    parser.add_argument(
        "--region",
        choices=["kr", "na1", "euw1", "all"],
        default="all",
        help="수집할 리전 (기본값: all)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="실제 저장 없이 카운트만 출력",
    )
    return parser.parse_args()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    args = _parse_args()
    target_regions = ["kr", "na1", "euw1"] if args.region == "all" else [args.region]

    total = asyncio.run(run(regions=target_regions, dry_run=args.dry_run))
    logger.info("완료. 총 저장 매치: %d", total)
    sys.exit(0)
