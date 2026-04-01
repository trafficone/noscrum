"""
User view and database controller
"""

import os
import uuid
from typing import Any

import dotenv
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi_users import BaseUserManager, FastAPIUsers, schemas
from fastapi_users.authentication import (
    AuthenticationBackend,
    CookieTransport,
    JWTStrategy,
)
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase
from loguru import logger as log
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from noscrum.db import get_async_session, get_user_db
from noscrum.model import User, UserSettings

UserDB = get_user_db()

dotenv.load_dotenv()

SECRET = os.environ["PASSWORD_SECRET"]


class UserRead(schemas.BaseUser[int]):
    pass


class UserUpdate(schemas.BaseUserUpdate):
    pass


class UserCreate(schemas.BaseUserCreate):
    username: str


class UserManager(BaseUserManager[User, int]):
    user_db_model = User
    reset_password_token_secret = SECRET
    verification_token_secret = SECRET

    async def on_after_register(self, user: User, request: Request | None = None):
        log.info(f"User {user.id} has registered.")

    async def on_after_forgot_password(self, user: User, token: str, request: Request | None = None):
        log.info(f"User {user.id} has forgotten their password. Reset token: {token}")

    async def on_after_request_verify(self, user: User, token: str, request: Request | None = None):
        log.info(f"Verification requested for user {user.id}. Verification token: {token}")

    def parse_id(self, value: Any) -> int:
        if isinstance(value, int):
            return value
        elif isinstance(value, str):
            try:
                int_value = int(value)
                return int_value
            except Exception:
                raise ValueError("UserID is not valid")
        else:
            raise NotImplementedError("Type not supported for UserID")

    """def parse_id(self, value: Any) -> uuid.UUID:
        log.info("Parsing proposed ID {}", value)
        if isinstance(value, str):
            id = uuid.UUID(value)
        elif isinstance(value, uuid.UUID):
            id = value
        else:
            raise Exception("Not able to parse User ID")
        return id"""


"""    async def get(self, id: uuid.UUID) -> User:
        #out = await super().get(id)
        id = self.parse_id(id)
        log.info("Attempting to pull User ID {id} to get record",id=str(id).replace('-',''))
        log.info("User DB Search for ID? {d}",d=dir(self.user_db))
        log.info("Example user? {u}",u=await self.user_db.get_by_email("user@example.com"))

        out_query = select(self.user_db.user_table).where(self.user_db.user_table.id == id)
        out = (await self.user_db.session.execute(out_query)).scalar_one_or_none()
        if out is None:
            raise Exception(f"User {id} not found")
        log.info("Found user {user}",user=out)
        log.info("Username: {username}", username=out.username)
        return out"""


async def get_user_settings(current_user: User, app_db: AsyncSession):
    if current_user is None or current_user.id is None:
        raise ValueError("Cannot get user settings without a user")
    settings = await app_db.execute(select(UserSettings).where(UserSettings.user_id == current_user.id))
    s = settings.scalar_one_or_none()
    if s is None:
        """
        Just going to create one with all the defaults
        """
        s = UserSettings(user_id=current_user.id)
        app_db.add(s)
        await app_db.commit()
    return s

async def set_user_settings(settings: UserSettings, current_user: User, app_db: AsyncSession):
    old_settings = await get_user_settings(current_user, app_db)
    # there's gotta be something
    await app_db.commit()
    return settings

async def get_user_manager(user_db: SQLAlchemyUserDatabase = Depends(get_user_db)):
    yield UserManager(user_db)
cookie_transport = CookieTransport()
def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret=SECRET, lifetime_seconds=3600 * 8)


auth_backend = AuthenticationBackend(
    name="jwt",
    transport=cookie_transport,
    get_strategy=get_jwt_strategy,
)

fastapi_users = FastAPIUsers[User, uuid.UUID](get_user_manager, [auth_backend])
current_active_user = fastapi_users.current_user(active=True)
current_user = fastapi_users.current_user(optional=True)

router = APIRouter(prefix="/user", tags=["users"])
templates = Jinja2Templates(directory="templates")


@router.get("/")
async def user_profile(user: User = Depends(current_user)):
    """
    The _currently active_ user's profile page
    GET: Return user information they provided
    PUT: not implemented, update a user's data
    """
    if not user:
        login_url = router.url_path_for("login")
        RedirectResponse(login_url)
    return user.username


@router.get("/login")
def login(request: Request, current_user: User = Depends(current_user)):  # _redirect(_):
    return templates.TemplateResponse(
        "/users/login.html", {"request": request, "current_user": current_user}
    )


@router.get("/logout", response_class=HTMLResponse)
def logout(request: Request, current_user: User = Depends(current_user)):
    return templates.TemplateResponse(
        "/users/logout.html", {"request": request, "current_user": current_user}
    )


@router.get("/register", response_class=HTMLResponse)
def register(request: Request, current_user: User = Depends(current_user)):
    return templates.TemplateResponse(
        "/users/register.html", {"request": request, "current_user": current_user}
    )

@router.get("/frontend/settings", tags=["frontend"], response_class=HTMLResponse)
async def fe_user_profile(request: Request, current_user: User = Depends(current_user), app_db: AsyncSession = Depends(get_async_session)):
    settings: UserSettings = await get_user_settings(current_user, app_db)
    return templates.TemplateResponse(
        "/users/settings.html", {"request": request, "current_user": current_user, "user_settings": settings}
    )

router.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)
router.include_router(
    fastapi_users.get_reset_password_router(),
    prefix="/auth",
    tags=["auth"],
)
router.include_router(
    fastapi_users.get_verify_router(UserRead),
    prefix="/auth",
    tags=["auth"],
)
router.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["users"],
)
router.include_router(fastapi_users.get_auth_router(auth_backend), prefix="/auth/jwt", tags=["auth"])
