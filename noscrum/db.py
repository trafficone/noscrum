import sqlite3

import click
from flask import current_app, g
from flask.cli import with_appcontext
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from flask_user import UserMixin
from noscrum import start_db

#Model = declarative_base()
def get_db():
    return start_db

db = start_db

class Work(db.Model):
    __tablename__ = 'work'
    id = db.Column(db.Integer(), primary_key=True)
    work_date = db.Column(db.Date(),nullable=False)
    hours_worked = db.Column(db.Integer(),nullable=False)
    task_id = db.Column(db.Integer(), db.ForeignKey('task.id'))
    status = db.Column(db.String(12),nullable=True,default='To-Do')
    user_id = db.Column(db.Integer(), db.ForeignKey('user.id'))
    story = relationship('Story','task')

class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer(),primary_key=True)
    username = db.Column(db.String(100),nullable=False,unique=True)
    active = db.Column('is_active',db.Boolean(), nullable=False, server_default='1')

    # User auth information. 
    # User authentication information. The collation='NOCASE' is required
    # to search case insensitively when USER_IFIND_MODE is 'nocase_collation'.
    email = db.Column(db.String(255, collation='NOCASE'), nullable=True, unique=True)
    email_confirmed_at = db.Column(db.DateTime())
    email_opt_in = db.Column(db.Boolean(), nullable=False, server_default='0')
    password = db.Column(db.String(255), nullable=False, server_default='')

    # User information
    first_name = db.Column(db.String(100, collation='NOCASE'), nullable=False, server_default='')
    last_name = db.Column(db.String(100, collation='NOCASE'), nullable=False, server_default='')

    # Define the relationship to Role via UserRoles
    roles = relationship('Role', 'user_roles')
    def __str__(self):
        return f"User(id={self.id})"
    

# Define the Role data-model
class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(50), unique=True)

# Define the UserRoles association table
class UserRoles(db.Model):
    __tablename__ = 'user_roles'
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('user.id', ondelete='CASCADE'))
    role_id = db.Column(db.Integer(), db.ForeignKey('roles.id', ondelete='CASCADE'))

class Task(db.Model):
    __tablename__ = 'task'
    id = db.Column(db.Integer(),primary_key=True)
    task = db.Column(db.String(1024),nullable=False)
    story_id = db.Column(db.Integer(),db.ForeignKey('story.id'),nullable=False)
    sprint_id = db.Column(db.Integer(),db.ForeignKey('sprint.id'),nullable=True)
    estimate = db.Column(db.Float())
    actual = db.Column(db.Float())
    deadline = db.Column(db.Date())
    recurring = db.Column(db.Boolean(),nullable=False,server_default='0')
    status = db.Column(db.String(12),nullable=False,server_default='To-Do')
    user_id = db.Column(db.Integer(),db.ForeignKey('user.id'))
    work_items = relationship('Work')
    schedules = relationship('ScheduleTask')

class Tag(db.Model):
    __tablename__ = 'tag'
    id = db.Column(db.Integer(),primary_key=True)
    tag = db.Column(db.String(255), nullable=False)
    user_id = db.Column(db.Integer,db.ForeignKey('user.id'),nullable=False)
    stories = relationship('Story','tag_story')

class Story(db.Model):
    __tablename__ = 'story'
    id = db.Column(db.Integer(),primary_key=True)
    story = db.Column(db.String(255),nullable=False)
    epic_id = db.Column(db.Integer(),db.ForeignKey('epic.id'),nullable=False)
    prioritization = db.Column(db.Integer(),server_default='1',nullable=False)
    deadline = db.Column(db.Date())
    user_id = db.Column(db.Integer(),db.ForeignKey('user.id'),nullable=False)
    tasks = relationship('Task')
    tags = relationship('Tag', 'tag_story')

class TagStory(db.Model):
    __tablename__ = 'tag_story'
    id = db.Column(db.Integer(),primary_key=True)
    tag_id = db.Column(db.Integer(),db.ForeignKey('tag.id'))
    story_id = db.Column(db.Integer(),db.ForeignKey('story.id'))

class Epic(db.Model):
    __tablename__ = 'epic'
    id = db.Column(db.Integer(), primary_key=True)
    epic = db.Column(db.String(255), nullable=False)
    color = db.Column(db.String(12))
    deadline = db.Column(db.Date())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    stories = relationship('Story')
    tasks = relationship('Task','story',primaryjoin=Story.epic_id==id,secondaryjoin=Task.story_id==Story.id)
    #tags = relationship('Tag','story')

class Sprint(db.Model):
    __tablename__ = 'sprint'
    id = db.Column(db.Integer(),primary_key=True)
    start_date = db.Column(db.Date(),nullable=False)
    end_date = db.Column(db.Date(),nullable=False)
    user_id = db.Column(db.Integer(),db.ForeignKey('user.id'),nullable=False)
    tasks = relationship('Task')
    stories = relationship('Story','task')
    #epics = relationship('epic',secondary='story',tertiary='task')
    schedule = relationship('ScheduleTask')

class ScheduleTask(db.Model):
    __tablename__ = 'schedule_task'
    id = db.Column(db.Integer(),primary_key=True)
    task_id = db.Column(db.Integer(),db.ForeignKey('task.id'),nullable=False)
    sprint_id = db.Column(db.Integer(),db.ForeignKey('sprint.id'),nullable=False)
    user_id = db.Column(db.Integer(),db.ForeignKey('user.id'),nullable=False)
    sprint_day = db.Column(db.Date(),nullable=False)
    sprint_hour = db.Column(db.Integer(),nullable=False)
    note = db.Column(db.String(2048),nullable=True)

    def to_dict(self):
        return {'id': self.id,
                'task_id': self.task_id,
                'sprint_id': self.sprint_id,
                'sprint_day': str(self.sprint_day) ,
                'sprint_hour':self.sprint_hour ,
                'note': self.note }

def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()


def init_db():
    db = get_db()
#    with current_app.open_resource('schema.sql') as f:
#        db.executescript(f.read().decode('utf8'))


@click.command('init-db')
@with_appcontext
def init_db_command():
    """Clear the existing data and create new tables"""
    init_db()
    click.echo('Initialized the database')


def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
