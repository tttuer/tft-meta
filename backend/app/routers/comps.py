import uuid
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.comp import Comp
from app.schemas.responses import BoardSchema, CompDetailSchema, CompSummarySchema
from app.services.cache import cache_get, cache_set

router = APIRouter(prefix="/api/v1/comps", tags=["comps"])

CACHE_TTL = 30 * 60  # 30 minutes


@router.get("", response_model=list[CompSummarySchema])
async def list_comps(
    tier: Literal["S", "A", "B", "C"] | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    cache_key = f"comps:list:{tier}:{limit}"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    stmt = select(Comp).order_by(Comp.tier, Comp.win_rate.desc()).limit(limit)
    if tier:
        stmt = stmt.where(Comp.tier == tier)

    result = await db.execute(stmt)
    comps = result.scalars().all()
    data = [CompSummarySchema.model_validate(c).model_dump() for c in comps]
    await cache_set(cache_key, data, CACHE_TTL)
    return data


@router.get("/{comp_id}", response_model=CompDetailSchema)
async def get_comp(comp_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    cache_key = f"comps:detail:{comp_id}"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    comp = await db.get(Comp, comp_id)
    if not comp:
        raise HTTPException(status_code=404, detail="Comp not found")

    data = CompDetailSchema.model_validate(comp).model_dump()
    await cache_set(cache_key, data, CACHE_TTL)
    return data


@router.get("/{comp_id}/board", response_model=BoardSchema)
async def get_comp_board(comp_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    comp = await db.get(Comp, comp_id)
    if not comp:
        raise HTTPException(status_code=404, detail="Comp not found")

    return BoardSchema(
        comp_id=comp.id,
        comp_name=comp.name,
        board_positions=comp.board_positions,
    )
