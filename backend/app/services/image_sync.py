"""
TFT 이미지 URL 동기화 서비스

이미지 파일은 저장하지 않고 CDN URL만 DB에 저장한다.

소스:
  - Community Dragon (비공식): 챔피언 (현재 세트 정확한 cost/traits/이미지), 증강
  - Data Dragon (Riot 공식): 아이템

CLI:
  python -m app.services.image_sync           # 패치 변경 시에만 동기화
  python -m app.services.image_sync --force   # 강제 전체 동기화
  python -m app.services.image_sync --check   # 패치 버전 확인만
"""
import argparse
import asyncio
import logging
import re
import sys

import httpx
from sqlalchemy.dialects.postgresql import insert

from app.database import AsyncSessionLocal
from app.models.augment import Augment
from app.models.champion import Champion
from app.models.item import Item
from app.services.riot_api import get_latest_patch_version

logger = logging.getLogger(__name__)

DDRAGON_BASE = "https://ddragon.leagueoflegends.com/cdn"
CDRAGON_BASE = "https://raw.communitydragon.org/latest"


# ---------------------------------------------------------------------------
# Community Dragon 공통 유틸
# ---------------------------------------------------------------------------

def _cdragon_asset_url(path: str) -> str:
    """
    CDragon 에셋 경로 → 실제 URL 변환.
    예: ASSETS/Characters/TFT14_Annie/HUD/...png
        → https://raw.communitydragon.org/latest/game/assets/characters/tft14_annie/hud/...png
    예: /lol-game-data/assets/ASSETS/TFT/Augments/...
        → https://raw.communitydragon.org/latest/game/assets/tft/augments/...
    """
    p = path.lower()
    for prefix in ["/lol-game-data/assets/", "lol-game-data/assets/"]:
        if p.startswith(prefix):
            p = p[len(prefix):]
            break
    return f"{CDRAGON_BASE}/game/{p}"


# ---------------------------------------------------------------------------
# 챔피언 (Community Dragon 현재 세트 데이터 사용)
# ---------------------------------------------------------------------------

def _build_cdragon_champion_url(champ_id: str) -> str | None:
    """
    apiName으로 CDragon HUD 이미지 URL 생성.
    예: TFT16_Fizz → tft16_fizz
        → https://raw.communitydragon.org/latest/game/assets/characters/tft16_fizz/hud/tft16_fizz_square.tft_set16.png
    """
    lower = champ_id.lower()
    match = re.match(r"tft(\d+)_", lower)
    if not match:
        return None
    set_num = match.group(1)
    return (
        f"{CDRAGON_BASE}/game/assets/characters/{lower}/hud/"
        f"{lower}_square.tft_set{set_num}.png"
    )


def sync_champion_images_from_cdragon(tft_data: dict) -> list[dict]:
    """
    cdragon/tft/en_us.json 에서 현재 세트(가장 높은 세트 번호) 챔피언 목록을 파싱.
    반환값: DB upsert용 dict 리스트
    """
    sets: dict = tft_data.get("sets", {})
    if not sets:
        logger.warning("[sync_champion_images] CDragon sets 키 없음")
        return []

    # 가장 높은 세트 번호 = 현재 세트
    current_set_key = str(max(int(k) for k in sets.keys()))
    current_set = sets[current_set_key]
    champions_raw: list = current_set.get("champions", [])

    logger.info("[sync_champion_images] 현재 세트: %s, 챔피언 수: %d", current_set_key, len(champions_raw))

    rows = []
    for champ in champions_raw:
        champ_id: str = champ.get("apiName", "")
        if not champ_id:
            continue

        cost: int = champ.get("cost", 0)
        traits_raw = champ.get("traits", [])
        traits = [t if isinstance(t, str) else t.get("name", "") for t in traits_raw]

        # cost 0 이거나 traits 없는 항목은 환경 유닛(엘더 드래곤, 골렘, 아타칸, 타워 등) → 제외
        if cost < 1 or not traits:
            continue

        name: str = champ.get("name", champ_id)

        # apiName에서 직접 URL 구성: TFT16_Fizz → CDragon HUD URL
        image_url = _build_cdragon_champion_url(champ_id)

        rows.append({
            "id": champ_id,
            "name": name,
            "cost": cost,
            "traits": traits,
            "best_items": {},
            "item_reasoning": {},
            "image_url": image_url,
            "splash_url": None,
        })

    return rows


async def _upsert_champions(rows: list[dict]) -> int:
    if not rows:
        logger.warning("[sync_champion_images] 챔피언 데이터 없음")
        return 0

    async with AsyncSessionLocal() as session:
        stmt = insert(Champion).values(rows)
        stmt = stmt.on_conflict_do_update(
            index_elements=["id"],
            set_={
                "name": stmt.excluded.name,
                "cost": stmt.excluded.cost,
                "traits": stmt.excluded.traits,
                "image_url": stmt.excluded.image_url,
                "splash_url": stmt.excluded.splash_url,
            },
        )
        await session.execute(stmt)
        await session.commit()

    logger.info("[sync_champion_images] %d개 챔피언 upsert 완료", len(rows))
    return len(rows)


# ---------------------------------------------------------------------------
# 아이템 (Data Dragon 사용)
# ---------------------------------------------------------------------------

async def sync_item_images(patch_version: str) -> int:
    url = f"{DDRAGON_BASE}/{patch_version}/data/en_US/tft-item.json"
    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.get(url)
        resp.raise_for_status()
    data: dict = resp.json().get("data", {})

    rows = []
    for item_id, info in data.items():
        image_full = info.get("image", {}).get("full", f"{item_id}.png")
        image_url = f"{DDRAGON_BASE}/{patch_version}/img/tft-item/{image_full}"
        from_field = info.get("from", [])
        is_component = not bool(from_field)

        rows.append({
            "id": str(item_id),
            "name": info.get("name", str(item_id)),
            "description": info.get("desc") or info.get("description"),
            "components": from_field if isinstance(from_field, list) else [],
            "image_url": image_url,
            "is_component": is_component,
        })

    if not rows:
        logger.warning("[sync_item_images] 아이템 데이터 없음")
        return 0

    async with AsyncSessionLocal() as session:
        stmt = insert(Item).values(rows)
        stmt = stmt.on_conflict_do_update(
            index_elements=["id"],
            set_={
                "name": stmt.excluded.name,
                "description": stmt.excluded.description,
                "components": stmt.excluded.components,
                "image_url": stmt.excluded.image_url,
                "is_component": stmt.excluded.is_component,
            },
        )
        await session.execute(stmt)
        await session.commit()

    logger.info("[sync_item_images] %d개 아이템 upsert 완료", len(rows))
    return len(rows)


# ---------------------------------------------------------------------------
# 증강 (Community Dragon 사용)
# ---------------------------------------------------------------------------

def _parse_augments_from_cdragon(tft_data: dict) -> list[dict]:
    augments_raw: list = tft_data.get("augments", [])
    rows = []
    for aug in augments_raw:
        aug_id = str(aug.get("apiName") or aug.get("id") or "")
        if not aug_id:
            continue

        name = aug.get("name", aug_id)
        icon_path: str = aug.get("iconPath") or aug.get("iconSmall") or ""
        image_url = _cdragon_asset_url(icon_path) if icon_path else None
        tier = _infer_augment_tier(name, aug.get("tier"))
        description = aug.get("desc") or aug.get("description")

        rows.append({
            "id": aug_id,
            "name": name,
            "tier": tier,
            "description": description,
            "image_url": image_url,
            "comp_synergy": [],
        })
    return rows


async def _upsert_augments(rows: list[dict]) -> int:
    if not rows:
        logger.warning("[sync_augment_images] 증강 데이터 없음")
        return 0

    async with AsyncSessionLocal() as session:
        stmt = insert(Augment).values(rows)
        stmt = stmt.on_conflict_do_update(
            index_elements=["id"],
            set_={
                "name": stmt.excluded.name,
                "tier": stmt.excluded.tier,
                "description": stmt.excluded.description,
                "image_url": stmt.excluded.image_url,
            },
        )
        await session.execute(stmt)
        await session.commit()

    logger.info("[sync_augment_images] %d개 증강 upsert 완료", len(rows))
    return len(rows)


def _infer_augment_tier(name: str, tier_field=None) -> str:
    """tier 필드 또는 이름에서 Silver/Gold/Prismatic 추론."""
    if isinstance(tier_field, int):
        return {1: "Silver", 2: "Gold", 3: "Prismatic"}.get(tier_field, "Silver")
    if isinstance(tier_field, str) and tier_field in ("Silver", "Gold", "Prismatic"):
        return tier_field
    name_lower = name.lower()
    if "prismatic" in name_lower:
        return "Prismatic"
    if "gold" in name_lower:
        return "Gold"
    return "Silver"


# ---------------------------------------------------------------------------
# 전체 동기화 / 패치 체크
# ---------------------------------------------------------------------------

async def sync_all_images(patch_version: str) -> None:
    """
    CDragon en_us.json을 한 번만 fetch하여 챔피언·증강을 동기화.
    아이템은 Data Dragon에서 별도 fetch.
    """
    # CDragon 통합 데이터 1회 fetch
    cdragon_url = f"{CDRAGON_BASE}/cdragon/tft/en_us.json"
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.get(cdragon_url)
            resp.raise_for_status()
        tft_data: dict = resp.json()
    except Exception as exc:
        logger.error("[sync_all_images] CDragon 조회 실패: %s", exc)
        tft_data = {}

    # 챔피언 (현재 세트)
    champ_rows = sync_champion_images_from_cdragon(tft_data)
    champ_count = await _upsert_champions(champ_rows)

    # 아이템 (Data Dragon)
    item_count = await sync_item_images(patch_version)

    # 증강 (CDragon)
    aug_rows = _parse_augments_from_cdragon(tft_data)
    aug_count = await _upsert_augments(aug_rows)

    logger.info(
        "동기화 완료 — 챔피언 %d개, 아이템 %d개, 증강 %d개",
        champ_count, item_count, aug_count,
    )


async def check_patch_changed() -> bool:
    """
    Data Dragon 최신 버전과 DB 저장 아이템 이미지 버전 비교.
    (챔피언 이미지는 CDragon URL이므로 버전 비교 불가 → 아이템으로 대체)
    다르면(또는 DB 비어있으면) True 반환.
    """
    latest = await get_latest_patch_version()

    async with AsyncSessionLocal() as session:
        from sqlalchemy import select
        # 아이템 이미지 URL에는 DDragon 버전이 포함됨
        result = await session.execute(
            select(Item.image_url).where(Item.image_url.isnot(None)).limit(1)
        )
        row = result.scalar_one_or_none()

    if row is None:
        # 아이템이 없으면 챔피언도 확인
        async with AsyncSessionLocal() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(Champion.image_url).where(Champion.image_url.isnot(None)).limit(1)
            )
            champ_row = result.scalar_one_or_none()
        if champ_row is None:
            logger.info("[check_patch_changed] DB 비어있음 → 동기화 필요")
            return True
        # 챔피언만 있고 아이템 없으면 동기화 필요
        return True

    # 아이템 image_url에서 버전 추출: https://ddragon.../cdn/{version}/img/...
    match = re.search(r"/cdn/([^/]+)/", row)
    db_version = match.group(1) if match else None

    changed = db_version != latest
    logger.info(
        "[check_patch_changed] DB 버전=%s, 최신=%s → %s",
        db_version, latest, "변경됨" if changed else "동일",
    )
    return changed


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

async def _main(force: bool, check_only: bool) -> None:
    if check_only:
        changed = await check_patch_changed()
        print("패치 변경됨" if changed else "패치 동일")
        return

    patch_version = await get_latest_patch_version()
    if not force:
        if not await check_patch_changed():
            logger.info("패치 변경 없음 — 동기화 스킵 (--force 로 강제 실행)")
            return

    logger.info("이미지 동기화 시작 (패치: %s)", patch_version)
    await sync_all_images(patch_version)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    parser = argparse.ArgumentParser(description="TFT 이미지 URL 동기화")
    parser.add_argument("--force", action="store_true", help="패치 변경 무관하게 강제 동기화")
    parser.add_argument("--check", action="store_true", help="패치 버전 확인만")
    args = parser.parse_args()

    asyncio.run(_main(force=args.force, check_only=args.check))
    sys.exit(0)
