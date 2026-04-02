from pydantic import BaseModel, Field, field_validator
from datetime import datetime, date, timedelta, timezone


class StationResponse(BaseModel):
    id: int
    name: str
    brand: str | None
    lat: float
    lng: float
    station_type: str
    county: str | None
    has_prices: bool = False

    model_config = {"from_attributes": True}



class PriceSubmission(BaseModel):
    station_id: int
    fuel_type: str = Field(..., pattern="^(petrol|diesel|lpg|e10|ev)$")
    price: float = Field(..., gt=0, lt=10)
    observed_at: date | None = None

    @field_validator("observed_at")
    @classmethod
    def validate_observed_at(cls, v):
        if v is None:
            return None
        today = date.today()
        if v > today:
            raise ValueError("Date cannot be in the future")
        if v < today - timedelta(days=30):
            raise ValueError("Date cannot be more than 30 days ago")
        return v


class PriceResponse(BaseModel):
    id: int
    station_id: int
    fuel_type: str
    price: float
    submitted_at: datetime
    observed_at: datetime
    is_verified: bool
    upvote_count: int
    is_credible: bool

    model_config = {"from_attributes": True}


class VoteSubmission(BaseModel):
    vote_type: str = Field(..., pattern="^(upvote|reject)$")


class VoteResponse(BaseModel):
    id: int
    price_id: int
    user_id: str
    vote_type: str
    created_at: datetime

    model_config = {"from_attributes": True}
