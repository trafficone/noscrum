"""
Handler for epic creation, read, and etc.
"""

from datetime import datetime

from flask_openapi3 import APIBlueprint as Blueprint
from flask import flash, redirect, request, url_for, abort
from flask_login import current_user, login_required
from pydantic import BaseModel
from noscrum_api.template_friendly import friendly_render as render_template
import noscrum_backend.epic as backend
from noscrum_api.template_friendly import NoscrumBaseQuery

bp = Blueprint("epic", __name__, url_prefix="/epic")


@bp.get("/create")
@login_required
def get_create(query: NoscrumBaseQuery):
    """
    Render form for epic creation
    """
    is_asc = query.is_asc
    return render_template("epic/create.html", asc=is_asc)


@bp.post("/create")
@login_required
def create(query: NoscrumBaseQuery):
    """
    Handle creation for a new epic / form data
    """
    is_asc = query.is_asc
    is_json = query.is_json
    req = request.form
    if request.get_json() is not None:
        req = request.get_json()
    epic = req.get("epic", None)
    color = req.get("color", None)
    deadline = req.get("deadline", None)
    if isinstance(deadline, str):
        deadline = datetime.strptime(deadline, "%Y-%m-%d").date()
    error = None

    if not epic:
        error = "Epic Name is Required"
    elif backend.get_epic_by_name(current_user, epic) is not None:
        error = f'Epic named "{epic}" already exists'

    if error is None:
        newEpic = backend.create_epic(current_user, epic, color, deadline)
        if is_json:
            return {"Success": True, "epic": newEpic.to_dict()}
        return redirect(url_for("task.list_all"))
    if is_json:
        print("OH NO! I ERRORED: " + str(error))
        abort(500, error)
    flash(error, "error")
    return render_template("epic/create.html", asc=is_asc)


class EpicPath(BaseModel):
    """
    Path Model for Epic API Requests
    """

    epic_id: int


@bp.get("/<int:epic_id>")
@login_required
def show(path: EpicPath, query: NoscrumBaseQuery):
    """
    Display information or process update epic
    @param epic_id the epic's identifier value
    """
    epic_id = path.epic_id
    is_json = query.is_json
    epic = backend.get_epic(current_user, epic_id)
    if epic is None:
        if is_json or request.method == "POST":
            abort(404, "Epic ID not found in Database")
        else:
            flash(f'Epid ID "{epic_id}" not found.', "error")
            return redirect(url_for("epic.list_all"))
    if is_json:
        return {"Success": True, "epic": epic.to_dict(), "stories": {}}
    return render_template("epic/show.html", epic=epic, stories={})


@bp.post("/<int:epic_id>")
@login_required
def update(path: EpicPath, query: NoscrumBaseQuery):
    """
    Update an epic
    """
    epic_id = path.epic_id
    is_json = query.is_json
    epic = backend.get_epic(current_user, epic_id)
    if epic is None:
        if is_json or request.method == "POST":
            abort(404, "Epic ID not found in Database")
        else:
            flash(f'Epid ID "{epic_id}" not found.', "error")
            return redirect(url_for("epic.list_all"))
    error = None
    epic_name = request.form.get("epic", epic.epic)
    color = request.form.get("color", epic.color)
    deadline = request.form.get("deadline", epic.deadline)
    other_epic = backend.get_epic_by_name(current_user, epic_name)

    if not epic_id:
        error = "Could not find ID for Epic being edited."
    elif other_epic is not None and other_epic.id != epic_id:
        error = f'A different Epic named "{epic.epic}" already exists'

    if error is None:
        backend.update_epic(current_user, epic_id, epic_name, color, deadline)
        if is_json:
            return {"Success": True, "epic": epic.to_dict()}
        return redirect(url_for("epic.show", epic_id=epic_id))
    if is_json:
        abort(500, error)
    flash(error, "error")

    return render_template("epic/show.html", epic=epic, stories={})


@bp.get("/")
@login_required
def list_all(query: NoscrumBaseQuery):
    """
    List all of the epics made by current user
    """
    is_json = query.is_json
    epics = backend.get_epics(current_user)
    if is_json:
        return {"Success": True, "epics": epics}  # [dict(x) for x in epics]}
    return render_template("epic/list.html", epics=epics)
