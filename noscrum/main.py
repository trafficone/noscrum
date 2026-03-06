"""
NoScrum Scheduling Application
See README.md for full details.
"""
import os

from dotenv import load_dotenv
from fastapi import Depends, FastAPI
from fastapi.staticfiles import StaticFiles

from noscrum import epic, semi_static, sprint, story, tag, task, user, work
from noscrum.db import create_db_and_tables
from noscrum.model import User


class ConfigClass:
    """Flask application config"""

    SECRET_KEY = os.environ.get("NOSCRUM_SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = "sqlite:///noscrum.sqlite"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    USER_APP_NAME = "NoScrum"
    USER_APP_VERSION = "βeta.1.0"
    USER_COPYRIGHT_YEAR = "2021"
    USER_CORPORATION_NAME = "Industrial Systems - A PLBL Brand"
    USER_ENABLE_EMAIL = False
    USER_ENABLE_USERNAME = True
    USER_ENABLE_REGISTER = True
    USER_EMAIL_SENDER_NAME = USER_APP_NAME
    USER_EMAIL_SENDER_EMAIL = "noreply@plbl.net"
    USER_LOGIN_URL = "/login"
    USER_LOGOUT_URL = "/logout"

    def get_dict(self):
        """
        Return a dictionary for ConfigClass locals
        """
        return {k: self.__getattribute__(k) for k in dir(self)}

    def __str__(self):
        return str(self.get_dict())

load_dotenv()
# Create and Configure the app
running_app = FastAPI()

running_app.mount('/static',StaticFiles(directory="static"),name="static")
running_app.include_router(epic.router)
running_app.include_router(story.router)
running_app.include_router(task.router)
running_app.include_router(sprint.router)
running_app.include_router(tag.router)
running_app.include_router(work.router)
running_app.include_router(user.router)
running_app.include_router(semi_static.router)
fastapi_users = user.fastapi_users
auth_backend = user.auth_backend
running_app.include_router(
    fastapi_users.get_auth_router(auth_backend), prefix="/auth/jwt", tags=["auth"]
)
running_app.include_router(fastapi_users.get_register_router(),
 prefix="/auth",
 tags=["auth"])
running_app.include_router(
    fastapi_users.get_reset_password_router(),
    prefix="/auth",
    tags=["auth"],
)
running_app.include_router(
    fastapi_users.get_verify_router(),
    prefix="/auth",
    tags=["auth"]
)
running_app.include_router(fastapi_users.get_users_router(), prefix="/users", tags=["users"])


@running_app.get("/authenticated-route")
async def authenticated_route(user: User = Depends(user.current_active_user)):
    return {"message": f"Hello {user.email}!"}

@running_app.on_event("startup")
async def on_startup():
    """
    Creates the FastAPI application for NoScrum.
    """
    await create_db_and_tables()
