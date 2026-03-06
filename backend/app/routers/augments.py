from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.augment import Augment
from app.schemas.responses import AugmentSchema

router = APIRouter(prefix="/api/v1/augments", tags=["augments"])


@router.get("", response_model=list[AugmentSchema])
async def list_augments(
    comp_id: str | None = Query(None, description="Filter augments by comp ID synergy"),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Augment).order_by(Augment.tier, Augment.name)
    result = await db.execute(stmt)
    augments = result.scalars().all()

    if comp_id:
        augments = [
            a for a in augments
            if any(s.get("comp_id") == comp_id for s in a.comp_synergy)
        ]

    return augments
