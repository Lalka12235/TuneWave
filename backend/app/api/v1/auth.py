from fastapi import APIRouter,Depends, Query,HTTPException,status
from sqlalchemy.orm import Session
from fastapi.responses import RedirectResponse
from typing import Annotated
from app.schemas.user import UserResponse, Token, GoogleOAuthData
from app.schemas.config_schemas import FrontendConfig
from app.services.user import UserService
from app.auth.auth import get_current_user
from app.config.session import get_db
from app.models.user import User
import httpx
from app.config.settings import settings
import jwt

auth = APIRouter(
    tags=['auth'],
    prefix='/auth'
)

@auth.get('/config', response_model=FrontendConfig)
def get_frontend_config() -> FrontendConfig:
    """
    Возвращает публичные конфигурационные данные, необходимые фронтенду.
    """
    return FrontendConfig(
        google_client_id=settings.GOOGLE_CLIENT_ID,
        google_redirect_uri=settings.GOOGLE_REDIRECT_URI,
        google_scopes=settings.GOOGLE_SCOPES,
        spotify_client_id=settings.SPOTIFY_CLIENT_ID, # Будет None, если не заполнен в .env
        spotify_redirect_uri=settings.SPOTIFY_REDIRECT_URI,
        spotify_scopes=settings.SPOTIFY_SCOPES,
    )

@auth.get('/me',response_model=UserResponse)
async def get_me(
    db: Annotated[Session,Depends(get_db)],
    user: Annotated[User,Depends(get_current_user)]
) -> UserResponse:
    """
    Получает профиль текущего аутентифицированного пользователя.
    
    Returns:
        UserResponse: Pydantic-модель с данными профиля пользователя.
    """
    return UserService._map_user_to_response(user)


@auth.get('/google/callback')
async def google_callback(
    code: Annotated[str,Query(..., description="Код авторизации от Google")],
    db: Annotated[Session, Depends(get_db)],
    state: str | None =  Query(None, description="Параметр состояния для защиты от CSRF"),
) -> Token:
    """
    Обрабатывает колбэк от Google OAuth после успешной авторизации пользователя.
    Обменивает код авторизации на токены Google и выдает JWT-токен вашего приложения.
    """
    token_url = "https://oauth2.googleapis.com/token"
    token_data = {
        'code': code,
        'client_id': settings.GOOGLE_CLIENT_ID,
        'client_secret': settings.GOOGLE_CLIENT_SECRET,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code",
    }

    try:
        with httpx.Client() as client:
            response = client.post(token_url,data=token_data)
            response.raise_for_status()
            google_tokens = response.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Не удалось обменять код авторизации Google: {e.response.text}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при запросе токенов Google: {e}"
        )
    
    id_token = google_tokens.get('id_token')
    if not id_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID-токен Google не получен."
        )
    
    try:
        decoded_google_id_token = jwt.decode(
            id_token,
            options={'verify_signature': False},
            algorithms=['RS256']
        )
    except jwt.PyJWTError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Недействительный ID-токен Google: {e}"
        )
    
    email = decoded_google_id_token.get('email')
    username = decoded_google_id_token.get('username')
    google_id = decoded_google_id_token.get('google_id')
    google_image_url = decoded_google_id_token('google_image_url')
    is_email_verified = decoded_google_id_token.get('is_email_verified')


    if not email or not username or not google_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Недостаточно данных пользователя от Google."
        )
    

    google_oauth_data = GoogleOAuthData(
        email=email,
        username=username,
        google_id=google_id,
        google_image_url=google_image_url,
        is_email_verified=is_email_verified
    )

    user_respone, app_token = UserService.authenticate_user_with_google(db,google_oauth_data)

    redirect_url = f"http://127.0.0.1:5500/frontend/index.html?access_token={app_token.access_token}"

    return RedirectResponse(url=redirect_url)