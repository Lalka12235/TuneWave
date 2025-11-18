from dishka import make_container, Container, Provider
from app.config.di.providers.db_provider import DataBaseProvider
from app.config.di.providers.mapper_provider import MapperProvider
from app.config.di.providers.interface_provider import InterfaceProvider
from app.config.di.providers.service_provider import ServiceProvider
from app.config.di.providers.auth_provider import AuthProvider
from app.config.di.providers.repository_provider import RepositoryProvider

def provide_set() -> list[Provider]:
    return [
        DataBaseProvider(),
        MapperProvider(),
        InterfaceProvider(),
        ServiceProvider(),
        AuthProvider(),
        RepositoryProvider(),
    ]


def get_container() -> Container:
    return make_container(*provide_set())