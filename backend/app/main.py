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
from app.models import Price, Station
from app.routers.push import router as push_router
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timezone
from app.models import PushSubscription



scheduler = AsyncIOScheduler()

async def send_reminders():
    from app.routers.push import send_push
    from datetime import timedelta
    freq_map = {"daily":1, "3days":3, "weekly":7, "2weeks":14}
    async with async_session() as db:
        result = await db.execute(select(PushSubscription))
        subs = result.scalars().all()
        now = datetime.now(timezone.utc)
        for sub in subs:
            days = freq_map.get(sub.frequency, 7)
            if (now - sub.created_at).days % days == 0:
                send_push(sub, {"title": "Fuel Price Tracker", "body": "Got a minute? Submit a fuel price near you!"})




@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    init_jwks(settings.clerk_frontend_api)
    scheduler.add_job(send_reminders, "cron", hour=10, minute=0)
    scheduler.start()

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
app.include_router(push_router)


@app.get("/sw.js")
async def service_worker():
    return FileResponse("frontend/sw.js", media_type="application/javascript")

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


@app.get("/api/prices/recent")
async def recent_prices(limit: int = 10, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(Price, Station.name, Station.brand)
        .join(Station, Price.station_id == Station.id)
        .order_by(Price.submitted_at.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    rows = result.all()
    return [
        {
            "station_name": name,
            "brand": brand,
            "fuel_type": price.fuel_type,
            "price": price.price,
            "is_verified": price.is_verified,
            "submitted_at": price.submitted_at.isoformat(),
        }
        for price, name, brand in rows
    ]
