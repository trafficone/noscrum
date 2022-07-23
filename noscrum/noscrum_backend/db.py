"""
Database Models and Controller (not much to do, thanks SQLAlchemy!)
"""
# pylint: disable=too-few-public-methods
import logging
from datetime import date
from collections.abc import Hashable, Iterable
import sqlalchemy as sa
from sqlalchemy.orm import relationship
from noscrum.noscrum_api import app_db

logger = logging.getLogger()
"""
    # TODO: Unused Import is implicitly used by DB, but this prevents import cycle
    from noscrum.noscrum_backend.db import (  # pylint: disable=unused-import,import-outside-toplevel
        User,  # pylint: disable=unused-import
        Role,  # pylint: disable=unused-import
        Task,  # pylint: disable=unused-import
        Story,  # pylint: disable=unused-import
        Epic,  # pylint: disable=unused-import
        Tag,  # pylint: disable=unused-import
        TagStory,  # pylint: disable=unused-import
        Sprint,  # pylint: disable=unused-import
        Work,  # pylint: disable=unused-import
        UserRoles,  # pylint: disable=unused-import
        ScheduleTask,  # pylint: disable=unused-import
    )
"""
db = app_db

if db is not None:

    def get_db():
        return db

    class DictableModel:
        @property
        def __table__(self):
            return NotImplemented

        def to_dict(self):
            ret = {}
            for c in self.__table__.columns:
                k = c.name
                v = getattr(self, c.name)
                if isinstance(v, Hashable):
                    pass
                elif isinstance(v, Iterable):
                    v = [x.to_dict() for x in v]
                elif isinstance(v, date):
                    v = str(v)
                elif hasattr(v, "to_dict"):
                    v = v.to_dict()
                ret[k] = v
            return ret

        @classmethod
        def from_dict(cls, input_dict):
            if set(input_dict.keys()) != set([c.name for c in cls.__table__.columns]):
                raise ValueError(
                    f'Input dictionary not compatible with class "{cls.__name__}"'
                )
            return cls(input_dict)

    class Work(db.Model):
        """
        Model class for task work objects.
        Tracks the number of hours worked on a specific task.
        """

        __tablename__ = "work"
        id = sa.Column(sa.Integer(), primary_key=True)
        work_date = sa.Column(sa.Date(), nullable=False)
        hours_worked = sa.Column(sa.Float(), nullable=False)
        task_id = sa.Column(sa.Integer(), sa.ForeignKey("task.id"))
        status = sa.Column(sa.String(12), nullable=True, default="To-Do")
        user_id = sa.Column(sa.Integer(), sa.ForeignKey("user.id"))
        # alter table work add column sprint_id; update work set sprint_id = task.sprint_id from task where task_id = task.id;
        # update work set sprint_id = sprint.id from sprint where work_date between sprint.start_date and sprint.end_date;
        sprint_id = sa.Column(sa.Integer, sa.ForeignKey("sprint.id"))

        def to_dict(self):
            return {
                "id": self.id,
                "work_date": str(self.work_date),
                "hours_worked": self.hours_worked,
                "task_id": self.task_id,
                "status": self.status,
                "user_id": self.user_id,
                "sprint_id": self.sprint_id,
            }

        @classmethod
        def from_dict(cls, input_dict):
            if set(input_dict.keys()) != set(cls.__table__.columns.keys()):
                raise ValueError('Invalid Input dict of type "Work"')
            _ = input_dict.pop("story_id")
            return cls(input_dict)

    class User(db.Model):
        """
        User model. Contains all properties for a user.
        """

        __tablename__ = "user"
        id = sa.Column(sa.Integer(), primary_key=True)
        username = sa.Column(sa.String(100), nullable=False, unique=True)
        active = sa.Column(
            "is_active", sa.Boolean(), nullable=False, server_default="1"
        )

        # User auth information.
        # User authentication information. The collation='NOCASE' is required
        # to search case insensitively when USER_IFIND_MODE is 'nocase_collation'.
        email = sa.Column(
            sa.String(255, collation="NOCASE"), nullable=True, unique=True
        )
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
        preferences = relationship("UserPreference")

        def __str__(self):
            """
            Return a string representation of the User model.
            Only returns user ID to protect user privacy by default.
            """
            return f"User(id={self.id})"

    class UserPreference(db.Model, DictableModel):
        """
        User Preferences - generic key-value store
        """

        __tablename__ = "user_preference"
        id = sa.Column(sa.Integer(), primary_key=True)
        user_id = sa.Column(
            sa.Integer(), sa.ForeignKey("user.id", ondelete="CASCADE"), primary_key=True
        )
        user = relationship("User")
        preference = sa.Column(sa.String(1024), primary_key=True)
        value = sa.Column(sa.String(5000))

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

    class Task(db.Model, DictableModel):
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
        story = relationship("Story")

        def __lt__(self, other):
            if not isinstance(other, Task):
                raise TypeError("Cannot compare Task with non-Task object")
            if self.deadline is None:
                return False
            if other.deadline is None:
                return True
            return self.deadline < other.deadline

        def __gt__(self, other):
            return not self < other

    class Tag(db.Model, DictableModel):
        """
        Tag model for story tags.
        Just an additional string to group stories differently from Epic.
        """

        __tablename__ = "tag"
        id = sa.Column(sa.Integer(), primary_key=True)
        tag = sa.Column(sa.String(255), nullable=False)
        user_id = sa.Column(sa.Integer, sa.ForeignKey("user.id"), nullable=False)
        stories = relationship("Story", "tag_story")

    class Story(db.Model, DictableModel):
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
        closure_state = sa.Column(
            sa.String(16)
        )  # Valid entries are "Closed" and "Cancelled"
        tasks = relationship("Task")
        tags = relationship("Tag", "tag_story")
        epic = relationship("Epic")

        def to_dict(self):
            """
            Return Story object representation val
            As a newly created dictionary object
            """
            ret = {}
            for c in self.__table__.columns:
                k = c.name
                v = getattr(self, c.name)
                if isinstance(v, date):
                    v = str(v)
                ret[k] = v
            ret["tasks"] = [x.to_dict() for x in self.tasks]
            ret["tags"] = [x.to_dict() for x in self.tags]
            return ret

        def __lt__(self, other):
            if not isinstance(other, Story):
                raise TypeError("Cannot compare Story to non-Story")
            if other.prioritization > self.prioritization:
                return True
            if other.prioritization < self.prioritization:
                return False
            # prioritizations are equal
            if self.deadline is None:
                return False
            if other.deadline is None:
                return True
            return self.deadline < other.deadline

        def __gt__(self, other):
            return not self < other

    class TagStory(db.Model):
        """
        TagStory model which joins Story to Tag.
        """

        __tablename__ = "tag_story"
        id = sa.Column(sa.Integer(), primary_key=True)
        tag_id = sa.Column(sa.Integer(), sa.ForeignKey("tag.id"))
        story_id = sa.Column(sa.Integer(), sa.ForeignKey("story.id"))

    class Epic(db.Model, DictableModel):
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

    class Sprint(db.Model, DictableModel):
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
        task = relationship(Task)

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
                "schedule_time": float(self.schedule_time),
                "note": self.note,
            }
