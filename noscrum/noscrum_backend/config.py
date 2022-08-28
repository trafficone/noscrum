"""
Configuration object for Noscrum Backend
"""
from starlette.config import Config
from starlette.datastructures import Secret

config = Config(".env")
APP_NAME = "NoScrum"
APP_VERSION = "βeta.1.0"
APP_YEAR = "2021"
APP_COPYRIGHT_HOLDER = "Industrial Systems - A PLBL Brand"

DATABASE_URI = config("DATABASE_URI", cast=str, default="sqlite:///noscrum.sqlite")
SECRET = config("PASSWORD_SECRET", cast=Secret)
ACCESS_TOKEN_EXPIRE_MINUTES = config(
    "ACCESS_TOKEN_EXPIRE_MINUTES", cast=int, default=60
)
JWT_ALGORITHM = config("JWT_ALGORITHM", cast=str, default="HS256")
JWT_AUDIENCE = config("JWT_AUDIENCE", cast=str, default="noscrum:auth")
JWT_TOKEN_PREFIX = config("JWT_TOKEN_PREFIX", cast=str, default="Bearer")

USER_EMAIL_SENDER_NAME = APP_NAME
USER_EMAIL_SENDER_EMAIL = "noreply@plbl.net"
