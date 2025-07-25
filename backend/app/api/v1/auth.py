from fastapi import APIRouter,Depends, Query,HTTPException,status
from sqlalchemy.orm import Session
from fastapi.responses import RedirectResponse
from typing import Annotated
from app.schemas.user import UserResponse, Token, GoogleOAuthData, SpotifyOAuthData
from app.schemas.config_schemas import FrontendConfig
from app.services.user import UserService
from app.auth.auth import get_current_user
from app.config.session import get_db
from app.models.user import User
import httpx
from app.config.settings import settings
import jwt
import base64
import time

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
    state: str | None = Query(None, description="Параметр состояния для защиты от CSRF"),
) -> RedirectResponse: 
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
    username = decoded_google_id_token.get('name')
    google_id = decoded_google_id_token.get('sub')
    google_image_url = decoded_google_id_token.get('picture')
    is_email_verified = decoded_google_id_token.get('email_verified')


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

    user_response, app_token = UserService.authenticate_user_with_google(db,google_oauth_data)

    redirect_url = f"http://127.0.0.1:5500/frontend/index.html?access_token={app_token.access_token}"

    return RedirectResponse(url=redirect_url)



@auth.get('/spotify/callback')
async def spotify_callback(
    code: Annotated[str, Query(..., description="Код авторизации от Spotify")],
    db: Annotated[Session, Depends(get_db)],
    state: str | None = Query(None,description="Параметр состояния для защиты от CSRF"),
) -> RedirectResponse: # ИСПРАВЛЕНО: Возвращает RedirectResponse
    """
    Обрабатывает колбэк от Spotify OAuth после успешной авторизации пользователя.
    Обменивает код авторизации на токены Spotify, получает данные пользователя
    и выдает JWT-токен вашего приложения.
    Затем перенаправляет пользователя обратно на фронтенд с этим токеном.
    """
    token_url = 'https://accounts.spotify.com/api/token'
    
    # Spotify требует Basic-аутентификацию для этого запроса
    # Кодируем client_id:client_secret в Base64
    auth_str = f"{settings.SPOTIFY_CLIENT_ID}:{settings.SPOTIFY_CLIENT_SECRET}"
    encoded_auth_str = base64.b64encode(auth_str.encode()).decode()

    token_headers = {
        'Authorization': f'Basic {encoded_auth_str}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    token_data = {
        'grant_type': "authorization_code",
        'code': code,
        'redirect_uri': settings.SPOTIFY_REDIRECT_URI,
    }

    try:
        with httpx.Client() as client:
            response = client.post(token_url, headers=token_headers, data=token_data)
            response.raise_for_status()
            spotify_tokens = response.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Не удалось обменять код авторизации Spotify: {e.response.text}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при запросе токенов Spotify: {e}"
        )
    
    spotify_access_token = spotify_tokens.get('access_token')
    spotify_refresh_token = spotify_tokens.get('refresh_token')
    expires_in = spotify_tokens.get('expires_in')
    
    if not spotify_access_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Токен доступа Spotify не получен."
        )

    spotify_token_expires_at = int(time.time()) + expires_in if expires_in else None


    user_profile_url = "https://api.spotify.com/v1/me"
    user_profile_headers = {
        'Authorization': f'Bearer {spotify_access_token}'
    }

    try:
        with httpx.Client() as client:
            user_profile_response = client.get(user_profile_url, headers=user_profile_headers)
            user_profile_response.raise_for_status()
            spotify_user_data = user_profile_response.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Не удалось получить данные профиля Spotify: {e.response.text}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при запросе профиля Spotify: {e}"
        )

    email = spotify_user_data.get('email')
    username = spotify_user_data.get('display_name')
    spotify_id = spotify_user_data.get('id')
    spotify_profile_url = spotify_user_data.get('external_urls', {}).get('spotify')
    
    spotify_image_url = None
    if spotify_user_data.get('images'):
        spotify_image_url = spotify_user_data['images'][0].get('url')

    if not email or not username or not spotify_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Недостаточно данных пользователя от Spotify."
        )
    
    spotify_oauth_data = SpotifyOAuthData(
        email=email,
        username=username,
        spotify_id=spotify_id,
        spotify_profile_url=spotify_profile_url,
        spotify_image_url=spotify_image_url,
        spotify_access_token=spotify_access_token,
        spotify_refresh_token=spotify_refresh_token,
        spotify_token_expires_at=spotify_token_expires_at
    )

    user_response, app_token = UserService.authenticate_user_with_spotify(db, spotify_oauth_data)

    redirect_url = f"http://127.0.0.1:5500/frontend/index.html?access_token={app_token.access_token}"

    return RedirectResponse(url=redirect_url)