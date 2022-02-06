"""
User view and database controller
"""
from flask import (
    Blueprint, redirect, url_for
)
from flask_user import current_user
from noscrum.db import User

bp = Blueprint('user', __name__, url_prefix='/user')
def get_user(user_id):
    """
    Return user record given an identity value
    @param user_id user's identification value
    """
    return User.query.filter(User.id == user_id).first()

def get_user_by_username(username):
    """
    Return user record given a username request
    """
    return User.query.filter(User.username == username).first()

def get_current_user():
    """
    Get the record for a currently active user
    """
    return User.query.filter(User.id == current_user.id).first()

def authenticate_user(username,credential):
    """
    Authenticate a user with their credentials
    @param username provided username for user
    @param crediential the shared secret given
    """
    user = get_user_by_username(username)
    if credential == user.password_hash:
        return user

@bp.route('/',methods=('GET','PUT'))
def profile():
    """
    The _currently active_ user's profile page
    GET: Return user information they provided
    PUT: not implemented, update a user's data
    """
    if not current_user:
        redirect(url_for('user.login'))
    return current_user.username
