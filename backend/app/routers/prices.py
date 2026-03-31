from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import Price, Station
from app.schemas import PriceSubmission, PriceResponse
from app.auth import get_current_user
from datetime import datetime, timezone

router = APIRouter(prefix="/api/prices", tags=["prices"])

# Simple in-memory rate limiting for anonymous users
_anon_submissions: dict[str, list[datetime]] = {}
ANON_RATE_LIMIT = 5  # max submissions per hour per IP


def check_anon_rate_limit(ip: str):
    now = datetime.now(timezone.utc)
    if ip not in _anon_submissions:
        _anon_submissions[ip] = []

    # Remove entries older than 1 hour
    _anon_submissions[ip] = [t for t in _anon_submissions[ip] if (now - t).seconds < 3600]

    if len(_anon_submissions[ip]) >= ANON_RATE_LIMIT:
        raise HTTPException(status_code=429, detail="Too many submissions. Please sign in or try again later.")

    _anon_submissions[ip].append(now)


@router.post("", response_model=PriceResponse)
async def submit_price(
    submission: PriceSubmission,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    # Check station exists
    station = await db.get(Station, submission.station_id)
    if not station:
        raise HTTPException(status_code=404, detail="Station not found")

    # Check auth
    user_id = get_current_user(request)
    is_verified = user_id is not None

    # Rate limit anonymous users
    if not is_verified:
        check_anon_rate_limit(request.client.host)

    observed = submission.observed_at
    if observed:
        observed_dt = datetime(observed.year, observed.month, observed.day, tzinfo=timezone.utc)
    else:
        observed_dt = datetime.now(timezone.utc)

    price = Price(
        station_id=submission.station_id,
        fuel_type=submission.fuel_type,
        price=submission.price,
        user_id=user_id,
        is_verified=is_verified,
        upvote_count=0,
        is_credible=False,
        observed_at=observed_dt,
    )

    

    db.add(price)
    await db.commit()
    await db.refresh(price)

    return price


@router.get("/station/{station_id}", response_model=list[PriceResponse])
async def get_station_prices(
    station_id: int,
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Price)
        .where(Price.station_id == station_id)
        .order_by(Price.submitted_at.desc())
        .limit(20)
    )
    result = await db.execute(stmt)
    prices = result.scalars().all()
    return prices
