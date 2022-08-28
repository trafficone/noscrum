"""
Backend component of Task API
"""
from noscrum_backend.db import get_db, Task


def get_tasks(current_user):
    """
    Get every task record for the current user
    """
    app_db = get_db()
    return app_db.session.execute(  # pylint: disable=no-member
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
        + "WHERE task.user_id = :user_id "
        + "ORDER BY task.status, coalesce(task.deadline,'2222-12-22') ASC ",
        {"user_id": current_user.id},
    )  # pylint: disable=no-member


def get_task(current_user, task_id):
    """
    Task record for user for identifier number
    @task_id task record identification number
    """
    return (
        Task.query.filter(Task.id == task_id)
        .filter(Task.user_id == current_user.id)
        .first()
    )


def get_tasks_for_story(current_user, story_id):
    """
    Get all task records for the current story
    @param story_id asked Story identification
    """
    return (
        Task.query.filter(Task.story_id == story_id)
        .filter(Task.user_id == current_user.id)
        .all()
    )


def get_story_summary(current_user):
    """
    Get task summary for each story by task ID
    """
    app_db = get_db()
    return (
        app_db.session.query(
            Task.story_id,
            app_db.func.sum(Task.estimate).label("est"),  # pylint: disable=no-member
            app_db.func.count(Task.id)
            .filter(Task.estimate is None)
            .label("unest"),  # pylint: disable=no-member
            app_db.func.count(Task.id)  # pylint: disable=no-member
            .filter(Task.status != "Done")
            .label("incomplete"),
            app_db.func.count().label("task_count"),  # pylint: disable=no-member
        )
        .filter(Task.user_id == current_user.id)
        .group_by(Task.story_id)
        .all()
    )


def get_tasks_for_epic(current_user, epic_id):
    """
    Get all task records for a certain epic id
    @param epic_id Epic record identity number
    """
    return (
        Task.query.filter(Task.stories.epic_id == epic_id)
        .filter(Task.user_id == current_user.id)
        .all()
    )


def get_task_by_name(current_user, task, story_id):
    """
    Get a task with a certain name in a sprint
    @param task Name of task being queried for
    @param story_id Identification for a story
    """
    return (
        Task.query.filter(Task.story_id == story_id)
        .filter(Task.task == task)
        .filter(Task.user_id == current_user.id)
        .first()
    )


def create_task(current_user, task, story_id, estimate, deadline, sprint_id):
    """
    Create a new task under a given story with
    @param task Name of task being queried for
    @param story_id Identification for a story
    @param estimate number of hours estimation
    @param deadline date when task will be due
    @param sprint_id Sprint where task planned
    """
    app_db = get_db()
    newtask = Task(
        task=task,
        story_id=story_id,
        estimate=estimate,
        deadline=deadline,
        sprint_id=sprint_id,
        user_id=current_user.id,
    )
    app_db.session.add(newtask)  # pylint: disable=no-member
    app_db.session.commit()  # pylint: disable=no-member
    return get_task_by_name(current_user, task, story_id)


def update_task(
    current_user,
    task_id,
    task,
    story_id,
    estimate,
    status,
    actual,
    deadline,
    sprint_id,
    recurring,
):
    """
    Update the properties for an existing task
    @task_id task record identification number
    @param task Name of task being queried for
    @param story_id Identification for a story
    @param estimate number of hours estimation
    @param actual hours spent to complete task
    @param deadline date when task will be due
    @param sprint_id Sprint where task planned
    @param recurring does it recur each sprint
    """
    app_db = get_db()
    data = {}
    query = Task.query.filter(Task.id == task_id).filter(
        Task.user_id == current_user.id
    )
    if task is not None:
        data["task"] = task
    if story_id is not None:
        data["story_id"] = story_id
    if estimate is not None:
        data["estimate"] = estimate
    if status is not None:
        data["status"] = status
    if actual is not None:
        data["actual"] = actual
    if deadline is not None:
        data["deadline"] = deadline
    if sprint_id is not None:
        data["sprint_id"] = sprint_id
    if recurring is not None:
        if isinstance(recurring, str) and (
            recurring.lower().startswith("f") or recurring == "0"
        ):
            recurring = False
        recurring = bool(recurring)
        data["recurring"] = recurring
    query.update(data, synchronize_session="fetch")
    app_db.session.commit()
    return get_task(current_user, task_id)


def delete_task(current_user, task_id):
    """
    Delete task, task deletion not implemented
    """
    # app_db = get_db()
    # Task.query.filter(Task.id==task_id).filter(Task.user_id==current_user.id).delete()
    # app_db.commit()
    raise NotImplementedError("Deleting Tasks is Not Supported")
