"""
User view and database controller
"""
from flask import (
    Blueprint, redirect, url_for
)
from flask_user import current_user
from noscrum.db import get_db, User

bp = Blueprint('user', __name__, url_prefix='/user')
def get_user(user_id):
    app_db = get_db()
    return User(*app_db.execute('SELECT id,username,password_hash FROM user WHERE id = ?',(user_id,)).fetchone())

def get_user_by_username(username):
    app_db = get_db()
    return User(*app_db.execute('SELECT id,username,password_hash FROM user WHERE username = ?',(username,)).fetchone())

def get_current_user():
    app_db = get_db()
    return app_db.execute('SELECT * FROM USER WHERE id = ?',current_user.id)

def authenticate_user(username,credential):
    user = get_user_by_username(username)
    if credential == user.password_hash:
        return user

@bp.route('/',methods=('GET','PUT'))
def profile():
    if not current_user:
        redirect(url_for('user.login'))
    return current_user.username 