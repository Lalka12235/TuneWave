from sqlalchemy import create_engine,Engine
from sqlalchemy.orm import Session, sessionmaker
from typing import Iterator
from app.config.settings import settings


def get_engine() -> Engine:
    return create_engine(
        url=settings.database.sync_db_url,
        echo=False,
        pool_pre_ping=True
    )

def get_sessionmaker(engine: Engine) -> sessionmaker[Session]:
    session_factory = sessionmaker(
        bind=engine
    )
    return session_factory

def get_session(session_factory: sessionmaker[Session]) -> Iterator[Session]:
    with session_factory() as session:
        yield session
