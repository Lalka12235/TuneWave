from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config.settings import settings

if settings.MODE == 'test':
    engine = create_engine(
        url=settings.test_sync_db_url,
        echo=False,
    )
else:
    engine = create_engine(
        url=settings.sync_db_url,
        echo=False, #True для отладки
    )

SessionLocal = sessionmaker(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()