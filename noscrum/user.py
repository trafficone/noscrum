import logging

from flask import (
    Blueprint, g, redirect, render_template, request, session, url_for, abort, flash
)
from flask_user import current_user
from noscrum.db import get_db, User

bp = Blueprint('user', __name__, url_prefix='/user')
def get_user(id):
    db = get_db()
    return User(*db.execute('SELECT id,username,password_hash FROM user WHERE id = ?',(id,)).fetchone())

def get_user_by_username(username):
    db = get_db()
    return User(*db.execute('SELECT id,username,password_hash FROM user WHERE username = ?',(username,)).fetchone())

def get_current_user():
    db = get_db()
    return db.execute('SELECT * FROM USER WHERE id = ?',current_user.id)

def create_user(username,email,message_opt_in=False):
    db = get_db()
    #fixme: how do i deal with password?
    db.execute('INSERT INTO user (username, email, message_opt_in) '+
               'VALUES (?,?,?)',
               (username,email,message_opt_in))
    db.commit()
    return get_user_by_username(username)

def authenticate_user(username,credential):
    user = get_user_by_username(username)
    if credential == user.password_hash:
        return user

#@bp.route('/login',methods=('GET','POST'))
#def login():
#   return render_template('user/login.html') 

@bp.route('/',methods=('GET','PUT'))
def profile():
    if not current_user:
        redirect(url_for('user.login'))
    return current_user.username 

