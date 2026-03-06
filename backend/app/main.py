from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import check_db_connection
from app.routers import augments, champions, comps, meta
from app.schemas.responses import HealthSchema

app = FastAPI(
    title="TFT Meta Advisor API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(comps.router)
app.include_router(champions.router)
app.include_router(augments.router)
app.include_router(meta.router)


@app.get("/health", response_model=HealthSchema, tags=["health"])
async def health():
    db_ok = await check_db_connection()
    return HealthSchema(
        status="ok" if db_ok else "degraded",
        db_connected=db_ok,
    )
