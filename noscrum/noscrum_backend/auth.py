"""
Handle auth in requests
"""
import jwt
import time
from typing import Optional, Dict
from fastapi import Depends, Request, APIRouter
from fastapi.security import OAuth2PasswordBearer
from noscrum.config import (
    SECRET,
    JWT_ALGORITHM,
    JWT_AUDIENCE,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from noscrum.model import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login/token")


class UserToken:
    def __init__(self, username: str, expires: int, **kwargs):
        if expires > time.time():
            raise Exception("Invalid Token: Expired")
        self.username = username


async def get_user_token(*, token: str = Depends(oauth2_scheme)) -> Optional[User]:
    try:
        decoded_token = jwt.decode(
            token, str(SECRET), audience=JWT_AUDIENCE, algorithms=[JWT_ALGORITHM]
        )
        return UserToken(**decoded_token)
    except Exception as e:
        raise e


async def signJWT(username: str) -> Dict[str, str]:
    payload = {
        "username": username,
        "iat": time.time(),
        "expires": time.time() + ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }
    token = jwt.encode(payload, SECRET, algorithm=JWT_ALGORITHM)

    return {"access_token": token}
