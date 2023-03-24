"""
User view controller
"""
import logging
import flask
from flask_openapi3 import APIBlueprint as Blueprint
from flask_login import current_user, login_required, login_user, logout_user, UserMixin
import noscrum_backend.user as backend

logger = logging.getLogger()
bp = Blueprint("user", __name__, url_prefix="/user")


@bp.get("/")
def profile():
    """
    The _currently active_ user's profile page
    GET: Return user information they provided
    PUT: not implemented, update a user's data
    """
    if not hasattr(current_user, "id") or not current_user.id:
        return flask.redirect(flask.url_for("user.get_login"))
    return flask.render_template(
        "user/profile.html", username=current_user.user.username, user=current_user
    )


@bp.get("/create")
def get_create():
    """
    Return user creation form
    """
    return flask.render_template("user/create.html")


@bp.post("/create")
def create():
    """
    Create a new user
    """
    # FIXME: Validate input somewhat
    form = flask.request.form
    insecure_password: str = form.get("password", "")
    user_properties = {
        "username": form.get("username"),
        "insecure_password": bytes(insecure_password, "utf-8"),
        "email": form.get("email"),
        "first_name": form.get("firstname", form.get("username")),
        "last_name": form.get("lastname"),
    }
    try:
        new_user = backend.UserClass.create_user(**user_properties)
    except ValueError as error_message:
        logger.error(error_message)
        flask.flash("Could not create user: %s" % str(error_message))
        return flask.redirect(flask.url_for("user.get_create"))
    login_user(new_user)
    return flask.redirect(flask.url_for("semi_static.index"))


@bp.post("/")
@login_required
def update():
    """
    Update user (not yet implemented)
    """
    # TODO: update user


@bp.get("/login")
def get_login():
    """
    Return login form for user
    """
    if (
        isinstance(current_user, UserMixin)
        and hasattr(current_user, "id")
        and current_user.id is not None
    ):
        return flask.redirect(flask.url_for("user.profile"))
    return flask.render_template("user/login.html")


@bp.get("/logout")
def logout():
    """
    Handle logout action for user
    """
    logout_user()
    return flask.redirect(flask.url_for("semi_static.index"))


@bp.post("/login")
def login():
    """
    Handle login request for user
    """
    username = flask.request.form.get("username")
    password = flask.request.form.get("password")
    user_db_instance = backend.get_user_by_username(username)
    if user_db_instance is None or password is None:
        flask.flash("Username or Password is Incorrect")
        return flask.render_template("user/login.html")

    user_instance = backend.UserClass(user_db_instance.id)
    if not user_instance.authenticate(password):
        flask.flash("Username or Password is Incorrect")
        return flask.render_template("user/login.html")
    login_user(user_instance)

    flask.flash("Logged in successfully.")

    next_pg = flask.request.args.get("next")
    # is_safe_url should check if the url is safe for redirects.
    # See http://flask.pocoo.org/snippets/62/ for an example.
    # if not is_safe_url(next_pg):
    #    return flask.abort(400)

    return flask.redirect(next_pg or flask.url_for("semi_static.index"))
