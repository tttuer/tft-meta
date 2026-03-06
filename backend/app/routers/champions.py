from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.champion import Champion
from app.schemas.responses import ChampionSchema

router = APIRouter(prefix="/api/v1/champions", tags=["champions"])


@router.get("", response_model=list[ChampionSchema])
async def list_champions(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Champion).order_by(Champion.cost, Champion.name))
    return result.scalars().all()
