from dishka import Provider, Scope, provide
from redis.asyncio import Redis
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import Engine
from typing import Iterator

from app.config.session import get_engine, get_sessionmaker, get_session
from app.infrastructure.redis.redis import get_redis_client


class DataBaseProvider(Provider):
    @provide(scope=Scope.APP)
    def provide_engine(self) -> Engine:
        return get_engine()

    @provide(scope=Scope.APP)
    def provide_sessionmaker(self, engine: Engine) -> sessionmaker[Session]:
        return get_sessionmaker(engine)

    @provide(scope=Scope.REQUEST, provides=Session)
    def provide_session(self, session_factory: sessionmaker[Session]) -> Iterator[Session]:
        yield from get_session(session_factory)

    @provide(scope=Scope.APP)
    async def redis_client(self) -> Redis:
        return await get_redis_client()