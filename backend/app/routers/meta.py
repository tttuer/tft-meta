from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.comp import Comp
from app.schemas.responses import CompSummarySchema, MetaSummarySchema
from app.services.ai_summary import generate_meta_summary
from app.services.cache import cache_get, cache_set
from app.services.riot_api import get_latest_patch_version

router = APIRouter(prefix="/api/v1/meta", tags=["meta"])

CACHE_TTL = 6 * 60 * 60  # 6 hours


@router.get("/summary", response_model=MetaSummarySchema)
async def meta_summary(db: AsyncSession = Depends(get_db)):
    cache_key = "meta:summary"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    patch_version = await get_latest_patch_version()

    result = await db.execute(
        select(Comp).where(Comp.tier.in_(["S", "A"])).order_by(Comp.win_rate.desc()).limit(5)
    )
    top_comps = result.scalars().all()

    # DB에 저장된 요약이 없으면 OpenRouter로 실시간 생성
    if top_comps and top_comps[0].ai_summary:
        ai_summary = top_comps[0].ai_summary
    else:
        comp_dicts = [
            {"name": c.name, "tier": c.tier, "win_rate": c.win_rate}
            for c in top_comps
        ]
        ai_summary = await generate_meta_summary(comp_dicts, patch_version)

    data = MetaSummarySchema(
        patch_version=patch_version,
        generated_at=datetime.utcnow().isoformat(),
        top_comps=[CompSummarySchema.model_validate(c) for c in top_comps],
        ai_summary=ai_summary,
    ).model_dump()

    await cache_set(cache_key, data, CACHE_TTL)
    return data
