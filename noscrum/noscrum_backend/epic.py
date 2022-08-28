"""
Handler for backend of Epic API for Noscrum
"""
from noscrum_backend.db import get_db, Epic


def get_epics(current_user, sprint_view=False, sprint_id=None):
    """
    Get all epics, optionally for given sprint
    """
    app_db = get_db()
    if not sprint_view:
        return Epic.query.filter(Epic.user_id == current_user.id).all()

    return app_db.session.execute(  # pylint: disable=no-member
        "SELECT epic.id, "
        + "CASE WHEN epic.epic == 'NULL' THEN 'No Epic' ELSE epic.epic END as epic, "
        + "color, epic.deadline, "
        + "sum(coalesce(estimate,0)) as estimate, count(task.id) as tasks, "
        + "COUNT(DISTINCT CASE WHEN task.status <> 'Done' THEN task.id ELSE NULL END) "
        + "as active_tasks, "
        + "COUNT(DISTINCT CASE WHEN task.estimate IS NULL THEN task.id ELSE NULL END) "
        + "as unestimated_tasks, "
        + "SUM(CASE WHEN task.status <> 'Done' THEN task.estimate - coalesce(task.actual,0)"
        + " ELSE 0 END) AS rem_estimate "
        + "FROM epic "
        + "LEFT OUTER JOIN story ON story.epic_id = epic.id "
        + "AND story.user_id = :user_id "
        + "LEFT OUTER JOIN task ON task.story_id = story.id "
        + "AND task.sprint_id = :sprint_id "
        + "AND task.user_id = :user_id "
        + "WHERE epic.user_id = :user_id "
        + "GROUP BY epic.epic, epic.id, epic.color",
        {"user_id": current_user.id, "sprint_id": sprint_id},
    ).fetchall()


def get_epic_by_name(current_user, epic_name):
    """
    Return the epic given the name of the epic
    @param epic the requsted epic name queried
    """
    return (
        Epic.query.filter(Epic.epic == epic_name)
        .filter(Epic.user_id == current_user.id)
        .first()
    )


def get_epic(current_user, epic_id):
    """
    Returns an epic given the specific epic_id
    @param epic_id the identifier for the epic
    """
    return (
        Epic.query.filter(Epic.id == epic_id)
        .filter(Epic.user_id == current_user.id)
        .first()
    )


def get_null_epic(current_user):
    """
    Returns the special null "story" record
    """
    epic = (
        Epic.query.filter(Epic.epic == "NULL")
        .filter(Epic.user_id == current_user.id)
        .first()
    )
    if epic is None:
        epic = create_epic(current_user, "NULL", None, None)
    return epic


def create_epic(current_user, epic, color, deadline):
    """
    Create a new epic with a given color, etc.
    @param epic name of the epic to be created
    @param color the highlighted color for use
    @param deadline (optional) planned end day
    """
    app_db = get_db()
    new_epic = Epic(epic=epic, color=color, deadline=deadline, user_id=current_user.id)
    app_db.session.add(new_epic)  # pylint: disable=no-member
    app_db.session.commit()  # pylint: disable=no-member
    return get_epic_by_name(current_user, epic)


def update_epic(current_user, epic_id, epic, color, deadline):
    """
    Update the existing epic with fresh values
    @param epic_id the epic identification val
    @param epic name of the epic to be updated
    @param deadline (optional) planned end day
    """
    app_db = get_db()
    Epic.query.filter(Epic.id == epic_id).update(
        {"epic": epic, "color": color, "deadline": deadline},
        synchronize_session="fetch",
    )
    app_db.session.commit()  # pylint: disable=no-member
    return get_epic(current_user, epic_id)
