"""
Story Tag controller/view logic of NoScrum
"""

import json

from fastapi import APIRouter, Depends, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from noscrum.db import get_db
from noscrum.model import Tag, User
from noscrum.user import current_user


async def get_tags(current_user: User = Depends(current_user), app_db=Depends(get_db)):
    """
    Get tag records for the given current user
    """
    return app_db.select(Tag).filter(Tag.user_id == current_user.id).distinct().all()


async def get_tags_for_story(
    story_id, current_user: User = Depends(current_user), app_db=Depends(get_db)
):
    """
    Get all the tag records for the given story
    @param story_id Identity record for a story
    """
    return await (
        app_db.select(Tag)
        .filter(Tag.user_id == current_user.id)
        .distinct()
        .filter(Tag.stories.any(id=story_id))
        .all()
    )


async def get_tag(tag_id, current_user: User = Depends(current_user), app_db=Depends(get_db)):
    """
    Get the Tag record having a given identity
    @param tag_id Identity for the queried tag
    """
    return (
        await app_db.select(Tag)
        .filter(Tag.id == tag_id)
        .filter(Tag.user_id == current_user.id)
        .scalar_one_or_none()
    )


async def get_tag_from_name(tag, current_user: User = Depends(current_user), app_db=Depends(get_db)):
    """
    Get the Tag record using a particular name
    @param tag The name of the tag in question
    """
    return (
        await app_db.select(Tag)
        .filter(Tag.tag == tag)
        .filter(Tag.user_id == current_user.id)
        .first()
    )


async def create_tag(tag, current_user: User = Depends(current_user), app_db=Depends(get_db)):
    """
    Create some new tag for organizing stories
    @param tag The name of the tag in question
    """
    newtag = Tag(tag=tag, user_id=current_user.id)
    await app_db.add(newtag)
    app_db.session.commit()
    return await get_tag_from_name(tag)


async def update_tag(
    tag_id, tag, current_user: User = Depends(current_user), app_db=Depends(get_db)
):
    """
    Update some tag record through using ident
    @param tag The name of the tag in question
    @param tag_id identity for the queried tag
    """
    app_db.select(Tag).filter(Tag.id == tag_id).filter(Tag.user_id == current_user.id).update(
        {tag: tag}, synchronize_session="fetch"
    )
    await app_db.commit()
    return await get_tag(tag_id)


async def delete_tag(tag_id, current_user: User = Depends(current_user), app_db=Depends(get_db)):
    """
    Delete tag record having provided identity
    @param tag_id identity for the deleted tag
    """
    app_db.select(Tag).filter(Tag.id == tag_id).filter(Tag.user_id == current_user.id).delete()
    await app_db.commit()


router = APIRouter(prefix="/tag", tags=["tags", "story"])
templates = Jinja2Templates(directory="templates")


def abort(response_code: int, message: str):
    return JSONResponse(status_code=response_code, content={"Error": {"message": message}})


@router.get("/frontend/create", tags=["frontend"], response_class=HTMLResponse)
def fe_tag_creation_template(request: Request):
    """
    Handle a request to create a new tag record
    """
    return templates.TemplateResponse("tag/create.html", {"request": request})


@router.put("/create")
async def tag_api_create_tag(tag: str):
    error = None
    tag_value = await get_tag_from_name(tag)
    if tag is not None and tag_value is not None:
        error = f"Tag {tag_value.tag} already exists."

    if error is None:
        tag_value = create_tag(tag)
        return json.dumps({"Success": True, "tag": jsonable_encoder(tag_value)})
    return abort(500, error)


@router.post("/{tag_id}")
async def tag_api_update_tag(tag_id: int, tag: Tag):
    if await get_tag(tag_id) is None:
        return abort(404, "Tag ID Not Found")
    error = None
    if await get_tag_from_name(tag.tag) is not None:
        error = f"Tag with name {tag.tag} already exists."
    if error is None:
        await update_tag(tag_id, tag)
        return JSONResponse({"Success": True, "tag": jsonable_encoder(tag)})
    return abort(500, error)


@router.get("/frontend/{tag_id}", tags=["frontend"], response_class=HTMLResponse)
async def fe_tag_show(tag_id: int, is_json: bool = False):
    """
    Return the tag information for a tag by id
    Handles updates as well as delete requests
    """
    tag = await get_tag(tag_id)
    if tag is None:
        return abort(404, "Tag ID Not Found")
    if is_json:
        return JSONResponse({"Success": True, tag: jsonable_encoder(tag)})
    return templates.TemplateResponse("tag/show.html", {"tag": tag})


@router.delete("/{tag_id}")
async def tag_api_delete(tag_id: int, is_json: bool = False):
    tag = await get_tag(tag_id)
    if tag is None:
        return abort(404, "Tag ID Not Found")
    await delete_tag(tag_id)
    if is_json:
        return json.dumps({"Success": True, "tag": jsonable_encoder(tag)})
    return RedirectResponse(router.url_path_for("tag.list_all", data={"tag_id": tag_id}))


@router.get("/frontend/", tags=["frontend"], response_class=HTMLResponse)
async def fe_tag_list_all(is_json: bool = False):
    """
    Handles requests to list all tags for user
    """
    tags = await get_tags()

    if is_json:
        return json.dumps({"Success": True, "tags": [jsonable_encoder(x) for x in tags]})
    return templates.TemplateResponse("tag/list.html", {"tags": tags})
