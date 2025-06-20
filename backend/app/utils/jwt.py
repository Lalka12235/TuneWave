import jwt
from datetime import datetime,timedelta
from app.config.settings import settings
from fastapi import HTTPException,status


#SECRET_KEY = settings.SECRET_KEY
ALGHORITHM = 'HS256'
ACCESS_TOKEN_MINUTES_EXPIRED = 15


def encode(
        payload,
        secret_key,
        algorithm,
        minutes_expired = ACCESS_TOKEN_MINUTES_EXPIRED,
):
    expired = datetime.utcnow() + timedelta(minutes=minutes_expired)
    payload.update({'exp': expired})
    token = jwt.encode(payload,secret_key,algorithm=algorithm)
    return token

def decode(
        token,
        secret_key,
        algorithm,
):
    try:
        decode = jwt.decode(token,secret_key,algorithms=[algorithm])
        return decode
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")