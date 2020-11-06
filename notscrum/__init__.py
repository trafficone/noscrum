import os

from flask import Flask, render_template


def create_app(test_config=None):
    "Create and Configure the app"
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'notscrum.sqlite'),
    )

    if test_config is None:
        # Load the instance config when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # Load test config if passed in
        app.config.from_mapping(test_config)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    from . import db
    db.init_app(app)

    from . import epic, story, task, sprint, tag, work
    app.register_blueprint(epic.bp)
    app.register_blueprint(story.bp)
    app.register_blueprint(task.bp)
    app.register_blueprint(sprint.bp)
    app.register_blueprint(tag.bp)
    app.register_blueprint(work.bp)

    #FIXME: Index and Static Pages should be defined elsewhere
    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/hello')
    def hello():
        return 'Hello, World'

    return app
