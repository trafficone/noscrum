import os

from flask import Flask
from dotenv import load_dotenv
from flask_babelex import Babel
from flask_sqlalchemy import SQLAlchemy
from flask_user import UserManager
import datetime

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
    load_dotenv()
    "Create and Configure the app"
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(__name__+'.ConfigClass')
    # Init Flask-BabelEx
    babel = Babel(app)

    if test_config is not None:
        # Load test config if passed in
        app.config.from_mapping(test_config)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Init SQLAlchemy
    from noscrum import db
    db.init_db(SQLAlchemy(app))
    app_db = db.get_db()
    app_db.create_all()
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
