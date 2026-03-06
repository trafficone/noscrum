"""
Handler for epic creation, read, and etc.
"""

import json

from fastapi import APIRouter
from fastapi.encoders import jsonable_encoder
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from noscrum.db import get_db
from noscrum.model import Epic
from noscrum.user import current_user


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


router = APIRouter(prefix="/epic", tags=["epic"])
templates = Jinja2Templates(directory="templates")


def abort(response_code: int, message: str):
    return JSONResponse(
        status_code=response_code, content={"Error": {"message": message}}
    )


@router.put("/create")
async def create(epic: Epic):
    """
    Handle creation for a new epic / form data
    """
    error = None
    if get_epic_by_name(epic.epic) is not None:
        error = f'Epic named "{epic.epic}" already exists'

    if error is None:
        epic = jsonable_encoder(create_epic(epic.epic, epic.color, epic.deadline))
        return JSONResponse({"Success": True, "epic": epic})
    abort(500, error)


@router.get("/create", response_class=HTMLResponse)
async def get_creation_template(is_asc: bool = False):
    return templates.TemplateResponse("epic/create.html", {"asc": is_asc})


@router.get("/{epic_id}")
async def show(epic_id: int):
    """
    Display information or process update epic
    @param epic_id the epic's identifier value
    """
    epic = jsonable_encoder(get_epic(epic_id))
    if epic is None:
        abort(404, "Epic ID not found in Database")
    return JSONResponse({"Success": True, "epic": epic})


@router.post("/{epic_id}")
async def update(epic_id: int, epic: Epic):
    epic = jsonable_encoder(get_epic(epic_id))
    if epic is None:
        abort(404, "Epic ID not found in Database")
    error = None
    epic_name = epic.epic
    color = epic.color
    deadline = epic.deadline
    other_epic = get_epic_by_name(epic_name)

    if other_epic is not None and other_epic.id != epic_id:
        error = f'A different Epic named "{epic.epic}" already exists'

    if error is None:
        update_epic(epic_id, epic_name, color, deadline)
        return json.dumps({"Success": True, "epic": jsonable_encoder(epic)})


@router.get("/")
async def list_all():
    """
    List all of the epics made by current user
    """
    epics = jsonable_encoder(get_epics())
    return JSONResponse({"Success": True, "epics": epics})
    # return render_template('epic/list.html', epics=epics)
