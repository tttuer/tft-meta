"""
증강 분석 서비스.

기능:
  - 각 증강 + 컴프 조합의 평균 순위 변화 계산
  - 스테이지별(2-1, 3-2, 4-2) 최적 증강 TOP 3 도출
  - match_raw 테이블의 participants JSONB 데이터 기반 분석

Riot API 매치 데이터에서 증강 정보는 participants[].augments 배열로 제공됨.
augment 선택 스테이지는 round 필드나 augment index로 추정:
  index 0 → 2-1 (stage 2), index 1 → 3-2 (stage 3), index 2 → 4-2 (stage 4)
"""
import logging
from collections import defaultdict
from datetime import date
from typing import Any

from sqlalchemy import cast, select
from sqlalchemy.types import Date

from app.database import AsyncSessionLocal
from app.models.match_raw import MatchRaw

logger = logging.getLogger(__name__)

# 스테이지별 증강 인덱스 매핑
STAGE_AUGMENT_INDEX: dict[str, int] = {
    "2-1": 0,
    "3-2": 1,
    "4-2": 2,
}

TOP_AUGMENTS_PER_STAGE = 3


# ---------------------------------------------------------------------------
# 내부 유틸
# ---------------------------------------------------------------------------

def _extract_augments_by_stage(participant: dict) -> dict[str, list[str]]:
    """
    참가자 데이터에서 스테이지별 증강 목록 추출.
    Riot API: participant.augments = ["Augment_ID_1", "Augment_ID_2", ...]
    """
    augments: list[str] = participant.get("augments", [])
    result: dict[str, list[str]] = {}
    for stage, idx in STAGE_AUGMENT_INDEX.items():
        if idx < len(augments):
            result[stage] = [augments[idx]]
    return result


def _get_comp_signature(participant: dict) -> str:
    """참가자의 활성 시너지 기반 간이 컴프 시그니처."""
    traits = participant.get("traits", [])
    active = sorted(
        t["name"] for t in traits if t.get("tier_current", 0) > 0
    )
    return "|".join(active) if active else "unknown"


# ---------------------------------------------------------------------------
# 핵심 분석 함수
# ---------------------------------------------------------------------------

def analyze_augment_stats(
    participants: list[dict],
) -> dict[str, Any]:
    """
    참가자 목록에서 스테이지별 증강 통계 계산.

    Returns:
        {
          "by_stage": {
            "2-1": [{"augment_id": str, "avg_placement": float, "count": int}, ...],
            "3-2": [...],
            "4-2": [...],
          },
          "by_comp_and_augment": {
            "comp_signature": {
              "augment_id": {"avg_placement": float, "count": int}
            }
          }
        }
    """
    # stage → augment_id → [placements]
    stage_augment_placements: dict[str, dict[str, list[float]]] = {
        stage: defaultdict(list) for stage in STAGE_AUGMENT_INDEX
    }
    # comp_sig → augment_id → [placements]
    comp_augment_placements: dict[str, dict[str, list[float]]] = defaultdict(
        lambda: defaultdict(list)
    )

    for participant in participants:
        placement = float(participant.get("placement", 8))
        comp_sig = _get_comp_signature(participant)
        augments_by_stage = _extract_augments_by_stage(participant)

        for stage, aug_list in augments_by_stage.items():
            for aug_id in aug_list:
                stage_augment_placements[stage][aug_id].append(placement)
                comp_augment_placements[comp_sig][aug_id].append(placement)

    # 스테이지별 집계 (낮은 avg_placement = 좋은 증강)
    by_stage: dict[str, list[dict]] = {}
    for stage, aug_map in stage_augment_placements.items():
        entries = [
            {
                "augment_id": aug_id,
                "avg_placement": sum(pls) / len(pls),
                "count": len(pls),
            }
            for aug_id, pls in aug_map.items()
            if len(pls) >= 10  # 최소 샘플 10개
        ]
        entries.sort(key=lambda x: x["avg_placement"])
        by_stage[stage] = entries[:TOP_AUGMENTS_PER_STAGE]

    # 컴프 + 증강 조합 집계
    by_comp_and_augment: dict[str, dict[str, dict]] = {}
    for comp_sig, aug_map in comp_augment_placements.items():
        by_comp_and_augment[comp_sig] = {
            aug_id: {
                "avg_placement": sum(pls) / len(pls),
                "count": len(pls),
            }
            for aug_id, pls in aug_map.items()
            if len(pls) >= 5
        }

    return {
        "by_stage": by_stage,
        "by_comp_and_augment": by_comp_and_augment,
    }


# ---------------------------------------------------------------------------
# DB 기반 분석 진입점
# ---------------------------------------------------------------------------

async def get_stage_best_augments(
    patch_version: str | None = None,
    run_date: str | None = None,
) -> dict[str, list[dict]]:
    """
    스테이지별 최적 증강 TOP 3 반환.

    Args:
        patch_version: 필터할 패치 버전. None이면 전체.
        run_date: YYYY-MM-DD 형식. None이면 patch_version 기준 전체.

    Returns:
        {"2-1": [...], "3-2": [...], "4-2": [...]}
    """
    async with AsyncSessionLocal() as session:
        query = select(MatchRaw)
        if patch_version:
            query = query.where(MatchRaw.patch_version == patch_version)
        if run_date:
            query = query.where(
                cast(MatchRaw.collected_at, Date) == date.fromisoformat(run_date)
            )
        result = await session.execute(query)
        matches = result.scalars().all()

    if not matches:
        logger.warning("[get_stage_best_augments] 매치 데이터 없음")
        return {stage: [] for stage in STAGE_AUGMENT_INDEX}

    all_participants: list[dict] = []
    for m in matches:
        all_participants.extend(m.participants)

    logger.info("[get_stage_best_augments] 참가자 수: %d", len(all_participants))
    stats = analyze_augment_stats(all_participants)
    return stats["by_stage"]


async def get_comp_augment_stats(
    comp_signature: str,
    patch_version: str | None = None,
) -> dict[str, dict]:
    """
    특정 컴프의 증강별 평균 순위 변화 반환.

    Args:
        comp_signature: 파이프로 구분된 시너지 시그니처 ("Trait1|Trait2|...")
        patch_version: 필터할 패치 버전

    Returns:
        {augment_id: {"avg_placement": float, "count": int}, ...}
    """
    async with AsyncSessionLocal() as session:
        query = select(MatchRaw)
        if patch_version:
            query = query.where(MatchRaw.patch_version == patch_version)
        result = await session.execute(query)
        matches = result.scalars().all()

    all_participants: list[dict] = []
    for m in matches:
        all_participants.extend(m.participants)

    stats = analyze_augment_stats(all_participants)
    return stats["by_comp_and_augment"].get(comp_signature, {})


async def get_full_augment_analysis(
    patch_version: str | None = None,
    run_date: str | None = None,
) -> dict[str, Any]:
    """
    전체 증강 분석 결과 반환 (캐시 또는 API 응답 용도).

    Returns:
        {
          "by_stage": {...},
          "total_matches_analyzed": int,
          "patch_version": str | None,
        }
    """
    async with AsyncSessionLocal() as session:
        query = select(MatchRaw)
        if patch_version:
            query = query.where(MatchRaw.patch_version == patch_version)
        if run_date:
            query = query.where(
                cast(MatchRaw.collected_at, Date) == date.fromisoformat(run_date)
            )
        result = await session.execute(query)
        matches = result.scalars().all()

    all_participants: list[dict] = []
    for m in matches:
        all_participants.extend(m.participants)

    stats = analyze_augment_stats(all_participants)
    return {
        "by_stage": stats["by_stage"],
        "total_matches_analyzed": len(matches),
        "patch_version": patch_version,
    }
