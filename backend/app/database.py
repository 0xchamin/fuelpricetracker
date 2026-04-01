from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/fuelpricetracker"
    cesium_ion_token: str = ""
    clerk_publishable_key: str = ""
    clerk_frontend_api: str = ""

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()

db_url = settings.database_url
db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")
db_url = db_url.replace("?sslmode=require", "")
db_url = db_url.replace("&sslmode=require", "")
db_url = db_url.replace("?channel_binding=require", "")
db_url = db_url.replace("&channel_binding=require", "")

engine = create_async_engine(
    db_url,
    echo=True,
    connect_args={"ssl": True} if "neon.tech" in db_url else {},
    pool_pre_ping=True,
)

async_session = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with async_session() as session:
        yield session