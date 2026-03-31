from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from geoalchemy2.functions import ST_MakeEnvelope, ST_Within
from app.database import get_db
from app.models import Station
from app.schemas import StationResponse
from sqlalchemy import select, func


router = APIRouter(prefix="/api/stations", tags=["stations"])


@router.get("", response_model=list[StationResponse])
async def get_stations(
    west: float = Query(..., description="Western longitude"),
    south: float = Query(..., description="Southern latitude"),
    east: float = Query(..., description="Eastern longitude"),
    north: float = Query(..., description="Northern latitude"),
    station_type: str | None = Query(None, description="Filter by station type: fuel, ev, both"),
    db: AsyncSession = Depends(get_db),
):
    bbox = ST_MakeEnvelope(west, south, east, north, 4326)
    stmt = select(Station).where(ST_Within(Station.geom, bbox))

    if station_type:
        stmt = stmt.where(Station.station_type == station_type)

    result = await db.execute(stmt)
    stations = result.scalars().all()
    return stations


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
