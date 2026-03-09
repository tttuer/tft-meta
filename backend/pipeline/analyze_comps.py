"""
컴프 클러스터링 엔진

알고리즘:
  1. 4위 이내 참가자의 챔피언 목록 추출
  2. 코스트 4~5 챔피언을 "앵커"로 설정
  3. 앵커 기준으로 자주 함께 등장하는 챔피언 조합 집계
  4. 코사인 유사도 0.7 이상이면 같은 컴프로 분류
  5. 샘플 수 50 미만 컴프 제외
  6. 최종 상위 20개 컴프 선정

레벨별 코어 챔피언: 레벨 6→TOP6 / 7→TOP7 / 8→TOP8 / 9→TOP9
배치 좌표: 상위 10% 순위 참가자의 평균 배치를 7×4 그리드로 변환
승률 통계: win_rate / top4_rate / avg_placement / play_rate

CLI:
  python analyze_comps.py --date yesterday
  python analyze_comps.py --date 2024-01-15
"""
import argparse
import asyncio
import logging
import sys
import uuid
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from typing import Any

import numpy as np
from sqlalchemy import cast, select
from sqlalchemy.types import Date

from app.database import AsyncSessionLocal
from app.models.comp import Comp
from app.models.match_raw import MatchRaw
from app.services.ai_summary import generate_comp_strategy_summary, generate_meta_change_summary
from app.services.riot_api import get_latest_patch_version

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 상수
# ---------------------------------------------------------------------------

COSINE_THRESHOLD = 0.7      # 같은 컴프로 분류할 유사도 하한
MIN_SAMPLE_COUNT = 50       # 최소 샘플 수
TOP_COMP_COUNT = 20         # 최종 선정 컴프 수
HIGH_COST_THRESHOLD = 4     # 앵커 챔피언의 최소 코스트
BOARD_ROWS = 4
BOARD_COLS = 7
TOP_PLACEMENT_PCT = 0.10    # 배치 데이터 분석에 사용할 상위 % (1위에 가까울수록 작은 값)

TIER_THRESHOLDS: list[tuple[str, float]] = [
    ("S", 0.20),
    ("A", 0.14),
    ("B", 0.08),
    ("C", 0.0),
]

# Riot API 매치 데이터에서 챔피언 코스트는 unit의 rarity 필드로 추정.
# rarity 0→1코스트, 1→2코스트, 2→3코스트, 4→4코스트, 6→5코스트
RARITY_TO_COST: dict[int, int] = {0: 1, 1: 2, 2: 3, 4: 4, 6: 5}


# ---------------------------------------------------------------------------
# 내부 유틸
# ---------------------------------------------------------------------------

def _rarity_to_cost(rarity: int) -> int:
    return RARITY_TO_COST.get(rarity, 1)


def _unit_vector(champion_ids: list[str], vocab: dict[str, int]) -> np.ndarray:
    """챔피언 목록 → vocab 기반 이진 벡터."""
    vec = np.zeros(len(vocab), dtype=float)
    for cid in champion_ids:
        if cid in vocab:
            vec[vocab[cid]] = 1.0
    return vec


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


def _assign_tier(win_rate: float) -> str:
    for tier, threshold in TIER_THRESHOLDS:
        if win_rate >= threshold:
            return tier
    return "C"


def _extract_anchor(units: list[dict]) -> str | None:
    """참가자 units 중 코스트 4~5 챔피언 ID 반환 (여럿이면 코스트 높은 순 첫 번째)."""
    high_cost = [
        u for u in units
        if _rarity_to_cost(u.get("rarity", 0)) >= HIGH_COST_THRESHOLD
    ]
    if not high_cost:
        return None
    high_cost.sort(key=lambda u: u.get("rarity", 0), reverse=True)
    return high_cost[0].get("character_id")


def _champion_ids(units: list[dict]) -> list[str]:
    return [u["character_id"] for u in units if "character_id" in u]


def _board_position_to_grid(row: int, col: int) -> tuple[int, int]:
    """Riot API의 행/열 값을 7×4 그리드 좌표로 정규화."""
    r = min(max(int(row), 0), BOARD_ROWS - 1)
    c = min(max(int(col), 0), BOARD_COLS - 1)
    return r, c


# ---------------------------------------------------------------------------
# 클러스터링 알고리즘
# ---------------------------------------------------------------------------

def _cluster_participants(
    participants: list[dict],
) -> list[dict]:
    """
    참가자 목록을 코사인 유사도 기반으로 클러스터링.

    Returns:
        클러스터 dict 목록. 각 항목:
          {
            "anchor": str,           # 대표 앵커 챔피언 ID
            "champion_counts": dict, # 챔피언별 등장 빈도
            "participants": list,    # 해당 클러스터에 포함된 참가자
          }
    """
    # 앵커가 있는 4위 이내 참가자만 선별
    top4 = [
        p for p in participants
        if p.get("placement", 9) <= 4
        and _extract_anchor(p.get("units", [])) is not None
    ]

    if not top4:
        return []

    # 전체 챔피언 vocab 구성
    all_champ_ids: set[str] = set()
    for p in top4:
        all_champ_ids.update(_champion_ids(p.get("units", [])))
    vocab = {cid: idx for idx, cid in enumerate(sorted(all_champ_ids))}

    # 앵커별 대표 벡터 구축 (앵커 → 가장 빈번한 챔피언 조합)
    anchor_groups: dict[str, list[dict]] = defaultdict(list)
    for p in top4:
        anchor = _extract_anchor(p.get("units", []))
        if anchor:
            anchor_groups[anchor].append(p)

    # 앵커 그룹 간 코사인 유사도로 합치기
    clusters: list[dict] = []
    for anchor, members in anchor_groups.items():
        counts: Counter = Counter()
        for m in members:
            counts.update(_champion_ids(m.get("units", [])))

        # 대표 벡터: 등장 빈도 정규화
        vec = np.zeros(len(vocab), dtype=float)
        for cid, cnt in counts.items():
            if cid in vocab:
                vec[vocab[cid]] = cnt / len(members)

        # 기존 클러스터와 유사도 비교
        merged = False
        for cluster in clusters:
            sim = _cosine_similarity(vec, cluster["_vec"])
            if sim >= COSINE_THRESHOLD:
                # 같은 컴프로 합산
                for cid, cnt in counts.items():
                    cluster["champion_counts"][cid] = cluster["champion_counts"].get(cid, 0) + cnt
                cluster["participants"].extend(members)
                # 대표 벡터 재계산
                total = len(cluster["participants"])
                new_vec = np.zeros(len(vocab), dtype=float)
                for cid, cnt in cluster["champion_counts"].items():
                    if cid in vocab:
                        new_vec[vocab[cid]] = cnt / total
                cluster["_vec"] = new_vec
                merged = True
                break

        if not merged:
            clusters.append({
                "anchor": anchor,
                "champion_counts": dict(counts),
                "participants": list(members),
                "_vec": vec,
            })

    # 내부 메타 키 제거
    for c in clusters:
        c.pop("_vec", None)

    return clusters


# ---------------------------------------------------------------------------
# 레벨별 코어 챔피언 도출
# ---------------------------------------------------------------------------

def _core_units_by_level(cluster: dict) -> dict[str, list[str]]:
    """
    레벨별(6/7/8/9) 코어 챔피언 ID 목록을 반환.
    각 참가자의 실제 보유 챔피언에서 해당 레벨에 맞는 TOP-N을 선별.
    """
    participants = cluster["participants"]
    level_champ: dict[int, Counter] = defaultdict(Counter)

    for p in participants:
        level = p.get("level", 8)
        champs = _champion_ids(p.get("units", []))
        for lv in [6, 7, 8, 9]:
            if level >= lv:
                level_champ[lv].update(champs)

    result: dict[str, list[str]] = {}
    for lv in [6, 7, 8, 9]:
        if level_champ[lv]:
            result[str(lv)] = [cid for cid, _ in level_champ[lv].most_common(lv)]
    return result


# ---------------------------------------------------------------------------
# 배치 좌표 도출
# ---------------------------------------------------------------------------

def _board_positions(cluster: dict) -> list[dict]:
    """
    상위 10% 순위 참가자의 배치 데이터 평균을 7×4 그리드 좌표로 변환.
    """
    participants = cluster["participants"]
    placements = sorted(p.get("placement", 9) for p in participants)
    cutoff_idx = max(1, int(len(placements) * TOP_PLACEMENT_PCT))
    cutoff_placement = placements[cutoff_idx - 1]

    top_players = [p for p in participants if p.get("placement", 9) <= cutoff_placement]
    if not top_players:
        top_players = participants

    # 챔피언별 평균 (row, col) 집계
    champ_positions: dict[str, list[tuple[int, int]]] = defaultdict(list)
    for p in top_players:
        for unit in p.get("units", []):
            cid = unit.get("character_id")
            row = unit.get("rarity", 0)   # 일부 Riot API 응답에 row 포함 (없으면 rarity 대체)
            col = unit.get("tier", 0)     # 일부 Riot API 응답에 col 포함 (없으면 tier 대체)
            # 실제 API 필드 이름이 다를 수 있으나 normalize
            real_row = unit.get("row", row)
            real_col = unit.get("col", col)
            if cid:
                champ_positions[cid].append((real_row, real_col))

    positions: list[dict] = []
    for cid, coords in champ_positions.items():
        avg_row = sum(r for r, _ in coords) / len(coords)
        avg_col = sum(c for _, c in coords) / len(coords)
        grid_r, grid_c = _board_position_to_grid(round(avg_row), round(avg_col))
        positions.append({"champion_id": cid, "row": grid_r, "col": grid_c})

    return positions


# ---------------------------------------------------------------------------
# 주요 시너지 추출
# ---------------------------------------------------------------------------

def _extract_traits(participants: list[dict]) -> list[str]:
    """참가자 목록에서 가장 자주 등장하는 활성 시너지 TOP 5 반환."""
    trait_counter: Counter = Counter()
    for p in participants:
        for trait in p.get("traits", []):
            if trait.get("tier_current", 0) > 0:
                trait_counter[trait.get("name", "")] += 1
    return [t for t, _ in trait_counter.most_common(5) if t]


# ---------------------------------------------------------------------------
# 통계 계산 및 DB 저장
# ---------------------------------------------------------------------------

def _calc_stats(cluster: dict, total_matches: int) -> dict:
    """클러스터에서 통계 지표 계산."""
    members = cluster["participants"]
    placements = [p.get("placement", 8) for p in members]
    n = len(placements)
    win_rate = sum(1 for pl in placements if pl == 1) / n
    top4_rate = sum(1 for pl in placements if pl <= 4) / n
    avg_placement = sum(placements) / n
    play_rate = n / max(total_matches, 1)
    return {
        "win_rate": win_rate,
        "top4_rate": top4_rate,
        "avg_placement": avg_placement,
        "play_rate": play_rate,
        "sample_count": n,
    }


async def _load_matches_for_date(run_date: str) -> list[MatchRaw]:
    """특정 날짜(collected_at)의 match_raw 레코드 로드."""
    target_date = date.fromisoformat(run_date)
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(MatchRaw).where(
                cast(MatchRaw.collected_at, Date) == target_date
            )
        )
        return result.scalars().all()


async def _load_matches_for_patch(patch_version: str) -> list[MatchRaw]:
    """현재 패치의 match_raw 레코드 전체 로드."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(MatchRaw).where(MatchRaw.patch_version == patch_version)
        )
        return result.scalars().all()


async def _upsert_comps(comps_data: list[dict], patch_version: str) -> int:
    """comps 테이블에 upsert (name + patch_version 기준으로 기존 레코드 삭제 후 재삽입)."""
    async with AsyncSessionLocal() as session:
        for data in comps_data:
            comp = Comp(
                id=uuid.uuid4(),
                name=data["name"],
                tier=data["tier"],
                win_rate=data["win_rate"],
                top4_rate=data["top4_rate"],
                avg_placement=data["avg_placement"],
                play_rate=data["play_rate"],
                sample_count=data["sample_count"],
                core_units=data["core_units"],
                board_positions=data["board_positions"],
                recommended_augments=data.get("recommended_augments", {}),
                entry_conditions=data.get("entry_conditions", []),
                ai_summary=data.get("ai_summary"),
                patch_version=patch_version,
                updated_at=datetime.utcnow(),
            )
            session.add(comp)
        await session.commit()
    return len(comps_data)


# ---------------------------------------------------------------------------
# Airflow 태스크 진입점
# ---------------------------------------------------------------------------

async def cluster_and_store(run_date: str) -> int:
    """
    Airflow cluster_comps 태스크 진입점.
    match_raw 데이터를 클러스터링하여 집계 결과를 comps 테이블에 임시 저장.

    Returns:
        생성된 클러스터(컴프) 수.
    """
    patch_version = await get_latest_patch_version()
    matches = await _load_matches_for_date(run_date)

    if not matches:
        logger.warning("[cluster_and_store] run_date=%s 매치 없음", run_date)
        return 0

    all_participants: list[dict] = []
    for m in matches:
        all_participants.extend(m.participants)

    logger.info("[cluster_and_store] 총 참가자: %d", len(all_participants))

    clusters = _cluster_participants(all_participants)
    # MIN_SAMPLE_COUNT 미만 제거
    clusters = [c for c in clusters if len(c["participants"]) >= MIN_SAMPLE_COUNT]
    # 상위 TOP_COMP_COUNT 선정 (win_rate 기준)
    total_participants = len(all_participants)

    ranked = sorted(
        clusters,
        key=lambda c: sum(1 for p in c["participants"] if p.get("placement", 9) == 1)
        / len(c["participants"]),
        reverse=True,
    )[:TOP_COMP_COUNT]

    comps_data: list[dict] = []
    for i, cluster in enumerate(ranked):
        stats = _calc_stats(cluster, total_participants)
        core_units = _core_units_by_level(cluster)
        board_pos = _board_positions(cluster)
        traits = _extract_traits(cluster["participants"])
        tier = _assign_tier(stats["win_rate"])

        anchor = cluster.get("anchor", "unknown")
        name = f"{anchor.replace('TFT', '').replace('_', ' ').strip()} 컴프 #{i+1}"

        comps_data.append({
            "name": name,
            "tier": tier,
            "win_rate": stats["win_rate"],
            "top4_rate": stats["top4_rate"],
            "avg_placement": stats["avg_placement"],
            "play_rate": stats["play_rate"],
            "sample_count": stats["sample_count"],
            "core_units": core_units,
            "board_positions": board_pos,
            "traits": traits,
            "recommended_augments": {},
            "entry_conditions": [],
            "ai_summary": None,
            "_cluster": cluster,  # 이후 태스크를 위해 보존
        })

    count = await _upsert_comps(comps_data, patch_version)
    logger.info("[cluster_and_store] 저장된 컴프: %d", count)
    return count


async def calculate_and_upsert_stats(run_date: str) -> int:
    """
    Airflow calculate_stats 태스크 진입점.
    이미 저장된 comps 레코드의 통계를 재계산하고 upsert.
    (cluster_and_store에서 이미 통계를 저장했으므로 count 반환만 수행)

    Returns:
        처리된 컴프 수.
    """
    patch_version = await get_latest_patch_version()
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Comp).where(Comp.patch_version == patch_version)
        )
        comps = result.scalars().all()

    logger.info("[calculate_and_upsert_stats] patch=%s, 컴프 수=%d", patch_version, len(comps))
    return len(comps)


async def generate_summaries_for_top_comps(run_date: str) -> int:
    """
    Airflow generate_ai_summary 태스크 진입점.
    상위 컴프에 AI 전략 요약을 생성하고 comps.ai_summary 컬럼을 갱신.
    오늘/전날 비교를 통한 메타 변화 요약도 생성.

    Returns:
        AI 요약이 생성된 컴프 수.
    """
    from app.services.ai_summary import generate_comp_strategy_summary, generate_meta_change_summary
    from app.services.cache import cache_set

    patch_version = await get_latest_patch_version()

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Comp)
            .where(Comp.patch_version == patch_version)
            .order_by(Comp.win_rate.desc())
            .limit(TOP_COMP_COUNT)
        )
        comps = result.scalars().all()

    if not comps:
        logger.warning("[generate_summaries_for_top_comps] 컴프 없음")
        return 0

    updated = 0
    for comp in comps:
        traits = []  # comps 테이블에 traits 컬럼 없으므로 빈 리스트
        try:
            summary = await generate_comp_strategy_summary(
                name=comp.name,
                win_rate=comp.win_rate,
                avg_placement=comp.avg_placement,
                core_units=comp.core_units,
                traits=traits,
            )
            comp.ai_summary = summary
            updated += 1
        except Exception as exc:
            logger.warning("[generate_summaries] %s 요약 실패: %s", comp.name, exc)

    async with AsyncSessionLocal() as session:
        for comp in comps:
            if comp.ai_summary:
                await session.merge(comp)
        await session.commit()

    # 메타 변화 요약 생성 후 캐시
    comp_dicts = [
        {
            "name": c.name,
            "win_rate": c.win_rate,
            "tier": c.tier,
        }
        for c in comps
    ]
    try:
        meta_summary = await generate_meta_change_summary(
            current_comps=comp_dicts,
            patch_version=patch_version,
        )
        await cache_set("meta:summary:ai_text", meta_summary, ttl=6 * 3600)
        logger.info("[generate_summaries] 메타 변화 요약 캐시 저장 완료")
    except Exception as exc:
        logger.warning("[generate_summaries] 메타 변화 요약 실패: %s", exc)

    logger.info("[generate_summaries_for_top_comps] 완료: %d 컴프 요약", updated)
    return updated


# ---------------------------------------------------------------------------
# 독립 실행 (CLI)
# ---------------------------------------------------------------------------

async def run(target_date: str | None = None) -> None:
    """단독 실행 진입점."""
    patch_version = await get_latest_patch_version()

    if target_date is None or target_date == "yesterday":
        target_date = (date.today() - timedelta(days=1)).isoformat()

    logger.info("분석 날짜: %s / 패치: %s", target_date, patch_version)

    count = await cluster_and_store(run_date=target_date)
    logger.info("클러스터링 완료: %d 컴프", count)

    upserted = await calculate_and_upsert_stats(run_date=target_date)
    logger.info("통계 계산 완료: %d 컴프", upserted)

    updated = await generate_summaries_for_top_comps(run_date=target_date)
    logger.info("AI 요약 완료: %d 컴프", updated)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="TFT 컴프 분석 엔진")
    parser.add_argument(
        "--date",
        default="yesterday",
        help="분석 날짜 (yesterday 또는 YYYY-MM-DD, 기본값: yesterday)",
    )
    return parser.parse_args()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    args = _parse_args()
    asyncio.run(run(target_date=args.date))
    sys.exit(0)
