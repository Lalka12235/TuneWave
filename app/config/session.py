from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from typing import Generator
from app.config.settings import settings 
from app.config.log_config import logger

class DBSessionManager:
    """Инкапсулирует создание Engine и SessionLocal."""
    
    def __init__(self, db_url: str):
        self.engine = create_engine(
            url=db_url,
            echo=False,
            pool_pre_ping=True 
        )
        
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )

db_manager = DBSessionManager(settings.database.sync_db_url)


def get_db() -> Generator[Session, None, None]:
    """
    Предоставляет сессию БД и закрывает её после запроса.
    """
    db = db_manager.SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        logger.error("Database error occurred. %r",e, exc_info=True)
        db.rollback()
        raise
    finally:
        db.close()