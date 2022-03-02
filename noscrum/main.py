"""
NoScrum Scheduling Application
See README.md for full details.
"""
import os

from dotenv import load_dotenv
from sqlmodel import SQLModel
from fastapi import FastAPI, APIRouter
from noscrum.db import get_db
from noscrum.model import *


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


def create_app(test_config=None):
    """
    Creates the Flask application for NoScrum.
    """
    load_dotenv()
    # Create and Configure the app
    running_app = FastAPI()

    if test_config is not None:
        # Load test config if passed in
        #running_app.config.from_mapping(test_config)
        pass

    #try:
    #    os.makedirs(running_app.instance_path)
    #except OSError:
    #    pass

    app_db = get_db()
    SQLModel.metadata.create_all(app_db)

    from noscrum import epic, story, task, sprint, tag, work, user, semi_static

    running_app.include_router(epic.router)
    running_app.include_router(story.router)
    running_app.include_router(task.router)
    running_app.include_router(sprint.router)
    running_app.include_router(tag.router)
    running_app.include_router(work.router)
    running_app.include_router(user.router)
    running_app.include_router(semi_static.router)

    return running_app


