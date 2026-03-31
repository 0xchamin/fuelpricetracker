from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.database import engine, Base
from app.database import settings

from fastapi.responses import FileResponse
from app.routers.stations import router as stations_router

from app.routers.prices import router as prices_router
from app.auth import init_jwks

from app.routers.votes import router as votes_router

from sqlalchemy import func, select
from app.database import get_db, async_session
from app.models import Price
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import FastAPI, Depends




@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    init_jwks(settings.clerk_frontend_api)
    yield

app = FastAPI(title="Fuel Price Tracker", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(stations_router)
app.include_router(prices_router)
app.include_router(votes_router)


app.mount("/assets", StaticFiles(directory="frontend"), name="frontend")

@app.get("/")
async def root():
    return FileResponse("frontend/index.html")

@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.get("/api/config")
async def config():
    return {
        "cesium_ion_token": settings.cesium_ion_token,
        "clerk_publishable_key": settings.clerk_publishable_key,
        "clerk_frontend_api": settings.clerk_frontend_api,
    }

@app.get("/api/stats")
async def stats(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(func.count(Price.id)))
    total_prices = result.scalar()
    return {"total_prices": total_prices}
