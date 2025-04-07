from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.config.settings import settings

engine = create_async_engine(
    url=settings.async_db_url,
    echo=True,
)

AsyncSessionLocal = async_sessionmaker(bind=engine)