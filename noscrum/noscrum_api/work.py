"""
Data handler for work view and controller
"""
from datetime import date, datetime
import logging
from flask_openapi3 import APIBlueprint as Blueprint
from flask import redirect, request, url_for, abort, flash
from flask_login import current_user, login_required
from pydantic import BaseModel
from noscrum_api.template_friendly import friendly_render as render_template
from noscrum_api.task import TaskPath
from noscrum_api.story import StoryPath
from noscrum_api.epic import EpicPath
from noscrum_api.template_friendly import NoscrumBaseQuery
import noscrum_backend.work as backend
from noscrum_backend.task import (
    get_task,
    get_tasks_for_story,
    get_tasks_for_epic,
    get_tasks,
)
from noscrum_backend.story import get_story
from noscrum_backend.epic import get_epic

logger = logging.getLogger()

bp = Blueprint("work", __name__, url_prefix="/work")


@bp.get("/create/<int:task_id>")
@login_required
def get_create(path: TaskPath, query: NoscrumBaseQuery):
    """
    Get form to create Work object
    """
    is_json = query.is_json
    task_id = path.task_id
    task = get_task(current_user, task_id)
    if task is None:
        error = f"Task {task_id} Not Found"
        if is_json:
            abort(404, error)
        else:
            flash(error, "error")
            return redirect(url_for("task.list_all"))
    return render_template("work/create.html", task=task)


@bp.post("/create/<int:task_id>")
@login_required
def create(path: TaskPath, query: NoscrumBaseQuery):
    """
    Handle requests to create work on the task
    GET: Return form to create new work record
    POST: Create new work record for some task
    @param task_id task which work is executed
    """
    is_json = query.is_json
    task_id = path.task_id
    task = get_task(current_user, task_id)
    if task is None:
        error = f"Task {task_id} Not Found"
        if is_json:
            abort(404, error)
        else:
            flash(error, "error")
            return redirect(url_for("task.list_all"))
    # Handle POST Request
    work_date = request.form.get("work_date", date.today())
    if isinstance(work_date, str):
        work_date = datetime.strptime(work_date, "%Y-%m-%d").date()
    hours_worked = request.form.get("hours_worked", 0)
    try:
        hours_worked = 0 if hours_worked == "" else float(hours_worked)
    except ValueError:
        if is_json:
            abort(500, "Could not convert hours_worked to number.")
        flash(f"Could not convert hours worked {hours_worked} to number.")
        return redirect(url_for("work.list_for_task", task_id=task_id))
    status = request.form.get("status", task.status)
    update_status = request.form.get("update_status", False)
    update_status = bool(update_status or update_status == "on")
    true_actual = sum(
        x.hours_worked for x in backend.get_work_for_task(current_user, task_id)
    )
    new_actual = hours_worked if true_actual is None else true_actual + hours_worked
    backend.create_work(
        current_user,
        work_date,
        hours_worked,
        status,
        task_id,
        new_actual,
        update_status,
    )
    if is_json:
        return {"Success": True, "task_id": task_id}
    return redirect(url_for("work.list_for_task", task_id=task_id))


class WorkPath(BaseModel):
    """
    Path model for Work API
    """

    work_id: int


@bp.get("/<int:work_id>")
@login_required
def show(path: WorkPath, query: NoscrumBaseQuery):
    """
    Display Work with a given WorkID
    """
    is_json = query.is_json
    work_id = path.work_id
    work_item = backend.get_work(current_user, work_id)
    if work_item is None:
        error = f"Work Item {work_id} Not Found"
        if is_json:
            abort(404, error)
        else:
            flash(error, "error")
            return redirect(url_for("sprint.active"))
    if is_json:
        return {"Success": True, "work_id": work_id, "work_item": work_item.to_dict()}
    return render_template("work/read_del", work_item=work_item)


@bp.route("/<int:work_id>", methods=("GET", "DELETE"))
@login_required
def delete(path: WorkPath, query: NoscrumBaseQuery):
    """
    Handle read or deletes on some work record
    GET: Information regarding specific record
    DELETE: Delete work record with identifier
    @param work_id work record identifier code
    """
    is_json = query.is_json
    work_id = path.work_id
    work_item = backend.get_work(current_user, work_id)
    if work_item is None:
        error = f"Work Item {work_id} Not Found"
        if is_json:
            abort(404, error)
        else:
            flash(error, "error")
            return redirect(url_for("sprint.active"))
    deleted_work_id = backend.delete_work(current_user, work_id)
    if is_json:
        return {"Success": True, "work_id": deleted_work_id}
    return redirect(url_for("work.list_for_task", task_id=work_item.task_id))


@bp.get("/list/task/<int:task_id>")
@login_required
def list_for_task(path: TaskPath, query: NoscrumBaseQuery):
    """
    Return all work records for the given task
    GET: route provides the response described
    @param task_id task record was executed on
    """
    is_json = query.is_json
    task_id = path.task_id
    tasks = get_task(current_user, task_id)
    if tasks is None:
        error = f"Task Item {task_id} not found"
        if is_json:
            abort(404, error)
        else:
            flash(error, "error")
            return redirect(url_for("sprint.active"))
    work_items = backend.get_work_for_task(current_user, task_id)
    if work_items is None:
        error = f"No Work Items found for Task {task_id}"
        if is_json:
            abort(404, error)
        else:
            flash(error, "error")
            return redirect(url_for("sprint.active"))
    if is_json:
        dict_work_items = [x.to_dict() for x in work_items]
        return {"Success": True, "work_items": dict_work_items}
    return render_template(
        "work/list.html", key="Task", tasks=tasks, work_items=work_items
    )


@bp.get("/list/story/<int:story_id>")
@login_required
def list_for_story(path: StoryPath, query: NoscrumBaseQuery):
    """
    List all work completed on tasks for story
    GET: route provides the response described
    @param story_id story where work described
    """
    is_json = query.is_json
    story_id = path.story_id
    story = get_story(current_user, story_id)
    if story is None:
        error = "Story Item not found"
        if is_json:
            abort(404, error)
        else:
            flash(error, "error")
            return redirect(url_for("sprint.active"))
    tasks = get_tasks_for_story(current_user, story_id)
    if tasks is None:
        error = f"No Tasks found for Story {story.id}"
        if is_json:
            abort(404, error)
        else:
            flash(error, "error")
            return redirect(url_for("sprint.active"))
    work_items = backend.get_work_for_story(current_user, story_id)
    if work_items is None:
        error = f"No Work Items found for Story {story.id}"
        if is_json:
            abort(404, error)
        else:
            flash(error, "error")
            return redirect(url_for("sprint.active"))
    if is_json:
        dict_work_items = [x.to_dict() for x in work_items]
        return {"Success": True, "work_items": dict_work_items}
    return render_template(
        "work/list.html",
        key="Story " + story["story"],
        tasks=tasks,
        work_items=work_items,
    )


@bp.get("/list/epic/<int:epic_id>")
@login_required
def list_for_epic(path: EpicPath, query: NoscrumBaseQuery):
    """
    List work completed on tasks an epic holds
    GET: route provides the response described
    @param epic_id record identity for an epic
    """
    epic_id = path.epic_id
    is_json = query.is_json
    epic = get_epic(current_user, epic_id)
    if epic is None:
        error = "Epic Item not found"
        if is_json:
            abort(404, error)
        else:
            flash(error, "error")
            return redirect(url_for("sprint.active"))
    tasks = get_tasks_for_epic(current_user, epic_id)
    if tasks is None:
        error = "No Tasks found for Epic {epic.id}"
        if is_json:
            abort(404, error)
        else:
            flash(error, "error")
            return redirect(url_for("sprint.active"))
    work_items = backend.get_work_for_epic(current_user, epic_id)
    if work_items is None:
        error = f"No Work Items found for Epic {epic.id}"
        if is_json:
            abort(404, error)
        else:
            flash(error, "error")
            return redirect(url_for("sprint.active"))
    if is_json:
        dict_work_items = [x.to_dict() for x in work_items]
        return {"Success": True, "work_items": dict_work_items}
    return render_template(
        "work/list.html", key="Epic " + epic["epic"], tasks=tasks, work_items=work_items
    )


@bp.get("/list/dates")
@login_required
def list_for_dates():
    """
    List all work completed within given dates
    GET: route provides the response described
    """
    is_json = request.args.get("is_json", False)
    start_date = request.args.get("start_date", date(2020, 1, 1))
    end_date = request.args.get("end_date", date.today())
    work_items = backend.get_work_by_dates(current_user, start_date, end_date)
    if work_items is None:
        error = "No work items found between dates_provided"
        if is_json:
            abort(404, error)
        else:
            flash(error, "error")
            return redirect(url_for("sprint.active"))
    all_tasks = get_tasks(
        current_user,
    )
    task_ids = [x.task_id for x in work_items]
    tasks = []
    for task in all_tasks:
        if task["id"] in task_ids:
            tasks.append(task)
    if is_json:
        dict_work_items = [x.to_dict() for x in work_items]
        return {"Success": True, "work_items": dict_work_items}
    return render_template(
        "work/list.html",
        key=f"Dates from {start_date} to {end_date}",
        tasks=tasks,
        work_items=work_items,
    )


@bp.get("/reporting")
@login_required
def display_report_page():
    """
    Render report page.
    """
    return render_template("work/report.html")
