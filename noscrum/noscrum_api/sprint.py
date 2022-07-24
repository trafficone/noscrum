"""
Sprint View and Database Interaction Module
"""
from datetime import date, timedelta, datetime
import logging
from flask_openapi3 import APIBlueprint as Blueprint
from flask import flash, redirect, request, url_for, abort
from flask_login import current_user, login_required
from pydantic import BaseModel, Field
from noscrum.noscrum_api.template_friendly import friendly_render as render_template
import noscrum.noscrum_backend.sprint as backend
from noscrum.noscrum_backend.task import get_task

logger = logging.getLogger()

bp = Blueprint("sprint", __name__, url_prefix="/sprint")

statuses = ["To-Do", "In Progress", "Done"]


def get_sprint_board(sprint_id, sprint, is_static=False):
    """
    Gather Sprint Board records for a specific
    @param sprint_id Sprint which the board is
    @param sprint record of board (only dates)
    @param is_static (optional) is unchanging?
    """
    (
        stories,
        epics,
        tasks,
        schedule_list,
        schedule_records,
        unplanned_tasks,
        work,
    ) = backend.get_sprint_details(current_user, sprint_id)
    details = {}
    details["tasks"] = {x["id"]: dict(x) for x in tasks}
    details["stories"] = {x["id"]: dict(x) for x in stories}
    details["epics"] = {x["id"]: dict(x) for x in epics}
    # Get Estimate Totals by story/epic at each status level
    totals = {}
    # sum up totals btw I don't like how this is implemented
    # this will appear in your next annual review >:-(
    for task in details["tasks"].values():
        estimate = task["estimate"]
        estimate = 0 if estimate is None else estimate
        story_id = task["story_id"]
        epic_id = task["epic_id"]
        status = task["status"]
        cuts = [
            status,
            f"e{epic_id}",
            f"e{epic_id}_{status}",
            f"s{story_id}",
            f"s{story_id}_{status}",
        ]
        for cut in cuts:
            totals[cut] = totals.get(cut, 0) + estimate
    for schedule_item in schedule_records:
        cuts = [f"d{schedule_item.sprint_day.strftime('%yyyy-%mm-%dd')}", "sprint"]
        for cut in cuts:
            if schedule_item.schedule_time is not None:
                totals[cut] = totals.get(cut, 0) + schedule_item.schedule_time
    return render_template(
        "sprint/board.html",
        sprint=sprint,
        sprint_id=sprint_id,
        stories=details["stories"],
        epics=details["epics"],
        tasks=details["tasks"],
        totals=totals,
        statuses=statuses,
        static=is_static,
        schedule=schedule_list,
        unplanned_tasks=unplanned_tasks,
        schedule_records=schedule_records,
        work=work,
    )


class SprintPath(BaseModel):
    """
    Sprint Path Model
    """

    sprint_id: int = Field(...)


@bp.get("/schedule/<int:sprint_id>")
@login_required
def get_sprint_schedule(path: SprintPath):
    """
    Return the schedule tasks for a given sprint
    """
    sprint_id = path.sprint_id
    task_id = request.args.get("task_id", None)
    sprint_day = request.args.get("sprint_day", None)
    sprint_hour = request.args.get("sprint_hour", None)
    schedule_tasks = backend.get_schedule_tasks_filtered(
        current_user, sprint_id, task_id, sprint_day, sprint_hour
    )
    if len(schedule_tasks) == 0:
        return abort(404, "No Schedules Found")
    keys = schedule_tasks[0].keys()
    schedule_tasks_out = []
    for task in schedule_tasks:
        task_dict = dict(
            zip(
                keys,
                [str(task[k]) if isinstance(task[k], date) else task[k] for k in keys],
            )
        )
        schedule_tasks_out.append(task_dict)
    return {"Success": True, "schedule_tasks": schedule_tasks_out}


@bp.post("/schedule/<int:sprint_id>")
@login_required
def schedule(path: SprintPath):
    """
    Get or set scheduling information for a given sprint.
    """
    sprint_id = path.sprint_id
    sprint = backend.get_sprint(current_user, sprint_id)
    schedule_id = request.form.get("schedule_id", None)
    schedule_record = (
        None if schedule_id is None else backend.get_schedule(current_user, schedule_id)
    )
    task_id = request.form.get("task_id", None)
    sprint_day = request.form.get("sprint_day", None)
    sprint_day = (
        datetime.strptime(sprint_day, "%Y-%m-%d").date()
        if isinstance(sprint_day, str)
        else sprint_day
    )
    sprint_hour = request.form.get("sprint_hour", None)
    schedule_time = request.form.get("schedule_time", 0)
    if schedule_time in (None, 0, "") and schedule_record is None:
        return {"Success": "False", "Error": "Cannot schedule 0 time"}
    schedule_time = schedule_record.schedule_time
    note = request.form.get("note")
    recurring = request.form.get("recurring", 0)
    error = None
    if recurring == "1":
        task = get_task(current_user, task_id)
        if not task.recurring:
            error = "Task not set as recurring, cannot schedule as recurring"
        else:
            sprint_id = 0
    if task_id is None:
        error = "No Task ID Found in Request"
    elif sprint_day is None:
        error = "No Sprint Day Found in Request"
    elif sprint_hour is None:
        error = "No Sprint Hour Found in Request"
    elif sprint_day > sprint.end_date:
        error = "Scheduled day is after sprint end"
    if error is None:
        old_record = backend.get_schedule_by_time(
            current_user,
            sprint_id,
            sprint_day,
            sprint_hour,
            schedule_id=schedule_id,
        )
        if old_record is not None:
            if old_record.id == schedule_id:
                raise Exception("Old schedule flagged as duplicate")
            backend.delete_schedule(current_user, old_record.id)
            schedule_id = None
            # Delete the existing task before scheduling another'
        if schedule_id is None:
            schedule_task = backend.create_schedule(
                current_user,
                sprint_id,
                task_id,
                sprint_day,
                sprint_hour,
                note,
                schedule_time,
            )
            retval = {"Success": True, "schedule_task": schedule_task.to_dict()}
        else:
            schedule_task = backend.update_schedule(
                current_user,
                schedule_id,
                task_id,
                sprint_day,
                sprint_hour,
                note,
                schedule_time,
            )

        retval = {"Success": True, "schedule_task": schedule_task.to_dict()}
        logger.info(retval)
        return retval
    return abort(500, error)


@bp.delete("/schedule/<int:sprint_id>")
@login_required
def del_schedule(path: SprintPath):
    """
    Delete schedule with a given schedule_id for a given sprint
    """
    logger.info("%s and %s", request.method, request.method == "DELETE")
    schedule_id = request.form.get("schedule_id", None)
    sprint_id = path.sprint_id
    if request.form.get("recurring", 0) == 1:
        sprint_id = 0
    error = None
    if schedule_id is None:
        error = "No Schedule ID Requested to Delete"
    deleted_schedule = backend.get_schedule(current_user, schedule_id)
    if deleted_schedule.sprint_id != sprint_id:
        error = "Schedule is not from requested sprint"
    if error is None:
        output = {
            "Success": True,
            "task_id": deleted_schedule.task_id,
            "schedule_id": deleted_schedule.id,
        }
        backend.delete_schedule(current_user, schedule_id)
        return output
    return abort(500, error)


@bp.post("/create/next")
@login_required
def create_next():
    """
    Create the next sprint assuming seven days
    """
    is_json = request.args.get("is_json", False)
    if is_json:
        abort(405, "Method not supported for AJAX mode")
    error = None
    last_sprint = backend.get_last_sprint(current_user)
    if last_sprint is None:
        error = "No sprint found for user. Next sprint can only be created after initial sprint"
    if error is None:
        (start_date,) = last_sprint.end_date + timedelta(1)
        end_date = last_sprint.end_date + timedelta(8)
        sprint = backend.create_sprint(current_user, start_date, end_date)
        if is_json:
            return {"Success": True, "sprint_id": sprint.id}
        return redirect(url_for("sprint.show", sprint_id=sprint.id))
    if is_json:
        abort(500, error)
    flash(error, "error")
    final_sprint = backend.get_last_sprint(current_user)
    start_date = date.today() if final_sprint is None else final_sprint.end_date
    end_date = start_date + timedelta(7)
    return render_template(
        "sprint/create.html", start_date=start_date, end_date=end_date
    )


@bp.get("/create")
@login_required
def get_create():
    """
    Retuns creation page for new sprint
    """
    final_sprint = backend.get_last_sprint(current_user)
    start_date = date.today() if final_sprint is None else final_sprint.end_date
    end_date = start_date + timedelta(6)
    return render_template(
        "sprint/create.html", start_date=start_date, end_date=end_date
    )


@bp.post("/create")
@login_required
def create():
    """
    Create a New Sprint defaulting last week's
    sprint, but it will accept input if needed
    """
    start_date = request.form["start_date"]
    end_date = request.form["end_date"]
    force_create = request.form.get("force_create", None)
    error = None
    same_sprint = backend.get_sprint_by_date(
        current_user, start_date=start_date, end_date=end_date
    )
    if same_sprint is not None:
        return {"Success": True, "sprint_id": same_sprint.id}
    start_sprint = backend.get_sprint_by_date(current_user, start_date=start_date)
    end_sprint = backend.get_sprint_by_date(current_user, end_date=end_date)
    if not start_date:
        error = "Unable to create sprint without a Start Date"
    elif not end_date:
        error = "Unable to create sprint without an End Date"
    elif end_sprint is not None:
        error = f"Sprint Ends same day as Existing Sprint {end_sprint.id}"
    elif start_sprint is not None:
        error = f"Sprint Starts same day as Existing Sprint {start_sprint.id}"
    elif force_create is False and (
        backend.get_sprint_by_date(current_user, middle_date=start_date) is not None
        or backend.get_sprint_by_date(current_user, middle_date=end_date) is not None
    ):
        error = "Sprint overlaps existing Sprint"

    if error is None:
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
        sprint = backend.create_sprint(current_user, start_date, end_date)
        return {"Success": True, "sprint_id": sprint.id}
    return abort(500, error)


@bp.get("/")
@login_required
def list_all():
    """
    List all of the Sprints for a current user
    """
    is_json = request.args.get("is_json", False)
    sprints = backend.get_sprints(current_user)
    current_sprint = backend.get_current_sprint(current_user)
    if not sprints:
        redirect(url_for("sprint.create"))
    if is_json:
        return {
            "Success": True,
            "sprints": [dict(x) for x in sprints],
            "has_current_sprint": current_sprint is not None,
        }
    return render_template(
        "sprint/list.html", sprints=sprints, current_sprint=current_sprint
    )


@bp.route("/<int:sprint_id>", methods=("GET", "POST", "DELETE"))
@login_required
def show(sprint_id):
    """
    Show Board for Sprint with sprint identity
    @param sprint_id identity for sprint board
    """
    is_json = request.args.get("is_json", False)
    is_static = request.args.get("static", "True")
    if is_static.lower() == "false":
        is_static = False
    sprint = backend.get_sprint(current_user, sprint_id)
    if not sprint:
        abort(404, f"Sprint with ID {sprint_id} was not found.")
    if request.method == "POST":
        start_date = request.form.get("start_date", None)
        end_date = request.form.get("end_date", None)
        error = None
        start_sprint = backend.get_sprint_by_date(current_user, start_date=start_date)
        end_sprint = backend.get_sprint_by_date(current_user, end_date=end_date)
        if not start_date:
            error = "Sprint Requires Start date"
        elif not end_date:
            error = "Sprint Requires End Date"
        elif start_sprint is not None:
            error = f"New start date is shared by sprint {start_sprint.id}"
        elif end_sprint is not None:
            error = f"New end date is shared by sprint {end_sprint.id}"
        if error is None:
            sprint = backend.update_sprint(current_user, id, start_date, end_date)
            if is_json:
                return {"Success": True, "sprint_id": sprint_id}
            return redirect(url_for("sprint.list_all", sprint_id=sprint_id))
        if is_json:
            abort(500, error)
        flash(error, "error")
    if request.method == "DELETE":
        # Not even pretending there's a non-JSON way to reach this
        if len(sprint.tasks) > 0:
            abort(500, "Cannot delete sprint with tasks in it")
        else:
            backend.delete_sprint(current_user, sprint.id)
            return {"Success": True, "sprint_id": sprint_id}
    if is_json:
        return {"Success": True, "sprint_id": sprint_id, "sprint": dict(sprint)}
    return get_sprint_board(sprint_id, sprint, is_static=is_static)


@bp.route("/active", methods=("GET",))
@login_required
def active():
    """
    Returns sprint board for the active sprint
    If two sprints overlap in date pick latter
    """
    is_json = request.args.get("is_json", False)
    current_sprint = backend.get_current_sprint(current_user)
    if not current_sprint:
        today = date.today()
        current_sprint = backend.create_sprint(
            current_user,
            today - timedelta(today.weekday()),
            today - timedelta(today.weekday() - 6),
        )
    sprint_id = current_sprint.id
    if is_json:
        return {"Success": True, "sprint_id": sprint_id, "sprint": dict(current_sprint)}
    return get_sprint_board(sprint_id, current_sprint, is_static=False)
