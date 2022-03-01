"""
Story Tag controller/view logic of NoScrum
"""
import json
from fastapi import FastAPI
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
from fastapi.encoders import jsonable_encoder
from fastapi.templating import Jinja2Templates
from noscrum.user import current_user
from noscrum.model import Tag
from noscrum.db import get_db


def get_tags():
    """
    Get tag records for the given current user
    """
    return Tag.query.filter(Tag.user_id == current_user.id).distinct().all()


def get_tags_for_story(story_id):
    """
    Get all the tag records for the given story
    @param story_id Identity record for a story
    """
    return Tag.query.filter(Tag.user_id == current_user.id).distinct()\
        .filter(Tag.stories.any(id=story_id)).all()


def get_tag(tag_id):
    """
    Get the Tag record having a given identity
    @param tag_id Identity for the queried tag
    """
    return Tag.query.filter(Tag.id == tag_id)\
        .filter(Tag.user_id == current_user.id).first()


def get_tag_from_name(tag):
    """
    Get the Tag record using a particular name
    @param tag The name of the tag in question
    """
    return Tag.query.filter(Tag.tag == tag)\
        .filter(Tag.user_id == current_user.id).first()


def create_tag(tag):
    """
    Create some new tag for organizing stories
    @param tag The name of the tag in question
    """
    app_db = get_db()
    newtag = Tag(tag=tag, user_id=current_user.id)
    app_db.session.add(newtag)
    app_db.session.commit()
    return get_tag_from_name(tag)


def update_tag(tag_id, tag):
    """
    Update some tag record through using ident
    @param tag The name of the tag in question
    @param tag_id identity for the queried tag
    """
    app_db = get_db()
    Tag.query.filter(Tag.id == tag_id)\
        .filter(Tag.user_id == current_user.id)\
        .update({tag: tag}, synchronize_session="fetch")
    app_db.session.commit()
    return get_tag(tag_id)


def delete_tag(tag_id):
    """
    Delete tag record having provided identity
    @param tag_id identity for the deleted tag
    """
    app_db = get_db()
    Tag.query.filter(Tag.id == tag_id)\
        .filter(Tag.user_id == current_user.id).delete()
    app_db.session.commit()

app = FastAPI()
templates = Jinja2Templates(directory="templates")
def abort(response_code: int, message: str):
    return JSONResponse(status_code = response_code, content={'Error':{'message':message}})


@app.get('/create',response_class=HTMLResponse)
def get_create_form():
    """
    Handle a request to creat a new tag record
    """
    return templates.TemplateResponse('tag/create.html',{})

@app.put('/create')
def api_create_tag(tag: str):
    error = None
    tag_value = get_tag_from_name(tag)
    if tag is not None and tag_value is not None:
        error = f"Tag {tag_value.tag} already exists."

    if error is None:
        tag_value = create_tag(tag)
        return json.dumps({'Success': True, 'tag': jsonable_encoder(tag_value)})
    return abort(500, error)

@app.post('/{tag_id}')
def api_update_tag(tag_id: int, tag: Tag):
    if get_tag(tag_id) is None:
        return abort(404, 'Tag ID Not Found')
    error = None
    if get_tag_from_name(tag.tag) is not None:
        error = f"Tag with name {tag.tag} already exists."
    if error is None:
        update_tag(tag_id, tag)
        return JSONResponse({'Success': True, 'tag': jsonable_encoder(tag)})
    return abort(500, error)

@app.get('/{tag_id}')
def show(tag_id: int, is_json: bool = False):
    """
    Return the tag information for a tag by id
    Handles updates as well as delete requests
    """
    tag = get_tag(tag_id)
    if tag is None:
        return abort(404, 'Tag ID Not Found')
    if is_json:
        return JSONResponse({'Success': True, tag: jsonable_encoder(tag)})
    return templates.TemplateResponse('tag/show.html', {"tag":tag})

@app.delete('/{tag_id}')
def api_delete(tag_id: int, is_json: bool = False):
    tag = get_tag(tag_id)
    if tag is None:
        return abort(404, 'Tag ID Not Found')
    delete_tag(tag_id)
    if is_json:
        return json.dumps({'Success': True, 'tag': jsonable_encoder(tag)})
    return RedirectResponse(app.url_path_for('tag.list_all', {"tag_id":tag_id}))


@app.get('/')
def list_all(is_json: bool = False):
    """
    Handles requests to list all tags for user
    """
    tags = get_tags()

    if is_json:
        return json.dumps({'Success': True, "tags": [jsonable_encoder(x) for x in tags]})
    return templates.TemplateResponse('tag/list.html', {"tags":tags})
