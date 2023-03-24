"""
Noscrum API Handler for Sprint (and sprint schedule) components
"""
from datetime import timedelta, datetime
import logging
from sqlalchemy import or_
from noscrum_backend.epic import get_epics
from noscrum_backend.story import get_stories
from noscrum_backend.db import get_db, Sprint, Task, ScheduleTask

logger = logging.getLogger()
statuses = ["To-Do", "In Progress", "Done"]


def get_work_for_sprint(current_user, sprint_id):
    """
    Get work performed for a particular sprint
    @param sprint_id the ID of the sprint work
    """
    app_db = get_db()
    return app_db.session.execute(  # pylint: disable=no-member
        "SELECT work.task_id||work_date as id, work.task_id, "
        + "work_date, sum(hours_worked) as hours_worked FROM work "
        + "join schedule_task st ON work.task_id = st.task_id "
        + "AND work.work_date = st.sprint_day "
        + "AND work.user_id = st.user_id "
        + "WHERE st.sprint_id = :sprint_id "
        + "AND st.user_id = :user_id "
        + "GROUP BY work.task_id, work_date",
        {"sprint_id": sprint_id, "user_id": current_user.id},
    ).fetchall()


def get_sprint_number_for_user(current_user, sprint_id):
    """
    Return the sprint number for a user/sprint
    @sprint_id the Sprint ID's number you want
    """
    app_db = get_db()
    sprint_numbers = (
        app_db.session.query(
            Sprint.id,
            app_db.func.row_number()  # pylint: disable=no-member
            .over(partition_by=Sprint.user_id, order_by=Sprint.id)
            .label("sprint_number"),
        )
        .filter(Sprint.id <= sprint_id)
        .filter(Sprint.user_id == current_user.id)
        .all()
    )
    user_numbers = {x.id: x.sprint_number for x in sprint_numbers}
    return user_numbers[sprint_id]


def get_sprints(
    current_user,
):
    """
    Return all sprint records for current user.
    """
    return (
        Sprint.query.filter(Sprint.user_id == current_user.id)
        .order_by(Sprint.start_date.desc())
        .all()
    )


def get_sprint(current_user, sprint_id):
    """
    Return Sprint record @param sprint_id for current user
    """
    return (
        Sprint.query.filter(Sprint.id == sprint_id)
        .filter(Sprint.user_id == current_user.id)
        .order_by(Sprint.start_date)
        .first()
    )


def get_sprint_by_date(current_user, start_date=None, end_date=None, middle_date=None):
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


def get_current_sprint(current_user):
    """
    Given a current date returns active sprint
    """
    current_date = datetime.now().date()  # .strftime('%Y-%m-%d')
    return get_sprint_by_date(current_user, middle_date=current_date)


def get_last_sprint(
    current_user,
):
    """
    Returns the last(final date) sprint record
    """
    return (
        Sprint.query.filter(Sprint.user_id == current_user.id)
        .order_by(Sprint.end_date)
        .first()
    )


def create_sprint(current_user, start_date, end_date):
    """
    Create new Sprint record having the period
    between @param start_date and the end date
    @param end_date
    """
    app_db = get_db()
    new_sprint = Sprint(
        start_date=start_date, end_date=end_date, user_id=current_user.id
    )

    app_db.session.add(new_sprint)  # pylint: disable=no-member
    app_db.session.commit()  # pylint: disable=no-member
    return get_sprint_by_date(current_user, start_date=start_date, end_date=end_date)


def update_sprint(current_user, sprint_id, start_date, end_date):
    """
    Update the start or end date of the sprint
    """
    app_db = get_db()
    Sprint.query.filter(Sprint.id == sprint_id).filter(
        Sprint.user_id == current_user.id
    ).update({start_date: start_date, end_date: end_date}, synchronize_session="fetch")
    app_db.session.commit()  # pylint: disable=no-member
    return get_sprint(current_user, sprint_id)


def delete_sprint(current_user, sprint_id):
    """
    Delete a sprint with a given sprint_id
    """
    app_db = get_db()
    Sprint.query.filter(Sprint.id == sprint_id).filter(
        Sprint.user_id == current_user.id
    ).delete()
    app_db.session.commit()  # pylint: disable=no-member
    return sprint_id


def get_schedules_for_sprint(current_user, sprint_id):
    """
    Get ScheduleTasks having a sprint_id value
    @param sprint_id the queried sprint ID val
    """
    return (
        ScheduleTask.query.filter(ScheduleTask.sprint_id == sprint_id)
        .filter(ScheduleTask.user_id == current_user.id)
        .all()
    )


def get_schedule_tasks_filtered(
    current_user, sprint_id, task_id, sprint_day, sprint_hour
):
    """
    Get ScheduleTasks having a sprint_id value
    @param sprint_id the queried sprint ID val
    @param sprint_day the day for the schedule
    @param sprint_hour the schedule time value
    """
    query = ScheduleTask.query.filter(ScheduleTask.sprint_id == sprint_id)
    query = query.filter(ScheduleTask.user_id == current_user.id)
    if task_id is not None:
        query = query.filter(ScheduleTask.task_id == task_id)
    if sprint_day is not None:
        query = query.filter(ScheduleTask.sprint_day == sprint_day)
    if sprint_hour is not None:
        query = query.filter(ScheduleTask.sprint_hour == sprint_hour)
    return query.all()


def get_schedule(current_user, sched_id):
    """
    Get a ScheduleTask with a certain sched_id
    @param sched_id ScheduleTask ID you desire
    """

    return (
        ScheduleTask.query.filter(ScheduleTask.id == sched_id)
        .filter(ScheduleTask.user_id == current_user.id)
        .first()
    )


def get_schedules(
    current_user,
):
    """
    Get all ScheduleTasks for a user
    """
    return ScheduleTask.query.filter(ScheduleTask.user_id == current_user.id).all()


def get_schedule_by_time(
    current_user, sprint_id, sprint_day, sprint_hour, schedule_id=None
):
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


def create_schedule(
    current_user, sprint_id, task_id, sprint_day, sprint_hour, note, schedule_time
):
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
        schedule_time=schedule_time,
        user_id=current_user.id,
    )
    app_db.session.add(new_schedule)  # pylint: disable=no-member
    app_db.session.commit()  # pylint: disable=no-member
    return get_schedule_by_time(current_user, sprint_id, sprint_day, sprint_hour)


def update_schedule(
    current_user, sched_id, task_id, sprint_day, sprint_hour, note, schedule_time
):
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
            schedule_time: schedule_time,
            note: note,
        },
        synchronize_session="fetch",
    )
    return get_schedule(current_user, sched_id)


def delete_schedule(current_user, sched_id):
    """
    Delete a ScheduleTask record with an ident
    @sched_id ScheduleTask chosen for deletion
    """
    app_db = get_db()
    ScheduleTask.query.filter(ScheduleTask.id == sched_id).filter(
        ScheduleTask.user_id == current_user.id
    ).delete()
    app_db.session.commit()  # pylint: disable=no-member


def get_sprint_details(current_user, sprint_id):
    """
    Get detailed records for given sprint with
    @param sprint_id sprint details are wanted
    """
    app_db = get_db()
    stories = get_stories(current_user, sprint_view=True, sprint_id=sprint_id)
    epics = get_epics(current_user, sprint_view=True, sprint_id=sprint_id)
    tasks = app_db.session.execute(  # pylint: disable=no-member
        "SELECT task.id, task, estimate, status, story_id, "
        + "epic_id,"
        + "actual,"
        + "task.deadline,"
        + "task.recurring,"
        + "coalesce(hours_worked,0) hours_worked,"
        + "coalesce(sum_sched,0) sum_sched,"
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
        + "AND (task.sprint_ID = :sprint_id or coalesce(task.recurring,0) = 1 or "
        + "task.id in "
        + "(select task_id from schedule_task where sprint_id = :sprint_id)) "
        + "ORDER BY coalesce(task.deadline,'2222-12-22') ASC ",
        {"sprint_id": sprint_id, "user_id": current_user.id},
    ).fetchall()
    unplanned_tasks = (
        # This weird comparison is used because of how SQLAlchemy works (I think?)
        Task.query.filter(Task.user_id == current_user.id)
        .filter(
            or_(
                Task.sprint_id == None, Task.sprint_id != sprint_id  # noqa: E711
            )  # pylint: disable:singleton-comparison
        )
        .all()
    )
    sprint_days = (
        Sprint.query.filter(Sprint.id == sprint_id)
        .filter(Sprint.user_id == current_user.id)
        .first()
    )
    schedule_records_std = (
        ScheduleTask.query.filter(ScheduleTask.sprint_id == sprint_id)
        .filter(ScheduleTask.user_id == current_user.id)
        .filter(ScheduleTask.sprint_hour >= 0)
    )
    work = get_work_for_sprint(current_user, sprint_id)
    work = {x.id: x for x in work}
    schedule_records_dict = {}
    for record_std in schedule_records_std:
        key = f"{record_std.sprint_day}T{record_std.sprint_hour}:00"
        schedule_records_dict[key] = record_std
    schedule_records = list(schedule_records_dict.values())
    logger.info(work.items())
    for i, record in enumerate(schedule_records):
        work_key = f"{record.task_id}{record.sprint_day}"
        schedule_work = work.get(work_key, 0)
        if isinstance(schedule_work, int):
            schedule_records[i].schedule_work = schedule_work
        else:
            schedule_records[i].schedule_work = schedule_work.hours_worked

    current_day = sprint_days.start_date
    i = 0
    schedule_list = []
    while current_day <= sprint_days.end_date:
        task_hours = [
            y.sprint_hour
            for x, y in schedule_records_dict.items()
            if x.startswith(str(current_day))
        ]
        if task_hours == []:
            task_hours = [1]
        else:
            task_hours.append(max(task_hours) + 1)
        schedule_list.append((i, current_day, task_hours))
        i += 1
        current_day += timedelta(1)
    return stories, epics, tasks, schedule_list, schedule_records, unplanned_tasks, work
