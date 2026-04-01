# pylint: disable=no-self-argument
"""
Database Models and Controller (not much to do, thanks SQLAlchemy!)
"""

# pylint: disable=too-few-public-methods
from collections.abc import Hashable, Iterable
from datetime import date

from sqlalchemy.orm import DeclarativeBase
from sqlmodel import Field, Relationship, SQLModel


class Base(DeclarativeBase):
    pass


class DictableModel(DeclarativeBase):
    """Interface class - any DB Model which can be converted to a dict by implementing to_dict()"""

    def to_dict(self):
        """
        Default transformation of table to dict object
        """
        ret = {}
        for column in self.__table__.columns:  # pylint: disable=no-member
            key = column.name
            value = getattr(self, column.name)
            if isinstance(value, Hashable):
                pass
            elif isinstance(value, Iterable):
                value = [x.to_dict() for x in value]
            elif isinstance(value, date):
                value = str(value)
            elif hasattr(value, "to_dict"):
                value = value.to_dict()
            ret[key] = value
        return ret

    @classmethod
    def from_dict(cls, input_dict):
        """
        Coerce dict object into table.
        """
        if set(input_dict.keys()) != {c.name for c in cls.__table__.columns}:
            raise ValueError(f'Input dictionary not compatible with class "{cls.__name__}"')
        return cls(**input_dict)


class User(SQLModel, table=True):
    """
    User model. Contains all properties for a user.
    """

    # The following are created by SQLAlchemyBaseUserTableUUID
    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True, nullable=False)
    hashed_password: str = Field(nullable=False)
    is_active: bool = Field(default=True, nullable=False)
    is_superuser: bool = Field(default=False, nullable=False)
    is_verified: bool = Field(default=False, nullable=False)
    username: str = Field(unique=True, index=True, nullable=False)
    email_opt_in: bool = Field(default=False)
    # User personal information
    first_name: str = Field(default="")
    last_name: str = Field(default="")

    def __str__(self):
        """
        Return a string representation of the User model.
        Only returns user ID to protect user privacy by default.
        """
        return f"User(id={self.id})"

class UserSettings(SQLModel, table=True):
    """
    User settings model.
    """
    # Settings
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")



class TagStory(SQLModel, table=True):
    """
    TagStory model which joins Story to Tag.
    """

    id: int | None = Field(default=None, primary_key=True)
    tag_id: int = Field(foreign_key="tag.id", default=None)
    story_id: int = Field(foreign_key="story.id", default=None)


class Story(SQLModel, table=True):
    """
    Story model between Epic and Task
    """

    id: int | None = Field(default=None, primary_key=True)
    story: str = Field(nullable=False)
    epic_id: int = Field(foreign_key="epic.id")
    epic: "Epic" = Relationship(back_populates="stories")
    prioritization: int = Field(default=1)
    deadline: date | None = Field(default=None)
    user_id: int = Field(foreign_key="user.id")
    tasks: list["Task"] = Relationship(back_populates="story")
    tags: list["Tag"] = Relationship(back_populates="stories", link_model=TagStory)
    # sprints: list["Sprint"] = Relationship(back_populates="stories", link_model="Task")


class Tag(SQLModel, table=True):
    """
    Tag model for story tags.
    Just an additional string to group stories differently from Epic.
    """

    # __tablename__ = "tag"
    id: int | None = Field(default=None, primary_key=True)
    tag: str
    user_id: int = Field(foreign_key="user.id")
    stories: list[Story] = Relationship(back_populates="tags", link_model=TagStory)


class Task(SQLModel, table=True):
    """
    Task model for Task objects which contain
    Task descriptions as well as task metadata
    such as status, sprint, deadline, etc.
    """

    # __tablename__ = "task"
    id: int | None = Field(default=None, primary_key=True)
    task: str
    story_id: int = Field(default=None, foreign_key="story.id")
    story: Story = Relationship(back_populates="tasks")
    sprint_id: int | None = Field(default=None, foreign_key="sprint.id")
    sprint: "Sprint" = Relationship(back_populates="tasks")
    estimate: float | None
    actual: float | None
    deadline: date | None
    recurring: bool = Field(default=False, nullable=False)
    status: str = Field(default="To-Do")
    user_id: int = Field(foreign_key="user.id")
    work_items: list["Work"] = Relationship(back_populates="task")
    schedules: list["ScheduleTask"] = Relationship(back_populates="scheduletask")


class Work(SQLModel, table=True):
    """
    Model class for task work objects.
    Tracks the number of hours worked on a specific task.
    """

    # __tablename__ = "work"
    id: int | None = Field(default=None, primary_key=True)
    work_date: date
    hours_worked: float
    task_id: int = Field(default=None, foreign_key="task.id")
    task: Task = Relationship(back_populates="work_items")
    status: str = Field(default="To-Do", nullable=True)
    user_id: int = Field(default=None, foreign_key="user.id")
    story: list["Story"] = Relationship(link_model=Task)


class Epic(SQLModel, table=True):
    """
    Epic model which defines the top level of project planning.
    """

    # __tablename__ = "epic"
    id: int | None = Field(default=None, primary_key=True)
    epic: str
    color: str = Field(default="green")
    deadline: date | None
    user_id: int = Field(foreign_key="user.id")
    stories: list["Story"] = Relationship(back_populates="epic")
    # tasks: list[Task] = Relationship(back_populates='task', 'story',
    #                     primaryjoin=Story.epic_id == id,
    #                     secondaryjoin=Task.story_id == Story.id)
    # tags = relationship('Tag','story')


class Sprint(SQLModel, table=True):
    """
    Sprint model for the sprint object which has
    a start date, end date, and
    is populated with tasks via Task.sprint_id
    """

    # __tablename__ = "sprint"
    id: int | None = Field(default=None, primary_key=True)
    start_date: date
    end_date: date
    user_id: int = Field(foreign_key="user.id")
    tasks: list[Task] = Relationship(back_populates="sprint")
    # stories: list[Story] = Relationship(link_model=Task)
    # epics = relationship('epic',secondary='story',tertiary='task')
    schedule: list["ScheduleTask"] = Relationship(back_populates="schedulesprint")


class ScheduleTask(SQLModel, table=True):
    """
    Scheduling model which associates Tasks with
    particular day/time in a given sprint.
    Each ScheduleTask object can have a note
    associated with it.
    """

    # __tablename__ = "schedule_task"
    __name__ = "schedule_task"
    id: int | None = Field(default=None, primary_key=True)
    task_id: int = Field(foreign_key="task.id")
    scheduletask: Task = Relationship(back_populates="schedules")
    sprint_id: int = Field(foreign_key="sprint.id")
    schedulesprint: Sprint = Relationship(back_populates="schedule")
    user_id: int = Field(foreign_key="user.id")
    sprint_day: date
    sprint_hour: int
    note: str | None
    recurring: bool

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
            "note": self.note,
        }
