from datetime import datetime
from sqlalchemy import String, Float, Boolean, Integer, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from geoalchemy2 import Geometry
from app.database import Base


class Station(Base):
    __tablename__ = "stations"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    brand: Mapped[str | None] = mapped_column(String(100))
    lat: Mapped[float] = mapped_column(Float)
    lng: Mapped[float] = mapped_column(Float)
    geom: Mapped[str] = mapped_column(Geometry(geometry_type="POINT", srid=4326))
    county: Mapped[str | None] = mapped_column(String(100))
    station_type: Mapped[str] = mapped_column(String(20), default="fuel")  # fuel / ev / both
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    prices: Mapped[list["Price"]] = relationship(back_populates="station", cascade="all, delete-orphan")


class Price(Base):
    __tablename__ = "prices"

    id: Mapped[int] = mapped_column(primary_key=True)
    station_id: Mapped[int] = mapped_column(ForeignKey("stations.id"))
    fuel_type: Mapped[str] = mapped_column(String(20))  # petrol, diesel, lpg, e10, etc.
    price: Mapped[float] = mapped_column(Float)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    user_id: Mapped[str | None] = mapped_column(String(255))  # clerk_id, nullable for anonymous
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    upvote_count: Mapped[int] = mapped_column(Integer, default=0)
    is_credible: Mapped[bool] = mapped_column(Boolean, default=False)

    station: Mapped["Station"] = relationship(back_populates="prices")
    votes: Mapped[list["Vote"]] = relationship(back_populates="price", cascade="all, delete-orphan")


class Vote(Base):
    __tablename__ = "votes"

    id: Mapped[int] = mapped_column(primary_key=True)
    price_id: Mapped[int] = mapped_column(ForeignKey("prices.id"))
    user_id: Mapped[str] = mapped_column(String(255))  # clerk_id
    vote_type: Mapped[str] = mapped_column(String(10))  # upvote / reject
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    price: Mapped["Price"] = relationship(back_populates="votes")


class User(Base):
    __tablename__ = "users"

    clerk_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    tier: Mapped[str] = mapped_column(String(10), default="free")  # free / paid
    questions_used: Mapped[int] = mapped_column(Integer, default=0)
    questions_reset_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
