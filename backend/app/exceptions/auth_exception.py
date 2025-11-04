class AuthenticationError(Exception):
    """Базовый класс для всех ошибок аутентификации."""
    def __init__(self, detail: str):
        super().__init__(detail)

class InvalidTokenError(AuthenticationError):
    """Ошибка невалидного токена."""
    def __init__(self, detail: str = "Недействительный или истекший токен"):
        super().__init__(detail)

class TokenDecodeError(AuthenticationError):
    """Ошибка декодирования токена."""
    def __init__(self, detail: str = "Ошибка при декодировании токена"):
        super().__init__(detail)

class MissingTokenError(AuthenticationError):
    """Ошибка отсутствия токена."""
    def __init__(self, detail: str = "Отсутствует токен аутентификации"):
        super().__init__(detail)

class UserBannedError(Exception):
    """Ошибка доступа забаненного пользователя."""
    def __init__(self, detail: str = "Ваш аккаунт заблокирован"):
        super().__init__(
            detail=detail
        )

class OAuth2Error(Exception):
    """Ошибка OAuth2 аутентификации."""
    def __init__(self, detail: str = "Ошибка OAuth2 аутентификации"):
        super().__init__(
            detail=detail
        )
