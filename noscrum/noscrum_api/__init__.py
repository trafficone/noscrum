"""
NoScrum Scheduling Application
See README.md for full details.
"""
import os

from dotenv import load_dotenv
from flask_babelex import Babel
import logging
from flask_sqlalchemy import SQLAlchemy
from flask_openapi3 import Info
from flask_openapi3 import OpenAPI

# from flask_user import UserManager
from flask_login import LoginManager
from flask_foundation import Foundation


logger = logging.getLogger()


class ConfigClass:
    """Flask application config"""

    SECRET_KEY = os.environ.get("FLASK_SECRET_KEY")
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
    USER_CHANGE_PASSWORD_URL = "/user/change-password"

    def get_dict(self):
        """
        Return a dictionary for ConfigClass locals
        """
        return {k: self.__getattribute__(k) for k in dir(self)}

    def __str__(self):
        return str(self.get_dict())


app_db = None


def create_app(test_config=None):
    """
    Creates the Flask application for NoScrum.
    """
    global app_db
    logger.info("Creating App!!!!!!!!")
    load_dotenv()
    # Create and Configure the app
    # running_app = Flask(__name__, instance_relative_config=True)
    info = Info(title="NoScrum API", version="1.0.0")
    running_app = OpenAPI(
        __name__,
        instance_relative_config=True,
        info=info,
        doc_prefix="/openapi",
        template_folder="../templates",
        static_folder="../static",
    )
    running_app.config.from_object(__name__ + ".ConfigClass")
    # Init Flask-BabelEx
    Babel(running_app)
    Foundation(running_app)

    if test_config is not None:
        # Load test config if passed in
        running_app.config.from_mapping(test_config)

    try:
        os.makedirs(running_app.instance_path)
    except OSError:
        pass

    logger.info("Creating Database")
    # Init SQLAlchemy
    app_db = SQLAlchemy(running_app)
    logger.info("Populating Database")
    from noscrum.noscrum_backend.db import db

    db.create_all()

    # These need app to exist before they can be imported
    # UserManager(running_app, app_db, User)
    from noscrum.noscrum_backend.user import UserClass

    login_manager = LoginManager()

    @login_manager.user_loader
    def load_user(user_id):
        return UserClass(user_id)

    login_manager.init_app(running_app)

    # pylint: disable=import-outside-toplevel
    from noscrum.noscrum_api.epic import bp as epicbp
    from noscrum.noscrum_api.story import bp as storybp
    from noscrum.noscrum_api.task import bp as taskbp
    from noscrum.noscrum_api.sprint import bp as sprintbp
    from noscrum.noscrum_api.tag import bp as tagbp
    from noscrum.noscrum_api.work import bp as workbp
    from noscrum.noscrum_api.user import bp as userbp
    from noscrum.noscrum_api.semi_static import bp as semi_staticbp
    from noscrum.noscrum_api.search import bp as searchbp

    running_app.register_api(epicbp)
    running_app.register_api(storybp)
    running_app.register_api(taskbp)
    running_app.register_api(sprintbp)
    running_app.register_api(tagbp)
    running_app.register_api(workbp)
    running_app.register_api(userbp)
    running_app.register_api(semi_staticbp)
    running_app.register_api(searchbp)

    return running_app


print(__name__)
if __name__.startswith("noscrum"):
    app = create_app()
