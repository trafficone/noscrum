"""
Handler for epic creation, read, and etc.
"""

import json
from datetime import date
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Form, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import Row, ScalarResult, Sequence, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from noscrum.db import get_async_session, get_db
from noscrum.model import Epic, User
from noscrum.user import current_user


async def get_epics(
    current_user: User,
    app_db: AsyncSession,
) -> ScalarResult[Epic]:
    """
    Get all epics, optionally for given sprint
    """
    if current_user is None:
        raise ValueError("Cannot perform function without User ID")
    epics = await app_db.execute(select(Epic).where(Epic.user_id == current_user.id))
    return epics.scalars()


async def get_epics_sprint_view(
    current_user: User,
    app_db: AsyncSession,
    sprint_id=None,
) -> Sequence[Row[Any]]:
    epics = await app_db.execute(
        text(
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
            + "GROUP BY epic.epic, epic.id, epic.color"
        ),
        {"user_id": current_user.id, "sprint_id": sprint_id},
    )
    return epics.all()


async def get_epic_by_name(
    epic: str,
    current_user: User,
    app_db: AsyncSession,
) -> Epic | None:
    """
    Return the epic given the name of the epic
    @param epic the requsted epic name queried
    """
    if current_user is None:
        raise ValueError("Cannot perform function without User ID")
    query = select(Epic).where(Epic.epic == epic).where(Epic.user_id == current_user.id)
    results = await app_db.execute(query)
    return results.scalar_one_or_none()


async def get_epic(
    epic_id: int,
    current_user: User,
    app_db: AsyncSession,
) -> Epic:
    """
    Returns an epic given the specific epic_id
    @param epic_id the identifier for the epic
    """
    if current_user is None:
        raise ValueError("Cannot perform function without User ID")
    epic = await app_db.execute(
        select(Epic).where(Epic.id == epic_id).where(Epic.user_id == current_user.id)
    )
    return epic.scalar_one()


async def get_null_epic(
    current_user: User,
    app_db: AsyncSession,
) -> Epic:
    """
    Returns the special null "story" record
    """
    if current_user is None:
        raise ValueError("Cannot perform function without User ID")
    epic_query = await app_db.execute(
        select(Epic).where(Epic.epic == "NULL").where(Epic.user_id == current_user.id)
    )
    epic = epic_query.scalar_one_or_none()
    if epic is None:
        epic = await create_epic("NULL", "green", None, current_user, app_db)
    if epic is None:
        raise ValueError("Could not create NULL epic, database may be unavailable")
    return epic


async def create_epic(
    epic: str,
    color: str,
    deadline: date | None,
    current_user: User,
    app_db: AsyncSession,
) -> Epic:
    """
    Create a new epic with a given color, etc.
    @param epic name of the epic to be created
    @param color the highlighted color for use
    @param deadline (optional) planned end day
    """
    if current_user is None:
        raise ValueError("Cannot perform function without User ID")
    new_epic = Epic(epic=epic, color=color, deadline=deadline, user_id=current_user.id)
    app_db.add(new_epic)
    await app_db.commit()
    epic_rec = await get_epic_by_name(epic, current_user, app_db)
    if epic_rec is None:
        raise ValueError("Could not create Epic")
    return epic_rec


async def update_epic(
    epic_id: int,
    epic: str,
    color: str,
    deadline: date | None,
    current_user: User,
    app_db: AsyncSession,
) -> Epic:
    """
    Update the existing epic with fresh values
    @param epic_id the epic identification val
    @param epic name of the epic to be updated
    @param deadline (optional) planned end day
    """
    if current_user is None:
        raise ValueError("Cannot perform function without User ID")
    epic_rec = await get_epic(epic_id, current_user, app_db)
    epic_rec.epic = epic
    epic_rec.color = color
    epic_rec.deadline = deadline
    await app_db.commit()
    return await get_epic(epic_id, current_user, app_db)


router = APIRouter(prefix="/epic", tags=["epic"])
templates = Jinja2Templates(directory="templates")


def abort(response_code: int, message: str):
    return JSONResponse(status_code=response_code, content={"Error": {"message": message}})


@router.put("/create")
async def epic_create(
    epic: str,
    color: str,
    current_user: User = Depends(current_user),
    app_db=Depends(get_async_session),
):
    """
    Handle creation for a new epic / form data
    """
    error = None
    if await get_epic_by_name(epic, current_user, app_db) is not None:
        error = f'Epic named "{epic}" already exists'

    if error is None:
        epic = jsonable_encoder(await create_epic(epic, color, None, current_user, app_db))
        return JSONResponse({"Success": True, "epic": epic})
    abort(500, error)


@router.get("/{epic_id}")
async def epic_show(
    epic_id: int, current_user: User = Depends(current_user), app_db=Depends(get_db)
):
    """
    Display information or process update epic
    @param epic_id the epic's identifier value
    """
    epic = jsonable_encoder(await get_epic(epic_id, current_user, app_db))
    if epic is None:
        abort(404, "Epic ID not found in Database")
    return JSONResponse({"Success": True, "epic": epic})


@router.post("/{epic_id}")
async def epic_update(
    epic_id: int, epic: Epic, current_user: User = Depends(current_user), app_db=Depends(get_db)
):
    epic = jsonable_encoder(get_epic(epic_id, current_user, app_db))
    if epic is None:
        abort(404, "Epic ID not found in Database")
    error = None
    epic_name = epic.epic
    color = epic.color
    deadline = epic.deadline
    other_epic = await get_epic_by_name(epic_name, current_user, app_db)

    if other_epic is not None and other_epic.id != epic_id:
        error = f'A different Epic named "{epic.epic}" already exists'

    if error is None:
        await update_epic(epic_id, epic_name, color, deadline, current_user, app_db)
        return json.dumps({"Success": True, "epic": jsonable_encoder(epic)})


@router.get("/")
async def epic_list_all(
    current_user: User = Depends(current_user), app_db: AsyncSession = Depends(get_async_session)
):
    """
    List all of the epics made by current user
    """
    if current_user is None:
        return abort(401, "User is not authorized")
    epics = jsonable_encoder(await get_epics(current_user, app_db))
    return JSONResponse({"Success": True, "epics": epics})


@router.post("/frontend/create", response_class=HTMLResponse, tags=["frontend"])
async def fe_epic_create_post(
    request: Request,
    epic: Annotated[str, Form()],
    color: Annotated[str, Form()],
    current_user: User = Depends(current_user),
    app_db=Depends(get_async_session),
):
    """
    Handle creation for a new epic / form data
    """
    error = None
    if await get_epic_by_name(epic, current_user, app_db) is not None:
        error = f'Epic named "{epic}" already exists'

    if error is None:
        epic_resp = await create_epic(epic, color, None, current_user, app_db)
        return templates.TemplateResponse(
            "epic/fragments/epic.html",
            {"request": request, "Success": True, "epic": epic_resp, "current_user": current_user},
        )
    abort(500, error)


@router.get("/frontend/create", response_class=HTMLResponse, tags=["frontend"])
async def fe_epic_creation_template(request: Request, is_asc: bool = False):
    return templates.TemplateResponse(
        "epic/create.html", {"request": request, "asc": is_asc, "current_user": current_user}
    )


@router.get("/frontend/", response_class=HTMLResponse, tags=["frontend"])
async def fe_epic_list_all_frontend(
    request: Request,
    current_user: User = Depends(current_user),
    app_db: AsyncSession = Depends(get_async_session),
):
    """
    List all of the epics made by current user
    """
    epics = await get_epics(current_user, app_db)
    return templates.TemplateResponse(
        "epic/list.html", {"request": request, "epics": epics, "current_user": current_user}
    )
