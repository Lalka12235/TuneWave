from urllib.parse import urlencode
from fastapi import APIRouter,Depends, Query,HTTPException,status
from sqlalchemy.orm import Session
from fastapi.responses import RedirectResponse
from typing import Annotated
from app.schemas.user_schemas import GoogleOAuthData, SpotifyOAuthData
from app.schemas.config_schemas import FrontendConfig
from app.services.user_service import UserService
from app.config.session import get_db
import httpx
from app.config.settings import settings
import jwt
import base64
import time
from fastapi_limiter.depends import RateLimiter

auth = APIRouter(
    tags=['auth'],
    prefix='/auth'
)

@auth.get('/config', response_model=FrontendConfig)
def get_frontend_config(
    dependencies=[Depends(RateLimiter(times=15, seconds=60))]
) -> FrontendConfig:
    """
    Возвращает публичные конфигурационные данные, необходимые фронтенду.
    """
    return FrontendConfig(
        google_client_id=settings.GOOGLE_CLIENT_ID,
        google_redirect_uri=settings.GOOGLE_REDIRECT_URI,
        google_scopes=settings.GOOGLE_SCOPES,
        spotify_client_id=settings.SPOTIFY_CLIENT_ID,
        spotify_redirect_uri=settings.SPOTIFY_REDIRECT_URI,
        spotify_scopes=settings.SPOTIFY_SCOPES,
    )


@auth.get('/google/login')
async def google_login():
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": settings.GOOGLE_SCOPES,
        "access_type": "offline", 
        "prompt": "consent"
    }
    google_auth_url = "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params)
    return RedirectResponse(url=google_auth_url)

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
        async with httpx.AsyncClient() as client:
            response = await client.post(token_url,data=token_data)
            response.raise_for_status()
            google_tokens: dict = response.json()
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
    google_access_token = google_tokens.get('access_token')
    google_refresh_token = google_tokens.get('refresh_token')
    expires_in = google_tokens.get('expires_in')
    
    if not id_token or not google_access_token or not expires_in:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Недостаточно данных токенов Google."
        )
    
    import time
    google_token_expires_at = int(time.time()) + expires_in
    
    try:
        decoded_google_id_token: dict = jwt.decode(
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
        is_email_verified=is_email_verified,
        google_access_token=google_access_token,
        google_refresh_token=google_refresh_token,
        google_token_expires_at=google_token_expires_at
    )

    user_response, app_token = await UserService.authenticate_user_with_google(db,google_oauth_data)

    redirect_url = f"http://127.0.0.1:5500/frontend/auth.html?access_token={app_token.access_token}"

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
        async with httpx.AsyncClient() as client:
            response = await client.post(token_url, headers=token_headers, data=token_data)
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
    spotify_scope = spotify_tokens.get('scope')
    
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
        async with httpx.AsyncClient() as client:
            user_profile_response = await client.get(user_profile_url, headers=user_profile_headers)
            user_profile_response.raise_for_status()
            spotify_user_data: dict = user_profile_response.json()
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
        spotify_token_expires_at=spotify_token_expires_at,
        spotify_scope=spotify_scope
    )

    user_response, app_token = await UserService.authenticate_user_with_spotify(db, spotify_oauth_data)

    redirect_url = f"http://127.0.0.1:5500/frontend/auth.html?access_token={app_token.access_token}"

    return RedirectResponse(url=redirect_url)