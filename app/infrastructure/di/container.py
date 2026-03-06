from dishka import Provider, make_async_container,AsyncContainer
from app.infrastructure.di.providers.db_provider import DataBaseProvider
from app.infrastructure.di.providers.gateway_provider import GatewayProvider
from app.infrastructure.di.providers.usecase_provider import UseCaseProvider

def provide_set() -> list[Provider]:
    return [
        DataBaseProvider(),
        GatewayProvider(),
        UseCaseProvider(),
    ]


def get_container() -> AsyncContainer:
    return make_async_container(*provide_set())