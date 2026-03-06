from dishka import Provider, make_async_container,AsyncContainer
from app.infrastructure.di.providers import DataBaseProvider,GatewayProvider,UseCaseProvider,ExternalProvider,AuthProvider


def provide_set() -> list[Provider]:
    return [
        DataBaseProvider(),
        GatewayProvider(),
        UseCaseProvider(),
        ExternalProvider(),
        AuthProvider(),
    ]


def get_container() -> AsyncContainer:
    return make_async_container(*provide_set())