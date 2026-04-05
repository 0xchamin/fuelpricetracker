from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from geoalchemy2.functions import ST_MakeEnvelope, ST_Within
from app.database import get_db
from app.models import Station
from app.schemas import StationResponse
from sqlalchemy import select, func
from sqlalchemy import select, func, exists
from app.models import Station, Price

router = APIRouter(prefix="/api/stations", tags=["stations"])


@router.get("", response_model=list[StationResponse])
async def get_stations(
    west: float = Query(...), south: float = Query(...),
    east: float = Query(...), north: float = Query(...),
    station_type: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    latest_price = (
        select(func.max(Price.submitted_at))
        .where(Price.station_id == Station.id)
        .correlate(Station)
        .scalar_subquery()
    )
    price_exists = exists().where(Price.station_id == Station.id).correlate(Station)
    stmt = (
        select(Station, price_exists.label("has_prices"), latest_price.label("last_price_at"))
        .where(ST_Within(Station.geom, ST_MakeEnvelope(west, south, east, north, 4326)))
    )
    if station_type:
        stmt = stmt.where(Station.station_type == station_type)
    result = await db.execute(stmt)
    rows = result.all()
    return [
        {
            "id": s.id, "name": s.name, "brand": s.brand,
            "lat": s.lat, "lng": s.lng, "station_type": s.station_type,
            "county": s.county, "has_prices": hp, "last_price_at": lp,
        }
        for s, hp, lp in rows
    ]


@router.get("/search", response_model=list[StationResponse])
async def search_stations(
    q: str = Query(..., min_length=2, description="Search query"),
    lat: float | None = Query(None, description="Latitude for distance sorting"),
    lng: float | None = Query(None, description="Longitude for distance sorting"),
    limit: int = Query(10, le=50),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Station).where(Station.name.ilike(f"%{q}%"))

    if lat is not None and lng is not None:
        point = func.ST_SetSRID(func.ST_MakePoint(lng, lat), 4326)
        stmt = stmt.order_by(func.ST_Distance(Station.geom, point))
    else:
        stmt = stmt.order_by(Station.name)

    stmt = stmt.limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()
