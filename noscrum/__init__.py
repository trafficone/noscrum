"""
NoScrum Scheduling Application
See README.md for full details.
"""
import os
import time
from asyncio import create_task
from dotenv import load_dotenv
from flask import Flask
from flask_babelex import Babel
from flask_sqlalchemy import SQLAlchemy
from flask_user import UserManager


class DatabaseSingleton(object):
    """
    Database singleton, holds the app database
    instance information in such a way that it
    does not break the app/developer's brains.
    """
    app_db = None
    __instance = None
    def __init__(self,db_object):
        """
        Create a database singleton object. Should
        only be called using the DatabaseSingleton
        """
        print('DB Instance',DatabaseSingleton.__instance)
        if DatabaseSingleton.__instance is None:
            self.app_db = db_object
            DatabaseSingleton.__instance = self
        else:
            raise Exception("DB is Singleton, cannot re-init")

    @staticmethod
    def create_singleton(database):
        """
        Returns only instance of DatabaseSingleton
        Creates a new instance if there is not one
        """
        if DatabaseSingleton.__instance is None:
            DatabaseSingleton(database)
        return DatabaseSingleton.__instance

    @staticmethod
    async def get_db_instance():
        """
        Get instance of the Singleton class. Waits
        until instance has been created via method
        DatabaseSingleton.create_singleton(d_base)
        """
        while DatabaseSingleton.__instance is None:
            # Forgive me father for I have sinned
            time.sleep(1)
        return DatabaseSingleton.__instance

    @staticmethod
    async def get_db():
        """
        Returns the app database instance used for
        the application controller modules. It can
        wait for the DatabaseSingleton instance to
        Initialize just like get_db_instance() can
        """
        instance = await create_task(DatabaseSingleton.get_db_instance())
        return instance.app_db

class ConfigClass(object):
    """Flask application config"""
    SECRET_KEY=os.environ.get('FLASK_SECRET_KEY')
    SQLALCHEMY_DATABASE_URI='sqlite:///noscrum.sqlite'
    SQLALCHEMY_TRACK_MODIFICATIONS=False

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


def create_app(test_config=None):
    """
    Creates the Flask application for NoScrum.
    """
    load_dotenv()
    # Create and Configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(__name__+'.ConfigClass')
    # Init Flask-BabelEx
    Babel(app)

    if test_config is not None:
        # Load test config if passed in
        app.config.from_mapping(test_config)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Init SQLAlchemy
    app_db = SQLAlchemy(app)
    DatabaseSingleton.create_singleton(app_db)
    app_db.create_all()

    # These need app to exist before they can be imported
    from noscrum.db import User
    UserManager(app, app_db, User)
    from noscrum import epic, story, task, sprint, tag, work, user, semi_static
    app.register_blueprint(epic.bp)
    app.register_blueprint(story.bp)
    app.register_blueprint(task.bp)
    app.register_blueprint(sprint.bp)
    app.register_blueprint(tag.bp)
    app.register_blueprint(work.bp)
    app.register_blueprint(user.bp)
    app.register_blueprint(semi_static.bp)

    return app
