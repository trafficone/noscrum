"""
User view and database controller
"""
import os
import uuid

import dotenv
from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi_users import BaseUserManager, FastAPIUsers, schemas, models
from fastapi_users.authentication import (
    AuthenticationBackend,
    CookieTransport,
    JWTStrategy,
)
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase
#from fasthtml import FastHTML
#import fasthtml.common as fh

from noscrum.db import get_db
from noscrum.model import User

UserDB = get_db()

dotenv.load_dotenv()

SECRET = os.environ["PASSWORD_SECRET"]

class UserRead(schemas.BaseUser[uuid.UUID]):
    pass

class UserUpdate(schemas.BaseUserUpdate):
    pass

class UserCreate(schemas.BaseUserCreate):
    username: str

class UserManager(BaseUserManager[User, uuid.UUID]):
    user_db_model = User
    reset_password_token_secret = SECRET
    verification_token_secret = SECRET

    async def on_after_register(self, user: User, request: Request | None = None):
        print(f"User {user.id} has registered.")

    async def on_after_forgot_password(
        self, user: User, token: str, request: Request | None = None
    ):
        print(f"User {user.id} has forgotten their password. Reset token: {token}")

    async def on_after_request_verify(
        self, user: User, token: str, request: Request | None = None
    ):
        print(f"Verification requested for user {user.id}. Verification token: {token}")

async def get_user_manager(user_db: SQLAlchemyUserDatabase = Depends(get_db)):
    yield UserManager(user_db)

bearer_transport = CookieTransport()#tokenUrl="auth/jwt/login")
#bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")
def get_jwt_strategy() -> JWTStrategy:#[models.UP, models.ID]:
    return JWTStrategy(secret=SECRET, lifetime_seconds=3600)

auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)

fastapi_users = FastAPIUsers[User, uuid.UUID](get_user_manager, [auth_backend])
current_active_user = fastapi_users.current_user(active=True)
current_user = current_active_user


def get_user(db, username: str):
    """
    Return user record given an identity value
    @param user_id user's identification value
    """
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)


def get_user_by_username(username):
    """
    Return user record given a username request
    """
    return User.where(User.username == username).first()


def get_current_user():
    """
    Get the record for a currently active user
    """
    return User.where(User.id == current_user.id).first()


def authenticate_user(username, credential):
    """
    Authenticate a user with their credentials
    @param username provided username for user
    @param crediential the shared secret given
    """
    user = get_user_by_username(username)
    if credential == user.password_hash:
        return user


router = APIRouter(prefix="/api/user", tags=["users"])
#web = FastHTML()
#web_router = web.route
templates = Jinja2Templates(directory="templates")

@router.get("/")
async def profile():
    """
    The _currently active_ user's profile page
    GET: Return user information they provided
    PUT: not implemented, update a user's data
    """
    if not current_user:
        login_url = router.url_path_for("login")
        RedirectResponse(login_url)
    return await current_user().username

@router.get("/login")
def login(request: Request):#_redirect(_):
    return templates.TemplateResponse("/users/login.html",{"request":request,"current_user":current_user})

@router.get("/logout")
def logout(request: Request):
    return templates.TemplateResponse("/users/logout.html",{"request":request,"current_user":current_user})
@router.get("/register")
def register(request: Request):
    return templates.TemplateResponse("/users/register.html",{"request":request,"current_user":current_user})
