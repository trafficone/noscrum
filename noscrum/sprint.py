"""
Sprint View and Database Interaction Module
"""
from datetime import date, timedelta, datetime
import json

from sqlalchemy import or_
from fastapi import APIRouter
from fastapi.encoders import jsonable_encoder
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from noscrum.db import get_db
from noscrum.model import Sprint, Task, ScheduleTask
from noscrum.epic import get_epics
from noscrum.story import get_stories
from noscrum.user import current_user

statuses = ["To-Do", "In Progress", "Done"]


def get_task(task_id):
    """
    Task record for user for identifier number
    @task_id task record identification number
    """
    return (
        Task.query.filter(Task.id == task_id)
        .filter(Task.user_id == current_user.id)
        .first()
    )


def get_sprint_number_for_user(sprint_id):
    """
    Return the sprint number for a user/sprint
    @sprint_id the Sprint ID's number you want
    """
    app_db = get_db()
    sprint_numbers = (
        app_db.session.query(
            Sprint.id,
            app_db.func.row_number()
            .over(partition_by=Sprint.user_id, order_by=Sprint.id)
            .label("sprint_number"),
        )
        .filter(Sprint.id <= sprint_id)
        .filter(Sprint.user_id == current_user.id)
        .all()
    )
    user_numbers = {x.id: x.sprint_number for x in sprint_numbers}
    return user_numbers[sprint_id]


def get_sprints():
    """
    Return all sprint records for current user.
    """
    return Sprint.query.filter(Sprint.user_id == current_user.id).all()


def get_sprint(sprint_id):
    """
    Return Sprint record @param sprint_id for current user
    """
    return (
        Sprint.query.filter(Sprint.id == sprint_id)
        .filter(Sprint.user_id == current_user.id)
        .first()
    )


def get_sprint_by_date(start_date=None, end_date=None, middle_date=None):
    """
    Returns the Sprint object (if exist) given
    provided search criteria for a sprint date
    @param start_date Date where sprint starts
    @param end_date Date when sprint then ends
    @param middle_date Any day within a sprint
    """
    query = Sprint.query.filter(Sprint.start_date != "1969-12-31").filter(
        Sprint.user_id == current_user.id
    )
    filter_vars = []
    if start_date is not None:
        query = query.filter(Sprint.start_date == start_date)
        filter_vars.append(start_date)
    if end_date is not None:
        query = query.filter(Sprint.end_date == end_date)
        filter_vars.append(end_date)
    if middle_date is not None:
        query = query.filter(Sprint.start_date <= middle_date).filter(
            Sprint.end_date >= middle_date
        )
        filter_vars.append(middle_date)
    if len(filter_vars) == 0:
        raise Exception("No criteria entered for get_sprint_by_date")
    return query.first()


def get_current_sprint():
    """
    Given a current date returns active sprint
    """
    current_date = datetime.now().date()  # .strftime('%Y-%m-%d')
    return get_sprint_by_date(middle_date=current_date)


def get_next_sprint():
    current_sprint = get_current_sprint()
    if current_sprint is None:
        return None
    next_sprint = get_sprint_by_date(start_date=current_sprint.end_date + timedelta(1))
    print(next_sprint)
    return next_sprint


def get_last_sprint():
    """
    Returns the last(final date) sprint record
    """
    return (
        Sprint.query.filter(Sprint.user_id == current_user.id)
        .order_by(Sprint.end_date)
        .first()
    )


def create_sprint(start_date, end_date):
    """
    Create new Sprint record having the period
    between @param start_date and the end date
    @param end_date
    """
    app_db = get_db()
    new_sprint = Sprint(
        start_date=start_date, end_date=end_date, user_id=current_user.id
    )
    app_db.session.add(new_sprint)
    app_db.session.commit()
    return get_sprint_by_date(start_date=start_date, end_date=end_date)


def update_sprint(sprint_id, start_date, end_date):
    """
    Update the start or end date of the sprint
    """
    app_db = get_db()
    Sprint.query.filter(Sprint.id == sprint_id).filter(
        Sprint.user_id == current_user.id
    ).update({start_date: start_date, end_date: end_date}, synchronize_session="fetch")
    app_db.session.commit()
    return get_sprint(sprint_id)

def delete_sprint(sprint_id):
    """
    Delete a sprint (if empty)
    """
    sprint = get_sprint(sprint_id)
    if len(sprint.tasks) > 0:
        raise Exception("Cannot delete empty sprint")
    app_db = get_db()
    Sprint.query.filter(Sprint.id == sprint_id).filter(
        Sprint.user_id == current_user.id
    ).delete()
    app_db.session.commit()
    return sprint_id


def get_schedules_for_sprint(sprint_id):
    """
    Get ScheduleTasks having a sprint_id value
    @param sprint_id the queried sprint ID val
    """
    return ScheduleTask.query.filter(ScheduleTask.sprint_id == sprint_id).all()


def get_schedule_tasks_filtered(sprint_id, task_id, sprint_day, sprint_hour):
    """
    Get ScheduleTasks having a sprint_id value
    @param sprint_id the queried sprint ID val
    @param sprint_day the day for the schedule
    @param sprint_hour the schedule time value
    """
    query = ScheduleTask.query.filter(ScheduleTask.sprint_id == sprint_id)
    query.filter(ScheduleTask.user_id == current_user.id)
    if task_id is not None:
        query.filter(ScheduleTask.task_id == task_id)
    if sprint_day is not None:
        query.filter(ScheduleTask.sprint_day == sprint_day)
    if sprint_hour is not None:
        query.filter(ScheduleTask.sprint_hour == sprint_hour)
    return query.all()


def get_schedule(sched_id):
    """
    Get a ScheduleTask with a certain sched_id
    @param sched_id ScheduleTask ID you desire
    """

    return (
        ScheduleTask.query.filter(ScheduleTask.id == sched_id)
        .filter(ScheduleTask.user_id == current_user.id)
        .first()
    )


def get_schedule_by_time(sprint_id, sprint_day, sprint_hour, schedule_id=None):
    """
    Get single ScheduleTask for a given sprint
    at a certain day on a certain time (with a
    schedule_id optional). Usedful if schedule
    records are being created and you want the
    @param schedule_id (optional) ID for query
    @param sprint_id ScheduleTask in Sprint ID
    @param sprint_day the day for the schedule
    @param sprint_hour the schedule time value
    """

    query = (
        ScheduleTask.query.filter(ScheduleTask.user_id == current_user.id)
        .filter(ScheduleTask.sprint_day == sprint_day)
        .filter(ScheduleTask.sprint_hour == sprint_hour)
        .filter(ScheduleTask.sprint_id == sprint_id)
    )
    if schedule_id is not None:
        query.filter(ScheduleTask.id != schedule_id)
    return query.first()


def create_schedule(sprint_id, task_id, sprint_day, sprint_hour, note):
    """
    Create a new schedule for the task with ID
    @param task_id ID for task being scheduled
    @param sprint_id ScheduleTask in Sprint ID
    @param sprint_day the day for the schedule
    @param sprint_hour the schedule time value
    @param note Free field for clarifying time
    """
    app_db = get_db()
    new_schedule = ScheduleTask(
        sprint_id=sprint_id,
        task_id=task_id,
        sprint_day=sprint_day,
        sprint_hour=sprint_hour,
        note=note,
        user_id=current_user.id,
    )
    app_db.session.add(new_schedule)
    app_db.session.commit()
    return get_schedule_by_time(sprint_id, sprint_day, sprint_hour)


def update_schedule(sched_id, task_id, sprint_day, sprint_hour, note):
    """
    Update a schedule with given ID for sprint
    @param sched_id a Schedule record identity
    @param task_id ID for task being scheduled
    @param sprint_id ScheduleTask in Sprint ID
    @param sprint_day the day for the schedule
    @param sprint_hour the schedule time value
    @param note Free field for clarifying time
    """
    ScheduleTask.query.filter(ScheduleTask.user_id == current_user.id).filter(
        ScheduleTask.id == sched_id
    ).update(
        {
            task_id: task_id,
            sprint_day: sprint_day,
            sprint_hour: sprint_hour,
            note: note,
        },
        synchronize_session="fetch",
    )
    return get_schedule(sched_id)


def delete_schedule(sched_id):
    """
    Delete a ScheduleTask record with an ident
    @sched_id ScheduleTask chosen for deletion
    """
    app_db = get_db()
    ScheduleTask.query.filter(ScheduleTask.id == sched_id).filter(
        ScheduleTask.user_id == current_user.id
    ).delete()
    app_db.session.commit()


def get_sprint_details(sprint_id):
    """
    Get detailed records for given sprint with
    @param sprint_id sprint details are wanted
    """
    app_db = get_db()
    stories = get_stories(sprint_view=True, sprint_id=sprint_id)
    epics = get_epics(sprint_view=True, sprint_id=sprint_id)
    # tasks = #get_tasks().filter(Task.sprint_id == sprint_id)
    tasks = app_db.session.execute(
        "SELECT task.id, task, estimate, status, story_id, "
        + "epic_id, actual, task.deadline, task.recurring, coalesce(hours_worked,0) hours_worked, "
        + "coalesce(sum_sched,0) sum_sched, "
        + "(task.sprint_ID = sched.sprint_id) single_sprint_task "
        + "FROM task "
        + "JOIN story ON task.story_id = story.id "
        + "LEFT OUTER JOIN (SELECT task_id, sum(hours_worked) hours_worked "
        + "FROM work group by task_id) woik "
        + "ON woik.task_id = task.id "
        + "LEFT OUTER JOIN (select task_id, sprint_id, count(1) * 2 sum_sched "
        + "FROM schedule_task group by task_id, sprint_id) sched "
        + "ON task.id = sched.task_id AND sched.sprint_id = :sprint_id "
        + "WHERE task.user_id = :user_id "
        + "AND (task.sprint_ID = :sprint_id or task.recurring or "
        + "task.id in (select task_id from schedule_task where sprint_id = sprint_id))",
        {"sprint_id": sprint_id, "user_id": current_user.id},
    ).fetchall()
    unplanned_tasks = (
        Task.query.filter(Task.user_id == current_user.id)
        .filter(or_(Task.sprint_id is None, Task.sprint_id != sprint_id))
        .all()
    )
    sprint_days = (
        Sprint.query.filter(Sprint.id == sprint_id)
        .filter(Sprint.user_id == current_user.id)
        .first()
    )
    schedule_records_std = ScheduleTask.query.filter(
        ScheduleTask.sprint_id == sprint_id
    ).filter(ScheduleTask.user_id == current_user.id)
    schedule_records_recurring = (
        ScheduleTask.query.join(Task)
        .filter(Task.recurring)
        .filter(ScheduleTask.user_id == current_user.id)
    )
    schedule_records_dict = {
        f"{x.sprint_day}T{x.sprint_hour}:00": x for x in schedule_records_recurring
    }
    for record_std in schedule_records_std:
        key = f"{record_std.sprint_day}T{record_std.sprint_hour}:00"
        schedule_records_dict[key] = record_std
    schedule_records = list(schedule_records_dict.values())

    current_day = sprint_days.start_date
    i = 0
    schedule_list = []
    while current_day <= sprint_days.end_date:
        schedule_list.append((i, current_day, range(9, 22, 2)))
        i += 1
        current_day += timedelta(1)
    return stories, epics, tasks, schedule_list, schedule_records, unplanned_tasks


router = APIRouter(prefix="/sprint", tags=["sprint"])
templates = Jinja2Templates(directory="templates")


def abort(response_code: int, message: str):
    return JSONResponse(
        status_code=response_code, content={"Error": {"message": message}}
    )


def get_sprint_board(sprint_id, sprint, is_static=False):
    """
    Gather Sprint Board records for a specific
    @param sprint_id Sprint which the board is
    @param sprint record of board (only dates)
    @param is_static (optional) is unchanging?
    """
    stories, epics, tasks, schedule_list, schedule_records, unplanned_tasks = get_sprint_details(
        sprint_id
    )
    tasks = {x["id"]: dict(x) for x in tasks}
    stories = {x["id"]: dict(x) for x in stories}
    epics = {x["id"]: dict(x) for x in epics}
    # Get Estimate Totals by story/epic at each status level
    totals = {}
    # sum up totals btw I don't like how this is implemented
    # this will appear in your next annual review >:-(
    for task in tasks.values():
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
    return templates.TemplateResponse(
        "sprint/board.html",
        {
            "sprint": sprint,
            "sprint_id": sprint_id,
            "stories": stories,
            "epics": epics,
            "tasks": tasks,
            "totals": totals,
            "statuses": statuses,
            "static": is_static,
            "schedule": schedule_list,
            "unplanned_tasks": unplanned_tasks,
            "schedule_records": schedule_records,
        },
    )


@router.post("/schedule/{sprint_id}")
def api_create_schedule(sprint_id: int, schedule: ScheduleTask):
    """
    Get or set scheduling information for a given sprint.
    """
    sprint = get_sprint(sprint_id)
    recurring = schedule.recurring
    error = None
    task = get_task(schedule.task_id)
    if recurring:
        if not task.recurring:
            error = "Task not set as recurring, cannot schedule as recurring"
        else:
            schedule.sprint_id = 0
    # TODO: This validation should be part of the model
    elif schedule.sprint_day > sprint.end_date:
        error = "Scheduled day is after sprint end"
    # TODO: This validation should be part of the model
    elif int(schedule.sprint_hour) > 24:
        error = "Sprint Hour is > 24"
    if error is None:
        old_record = get_schedule_by_time(
            schedule.sprint_id,
            schedule.sprint_day,
            schedule.sprint_hour,
            schedule_id=schedule.id,
        )
        if old_record is not None:
            if old_record.id == schedule.id:
                raise Exception("Old schedule flagged as duplicate")
            delete_schedule(old_record.id)
            schedule.id = None
        if schedule.id is None:
            schedule_task = create_schedule(
                schedule.sprint_id,
                schedule.task_id,
                schedule.sprint_day,
                schedule.sprint_hour,
                schedule.note,
            )
        else:
            schedule_task = update_schedule(
                schedule.id,
                schedule.task_id,
                schedule.sprint_day,
                schedule.sprint_hour,
                schedule.note,
            )

            return JSONResponse(
                {"Success": True, "schedule_task": schedule_task.to_dict()}
            )
    return abort(500, error)


@router.delete("/schedule/")
def api_delete_schedule(schedule_id: int):
    deleted_schedule = jsonable_encoder(get_schedule(schedule_id))
    if deleted_schedule is None:
        return abort(404, f"Cannot find schedule with ID {schedule_id}")
    output = {"Success": True, "schedule": deleted_schedule}
    delete_schedule(schedule_id)
    return JSONResponse(output)


@router.get("/schedule/{sprint_id}")
def list_schedules(sprint_id: int, task_id: int, sprint_day: date, sprint_hour: int):
    schedule_tasks = get_schedule_tasks_filtered(
        sprint_id, task_id, sprint_day, sprint_hour
    )
    if len(schedule_tasks) == 0:
        return abort(404, "No Schedules Found")
    schedule_tasks_out = jsonable_encoder(schedule_tasks)
    return json.dumps({"Success": True, "schedule_tasks": schedule_tasks_out})


@router.post("/create/next")
def create_next():
    """
    Create the next sprint assuming seven days
    """
    error = None
    last_sprint = get_last_sprint()
    if last_sprint is None:
        error = "No sprint found for user. Next sprint can only be created after initial sprint"
    if error is None:
        start_date, = last_sprint.end_date + timedelta(1)
        end_date = last_sprint.end_date + timedelta(8)
        sprint = jsonable_encoder(create_sprint(start_date, end_date))
        return JSONResponse({"Success": True, "sprint": sprint})
    return abort(500, error)


@router.get("/create/next", response_class=HTMLResponse)
def get_next_html():
    _ = create_next()
    final_sprint = get_last_sprint()
    start_date = date.today() if final_sprint is None else final_sprint.end_date
    end_date = start_date + timedelta(7)
    return templates.TemplateResponse(
        "sprint/create.html", {"start_date": start_date, "end_date": end_date}
    )


@router.post("/create")
def create(sprint: Sprint, force_create: bool = False):
    """
    Create a New Sprint defaulting last week's
    sprint, but it will accept input if needed
    """
    error = None
    start_sprint = get_sprint_by_date(start_date=sprint.start_date)
    end_sprint = get_sprint_by_date(end_date=sprint.end_date)
    if end_sprint is not None:
        error = f"Sprint Ends same day as Existing Sprint {end_sprint.id}"
    elif start_sprint is not None:
        error = f"Sprint Starts same day as Existing Sprint {start_sprint.id}"
    elif force_create is False and (
        get_sprint_by_date(middle_date=sprint.start_date) is not None
        or get_sprint_by_date(middle_date=sprint.end_date) is not None
    ):
        error = "Sprint overlaps existing Sprint"

    if error is None:
        sprint = jsonable_encoder(create_sprint(sprint.start_date, sprint.end_date))
        return JSONResponse({"Success": True, "sprint": sprint})
    return abort(500, error)


@router.get("/create", response_class=HTMLResponse)
def get_creation_form():
    final_sprint = get_last_sprint()
    start_date = date.today() if final_sprint is None else final_sprint.end_date
    end_date = start_date + timedelta(6)
    return templates.TemplateResponse(
        "sprint/create.html", {"start_date": start_date, "end_date": end_date}
    )


@router.get("/")
async def list_all(is_json: bool = False):
    """
    List all of the Sprints for a current user
    """
    sprints = get_sprints()
    current_sprint = get_current_sprint()
    if not sprints:
        return RedirectResponse(router.url_path_for("create"))
    sprint_numbers = {s.id: get_sprint_number_for_user(s.id) for s in sprints}
    if is_json:
        return JSONResponse(
            {
                "Success": True,
                "sprints": [dict(x) for x in sprints],
                "has_current_sprint": current_sprint is not None,
            }
        )
    return templates.TemplateResponse(
        "sprint/list.html", {"sprints": sprints, "sprint_numbers": sprint_numbers}
    )


@router.post("/{sprint_id}")
async def update(sprint_id: int, sprint: Sprint):
    error = None
    old_sprint = get_sprint(sprint_id)
    start_sprint = get_sprint_by_date(start_date=sprint.start_date)
    end_sprint = get_sprint_by_date(end_date=sprint.end_date)
    if old_sprint is None:
        return abort(404, f"Sprint with ID {sprint_id} not found")
    elif start_sprint is not None:
        error = f"New start date is shared by sprint {start_sprint.id}"
    elif end_sprint is not None:
        error = f"New end date is shared by sprint {end_sprint.id}"
    if error is None:
        sprint = update_sprint(id, sprint.start_date, sprint.end_date)
        return json.dumps({"Success": True, "sprint_id": sprint_id})
    return abort(500, error)


@router.get("/{sprint_id}")
def show(sprint_id: int, is_json: bool = False):
    """
    Show Board for Sprint with sprint identity
    @param sprint_id identity for sprint board
    """
    sprint = get_sprint(sprint_id)
    if not sprint:
        return abort(404, f"Sprint with ID {sprint_id} was not found.")
    if is_json:
        return json.dumps(
            {"Success": True, "sprint_id": sprint_id, "sprint": dict(sprint)}
        )
    return get_sprint_board(sprint_id, sprint, is_static=True)


@router.get("/active")
def active(is_json: bool = False):
    """
    Returns sprint board for the active sprint
    If two sprints overlap in date pick latter
    """
    current_sprint = get_current_sprint()
    if not current_sprint:
        has_sprints = get_sprints()
        if len(has_sprints) == 0:
            return abort(401, "Please create your first sprint.")
            # flash('Please create your first sprint.')
        else:
            return RedirectResponse(router.url_path_for("sprint.create"))
            # flash('No currently active sprint. Create new sprint')
    sprint_id = current_sprint.id
    if is_json:
        return JSONResponse(
            {
                "Success": True,
                "sprint_id": sprint_id,
                "sprint": jsonable_encoder(current_sprint),
            }
        )
    return get_sprint_board(sprint_id, current_sprint, is_static=False)
