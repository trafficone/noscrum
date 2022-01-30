import os

from flask import Flask, render_template, g
from dotenv import load_dotenv
#from flask_login import login_manager, LoginManager
from flask_babelex import Babel
from flask_sqlalchemy import SQLAlchemy
from flask_user import current_user, login_required, roles_required, UserManager, UserMixin
import datetime

start_db = 'start_db'

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
    

def create_app(test_config=None):
    load_dotenv()
    "Create and Configure the app"
    global start_db
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(__name__+'.ConfigClass')
    
    # Init Flask-BabelEx
    babel = Babel(app)

    # Init SQLAlchemy

    """
    if test_config is None:
        # Load the instance config when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # Load test config if passed in
        app.config.from_mapping(test_config)
    """

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    start_db = SQLAlchemy(app)
    from noscrum.db import User
    user_manager = UserManager(app, start_db, User)
    start_db.create_all()
    if not User.query.filter(User.username == 'trafficone').first():
        user = User(
            username='trafficone',
            email='member@example.com',
            email_confirmed_at=datetime.datetime.utcnow(),
            password=user_manager.hash_password('password'))
        start_db.session.add(user)
        start_db.session.commit()

    from noscrum import epic, story, task, sprint, tag, work, user
    app.register_blueprint(epic.bp)
    app.register_blueprint(story.bp)
    app.register_blueprint(task.bp)
    app.register_blueprint(sprint.bp)
    app.register_blueprint(tag.bp)
    app.register_blueprint(work.bp)
    app.register_blueprint(user.bp)


    #FIXME: Index and Static Pages should be defined elsewhere
    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/hello')
    def hello():
        return 'Hello, World'

    return app
