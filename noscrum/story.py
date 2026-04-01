"""
To handle Story Model controller and views
"""

import json
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Form, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import Row, ScalarResult, Sequence, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from noscrum.db import get_async_session, get_db
from noscrum.epic import get_epic, get_epics, get_null_epic
from noscrum.model import Story, Tag, TagStory, User
from noscrum.tag import get_tags_for_story
from noscrum.user import current_user


async def get_stories(
    current_user: User,
    app_db: AsyncSession,
) -> ScalarResult[Story]:
    """
    Get story records with calculated metadata
    @sprint_view True if querying for a sprint
    @sprint_id Identity of the sprint to query
    """
    stories = await app_db.execute(select(Story).where(Story.user_id == current_user.id))
    return stories.scalars()


async def get_stories_sprint_view(
    current_user: User,
    app_db: AsyncSession,
    sprint_id=None,
) -> Sequence[Row[Any]]:
    stories = await app_db.execute(
        text(
            "SELECT story.id, "
            + "CASE WHEN story = 'NULL' THEN 'No Story' ELSE story END as story, "
            + "epic_id, prioritization, story.deadline, "
            + "sum(coalesce(estimate,0)) as estimate, "
            + "count(task.id) as tasks, "
            + "COUNT(DISTINCT CASE WHEN task.status <> 'Done' THEN task.id ELSE NULL END) "
            + "as active_tasks, "
            + "COUNT(DISTINCT CASE WHEN task.estimate IS NULL THEN task.id ELSE NULL END) "
            + "as unestimated_tasks, "
            + "SUM(CASE WHEN task.status <> 'Done' THEN task.estimate - coalesce(task.actual,0) ELSE 0 "
            + "END) AS rem_estimate "
            + "FROM story "
            + "LEFT OUTER JOIN task on task.story_id = story.id "
            + "AND task.user_id = :user_id "
            + "AND task.sprint_id = :sprint_id "
            + "GROUP BY story.id, story.story, story.epic_id, story.prioritization "
            + "ORDER BY prioritization DESC"
        ),
        {"user_id": current_user.id, "sprint_id": sprint_id},
    )
    return stories.all()


async def get_stories_by_epic(
    epic_id,
    current_user: User,
    app_db: AsyncSession,
) -> ScalarResult[Story]:
    """
    Return queried stories for the given epic
    @param epic_id Identity of epic being used
    """
    query = await app_db.execute(
        select(Story).where(Story.epic_id == epic_id).where(Story.user_id == current_user.id)
    )
    return query.scalars()


async def get_story_by_name(
    story, epic_id, current_user: User, app_db: AsyncSession
) -> Story | None:
    """
    Returns the story record with a name given
    @param story Story name (unique per users)
    @param epic_id Identity of epic being used
    """
    story = await app_db.execute(
        select(Story)
        .where(Story.story == story)
        .where(Story.epic_id == epic_id)
        .where(Story.user_id == current_user.id)
    )
    return story.scalar_one_or_none()


async def get_story(
    story_id,
    current_user: User,
    app_db: AsyncSession,
    exclude_nostory=True,
) -> Story:
    """
    Get the story record by its identity value
    @param story_id story identification value
    @param exclude_nostory exclude special val
    "story" which is null (optional parameter)
    """
    if story_id == 0:
        return await get_null_story_for_epic(0, current_user, app_db)
    query = select(Story).where(Story.id == story_id)
    if exclude_nostory:
        query = query.where(Story.story is not None)
    query = query.where(Story.user_id == current_user.id)
    story = await app_db.execute(query)
    story_scalar = story.scalar_one_or_none()
    if story_scalar is None:
        raise ValueError(f"Could not find story with ID {story_id} for user {current_user.id}")
    return story_scalar


async def get_null_story_for_epic(
    epic_id,
    current_user: User,
    app_db: AsyncSession,
) -> Story:
    """
    Returns the special null "story" record
    """
    if epic_id == 0:
        epic = await get_null_epic(current_user, app_db)
        epic_id = epic.id
    story_query = await app_db.execute(
        select(Story)
        .where(Story.story == "NULL")
        .where(Story.epic_id == epic_id)
        .where(Story.user_id == current_user.id)
    )
    story = story_query.scalar_one_or_none()
    if story is None:
        story = await create_story(epic_id, "NULL", None, None)
    if story is None:
        raise Exception("Could not create null story, database may be disconnected")
    return story


async def create_story(
    epic_id,
    story,
    prioritization,
    deadline,
    current_user: User = Depends(current_user),
    app_db=Depends(get_db),
) -> Story | None:
    """
    Create a new story under the given epic id
    @param epic_id Epic record identity number
    @param story Name to describe a story with
    @param prioritization 1-5 with 1 being low
    @param deadline date the story will be due
    """
    if epic_id == 0:
        raise Exception("Tried to create a story without an epic")
    if prioritization is None:
        new_story = Story(story=story, epic_id=epic_id, deadline=deadline, user_id=current_user.id)
    else:
        new_story = Story(
            story=story,
            epic_id=epic_id,
            prioritization=prioritization,
            deadline=deadline,
            user_id=current_user.id,
        )
    app_db.add(new_story)
    await app_db.commit()
    story = await get_story_by_name(story, epic_id, current_user, app_db)
    return story


async def update_story(
    story_id,
    story,
    epic_id,
    prioritization,
    deadline,
    current_user: User = Depends(current_user),
    app_db=Depends(get_db),
) -> Story:
    """
    Update properties for a given story record.
    @param story_id story identification value
    @param story Name to describe a story with
    @param epic_id Epic record identity number
    @param prioritization 1-5 with 1 being low
    @param deadline date the story will be due
    """
    story = await app_db.execute(
        select(Story).where(Story.id == story_id).where(Story.user_id == current_user.id)
    )
    story.update(
        {
            "story": story,
            "epic_id": epic_id,
            "prioritization": prioritization,
            "deadline": deadline,
        },
        synchronize_session="fetch",
    )
    await app_db.session.commit()
    return await get_story(story_id, current_user, app_db)


async def get_tag_story(
    story_id,
    tag_id,
    current_user: User,
    app_db: AsyncSession,
):
    """
    Get a tag for a story given their id value
    @param story_id story identification value
    @param tag_id tag record identifier number
    """
    story = get_story(story_id, current_user, app_db)
    tag_story_q = await app_db.execute(
        select(Tag)
        .where(story in Tag.stories)
        .where(Tag.user_id == current_user.id)
        .where(Tag.id == tag_id)
    )
    return tag_story_q.scalar_one()


async def insert_tag_story(
    story_id,
    tag_id,
    current_user: User,
    app_db: AsyncSession,
):
    """
    Attach a tag to a given story using the id
    @param story_id story identification value
    @param tag_id tag record identifier number
    """
    tag_story_record = TagStory(story_id=story_id, tag_id=tag_id)
    app_db.add(tag_story_record)
    await app_db.commit()
    return await get_tag_story(story_id, tag_id, current_user, app_db)


async def delete_tag_story(
    story_id,
    tag_id,
    current_user: User,
    app_db: AsyncSession,
):
    """
    Remove tag from story by their identifiers
    @param story_id story identification value
    @param tag_id tag record identifier number
    """
    tag_story_q = await app_db.execute(
        select(TagStory).where(TagStory.story_id == story_id).where(TagStory.tag_id == tag_id)
    )
    await app_db.delete(tag_story_q)
    await app_db.commit()


router = APIRouter(prefix="/story", tags=["story"])
templates = Jinja2Templates(directory="templates")


def abort(response_code: int, message: str):
    return JSONResponse(status_code=response_code, content={"Error": {"message": message}})


@router.get("/frontend/create/{epic_id}", tags=["frontend"], response_class=HTMLResponse)
async def fe_story_creation_template(
    request: Request,
    epic_id: int,
    is_asc: bool = False,
    current_user: User = Depends(current_user),
    app_db: AsyncSession = Depends(get_async_session),
):
    """
    Handle creation requests for the new story
    GET: Returns form: create new story record
    POST: Create new story record for database
    @param epic_id Epic record identity number
    """
    if epic_id is None:
        return abort(404, "Epic ID is required")
    epic = await get_epic(epic_id, current_user, app_db)
    if epic is None:
        return abort(404, f"Epic with ID {epic_id} could not be found")
    return templates.TemplateResponse(
        "story/fragments/create.html", {"request": request, "epic": epic, "asc": is_asc}
    )


@router.post("/create/{epic_id}")
async def story_create(
    epic_id: int,
    story: Annotated[str, Form()],
    prioritization: Annotated[str, Form()],
    current_user: User = Depends(current_user),
    app_db=Depends(get_db),
):
    error = None
    if await get_story_by_name(story, epic_id, current_user, app_db) is not None:
        return abort(403, f"Story with name {story} already exists for epic")

    if error is None:
        story_c = await create_story(epic_id, story, prioritization, None, current_user, app_db)
        if story_c is not None:
            return JSONResponse({"Success": True, "story": jsonable_encoder(story_c)})
        else:
            error = "Could not find created story"
    return abort(500, error)


@router.put("/create/{epic_id}")
async def story_api_create(
    storyname: str,
    prioritization: int,
    epic_id: int,
    current_user: User = Depends(current_user),
    app_db=Depends(get_db),
):
    error = None
    if await get_story_by_name(storyname, epic_id, current_user, app_db) is not None:
        return abort(403, f"Story with name {storyname} already exists for epic")

    if error is None:
        # deadline not yet supported on story creation
        story_c = await create_story(epic_id, storyname, prioritization, None, current_user, app_db)
        if story_c is not None:
            story = story_c
            return JSONResponse({"Success": True, "story": jsonable_encoder(story)})
        else:
            error = "Could not find created story"
    return abort(500, error)


@router.get(
    "/frontend/{story_id}/tag", tags=["frontend", "tags"], response_class=HTMLResponse
)  # , methods=('GET', 'POST', 'DELETE'))
async def fe_story_list_tags(
    request: Request,
    story_id: int,
    is_json: bool = True,
    current_user: User = Depends(current_user),
    app_db=Depends(get_db),
):
    """
    Handle tag records for a given story value
    GET: Get tags for some particular story id
    POST: Attach some tag to an inquired story
    DELETE: Remove a tag from the story record
    @param story_id story identification value
    """
    story = await get_story(story_id, current_user, app_db)
    if story is None:
        error = 'Story "{story_id}" not found, unable to tag'
        if is_json:
            return abort(404, error)
        else:
            return RedirectResponse(router.url_path_for("story.list_all"))
    tags = await get_tags_for_story(story_id)
    if is_json:
        return json.dumps(
            {
                "Success": True,
                "story_id": story_id,
                "story": story,  # .to_dict(),
                "tags": [tag for tag in tags if tag.tag_in_story],
            }
        )
    return templates.TemplateResponse(
        "story/tag.html", {"request": request, "story_id": story_id, "story": story, "tags": tags}
    )


@router.put("/{story_id}/tag", tags=["tags"])
async def story_api_create_tag(
    story_id: int,
    tag_id: int,
    is_json: bool = True,
    current_user: User = Depends(current_user),
    app_db=Depends(get_db),
):
    story = await get_story(story_id, current_user, app_db)
    if story is None:
        error = 'Story "{story_id}" not found, unable to tag'
        if is_json:
            return abort(404, error)
        else:
            return RedirectResponse(router.url_path_for("story.list_all"))
    error = None
    if get_tag_story(story_id, tag_id, current_user, app_db) is not None:
        error = "Tag already exists on Story"

    if error is None:
        tag_story = await insert_tag_story(story_id, tag_id, current_user, app_db)
        if is_json:
            return JSONResponse(
                {
                    "Success": True,
                    "story_id": story_id,
                    "tag_id": tag_id,
                    "tag_story_id": tag_story.id,
                }
            )
        return RedirectResponse(router.url_path_for("story.list_tags", story_id=story_id))
    return abort(500, error)


@router.delete("/{story_id}/tag", tags=["tags"])
async def story_api_remove_tag(
    story_id: int,
    tag_id: int,
    is_json: bool = True,
    current_user: User = Depends(current_user),
    app_db=Depends(get_db),
):
    story = await get_story(story_id, current_user, app_db)
    if story is None:
        error = 'Story "{story_id}" not found, unable to tag'
        if is_json:
            return abort(404, error)
        else:
            return RedirectResponse(router.url_path_for("story.list_all"))
    error = None
    await delete_tag_story(story_id, tag_id, current_user, app_db)
    if is_json:
        return json.dumps({"Success": True, "story_id": story_id, "tag_id": tag_id})
    return RedirectResponse(router.url_path_for("story.list_tag", story_id=story_id))


@router.get("/frontend/", tags=["frontend"], response_class=HTMLResponse)
async def fe_story_list_all(
    is_json: bool = False, current_user: User = Depends(current_user), app_db=Depends(get_db)
):
    """
    List all the stories for a particular user
    """
    stories = await get_stories(current_user, app_db)
    epics = await get_epics(current_user, app_db)
    if is_json:
        return json.dumps({"Success": True, "stories": [dict(x) for x in stories]})
    return templates.TemplateResponse(
        "story/list.html", {"stories": stories, "epics": epics, "current_user": current_user}
    )


@router.get("/frontend/{story_id}", response_class=HTMLResponse, tags=["frontend"])
async def fe_story_show(
    request: Request,
    story_id: int,
    is_json: bool = False,
    current_user: User = Depends(current_user),
    app_db: AsyncSession = Depends(get_db),
):
    """
    Show details of a story with some identity
    @param story_id identity for a story value
    """
    story = await get_story(story_id, current_user, app_db)
    if not story:
        error = "Story ID does not exist."
        if is_json:
            return abort(404, error)
        else:
            return RedirectResponse(router.url_path_for("story.list_all"))
    if is_json:
        return json.dumps({"Success": True, "story": jsonable_encoder(story)})
    return templates.TemplateResponse(
        "story/show.html", {"request": request, "story": story, "current_user": current_user}
    )


@router.get("/frontend/list/{epic_id}", response_class=HTMLResponse, tags=["frontend"])
async def fe_list_stories_for_epic(
    request: Request,
    epic_id: int,
    current_user: User = Depends(current_user),
    app_db=Depends(get_db),
):
    """
    Show details of a story with some identity
    @param story_id identity for a story value
    """
    stories = await get_stories_by_epic(epic_id, current_user, app_db)
    return templates.TemplateResponse(
        "story/fragments/list.html",
        {
            "request": request,
            "stories": stories,
            "current_user": current_user,
            "colors": ["primary", "secondary", "success", "alert", "warning"],
        },
    )


@router.post("/{story_id}")
async def story_api_update_story(
    story_id: int, story: Story, current_user: User = Depends(current_user), app_db=Depends(get_db)
):
    error = None
    if await get_epic(story.epic_id, current_user, app_db) is None:
        error = f"Epic {story.epic_id} not found."

    if error is None:
        story = await update_story(
            story_id,
            story.story,
            story.epic_id,
            story.prioritization,
            story.deadline,
            current_user,
            app_db,
        )
        return JSONResponse({"Success": True, "story": jsonable_encoder(story.id)})

    return abort(500, error)
