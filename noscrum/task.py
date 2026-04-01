"""
Task View and Database Interaction Module
"""

import json
from datetime import date
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Form, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import (
    HTMLResponse,
    JSONResponse,
    PlainTextResponse,
    RedirectResponse,
)
from fastapi.templating import Jinja2Templates
from loguru import logger as _log
from sqlalchemy import Row, ScalarResult, Sequence, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import func, select

from noscrum.db import get_async_session, get_db
from noscrum.epic import get_epics, get_null_epic
from noscrum.model import Task, User
from noscrum.sprint import (
    get_current_sprint,
    get_next_sprint,
    get_sprint,
    get_sprint_number_for_user,
)
from noscrum.story import get_null_story_for_epic, get_stories, get_story
from noscrum.user import current_user


async def get_tasks(current_user: User, app_db: AsyncSession) -> Sequence[Row[Any]]:
    """
    Get every task record for the current user
    """
    results = await app_db.execute(
        text(
            "SELECT task.id, task, estimate, status, story_id, "
            + "epic_id, actual, task.deadline, task.recurring, "
            + "coalesce(hours_worked,0) hours_worked, "
            + "coalesce(sum_sched,0) sum_sched, "
            + "(task.sprint_ID = sched.sprint_id) single_sprint_task "
            + "FROM task "
            + "JOIN story ON task.story_id = story.id "
            + "LEFT OUTER JOIN (SELECT task_id, "
            + "sum(hours_worked) hours_worked "
            + "from work group by task_id) woik "
            + "ON woik.task_id = task.id "
            + "LEFT OUTER JOIN (select task_id, sprint_id, "
            + "count(1) * 2 sum_sched "
            + "FROM schedule_task group by task_id, sprint_id) sched "
            + "ON task.id = sched.task_id "
            + "WHERE task.user_id = :user_id"
        ),
        {"user_id": current_user.id},
    )
    return results.all()


async def get_task(task_id: int, current_user: User, app_db: AsyncSession) -> Task | None:
    """
    Task record for user for identifier number
    @task_id task record identification number
    """
    if current_user.id is None:
        raise ValueError("Cannot perform function without User ID")
    task = await app_db.execute(
        select(Task).where(Task.id == task_id).where(Task.user_id == current_user.id)
    )
    return task.scalar_one_or_none()


async def get_tasks_for_story(
    story_id: int, current_user: User, app_db: AsyncSession
) -> ScalarResult[Task]:
    """
    Get all task records for the current story
    @param story_id asked Story identification
    """
    if current_user.id is None:
        raise ValueError("Cannot perform function without User ID")
    query = select(Task).where(Task.story_id == story_id).where(Task.user_id == current_user.id)
    return (await app_db.execute(query)).scalars()


async def get_story_summary(current_user: User, app_db: AsyncSession) -> ScalarResult[Any]:
    """
    Get task summary for each story by task ID
    """
    return (
        await app_db.execute(
            select(
                Task.story_id,
                func.sum(Task.estimate).label("est"),
                func.count(Task.id).where(Task.estimate is None).label("unest"),
                func.count(Task.id),
                func.where(Task.status != "Done").label("incomplete"),
                func.count().label("task_count"),
            )
            .where(Task.user_id == current_user.id)
            .group_by(Task.story_id)
        )
    ).scalars()


async def get_tasks_for_epic(
    epic_id: int, current_user: User, app_db: AsyncSession
) -> ScalarResult[Task]:
    """
    Get all task records for a certain epic id
    @param epic_id Epic record identity number
    """
    if current_user.id is None:
        raise ValueError("Cannot perform function without User ID")
    return (
        await app_db.execute(
            select(Task).where(Task.story.epic_id == epic_id).where(Task.user_id == current_user.id)
        )
    ).scalars()


async def get_task_by_name(
    task: str, story_id: int, current_user: User, app_db: AsyncSession
) -> Task | None:
    """
    Get a task with a certain name in a sprint
    @param task Name of task being queried for
    @param story_id Identification for a story
    """
    if current_user.id is None:
        raise ValueError("Cannot perform function without User ID")
    return (
        await app_db.execute(
            select(Task)
            .where(Task.story_id == story_id)
            .where(Task.task == task)
            .where(Task.user_id == current_user.id)
        )
    ).scalar_one_or_none()


async def create_task(
    task: str,
    story_id: int,
    estimate: float | None,
    deadline: date | None,
    sprint_id: int | None,
    current_user: User,
    app_db: AsyncSession,
) -> Task:
    """
    Create a new task for a given story with.
    @param task Name of task being queried for
    @param story_id Identification for a story
    @param estimate number of hours estimation
    @param deadline date when task will be due
    @param sprint_id Sprint where task planned
    """
    if current_user.id is None:
        raise ValueError("User ID is None, cannot create task")
    newtask = Task(
        task=task,
        story_id=story_id,
        estimate=estimate,
        deadline=deadline,
        sprint_id=sprint_id,
        user_id=current_user.id,
        actual=None,
    )
    app_db.add(newtask)
    await app_db.commit()
    created_task = await get_task_by_name(task, story_id, current_user, app_db)
    if created_task is None:
        raise ValueError("Could not create task")
    return created_task


async def update_task(
    task_id: int,
    task: str | None,
    story_id: int | None,
    estimate: float | None,
    status: str | None,
    actual: float | None,
    deadline: date | None,
    sprint_id: int | None,
    recurring: bool | str | None,
    current_user: User,
    app_db: AsyncSession,
) -> Task:
    """
    Update the properties for an existing task.
    @task_id task record identification number.
    @param task Name of task being queried for.
    @param story_id Identification for a story.
    @param estimate number of hours estimation.
    @param actual hours spent to complete task.
    @param deadline date when task will be due.
    @param sprint_id Sprint where task planned.
    @param recurring does it recur each sprint.
    """
    query = select(Task).where(Task.id == task_id).where(Task.user_id == current_user.id)
    task_record = (await app_db.execute(query)).scalar_one()
    if task is not None:
        task_record.task = task
    if story_id is not None:
        task_record.story_id = story_id
    if estimate is not None:
        task_record.estimate = estimate
    if status is not None:
        task_record.status = status
    if actual is not None:
        task_record.actual = actual
    if deadline is not None:
        task_record.deadline = deadline
    if sprint_id is not None:
        task_record.sprint_id = sprint_id
    if recurring is not None:
        if (isinstance(recurring, str) or isinstance(recurring, int)) and recurring in [
            "1",
            1,
            "true",
            "T",
            "Y",
        ]:
            recurring = True
        else:
            recurring = False
        task_record.recurring = recurring
    await app_db.commit()
    updated_task = await get_task(task_id, current_user, app_db)
    if updated_task is None:
        raise ValueError("Could not create task")
    return updated_task


def task_delete(task_id: int, current_user: User, app_db: AsyncSession) -> int:
    """
    Delete task, task deletion not implemented
    """
    # Task.query.where(Task.id==task_id).where(Task.user_id==current_user.id).delete()
    # app_db.commit()
    raise NotImplementedError("Deleting Tasks is Not Supported")


router = APIRouter(prefix="/task", tags=["task"])
templates = Jinja2Templates(directory="templates")


def abort(response_code: int, message: str):
    return JSONResponse(status_code=response_code, content={"Error": {"message": message}})


@router.get("/frontend/create/{story_id}", response_class=HTMLResponse, tags=["frontend"])
async def fe_task_creation_template(
    request: Request,
    story_id: int,
    is_asc: bool = False,
    current_user: User = Depends(current_user),
    app_db: AsyncSession = Depends(get_async_session),
):
    """
    Handle creation requests for task in story
    GET: Get form to create a story's new task
    POST: Create task in story using the input
    @param story_id story in which task will be
    """
    _log.debug("Sending task creation form for story {}, is_asc? {}", story_id, str(is_asc))
    story = await get_story(story_id, current_user, app_db)
    if not story:
        error = f"Cannot create task, parent story ID {story_id} not found"
        return abort(404, error)
    return templates.TemplateResponse(
        "task/fragments/create.html",
        {"request": request, "story": story, "asc": is_asc, "current_user": current_user},
    )


@router.put("/create/{story_id}")
async def task_create(
    story_id: int,
    taskname: str,
    estimate: float | None,
    epic_id: int = 0,
    current_user: User = Depends(current_user),
    app_db: AsyncSession = Depends(get_async_session),
):
    _log.debug("Creating task {} for story {}", taskname, story_id)
    story = await get_story(story_id, current_user, app_db)
    if story is None:
        error = f"Cannot create task, parent story ID {story_id} not found"
        return abort(404, error)
    error = None
    if story_id == 0:
        if epic_id == 0:
            epic = await get_null_epic(current_user, app_db)
            if epic is None or epic.id is None:
                return abort(500, "Could not get or create Null epic")
            epic_id = epic.id
        story = await get_null_story_for_epic(epic_id, current_user, app_db)
        if story is None or story.id is None:
            return abort(500, "Could not get or create Null story")
        story_id = story.id
    if (await get_task_by_name(taskname, story_id, current_user, app_db)) is not None:
        error = f"Task {taskname} already in Story {story_id}"
    if error is None:
        task_create = await create_task(
            taskname, story_id, estimate, None, None, current_user, app_db
        )
        if task_create is None:
            return PlainTextResponse("Could not create task: unknown error")
        return JSONResponse({"Success": True, "task": jsonable_encoder(task_create)})
    return abort(500, error)


@router.get("/frontend/{task_id}", tags=["frontend"], response_class=HTMLResponse)
async def fe_task_show(
    request: Request,
    task_id: int,
    current_user: User = Depends(current_user),
    app_db = Depends(get_db),
):
    """
    Show details of the specific task given id
    GET: Get a task's information nothing else
    POST: Update the task given input provided
    @param task_id Task Identity being queried
    """
    task = await get_task(task_id, current_user, app_db)
    if not task:
        error = f"Task with ID {task_id} not found"
        return abort(404, error)
    current_sprint = await get_current_sprint(current_user, app_db)
    return templates.TemplateResponse(
        "task/show.html", {"request": request, "task": task, "current_user": current_user, "current_sprint": current_sprint}
    )

@router.post("/{task_id}", tags=["frontend"], response_class=HTMLResponse)
async def fe_list_task_update(
    request: Request,
    task_id: int,
    task: Annotated[Task, Form()],
    current_user=Depends(current_user),
    app_db: AsyncSession = Depends(get_async_session),
):
    _log.debug("Updating task {} with id {}", task, task_id)
    api_resp = await task_api_update(task_id, task, current_user, app_db)
    if api_resp.status_code != 200:
        return api_resp
    current_sprint = await get_current_sprint(current_user, app_db)
    return templates.TemplateResponse(
        "task/fragments/list_task.html", {"request": request, "task": task, "current_user": current_user, "current_sprint": current_sprint}
    )


@router.put("/{task_id}")
async def task_api_update(
    task_id: int,
    task: Task,
    current_user=Depends(current_user),
    app_db: AsyncSession = Depends(get_async_session),
) -> JSONResponse:
    error = None
    # TODO: Handle this in model
    if task.status not in ["To-Do", "In Progress", "Done"]:
        error = "Status is invalid. Valid statuses are ['To-Do','In Progress','Done']"
    old_task = await get_task(task_id, current_user, app_db)
    if old_task is None:
        raise ValueError("No task found with provided ID")

    story = await get_story(old_task.story_id, current_user, app_db)
    if story is None:
        error = f"Story with ID {task.story_id} not found"
    elif (
        task.sprint_id is not None
        and (await get_sprint(task.sprint_id, current_user, app_db)) is None
    ):
        error = f"Sprint {task.sprint_id} not found."

    if error is None:
        task_nullable = await update_task(
            task_id,
            task.task,
            task.story_id,
            task.estimate,
            task.status,
            task.actual,
            task.deadline,
            task.sprint_id,
            task.recurring,
            current_user,
            app_db,
        )
        if task_nullable is None:
            return abort(500, "Task update did not return a task.")
        task = task_nullable
        return JSONResponse(content=jsonable_encoder(task))
    return abort(500, error)


@router.get("/frontend", tags=["frontend"], response_class=HTMLResponse)
async def fe_task_list_all(
    request: Request,
    current_user=Depends(current_user),
    app_db: AsyncSession = Depends(get_async_session),
):
    """
    Task showcase: lists epics stories & tasks
    """
    if current_user is None:
        return RedirectResponse("/user/login")
    _log.debug("GETTING TASKS")
    tasks = [
        {key: value for key, value in zip(task._fields, task.tuple())}
        for task in (await get_tasks(current_user, app_db))
    ]
    stories = await get_stories(current_user, app_db)
    epics = await get_epics(current_user, app_db)

    colors = ["primary", "secondary", "success", "alert", "warning"]
    current_sprint = await get_current_sprint(current_user, app_db)
    sprint_number = {}
    if current_sprint is not None:
        sprint_number[current_sprint.id] = await get_sprint_number_for_user(
            current_sprint.id, current_user, app_db
        )
    next_sprint = await get_next_sprint(current_user, app_db)
    if next_sprint is not None:
        sprint_number[next_sprint.id] = await get_sprint_number_for_user(
            next_sprint.id, current_user, app_db
        )
    return templates.TemplateResponse(
        "task/list.html",
        {
            "request": request,
            "current_user": current_user,
            "current_sprint": current_sprint,
            "next_sprint": next_sprint,
            "sprint_number": sprint_number,
            "tasks": tasks,
            "epics": epics,
            "stories": stories,
            "colors": colors,
        },
    )


@router.get("/frontend/list/{story_id}", response_class=HTMLResponse, tags=["frontend"])
async def fe_tasks_list_for_story(
    request: Request,
    story_id: int,
    frag: bool = True,
    current_user: User = Depends(current_user),
    app_db: AsyncSession = Depends(get_async_session),
):
    tasks = await get_tasks_for_story(story_id, current_user, app_db)
    current_sprint = get_current_sprint(current_user, app_db)
    return templates.TemplateResponse(
        f"task/{'fragments/' if frag else '/story_'}list.html",
        {
            "request": request,
            "tasks": tasks,
            "current_sprint": current_sprint,
            "current_user": current_user,
        },
    )


@router.get("/")
async def list_all_backend(current_user=Depends(current_user), app_db=Depends(get_db)):
    if current_user is None:
        return RedirectResponse("/user/login")
    tasks = await get_tasks(current_user, app_db)
    stories = await get_stories(current_user, app_db)

    epics = await get_epics(current_user, app_db)
    # colors = ["primary", "secondary", "success", "alert", "warning"]
    current_sprint = await get_current_sprint(current_user, app_db)
    sprint_number = dict()
    if current_sprint is not None:
        sprint_number[current_sprint.id] = get_sprint_number_for_user(
            current_sprint.id, current_user, app_db
        )
    next_sprint = await get_next_sprint(current_user, app_db)
    if next_sprint is not None and current_sprint is not None:
        sprint_number[next_sprint.id] = get_sprint_number_for_user(
            next_sprint.id, current_user, app_db
        )
        return JSONResponse(
            {
                "Success": True,
                "tasks": [dict(x) for x in tasks],
                "epics": [dict(x) for x in epics],
                "stories": [dict(x) for x in stories],
                "current_sprint": current_sprint.id,
            }
        )
    return JSONResponse({"Success": False, "error": "Could not find current or next sprint"})
