from dishka import Provider, make_async_container,AsyncContainer
from app.config.di.providers.db_provider import DataBaseProvider
from app.config.di.providers.mapper_provider import MapperProvider
from app.config.di.providers.service_provider import ServiceProvider
from app.config.di.providers.auth_provider import AuthProvider
from app.config.di.providers.gateway_provider import GatewayProvider

def provide_set() -> list[Provider]:
    return [
        DataBaseProvider(),
        MapperProvider(),
        ServiceProvider(),
        AuthProvider(),
        GatewayProvider(),
    ]


def get_container() -> AsyncContainer:
    return make_async_container(*provide_set())