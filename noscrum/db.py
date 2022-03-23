"""
Database Models and Controller (not much to do, thanks SQLAlchemy!)
"""

import asyncio
import sqlalchemy as sa
from flask_user import UserMixin
from sqlalchemy.orm import relationship
from noscrum import DatabaseSingleton


def get_db():
    """
    Returns the DB for the instance of the app.
    """
    return asyncio.run(DatabaseSingleton.get_db())


db = get_db()


class Work(db.Model):
    """
    Model class for task work objects.
    Tracks the number of hours worked on a specific task.
    """

    __tablename__ = "work"
    id = sa.Column(sa.Integer(), primary_key=True)
    work_date = sa.Column(sa.Date(), nullable=False)
    hours_worked = sa.Column(sa.Integer(), nullable=False)
    task_id = sa.Column(sa.Integer(), sa.ForeignKey("task.id"))
    status = sa.Column(sa.String(12), nullable=True, default="To-Do")
    user_id = sa.Column(sa.Integer(), sa.ForeignKey("user.id"))
    story = relationship("Story", "task")


class User(db.Model, UserMixin):
    """
    User model. Contains all properties for a user.
    """

    __tablename__ = "user"
    id = sa.Column(sa.Integer(), primary_key=True)
    username = sa.Column(sa.String(100), nullable=False, unique=True)
    active = sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1")

    # User auth information.
    # User authentication information. The collation='NOCASE' is required
    # to search case insensitively when USER_IFIND_MODE is 'nocase_collation'.
    email = sa.Column(sa.String(255, collation="NOCASE"), nullable=True, unique=True)
    email_confirmed_at = sa.Column(sa.DateTime())
    email_opt_in = sa.Column(sa.Boolean(), nullable=False, server_default="0")
    password = sa.Column(sa.String(255), nullable=False, server_default="")
    # User personal information
    first_name = sa.Column(
        sa.String(100, collation="NOCASE"), nullable=False, server_default=""
    )
    last_name = sa.Column(
        sa.String(100, collation="NOCASE"), nullable=False, server_default=""
    )
    # Define the relationship to Role via UserRoles
    roles = relationship("Role", "user_roles")

    def __str__(self):
        """
        Return a string representation of the User model.
        Only returns user ID to protect user privacy by default.
        """
        return f"User(id={self.id})"


# Define the Role data-model
class Role(db.Model):
    """
    Role Model for App roles.
    Currently unused.
    """

    __tablename__ = "roles"
    id = sa.Column(sa.Integer(), primary_key=True)
    name = sa.Column(sa.String(50), unique=True)


# Define the UserRoles association table


class UserRoles(db.Model):
    """
    UserRoles model which joins User to Role.
    """

    __tablename__ = "user_roles"
    id = sa.Column(sa.Integer(), primary_key=True)
    user_id = sa.Column(sa.Integer(), sa.ForeignKey("user.id", ondelete="CASCADE"))
    role_id = sa.Column(sa.Integer(), sa.ForeignKey("roles.id", ondelete="CASCADE"))


class Task(db.Model):
    """
    Task model for Task objects which contain
    Task descriptions as well as task metadata
    such as status, sprint, deadline, etc.
    """

    __tablename__ = "task"
    id = sa.Column(sa.Integer(), primary_key=True)
    task = sa.Column(sa.String(1024), nullable=False)
    story_id = sa.Column(sa.Integer(), sa.ForeignKey("story.id"), nullable=False)
    sprint_id = sa.Column(sa.Integer(), sa.ForeignKey("sprint.id"), nullable=True)
    estimate = sa.Column(sa.Float())
    actual = sa.Column(sa.Float())
    deadline = sa.Column(sa.Date())
    recurring = sa.Column(sa.Boolean(), nullable=False, server_default="0")
    status = sa.Column(sa.String(12), nullable=False, server_default="To-Do")
    user_id = sa.Column(sa.Integer(), sa.ForeignKey("user.id"))
    work_items = relationship("Work")
    schedules = relationship("ScheduleTask")

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class Tag(db.Model):
    """
    Tag model for story tags.
    Just an additional string to group stories differently from Epic.
    """

    __tablename__ = "tag"
    id = sa.Column(sa.Integer(), primary_key=True)
    tag = sa.Column(sa.String(255), nullable=False)
    user_id = sa.Column(sa.Integer, sa.ForeignKey("user.id"), nullable=False)
    stories = relationship("Story", "tag_story")


class Story(db.Model):
    """
    Story model for the Story object.
    Project object between Epic and Task level
    """

    __tablename__ = "story"
    id = sa.Column(sa.Integer(), primary_key=True)
    story = sa.Column(sa.String(255), nullable=False)
    epic_id = sa.Column(sa.Integer(), sa.ForeignKey("epic.id"), nullable=False)
    prioritization = sa.Column(sa.Integer(), server_default="1", nullable=False)
    deadline = sa.Column(sa.Date())
    user_id = sa.Column(sa.Integer(), sa.ForeignKey("user.id"), nullable=False)
    tasks = relationship("Task")
    tags = relationship("Tag", "tag_story")

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class TagStory(db.Model):
    """
    TagStory model which joins Story to Tag.
    """

    __tablename__ = "tag_story"
    id = sa.Column(sa.Integer(), primary_key=True)
    tag_id = sa.Column(sa.Integer(), sa.ForeignKey("tag.id"))
    story_id = sa.Column(sa.Integer(), sa.ForeignKey("story.id"))


class Epic(db.Model):
    """
    Epic model which defines the top level of project planning.
    """

    __tablename__ = "epic"
    id = sa.Column(sa.Integer(), primary_key=True)
    epic = sa.Column(sa.String(255), nullable=False)
    color = sa.Column(sa.String(12))
    deadline = sa.Column(sa.Date())
    user_id = sa.Column(sa.Integer, sa.ForeignKey("user.id"))
    stories = relationship("Story")
    tasks = relationship(
        "Task",
        "story",
        primaryjoin=Story.epic_id == id,
        secondaryjoin=Task.story_id == Story.id,
    )
    # tags = relationship('Tag','story')

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class Sprint(db.Model):
    """
    Sprint model for the sprint object which has
    a start date, end date, and
    is populated with tasks via Task.sprint_id
    """

    __tablename__ = "sprint"
    id = sa.Column(sa.Integer(), primary_key=True)
    start_date = sa.Column(sa.Date(), nullable=False)
    end_date = sa.Column(sa.Date(), nullable=False)
    user_id = sa.Column(sa.Integer(), sa.ForeignKey("user.id"), nullable=False)
    tasks = relationship("Task")
    stories = relationship("Story", "task")
    # epics = relationship('epic',secondary='story',tertiary='task')
    schedule = relationship("ScheduleTask")

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class ScheduleTask(db.Model):
    """
    Scheduling model which associates Tasks with
    particular day/time in a given sprint.
    Each ScheduleTask object can have a note
    associated with it.
    """

    __tablename__ = "schedule_task"
    id = sa.Column(sa.Integer(), primary_key=True)
    task_id = sa.Column(sa.Integer(), sa.ForeignKey("task.id"), nullable=False)
    sprint_id = sa.Column(sa.Integer(), sa.ForeignKey("sprint.id"), nullable=False)
    user_id = sa.Column(sa.Integer(), sa.ForeignKey("user.id"), nullable=False)
    sprint_day = sa.Column(sa.Date(), nullable=False)
    sprint_hour = sa.Column(sa.Integer(), nullable=False)
    schedule_time = sa.Column(sa.Numeric(), nullable=True)
    note = sa.Column(sa.String(2048), nullable=True)

    def to_dict(self):
        """
        Generate a dict representation of the ScheduleTask object.
        """
        return {
            "id": self.id,
            "task_id": self.task_id,
            "sprint_id": self.sprint_id,
            "sprint_day": str(self.sprint_day),
            "sprint_hour": self.sprint_hour,
            "schedule_time": self.schedule_time,
            "note": self.note,
        }
