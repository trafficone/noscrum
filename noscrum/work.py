"""
Data handler for work view and controller
"""
from datetime import date

from fastapi import APIRouter
from fastapi.encoders import jsonable_encoder
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from noscrum.db import get_db
from noscrum.epic import get_epic
from noscrum.model import Work
from noscrum.story import get_story
from noscrum.task import (
    get_task,
    get_tasks,
    get_tasks_for_epic,
    get_tasks_for_story,
    update_task,
)
from noscrum.user import current_user


def create_work(work_date, hours_worked, status, task_id, new_actual, update_status):
    """
    Create new work for task on the given date
    @param work_date when some action was done
    @param hours_worked number of hours worked
    @param status a new task status given work
    @param task_id task which work is executed
    @param new_actual task actual hours worked
    @param update_status boolean update status
    """
    app_db = get_db()
    new_work = Work(
        work_date=work_date, hours_worked=hours_worked, status=status, task_id=task_id
    )
    app_db.session.add(new_work)
    new_status = status if update_status else None
    update_task(task_id, None, None, None, new_status, new_actual, None, None, None)
    app_db.session.commit()


def get_work(work_id):
    """
    Get work record from identification number
    @param work_id work record identity number
    """
    return (
        Work.query.filter(Work.id == work_id)
        .filter(Work.user_id == current_user.id)
        .first()
    )


def get_work_for_task(task_id):
    """
    Get the work records given the task record
    @param task_id task record work is queried
    """
    return (
        Work.query.filter(Work.task_id == task_id)
        .filter(Work.user_id == current_user.id)
        .all()
    )


def get_work_for_story(story_id):
    """
    Get the work for a particular story record
    @param story_id a Story record locator val
    """
    return (
        Work.query.filter(Work.story.id == story_id)
        .filter(Work.user_id == current_user.id)
        .all()
    )


def get_work_for_epic(epic_id):
    """
    Get all work records under the epic record
    @param epic_id epic for which work queried
    """
    app_db = get_db()
    return Work(
        *app_db.execute(
            "SELECT work.id, task_id, work_date, hours_worked, status "
            + "FROM work JOIN task on work.task_id = task.id "
            + "JOIN story ON task.story_id = story.id "
            + " WHERE story.epic_id = ? order by work_date",
            (epic_id,),
        ).fetchall()
    )


def get_work_by_dates(start_date, end_date):
    """
    Get work executed between two dates values
    @param start_date date request lower limit
    @param end_date date requested upper limit
    """
    app_db = get_db()
    return Work(
        *app_db.execute(
            "SELECT id, task_id, work_date, hours_worked, status FROM work "
            + "WHERE work_date BETWEEN ? and ? order by work_date",
            (start_date, end_date),
        ).fetchall()
    )


def delete_work(work_id):
    """
    Delete work record given a certain identiy
    @param work_id a work record to be deleted
    """
    app_db = get_db()
    work = get_work(work_id)
    Work.query.filter(Work.id == work_id).filter(
        Work.user_id == current_user.id
    ).delete()
    app_db.session.commit()
    return work.id


router = APIRouter(prefix="/work", tags=["work"])

templates = Jinja2Templates(directory="templates")


def abort(response_code: int, message: str):
    return JSONResponse(
        status_code=response_code, content={"Error": {"message": message}}
    )


@router.get("/create/{task_id}", response_class=HTMLResponse)
def get_create_form(task_id: int):
    """
    Handle requests to create work on the task
    GET: Return form to create new work record
    POST: Create new work record for some task
    @param task_id task which work is executed
    """
    task = get_task(task_id)
    if task is None:
        error = f"Task {task_id} Not Found"
        return abort(404, error)
    return templates.TemplateResponse("work/create.html", {"task": task})


@router.put("/create/{task_id}")
def api_create_work(task_id: int, work: Work):
    true_actual = sum([x.hours_worked for x in get_work_for_task(task_id)])
    new_actual = (
        work.hours_worked if true_actual is None else true_actual + work.hours_worked
    )
    create_work(
        work.work_date,
        work.hours_worked,
        work.status,
        task_id,
        new_actual,
        work.update_status,
    )
    return JSONResponse({"Success": True, "work": jsonable_encoder(work)})


@router.get("/{work_id}")
def api_read(work_id: int, is_json: bool = False):
    """
    Handle read or deletes on some work record
    GET: Information regarding specific record
    DELETE: Delete work record with identifier
    @param work_id work record identifier code
    """
    work_item = get_work(work_id)
    if work_item is None:
        error = f"Work Item {work_id} Not Found"
        return abort(404, error)
    if is_json:
        return JSONResponse(
            {"Success": True, "work_id": work_id, "work_item": work_item}
        )
    return templates.TemplateResponse("work/read_del", {"work_item": work_item})


@router.delete("/{work_id}")
def api_delete(work_id: int, is_json: bool = False):
    work_item = get_work(work_id)
    if work_item is None:
        error = f"Work Item {work_id} Not Found"
        return abort(404, error)
    _ = delete_work(work_id)
    if is_json:
        return JSONResponse({"Success": True, "work": jsonable_encoder(work_item)})
    return RedirectResponse(
        router.url_path_for("work.list_for_task", task_id=work_item.task_id)
    )


@router.get("/list/task/{task_id}")
def list_for_task(task_id: int, is_json: bool = False):
    """
    Return all work records for the given task
    GET: route provides the response described
    @param task_id task record was executed on
    """
    tasks = get_task(task_id)
    if tasks is None:
        error = f"Task Item {task_id} not found"
        return abort(404, error)
    work_items = get_work_for_task(task_id)
    if work_items is None:
        error = f"No Work Items found for Task {task_id}"
        return abort(404, error)
    if is_json:
        return JSONResponse({"Sucecss": True, "work_items": work_items})
    return templates.TemplateResponse(
        "work/list.html", {"key": "Task", "tasks": tasks, "work_items": work_items}
    )


@router.get("/list/story/{story_id}")
def list_for_story(story_id: int, is_json: bool = False):
    """
    List all work completed on tasks for story
    GET: route provides the response described
    @param story_id story where work described
    """
    story = get_story(story_id)
    if story is None:
        error = "Story Item not found"
        return abort(404, error)
    tasks = get_tasks_for_story(story_id)
    if tasks is None:
        error = f"No Tasks found for Story {story.id}"
        return abort(404, error)
    work_items = get_work_for_story(story_id)
    if work_items is None:
        error = f"No Work Items found for Story {story.id}"
        return abort(404, error)
    if is_json:
        return JSONResponse({"Sucecss": True, "work_items": work_items})
    return templates.TemplateResponse(
        "work/list.html",
        {"key": "Story " + story["story"], "tasks": tasks, "work_items": work_items},
    )


@router.get("/list/epic/{epic_id}")
def list_for_epic(epic_id: int, is_json: bool = False):
    """
    List work completed on tasks an epic holds
    GET: route provides the response described
    @param epic_id record identity for an epic
    """
    epic = get_epic(epic_id)
    if epic is None:
        error = "Epic Item not found"
        return abort(404, error)
    tasks = get_tasks_for_epic(epic_id)
    if tasks is None:
        error = "No Tasks found for Epic {epic.id}"
        return abort(404, error)
    work_items = get_work_for_epic(epic_id)
    if work_items is None:
        error = f"No Work Items found for Epic {epic.id}"
        return abort(404, error)
    if is_json:
        return JSONResponse({"Sucecss": True, "work_items": work_items})
    return templates.TemplateResponse(
        "work/list.html",
        {"key": "Epic " + epic["epic"], "tasks": tasks, "work_items": work_items},
    )


@router.get("/list/dates")
def list_for_dates(
    is_json: bool = False,
    start_date: date = date(2020, 1, 1),
    end_date: date = date.today(),
):
    """
    List all work completed within given dates
    GET: route provides the response described
    """
    work_items = get_work_by_dates(start_date, end_date)
    if work_items is None:
        error = "No work items found between dates_provided"
        return abort(404, error)
    all_tasks = get_tasks()
    task_ids = [x["task_id"] for x in work_items]
    tasks = []
    for task in all_tasks:
        if task["id"] in task_ids:
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
