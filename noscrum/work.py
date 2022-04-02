"""
Data handler for work view and controller
"""
import json
from datetime import date, datetime

from flask import Blueprint, redirect, render_template, request, url_for, abort, flash
from flask_user import current_user

from noscrum.db import get_db, Work
from noscrum.task import (
    get_task,
    update_task,
    get_tasks_for_story,
    get_tasks_for_epic,
    get_tasks,
)
from noscrum.story import get_story
from noscrum.epic import get_epic

bp = Blueprint("work", __name__, url_prefix="/work")


# pylint: disable-next=too-many-arguments
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


@bp.route("/create/<int:task_id>", methods=("POST", "GET"))
def create(task_id):
    """
    Handle requests to create work on the task
    GET: Return form to create new work record
    POST: Create new work record for some task
    @param task_id task which work is executed
    """
    is_json = request.args.get("is_json", False)
    task = get_task(task_id)
    if task is None:
        error = f"Task {task_id} Not Found"
        if is_json:
            abort(404, error)
        else:
            flash(error, "error")
            return redirect(url_for("task.list_all"))
    if request.method == "GET":
        return render_template("work/create.html", task=task)
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
    update_status = True if update_status or update_status == "on" else False
    true_actual = sum([x.hours_worked for x in get_work_for_task(task_id)])
    new_actual = hours_worked if true_actual is None else true_actual + hours_worked
    create_work(work_date, hours_worked, status, task_id, new_actual, update_status)
    if is_json:
        return {"Success": True, "task_id": task_id}
    return redirect(url_for("work.list_for_task", task_id=task_id))


@bp.route("/<int:work_id>", methods=("GET", "DELETE"))
def read_delete(work_id):
    """
    Handle read or deletes on some work record
    GET: Information regarding specific record
    DELETE: Delete work record with identifier
    @param work_id work record identifier code
    """
    is_json = request.args.get("is_json", False)
    work_item = get_work(work_id)
    if work_item is None:
        error = f"Work Item {work_id} Not Found"
        if is_json:
            abort(404, error)
        else:
            flash(error, "error")
            return redirect(url_for("sprint.active"))
    if request.method == "GET":
        if is_json:
            return json.dumps(
                {"Success": True, "work_id": work_id, "work_item": work_item}
            )
        return render_template("work/read_del", work_item=work_item)
    elif request.method == "DELETE":
        deleted_work_id = delete_work(work_id)
        if is_json:
            return json.dumps({"Success": True, "work_id": deleted_work_id})
        return redirect(url_for("work.list_for_task", task_id=work_item.task_id))


@bp.route("/list/task/<int:task_id>", methods=("GET",))
def list_for_task(task_id):
    """
    Return all work records for the given task
    GET: route provides the response described
    @param task_id task record was executed on
    """
    is_json = request.args.get("is_json", False)
    tasks = get_task(task_id)
    if tasks is None:
        error = f"Task Item {task_id} not found"
        if is_json:
            abort(404, error)
        else:
            flash(error, "error")
            return redirect(url_for("sprint.active"))
    work_items = get_work_for_task(task_id)
    if work_items is None:
        error = f"No Work Items found for Task {task_id}"
        if is_json:
            abort(404, error)
        else:
            flash(error, "error")
            return redirect(url_for("sprint.active"))
    if is_json:
        return json.dumps({"Sucecss": True, "work_items": work_items})
    return render_template(
        "work/list.html", key="Task", tasks=tasks, work_items=work_items
    )


@bp.route("/list/story/<int:story_id>", methods=("GET",))
def list_for_story(story_id):
    """
    List all work completed on tasks for story
    GET: route provides the response described
    @param story_id story where work described
    """
    is_json = request.args.get("is_json", False)
    story = get_story(story_id)
    if story is None:
        error = "Story Item not found"
        if is_json:
            abort(404, error)
        else:
            flash(error, "error")
            return redirect(url_for("sprint.active"))
    tasks = get_tasks_for_story(story_id)
    if tasks is None:
        error = f"No Tasks found for Story {story.id}"
        if is_json:
            abort(404, error)
        else:
            flash(error, "error")
            return redirect(url_for("sprint.active"))
    work_items = get_work_for_story(story_id)
    if work_items is None:
        error = f"No Work Items found for Story {story.id}"
        if is_json:
            abort(404, error)
        else:
            flash(error, "error")
            return redirect(url_for("sprint.active"))
    if is_json:
        return json.dumps({"Sucecss": True, "work_items": work_items})
    return render_template(
        "work/list.html",
        key="Story " + story["story"],
        tasks=tasks,
        work_items=work_items,
    )


@bp.route("/list/epic/<int:epic_id>", methods=("GET",))
def list_for_epic(epic_id):
    """
    List work completed on tasks an epic holds
    GET: route provides the response described
    @param epic_id record identity for an epic
    """
    is_json = request.args.get("is_json", False)
    epic = get_epic(epic_id)
    if epic is None:
        error = "Epic Item not found"
        if is_json:
            abort(404, error)
        else:
            flash(error, "error")
            return redirect(url_for("sprint.active"))
    tasks = get_tasks_for_epic(epic_id)
    if tasks is None:
        error = "No Tasks found for Epic {epic.id}"
        if is_json:
            abort(404, error)
        else:
            flash(error, "error")
            return redirect(url_for("sprint.active"))
    work_items = get_work_for_epic(epic_id)
    if work_items is None:
        error = f"No Work Items found for Epic {epic.id}"
        if is_json:
            abort(404, error)
        else:
            flash(error, "error")
            return redirect(url_for("sprint.active"))
    if is_json:
        return json.dumps({"Sucecss": True, "work_items": work_items})
    return render_template(
        "work/list.html", key="Epic " + epic["epic"], tasks=tasks, work_items=work_items
    )


@bp.route("/list/dates", methods=("GET",))
def list_for_dates():
    """
    List all work completed within given dates
    GET: route provides the response described
    """
    is_json = request.args.get("is_json", False)
    start_date = request.args.get("start_date", date(2020, 1, 1))
    end_date = request.args.get("end_date", date.today())
    work_items = get_work_by_dates(start_date, end_date)
    if work_items is None:
        error = "No work items found between dates_provided"
        if is_json:
            abort(404, error)
        else:
            flash(error, "error")
            return redirect(url_for("sprint.active"))
    all_tasks = get_tasks()
    task_ids = [x["task_id"] for x in work_items]
    tasks = []
    for task in all_tasks:
        if task["id"] in task_ids:
            tasks.append(task)
    if is_json:
        return json.dumps({"Success": True, "work_items": work_items})
    return render_template(
        "work/list.html",
        key=f"Dates from {start_date} to {end_date}",
        tasks=tasks,
        work_items=work_items,
    )
