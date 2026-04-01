"""
Data handler for work view and controller
"""

from datetime import date

from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import ScalarResult, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import delete, select

from noscrum.db import get_db
from noscrum.epic import get_epic
from noscrum.model import User, Work
from noscrum.story import get_story
from noscrum.task import (
    get_task,
    get_tasks,
    get_tasks_for_epic,
    get_tasks_for_story,
    update_task,
)
from noscrum.user import current_user


async def create_work(
    work_date: date,
    hours_worked: float,
    status: str,
    task_id: int,
    new_actual: float,
    update_status: str,
    current_user: User,
    app_db: AsyncSession,
) -> Work:
    """
    Create new work for task on the given date.
    @param work_date when some action was done.
    @param hours_worked number of hours worked.
    @param status a new task status given work.
    @param task_id task which work is executed.
    @param new_actual task actual hours worked.
    @param update_status boolean update status.
    """
    if current_user.id is None:
        raise ValueError("Cannot perform function without User ID")
    new_work = Work(
        work_date=work_date,
        hours_worked=hours_worked,
        status=status,
        task_id=task_id,
        user_id=current_user.id,
    )
    app_db.add(new_work)
    new_status = status if update_status else None
    await update_task(
        task_id, None, None, None, new_status, new_actual, None, None, None, current_user, app_db
    )
    await app_db.commit()
    new_work_result = await get_work(new_work.id, current_user, app_db)
    if new_work_result is None:
        raise ValueError("Could not get new work record")
    return new_work_result


async def get_work(work_id: int, current_user: User, app_db: AsyncSession) -> Work | None:
    """
    Get work record from identification number
    @param work_id work record identity number
    """
    if current_user.id is None:
        raise ValueError("Cannot perform function without User ID")
    return (
        await app_db.execute(
            select(Work).where(Work.id == work_id).where(Work.user_id == current_user.id)
        )
    ).scalar_one_or_none()


async def get_work_for_task(
    task_id: int, current_user: User, app_db: AsyncSession
) -> ScalarResult[Work]:
    """
    Get the work records given the task record
    @param task_id task record work is queried
    """
    if current_user.id is None:
        raise ValueError("Cannot perform function without User ID")
    return (
        await app_db.execute(
            select(Work).where(Work.task_id == task_id).where(Work.user_id == current_user.id)
        )
    ).scalars()


async def get_work_for_story(
    story_id: int, current_user: User, app_db: AsyncSession
) -> ScalarResult[Work]:
    """
    Get the work for a particular story record
    @param story_id a Story record locator val
    """
    if current_user.id is None:
        raise ValueError("Cannot perform function without User ID")
    return (
        await app_db.execute(
            select(Work).where(Work.story.id == story_id).where(Work.user_id == current_user.id)
        )
    ).scalars()


async def get_work_for_epic(epic_id: int, current_user: User, app_db: AsyncSession) -> list[Work]:
    """
    Get all work records under the epic record
    @param epic_id epic for which work queried
    """
    if current_user.id is None:
        raise ValueError("Cannot perform function without User ID")
    all_work = (
        await app_db.execute(
            text(
                "SELECT work.id, task_id, work_date, hours_worked, status "
                + "FROM work JOIN task on work.task_id = task.id "
                + "JOIN story ON task.story_id = story.id "
                + " WHERE story.epic_id = :epic_id "
                + " AND story.user_id = :current_user "
                + "order by work_date"
            ),
            {"epic_id": epic_id, "current_user": current_user.id},
        )
    ).scalars()
    return list(Work(**w) for w in all_work)


async def get_work_by_dates(
    start_date: date, end_date: date, current_user: User, app_db: AsyncSession
) -> list[Work]:
    """
    Get work executed between two dates values
    @param start_date date request lower limit
    @param end_date date requested upper limit
    """
    if current_user.id is None:
        raise ValueError("Cannot perform function without User ID")
    all_work = (
        await app_db.execute(
            text(
                "SELECT id, task_id, work_date, hours_worked, status FROM work "
                + "WHERE work_date BETWEEN :start and :end AND user_id = :current_user "
                + " order by work_date"
            ),
            {"start": start_date, "end": end_date, "current_user": current_user.id},
        )
    ).scalars()
    return list(Work(**w) for w in all_work)


async def delete_work(work_id: int, current_user: User, app_db: AsyncSession) -> int:
    """
    Delete work record given a certain identiy
    @param work_id a work record to be deleted
    """
    if current_user.id is None:
        raise ValueError("Cannot perform function without User ID")
    work = await get_work(work_id, current_user, app_db)
    if work is None:
        return work_id
    await app_db.execute(
        delete(Work).where(Work.id == work_id).where(Work.user_id == current_user.id)
    )
    await app_db.commit()
    return work_id


router = APIRouter(prefix="/work", tags=["work"])

templates = Jinja2Templates(directory="templates")


def abort(response_code: int, message: str):
    return JSONResponse(status_code=response_code, content={"Error": {"message": message}})


@router.get("/create/{task_id}", response_class=HTMLResponse)
async def get_create_form(
    task_id: int, current_user: User = Depends(current_user), app_db=Depends(get_db)
):
    """
    Handle requests to create work on the task
    GET: Return form to create new work record
    POST: Create new work record for some task
    @param task_id task which work is executed
    """
    task = await get_task(task_id, current_user, app_db)
    if task is None:
        error = f"Task {task_id} Not Found"
        return abort(404, error)
    return templates.TemplateResponse("work/create.html", {"task": task})


@router.put("/create/{task_id}")
async def api_create_work(
    task_id: int, work: Work, current_user: User = Depends(current_user), app_db=Depends(get_db)
):
    true_actual = sum(
        [x.hours_worked for x in await get_work_for_task(task_id, current_user, app_db)]
    )
    new_actual = work.hours_worked if true_actual is None else true_actual + work.hours_worked
    await create_work(
        work.work_date,
        work.hours_worked,
        work.status,
        task_id,
        new_actual,
        work.status,
        current_user,
        app_db,
    )
    return JSONResponse({"Success": True, "work": jsonable_encoder(work)})


@router.get("/{work_id}")
async def api_read(
    work_id: int,
    is_json: bool = False,
    current_user: User = Depends(current_user),
    app_db=Depends(get_db),
):
    """
    Handle read or deletes on some work record
    GET: Information regarding specific record
    DELETE: Delete work record with identifier
    @param work_id work record identifier code
    """
    work_item = await get_work(work_id, current_user, app_db)
    if work_item is None:
        error = f"Work Item {work_id} Not Found"
        return abort(404, error)
    if is_json:
        return JSONResponse({"Success": True, "work_id": work_id, "work_item": work_item})
    return templates.TemplateResponse("work/read_del", {"work_item": work_item})


@router.delete("/{work_id}")
async def api_delete(
    work_id: int,
    is_json: bool = False,
    current_user: User = Depends(current_user),
    app_db=Depends(get_db),
):
    work_item = await get_work(work_id, current_user, app_db)
    if work_item is None:
        error = f"Work Item {work_id} Not Found"
        return abort(404, error)
    _ = await delete_work(work_id, current_user, app_db)
    if is_json:
        return JSONResponse({"Success": True, "work": jsonable_encoder(work_item)})
    return RedirectResponse(router.url_path_for("work.list_for_task", task_id=work_item.task_id))


@router.get("/list/task/{task_id}")
async def list_for_task(
    task_id: int,
    is_json: bool = False,
    current_user: User = Depends(current_user),
    app_db=Depends(get_db),
):
    """
    Return all work records for the given task
    GET: route provides the response described
    @param task_id task record was executed on
    """
    tasks = await get_task(task_id, current_user, app_db)
    if tasks is None:
        error = f"Task Item {task_id} not found"
        return abort(404, error)
    work_items = await get_work_for_task(task_id, current_user, app_db)
    if work_items is None:
        error = f"No Work Items found for Task {task_id}"
        return abort(404, error)
    if is_json:
        return JSONResponse({"Sucecss": True, "work_items": work_items})
    return templates.TemplateResponse(
        "work/list.html", {"key": "Task", "tasks": tasks, "work_items": work_items}
    )


@router.get("/list/story/{story_id}")
async def list_for_story(
    story_id: int,
    is_json: bool = False,
    current_user: User = Depends(current_user),
    app_db=Depends(get_db),
):
    """
    List all work completed on tasks for story
    GET: route provides the response described
    @param story_id story where work described
    """
    story = await get_story(story_id, current_user, app_db)
    if story is None:
        error = "Story Item not found"
        return abort(404, error)
    tasks = await get_tasks_for_story(story_id, current_user, app_db)
    if tasks is None:
        error = f"No Tasks found for Story {story_id}"
        return abort(404, error)
    work_items = await get_work_for_story(story_id, current_user, app_db)
    if work_items is None:
        error = f"No Work Items found for Story {story_id}"
        return abort(404, error)
    if is_json:
        return JSONResponse({"Sucecss": True, "work_items": work_items})
    return templates.TemplateResponse(
        "work/list.html",
        {"key": "Story " + story.story, "tasks": tasks, "work_items": work_items},
    )


@router.get("/list/epic/{epic_id}")
async def list_for_epic(
    epic_id: int,
    is_json: bool = False,
    current_user: User = Depends(current_user),
    app_db=Depends(get_db),
):
    """
    List work completed on tasks an epic holds
    GET: route provides the response described
    @param epic_id record identity for an epic
    """
    epic = await get_epic(epic_id, current_user, app_db)
    if epic is None:
        error = "Epic Item not found"
        return abort(404, error)
    tasks = await get_tasks_for_epic(epic_id, current_user, app_db)
    if tasks is None:
        error = "No Tasks found for Epic {epic.id}"
        return abort(404, error)
    work_items = await get_work_for_epic(epic_id, current_user, app_db)
    if work_items is None:
        error = f"No Work Items found for Epic {epic.id}"
        return abort(404, error)
    if is_json:
        return JSONResponse({"Sucecss": True, "work_items": work_items})
    return templates.TemplateResponse(
        "work/list.html",
        {"key": "Epic " + epic.epic, "tasks": tasks, "work_items": work_items},
    )


@router.get("/frontend/list/dates", response_class=HTMLResponse)
async def list_for_dates(
    is_json: bool = False,
    start_date: date = date(2020, 1, 1),
    end_date: date = date.today(),
    current_user: User = Depends(current_user),
    app_db=Depends(get_db),
):
    """
    List all work completed within given dates
    GET: route provides the response described
    """
    work_items = await get_work_by_dates(start_date, end_date, current_user, app_db)
    if work_items is None:
        error = "No work items found between dates_provided"
        return abort(404, error)
    all_tasks = await get_tasks(current_user, app_db)
    task_ids = [x.task_id for x in work_items]
    tasks = []
    for task in all_tasks:
        if task.id in task_ids:
            tasks.append(task)
    if is_json:
        return JSONResponse({"Success": True, "work_items": work_items})
    return templates.TemplateResponse(
        "work/list.html",
        {
            "key": f"Dates from {start_date} to {end_date}",
            "tasks": tasks,
            "work_items": work_items,
        },
    )
