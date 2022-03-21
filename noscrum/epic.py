"""
Handler for epic creation, read, and etc.
"""

import json
from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for, abort
from flask_user import current_user, login_required

from noscrum.db import get_db, Epic

bp = Blueprint("epic", __name__, url_prefix="/epic")


def get_epics(sprint_view=False, sprint_id=None):
    """
    Get all epics, optionally for given sprint
    """
    app_db = get_db()
    if not sprint_view:
        return Epic.query.filter(Epic.user_id == current_user.id).all()

    return app_db.session.execute(
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


def get_epic_by_name(epic):
    """
    Return the epic given the name of the epic
    @param epic the requsted epic name queried
    """
    return (
        Epic.query.filter(Epic.epic == epic)
        .filter(Epic.user_id == current_user.id)
        .first()
    )


def get_epic(epic_id):
    """
    Returns an epic given the specific epic_id
    @param epic_id the identifier for the epic
    """
    return (
        Epic.query.filter(Epic.id == epic_id)
        .filter(Epic.user_id == current_user.id)
        .first()
    )


def get_null_epic():
    """
    Returns the special null "story" record
    """
    epic = (
        Epic.query.filter(Epic.epic == "NULL")
        .filter(Epic.user_id == current_user.id)
        .first()
    )
    if epic is None:
        epic = create_epic("NULL", None, None)
    return epic


def create_epic(epic, color, deadline):
    """
    Create a new epic with a given color, etc.
    @param epic name of the epic to be created
    @param color the highlighted color for use
    @param deadline (optional) planned end day
    """
    app_db = get_db()
    new_epic = Epic(epic=epic, color=color, deadline=deadline, user_id=current_user.id)
    app_db.session.add(new_epic)
    app_db.session.commit()
    return get_epic_by_name(epic)


def update_epic(epic_id, epic, color, deadline):
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
    app_db.session.commit()
    return get_epic(epic_id)


@bp.route("/create", methods=("GET", "POST"))
@login_required
def create():
    """
    Handle creation for a new epic / form data
    """
    is_json = request.args.get("is_json", False)
    is_asc = request.args.get("is_asc", False)
    if request.method == "POST":
        epic = request.form.get("epic", None)
        color = request.form.get("color", None)
        deadline = request.form.get("deadline", None)
        if isinstance(deadline, str):
            deadline = datetime.strptime(deadline, "%Y-%m-%d").date()
        error = None

        if not epic:
            error = "Epic Name is Required"
        elif get_epic_by_name(epic) is not None:
            error = f'Epic named "{epic}" already exists'

        if error is None:
            epic = create_epic(epic, color, deadline)
            if is_json:
                return json.dumps(
                    {"Success": True, "epic_id": epic.id, "epic_name": epic.epic}
                )
            return redirect(url_for("epic.show", epic_id=epic.id))
        if is_json:
            abort(500, error)
        flash(error, "error")

    return render_template("epic/create.html", asc=is_asc)


@bp.route("/<int:epic_id>", methods=("GET", "POST"))
@login_required
def show(epic_id):
    """
    Display information or process update epic
    @param epic_id the epic's identifier value
    """
    is_json = request.args.get("is_json", False)
    epic = get_epic(epic_id)
    if epic is None:
        if is_json or request.method == "POST":
            abort(404, "Epic ID not found in Database")
        else:
            flash(f'Epid ID "{epic_id}" not found.', "error")
            return redirect(url_for("epic.list_all"))
    if request.method == "POST":
        error = None
        epic_name = request.form.get("name", epic["epic"])
        color = request.form.get("color", epic["color"])
        deadline = request.form.get("deadline", epic["deadline"])
        other_epic = get_epic_by_name(epic_name)

        if not epic_id:
            error = "Could not find ID for Epic being edited."
        elif other_epic is not None and other_epic.id != epic_id:
            error = f'A different Epic named "{epic.epic}" already exists'

        if error is None:
            update_epic(epic_id, epic_name, color, deadline)
            if is_json:
                return json.dumps({"Success": True, "epic_id": epic_id})
            return redirect(url_for("epic.show", epic_id=epic_id))
        if is_json:
            abort(500, error)
        flash(error, "error")

    if is_json:
        return json.dumps({"Success": True, "epic": dict(epic), "stories": {}})
    return render_template("epic/show.html", epic=epic, stories={})


@bp.route("/", methods=("GET",))
@login_required
def list_all():
    """
    List all of the epics made by current user
    """
    is_json = request.args.get("is_json", False)
    epics = get_epics()
    if is_json:
        return json.dumps({"Success": True, "epics": [dict(x) for x in epics]})
    return render_template("epic/list.html", epics=epics)
