from dishka import Provider,Scope,provide_all,provide
from fastapi import Request
from app.domain.entity.user import UserEntity
from app.domain.exceptions.user_exception import UserNotAuthorized
from app.infrastructure.auth.indentity_provider import IndentityProvider
from app.infrastructure.auth.session_service import SessionService
from app.presentation.auth.auth import AuthService


class AuthProvider(Provider):
    scope = Scope.REQUEST
    
    @provide(scope=Scope.REQUEST)
    def get_current_user(request: Request) -> UserEntity:
        user = getattr(request.state, "user", None)
        if not user:
            raise UserNotAuthorized()
        return user
    
    interactors = provide_all(
        IndentityProvider,
        SessionService,
        AuthService
    )