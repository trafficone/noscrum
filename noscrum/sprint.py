"""
Sprint View and Database Interaction Module
"""

import json
from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import ScalarResult, delete, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import or_, select

from noscrum.db import get_db
from noscrum.epic import get_epics
from noscrum.model import Epic, ScheduleTask, Sprint, Story, Task, User
from noscrum.story import get_stories_sprint_view
from noscrum.user import current_user

# from noscrum.task import get_task

statuses = ["To-Do", "In Progress", "Done"]


async def get_task(task_id, current_user: User, app_db: AsyncSession) -> Task:
    """
    Task record for user for identifier number
    @task_id task record identification number
    """
    if current_user.id is None:
        raise ValueError("Cannot perform function without User ID")
    task = await app_db.execute(
        select(Task).where(Task.id == task_id).where(Task.user_id == current_user.id)
    )
    return task.scalar_one()


async def get_sprint_number_for_user(sprint_id, current_user: User, app_db: AsyncSession) -> int:
    """
    Return the sprint number for a user/sprint
    @sprint_id the Sprint ID's number you want
    """
    sprint_numbers = await app_db.execute(
        select(
            Sprint.id,
            app_db.func.row_number()
            .over(partition_by=Sprint.user_id, order_by=Sprint.id)
            .label("sprint_number"),
        )
        .where(Sprint.id <= sprint_id)
        .where(Sprint.user_id == current_user.id)
    )
    sprints = sprint_numbers.scalars()
    user_numbers = {x.id: x.sprint_number for x in sprints}
    return user_numbers[sprint_id]


async def get_sprints(current_user: User, app_db: AsyncSession) -> ScalarResult[Sprint]:
    """
    Return all sprint records for current user.
    """
    if current_user.id is None:
        raise ValueError("Cannot perform function without User ID")
    sprints = await app_db.execute(select(Sprint).where(Sprint.user_id == current_user.id))
    return sprints.scalars()


async def get_sprint(sprint_id, current_user: User, app_db: AsyncSession) -> Sprint | None:
    """
    Return Sprint record @param sprint_id for current user
    """
    if current_user.id is None:
        raise ValueError("Cannot perform function without User ID")
    sprint = await app_db.execute(
        select(Sprint).where(Sprint.id == sprint_id).where(Sprint.user_id == current_user.id)
    )
    return sprint.scalar_one_or_none()


async def get_sprint_by_date(
    current_user: User,
    app_db: AsyncSession,
    start_date=None,
    end_date=None,
    middle_date=None,
) -> Sprint | None:
    """
    Returns the Sprint object (if exist) given
    provided search criteria for a sprint date
    @param start_date Date where sprint starts
    @param end_date Date when sprint then ends
    @param middle_date Any day within a sprint
    """
    query = (
        select(Sprint)
        .where(Sprint.start_date != "1969-12-31")
        .where(Sprint.user_id == current_user.id)
    )
    filter_vars = []
    if start_date is not None:
        query = query.where(Sprint.start_date == start_date)
        filter_vars.append(start_date)
    if end_date is not None:
        query = query.where(Sprint.end_date == end_date)
        filter_vars.append(end_date)
    if middle_date is not None:
        query = query.where(Sprint.start_date <= middle_date).where(Sprint.end_date >= middle_date)
        filter_vars.append(middle_date)
    if len(filter_vars) == 0:
        raise Exception("No criteria entered for get_sprint_by_date")
    sprint = await app_db.execute(query)
    return sprint.scalar_one_or_none()


async def get_current_sprint(current_user: User, app_db: AsyncSession) -> Sprint | None:
    """
    Given a current date returns active sprint
    """
    current_date = datetime.now().date()  # .strftime('%Y-%m-%d')
    return await get_sprint_by_date(current_user, app_db, middle_date=current_date)


async def get_next_sprint(current_user: User, app_db: AsyncSession) -> Sprint | None:
    current_sprint = await get_current_sprint(current_user, app_db)
    if current_sprint is None:
        return None
    next_sprint = await get_sprint_by_date(
        current_user,
        app_db,
        start_date=current_sprint.end_date + timedelta(1),
    )
    print(next_sprint)
    return next_sprint


async def get_last_sprint(current_user: User, app_db: AsyncSession) -> Sprint | None:
    """
    Returns the last(final date) sprint record
    """
    sprint = await app_db.execute(
        select(Sprint).where(Sprint.user_id == current_user.id).order_by(Sprint.end_date)
    )
    return sprint.scalar_one_or_none()


async def create_sprint(
    start_date, end_date, current_user: User, app_db: AsyncSession
) -> Sprint | None:
    """
    Create new Sprint record having the period
    between @param start_date and the end date
    @param end_date
    """
    if current_user.id is None:
        raise Exception("Cannot create Sprint without current User ID")
    new_sprint = Sprint(start_date=start_date, end_date=end_date, user_id=current_user.id)
    app_db.add(new_sprint)
    await app_db.commit()
    return await get_sprint_by_date(current_user, app_db, start_date=start_date, end_date=end_date)


async def update_sprint(
    sprint_id,
    start_date,
    end_date,
    current_user: User,
    app_db: AsyncSession,
) -> Sprint | None:
    """
    Update the start or end date of the sprint
    """
    if current_user.id is None:
        raise Exception("Cannot update Sprint without current User ID")
    sprint_q = await app_db.execute(
        select(Sprint).where(Sprint.id == sprint_id).where(Sprint.user_id == current_user.id)
    )
    sprint = sprint_q.scalar_one()
    sprint.start_date = start_date
    sprint.end_date = end_date
    await app_db.commit()
    return await get_sprint(sprint_id, current_user, app_db)


async def delete_sprint(sprint_id: int, current_user: User, app_db: AsyncSession) -> int:
    """
    Delete a sprint (if empty)
    """
    if current_user.id is None:
        raise ValueError("Cannot perform function without User ID")
    sprint = await get_sprint(sprint_id, current_user, app_db)
    if sprint is None:
        # it's either already deleted or never existed
        return sprint_id
    if len(sprint.tasks) > 0:
        raise Exception("Cannot delete empty sprint")
    await app_db.execute(
        delete(Sprint).where(Sprint.id == sprint_id).where(Sprint.user_id == current_user.id)
    )
    await app_db.commit()
    return sprint_id


async def get_schedules_for_sprint(
    sprint_id: int, current_user: User, app_db: AsyncSession
) -> ScalarResult[ScheduleTask]:
    """
    Get ScheduleTasks having a sprint_id value
    @param sprint_id the queried sprint ID val
    """
    if current_user.id is None:
        raise ValueError("Cannot perform function without User ID")
    schedules = await app_db.execute(
        select(ScheduleTask)
        .where(ScheduleTask.sprint_id == sprint_id)
        .where(current_user.id == ScheduleTask.user_id)
    )
    return schedules.scalars()


async def get_schedule_tasks_filtered(
    sprint_id: int,
    task_id: int,
    sprint_day: date,
    sprint_hour: int,
    current_user: User,
    app_db: AsyncSession,
) -> ScalarResult[ScheduleTask]:
    """
    Get ScheduleTasks having a sprint_id value
    @param sprint_id the queried sprint ID val
    @param sprint_day the day for the schedule
    @param sprint_hour the schedule time value
    """
    query = select(ScheduleTask).where(ScheduleTask.sprint_id == sprint_id)
    query.where(ScheduleTask.user_id == current_user.id)
    if task_id is not None:
        query.where(ScheduleTask.task_id == task_id)
    if sprint_day is not None:
        query.where(ScheduleTask.sprint_day == sprint_day)
    if sprint_hour is not None:
        query.where(ScheduleTask.sprint_hour == sprint_hour)
    sched = await app_db.execute(query)
    return sched.scalars()


async def get_schedule(sched_id, current_user: User, app_db: AsyncSession) -> ScheduleTask | None:
    """
    Get a ScheduleTask with a certain sched_id
    @param sched_id ScheduleTask ID you desire
    """

    schedule_task = await app_db.execute(
        select(ScheduleTask)
        .where(ScheduleTask.id == sched_id)
        .where(ScheduleTask.user_id == current_user.id)
    )
    return schedule_task.scalar_one_or_none()


async def get_schedule_by_time(
    sprint_id: int,
    sprint_day: date,
    sprint_hour: int,
    current_user: User,
    app_db: AsyncSession,
    schedule_id: int | None = None,
) -> ScheduleTask | None:
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
    if current_user.id is None:
        raise ValueError("Cannot perform function without User ID")
    query = (
        select(ScheduleTask)
        .where(ScheduleTask.user_id == current_user.id)
        .where(ScheduleTask.sprint_day == sprint_day)
        .where(ScheduleTask.sprint_hour == sprint_hour)
        .where(ScheduleTask.sprint_id == sprint_id)
    )
    if schedule_id is not None:
        query.where(ScheduleTask.id != schedule_id)
    sched = await app_db.execute(query)
    return sched.scalar_one_or_none()


async def create_schedule(
    sprint_id: int,
    task_id: int,
    sprint_day: date,
    sprint_hour: int,
    note: str,
    current_user: User,
    app_db: AsyncSession,
) -> ScheduleTask:
    """
    Create a new schedule for the task with ID
    @param task_id ID for task being scheduled
    @param sprint_id ScheduleTask in Sprint ID
    @param sprint_day the day for the schedule
    @param sprint_hour the schedule time value
    @param note Free field for clarifying time
    """
    if current_user.id is None:
        raise ValueError("Cannot perform function without User ID")
    new_schedule = ScheduleTask(
        sprint_id=sprint_id,
        task_id=task_id,
        sprint_day=sprint_day,
        sprint_hour=sprint_hour,
        note=note,
        user_id=current_user.id,
        recurring=False,
    )
    app_db.add(new_schedule)
    await app_db.commit()
    schedule_task = await get_schedule_by_time(
        sprint_id, sprint_day, sprint_hour, current_user, app_db
    )
    if schedule_task is None:
        raise Exception("Could not create schedule task. Database connection may be unstable.")
    return schedule_task


async def update_schedule(
    sched_id: int,
    task_id: int,
    sprint_day: date,
    sprint_hour: int,
    note: str,
    current_user: User,
    app_db: AsyncSession,
) -> ScheduleTask | None:
    """
    Update a schedule with given ID for sprint.
    @param sched_id a Schedule record identity.
    @param task_id ID for task being scheduled.
    @param sprint_id ScheduleTask in Sprint ID.
    @param sprint_day the day for the schedule.
    @param sprint_hour the schedule time value.
    @param note Free field for clarifying time.
    """
    if current_user.id is None:
        raise ValueError("Cannot perform function without User ID")
    schedule_task_q = await app_db.execute(
        select(ScheduleTask)
        .where(ScheduleTask.user_id == current_user.id)
        .where(ScheduleTask.id == sched_id)
    )
    schedule_task = schedule_task_q.scalar_one()
    schedule_task.task_id = task_id
    schedule_task.sprint_day = sprint_day
    schedule_task.sprint_hour = sprint_hour
    schedule_task.note = note
    await app_db.commit()
    return await get_schedule(sched_id, current_user, app_db)


async def delete_schedule(sched_id: int, current_user: User, app_db: AsyncSession) -> int:
    """
    Delete a ScheduleTask record with an ident
    @sched_id ScheduleTask chosen for deletion
    """
    if current_user.id is None:
        raise ValueError("Cannot perform function without User ID")
    await app_db.execute(
        delete(ScheduleTask)
        .where(ScheduleTask.id == sched_id)
        .where(ScheduleTask.user_id == current_user.id)
    )
    await app_db.commit()
    return sched_id


async def get_sprint_details(
    sprint_id: int, current_user: User, app_db: AsyncSession
) -> tuple[
    ScalarResult[Story],
    ScalarResult[Epic],
    ScalarResult[Task],
    list[ScheduleTask],
    ScalarResult[ScheduleTask],
    ScalarResult[Task],
]:
    """
    Get detailed records for given sprint with
    @param sprint_id sprint details are wanted
    @return stories, epics, tasks, schedule_list, schedule_records, unplanned_tasks
    """
    if current_user.id is None:
        raise ValueError("Cannot perform function without User ID")
    stories = await get_stories_sprint_view(current_user, app_db, sprint_id=sprint_id)
    epics = await get_epics(current_user, app_db, sprint_view=True, sprint_id=sprint_id)
    tasks_q = await app_db.execute(
        text(
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
            + "task.id in (select task_id from schedule_task where sprint_id = sprint_id))"
        ),
        {"sprint_id": sprint_id, "user_id": current_user.id},
    )
    tasks = tasks_q.scalars()
    unplanned_tasks = (
        await app_db.execute(
            select(Task)
            .where(Task.user_id == current_user.id)
            .where(or_(Task.sprint_id is None, Task.sprint_id != sprint_id))
        )
    ).scalars()
    sprint_days = (
        await app_db.execute(
            select(Sprint).where(Sprint.id == sprint_id).where(Sprint.user_id == current_user.id)
        )
    ).scalar_one()
    schedule_records_std = await app_db.execute(
        select(ScheduleTask)
        .where(ScheduleTask.sprint_id == sprint_id)
        .where(ScheduleTask.user_id == current_user.id)
    )
    schedule_records_recurring = await app_db.execute(
        select(ScheduleTask)
        .join(Task)
        .where(Task.recurring)
        .where(ScheduleTask.user_id == current_user.id)
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
    return JSONResponse(status_code=response_code, content={"Error": {"message": message}})


# Frontend function for sprint board
async def get_sprint_board(
    request: Request, sprint_id: int, sprint: Sprint, current_user: User, app_db: AsyncSession, is_static=False
):
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
    ) = await get_sprint_details(sprint_id, current_user, app_db)
    tasks = {x.id: dict(x) for x in tasks}
    stories = {x.id: dict(x) for x in stories}
    epics = {x.id: dict(x) for x in epics}
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
            "request": request,
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
async def api_create_schedule(
    sprint_id: int,
    schedule: ScheduleTask,
    current_user: User = Depends(current_user),
    app_db=Depends(get_db),
):
    """
    Get or set scheduling information for a given sprint.
    """
    sprint = await get_sprint(sprint_id, current_user, app_db)
    recurring = schedule.recurring
    error = None
    task = await get_task(schedule.task_id, current_user, app_db)
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
        old_record = await get_schedule_by_time(
            schedule.sprint_id,
            schedule.sprint_day,
            schedule.sprint_hour,
            current_user,
            app_db,
            schedule_id=schedule.id,
        )
        if old_record is not None:
            if old_record.id == schedule.id:
                raise Exception("Old schedule flagged as duplicate")
            await delete_schedule(old_record.id, current_user, app_db)
            schedule.id = None
        if schedule.id is None:
            schedule_task = await create_schedule(
                schedule.sprint_id,
                schedule.task_id,
                schedule.sprint_day,
                schedule.sprint_hour,
                schedule.note,
                current_user,
                app_db,
            )
        else:
            schedule_task = await update_schedule(
                schedule.id,
                schedule.task_id,
                schedule.sprint_day,
                schedule.sprint_hour,
                schedule.note,
                current_user,
                app_db,
            )

            return JSONResponse({"Success": True, "schedule_task": schedule_task.to_dict()})
    return abort(500, error)


@router.delete("/schedule/")
async def api_delete_schedule(
    schedule_id: int, current_user: User = Depends(current_user), app_db=Depends(get_db)
):
    deleted_schedule = await jsonable_encoder(get_schedule(schedule_id, current_user, app_db))
    if deleted_schedule is None:
        return abort(404, f"Cannot find schedule with ID {schedule_id}")
    output = {"Success": True, "schedule": deleted_schedule}
    await delete_schedule(schedule_id, current_user, app_db)
    return JSONResponse(output)


@router.get("/frontend/schedule/{sprint_id}", tags=["frontend"], response_class=HTMLResponse)
async def fe_list_schedules(
    sprint_id: int,
    task_id: int,
    sprint_day: date,
    sprint_hour: int,
    current_user: User = Depends(current_user),
    app_db=Depends(get_db),
):
    schedule_tasks = await get_schedule_tasks_filtered(
        sprint_id, task_id, sprint_day, sprint_hour, current_user, app_db
    )
    if len(list(schedule_tasks)) == 0:
        return abort(404, "No Schedules Found")
    schedule_tasks_out = jsonable_encoder(schedule_tasks)
    return json.dumps({"Success": True, "schedule_tasks": schedule_tasks_out})


@router.post("/create/next")
async def create_next(current_user: User = Depends(current_user), app_db=Depends(get_db)):
    """
    Create the next sprint assuming seven days
    """
    error = None
    last_sprint = await get_last_sprint(current_user, app_db)
    if last_sprint is None:
        return abort(
            500, "No sprint found for user. Next sprint can only be created after initial sprint"
        )
    if error is None:
        start_date = last_sprint.end_date + timedelta(1)
        end_date = last_sprint.end_date + timedelta(8)
        sprint = jsonable_encoder(create_sprint(start_date, end_date, current_user, app_db))
        return JSONResponse({"Success": True, "sprint": sprint})
    return abort(500, error)


@router.get("/frontend/create/next", tags=["frontend"], response_class=HTMLResponse)
async def fe_get_next_html(current_user: User = Depends(current_user), app_db=Depends(get_db)):
    _ = create_next()
    final_sprint = await get_last_sprint(current_user, app_db)
    start_date = date.today() if final_sprint is None else final_sprint.end_date
    end_date = start_date + timedelta(7)
    return templates.TemplateResponse(
        "sprint/create.html", {"start_date": start_date, "end_date": end_date}
    )


@router.post("/create")
async def sprint_create(
    sprint: Sprint,
    force_create: bool = False,
    current_user: User = Depends(current_user),
    app_db=Depends(get_db),
):
    """
    Create a New Sprint defaulting last week's
    sprint, but it will accept input if needed
    """
    error = None
    start_sprint = await get_sprint_by_date(current_user, app_db, start_date=sprint.start_date)
    end_sprint = await get_sprint_by_date(current_user, app_db, end_date=sprint.end_date)
    if end_sprint is not None:
        error = f"Sprint Ends same day as Existing Sprint {end_sprint.id}"
    elif start_sprint is not None:
        error = f"Sprint Starts same day as Existing Sprint {start_sprint.id}"
    elif force_create is False and (
        get_sprint_by_date(current_user, app_db, middle_date=sprint.start_date) is not None
        or get_sprint_by_date(current_user, app_db, middle_date=sprint.end_date) is not None
    ):
        error = "Sprint overlaps existing Sprint"

    if error is None:
        sprint = jsonable_encoder(
            create_sprint(sprint.start_date, sprint.end_date, current_user, app_db)
        )
        return JSONResponse({"Success": True, "sprint": sprint})
    return abort(500, error)


@router.get("/frontend/create", tags=["frontend"], response_class=HTMLResponse)
async def fe_sprint_creation_template(
    request: Request, current_user: User = Depends(current_user), app_db=Depends(get_db)
):
    final_sprint = await get_last_sprint(current_user, app_db)
    start_date = date.today() if final_sprint is None else final_sprint.end_date
    end_date = start_date + timedelta(6)
    return templates.TemplateResponse(
        "sprint/create.html",
        {
            "request": request,
            "start_date": start_date,
            "end_date": end_date,
            "current_user": current_user,
        },
    )


@router.get("/frontend/", tags=["frontend"], response_class=HTMLResponse)
async def fe_sprint_list_all(current_user: User = Depends(current_user), app_db=Depends(get_db)):
    """
    List all of the Sprints for a current user
    """
    sprints = await get_sprints(current_user, app_db)
    # current_sprint = await get_current_sprint(current_user, app_db)
    if not sprints:
        return RedirectResponse(router.url_path_for("create"))
    sprint_numbers = {s.id: get_sprint_number_for_user(s.id, current_user, app_db) for s in sprints}
    return templates.TemplateResponse(
        "sprint/list.html", {"sprints": sprints, "sprint_numbers": sprint_numbers}
    )


@router.get("/")
async def list_all_backend(current_user: User = Depends(current_user), app_db=Depends(get_db)):
    """
    List all of the Sprints for a current user
    """
    sprints = await get_sprints(current_user, app_db)
    current_sprint = await get_current_sprint(current_user, app_db)
    if not sprints:
        return RedirectResponse(router.url_path_for("create"))
    return JSONResponse(
        {
            "Success": True,
            "sprints": [dict(x) for x in sprints],
            "has_current_sprint": current_sprint is not None,
        }
    )


@router.post("/{sprint_id}")
async def update(
    sprint_id: int,
    sprint: Sprint,
    current_user: User = Depends(current_user),
    app_db=Depends(get_db),
):
    error = None
    old_sprint = await get_sprint(sprint_id, current_user, app_db)
    start_sprint = await get_sprint_by_date(current_user, app_db, start_date=sprint.start_date)
    end_sprint = await get_sprint_by_date(current_user, app_db, end_date=sprint.end_date)
    if old_sprint is None:
        return abort(404, f"Sprint with ID {sprint_id} not found")
    elif start_sprint is not None:
        error = f"New start date is shared by sprint {start_sprint.id}"
    elif end_sprint is not None:
        error = f"New end date is shared by sprint {end_sprint.id}"
    if error is None:
        sprint_nullable = await update_sprint(
            id, sprint.start_date, sprint.end_date, current_user, app_db
        )
        if sprint_nullable is None:
            return abort(500, "Could not get updated Sprint")
        sprint = sprint_nullable
        return json.dumps({"Success": True, "sprint_id": sprint_id})
    return abort(500, error)


@router.get("/frontend/show/{sprint_id}", tags=["frontend"], response_class=HTMLResponse)
async def fe_show(request: Request, sprint_id: int, current_user: User = Depends(current_user), app_db=Depends(get_db)):
    """
    Show Board for Sprint with sprint identity
    @param sprint_id identity for sprint board
    """
    sprint = await get_sprint(sprint_id, current_user, app_db)
    if not sprint:
        return abort(404, f"Sprint with ID {sprint_id} was not found.")
    return get_sprint_board(request, sprint_id, sprint, current_user, app_db, is_static=True)


@router.get("/frontend/active", tags=["frontend"], response_class=HTMLResponse)
async def fe_sprint_active(
    request: Request, current_user: User = Depends(current_user), app_db=Depends(get_db)
):
    """
    Returns sprint board for the active sprint
    If two sprints overlap in date pick latter
    """
    current_sprint = await get_current_sprint(current_user, app_db)
    if not current_sprint:
        has_sprints = await get_sprints(current_user, app_db)
        if len(list(has_sprints)) == 0:
            return abort(401, "Please create your first sprint.")
        else:
            return RedirectResponse(router.url_path_for("fe_sprint_creation_template"))
    sprint_id = current_sprint.id
    if not sprint_id:
        return abort(404, "Sprint has no ID")
    sprint_board = await get_sprint_board(request,
        sprint_id, current_sprint, current_user, app_db, is_static=False
    )
    return sprint_board


@router.get("/active", tags=["frontend"], response_class=HTMLResponse)
async def sprint_active(
    current_user: User = Depends(current_user), app_db=Depends(get_db)
):
    """
    Returns sprint board for the active sprint
    If two sprints overlap in date pick latter
    """
    current_sprint = await get_current_sprint(current_user, app_db)
    if not current_sprint:
        has_sprints = await get_sprints(current_user, app_db)
        if len(list(has_sprints)) == 0:
            return abort(401, "Please create your first sprint.")
            # flash('Please create your first sprint.')
        else:
            return RedirectResponse(router.url_path_for("sprint.create"))
            # flash('No currently active sprint. Create new sprint')
    sprint_id = current_sprint.id
    return JSONResponse(
        {
            "Success": True,
            "sprint_id": sprint_id,
            "sprint": jsonable_encoder(current_sprint),
        }
    )
