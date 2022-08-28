"""
Backend components to Noscrum Work API
"""
from noscrum_backend.db import get_db, Work, ScheduleTask
from noscrum_backend.task import update_task

# pylint: disable-next=too-many-arguments
def create_work(
    current_user, work_date, hours_worked, status, task_id, new_actual, update_status
):
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
    work_schedule = (
        ScheduleTask.query.filter(ScheduleTask.sprint_day == work_date)
        .filter(ScheduleTask.task_id == task_id)
        .filter(ScheduleTask.user_id == current_user.id)
        .first()
    )
    if work_schedule is None:
        raise Exception("Cannot log work on unscheduled task")
    new_work = Work(
        work_date=work_date,
        hours_worked=hours_worked,
        status=status,
        task_id=task_id,
        user_id=current_user.id,
    )
    app_db.session.add(new_work)  # pylint: disable=no-member
    new_status = status if update_status else None
    update_task(
        current_user,
        task_id,
        None,
        None,
        None,
        new_status,
        new_actual,
        None,
        None,
        None,
    )
    app_db.session.commit()  # pylint: disable=no-member


def get_all_work(current_user):
    """
    Get work record from identification number
    @param work_id work record identity number
    """
    return Work.query.filter(Work.user_id == current_user.id).first()


def get_work(current_user, work_id):
    """
    Get work record from identification number
    @param work_id work record identity number
    """
    return (
        Work.query.filter(Work.id == work_id)
        .filter(Work.user_id == current_user.id)
        .first()
    )


def get_work_for_task(current_user, task_id):
    """
    Get the work records given the task record
    @param task_id task record work is queried
    """
    return (
        Work.query.filter(Work.task_id == task_id)
        .filter(Work.user_id == current_user.id)
        .all()
    )


def get_work_for_story(current_user, story_id):
    """
    Get the work for a particular story record
    @param story_id a Story record locator val
    """
    return (
        Work.query.filter(Work.story.id == story_id)
        .filter(Work.user_id == current_user.id)
        .all()
    )


def get_work_for_epic(current_user, epic_id):
    """
    Get all work records under the epic record
    @param epic_id epic for which work queried
    """
    app_db = get_db()
    return Work(
        *app_db.session.execute(  # pylint: disable=no-member
            "SELECT work.id, task_id, work_date, hours_worked, status "
            + "FROM work JOIN task on work.task_id = task.id "
            + "JOIN story ON task.story_id = story.id "
            + " WHERE story.epic_id = ? "
            + " AND story.user_id = ? ORDER BY work_date",
            (epic_id, current_user),
        ).fetchall()
    )


def get_work_by_dates(current_user, start_date, end_date):
    """
    Get work executed between two dates values
    @param start_date date request lower limit
    @param end_date date requested upper limit
    """
    return (
        Work.query.filter(Work.work_date >= start_date)
        .filter(Work.work_date <= end_date)
        .filter(Work.user_id == current_user.id)
        .all()
    )


def delete_work(current_user, work_id):
    """
    Delete work record given a certain identiy
    @param work_id a work record to be deleted
    """
    app_db = get_db()
    work = get_work(current_user, work_id)
    Work.query.filter(Work.id == work_id).filter(
        Work.user_id == current_user.id
    ).delete()
    app_db.session.commit()  # pylint: disable=no-member
    return work.id
