from dishka import Provider,Scope,provide_all
from app.infrastructure.external.http_service import HttpService
from app.infrastructure.external.google import GoogleService
from app.infrastructure.external.spotify import SpotifyPublicService,SpotifyService


class ExternalProvider(Provider):
    scope = Scope.REQUEST
    
    interactors = provide_all(
        HttpService,
        GoogleService,
        SpotifyPublicService,
        SpotifyService
    )