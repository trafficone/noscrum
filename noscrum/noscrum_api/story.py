"""
To handle Story Model controller and views
"""
from datetime import datetime
import logging
from flask_openapi3 import APIBlueprint as Blueprint
from flask import flash, redirect, request, url_for, abort
from flask_login import current_user, login_required
from pydantic import BaseModel, Field
from noscrum_api.template_friendly import (
    friendly_render as render_template,
    NoscrumBaseQuery,
)
from noscrum_api.epic import EpicPath
import noscrum_backend.story as backend
from noscrum_backend.epic import get_epic, get_epics
from noscrum_backend.db import Story
from noscrum_backend.tag import get_tags_for_story

logger = logging.getLogger()
bp = Blueprint("story", __name__, url_prefix="/story")


@bp.get("/create/<int:epic_id>")
@login_required
def get_create(path: EpicPath, query: NoscrumBaseQuery):
    """
    Returns form to create new story for a given epic
    """
    epic_id = path.epic_id
    is_asc = query.is_asc
    epic = get_epic(current_user, epic_id)
    if epic is None:
        flash(f'Epic with ID "{epic_id}" Not found.', "error")
        return redirect(url_for("story.list_all"))
    return render_template("story/create.html", epic=epic, asc=is_asc)


@bp.post("/create/<int:epic_id>")
@login_required
def create(path: EpicPath, query: NoscrumBaseQuery):
    """
    Handle creation requests for the new story
    GET: Returns form: create new story record
    POST: Create new story record for database
    @param epic_id Epic record identity number
    """
    is_json = query.is_json
    epic_id = path.epic_id
    epic = get_epic(current_user, epic_id)
    if epic is None:
        flash(f'Epic with ID "{epic_id}" Not found.', "error")
        return redirect(url_for("story.list_all"))
    story = request.form.get("story", None)
    prioritization = request.form.get("prioritization", None)
    deadline = request.form.get("deadline", None)
    error = None
    if not story or story == "NULL":
        error = "Story Name is Required"
    elif not epic_id:
        error = "Epic Name not Found, Reload Page"
    elif backend.get_story_by_name(current_user, story, epic_id) is not None:
        error = f"Story {story} already exists"
    if error is None:
        story = backend.create_story(
            current_user, epic_id, story, prioritization, deadline
        )
        if not is_json:
            return redirect(url_for("task.list_all"))
        return {"Success": True, "story_id": story.id}
    return abort(500, error)


class StoryPath(BaseModel):
    """
    API Path Model for Story
    """

    story_id: int = Field(...)


@bp.get("/<int:story_id>/tag")
@login_required
def get_tag(path: StoryPath, query: NoscrumBaseQuery):
    """
    Get a tag for a given story
    """
    is_json = query.is_json
    story_id = path.story_id
    story = backend.get_story(current_user, story_id)
    if story is None:
        error = 'Story "{story_id}" not found, unable to tag'
        if is_json:
            abort(404, error)
        else:
            flash(error, "error")
            return redirect(url_for("story.list_all"))
    tags = get_tags_for_story(current_user, story.id)
    if is_json:
        return {
            "Success": True,
            "story_id": story_id,
            "story": story.to_dict(),
            "tags": [tag for tag in tags if tag.tag_in_story],
        }
    return render_template("story/tag.html", story_id=story_id, story=story, tags=tags)


@bp.post("/<int:story_id>/tag")
@login_required
def tag(path: StoryPath, query: NoscrumBaseQuery):
    """
    Handle tag records for a given story value
    GET: Get tags for some particular story id
    POST: Attach some tag to an inquired story
    DELETE: Remove a tag from the story record
    @param story_id story identification value
    """
    story_id = path.story_id
    is_json = query.is_json
    story = backend.get_story(current_user, story_id)
    if story is None:
        error = 'Story "{story_id}" not found, unable to tag'
        if is_json:
            return abort(404, error)
        flash(error, "error")
        return redirect(url_for("story.list_all"))
    tag_id = request.form.get("tag_id", None)
    error = None
    if not story_id:
        error = "Story ID not found, how did this happen? Return home"
    elif not tag_id:
        error = "TagID not found, Reload Page"
    elif backend.get_tag_story(current_user, story_id, tag_id) is not None:
        error = "Tag already exists on Story"
    if error is None:
        tag_story = backend.insert_tag_story(current_user, story_id, tag_id)
        if is_json:
            return {
                "Success": True,
                "story_id": story_id,
                "tag_id": tag_id,
                "tag_story_id": tag_story.id,
            }
        return redirect(url_for("story.tag", story_id=story_id))
    if is_json:
        return abort(500, error)
    flash(error, "error")
    return redirect(url_for("story.tag", story_id=story_id))


@bp.delete("<int:story_id>/tag")
@login_required
def delete_tag(path: StoryPath, query: NoscrumBaseQuery):
    """
    Delete a tag from a given story
    """
    story_id = path.story_id
    is_json = query.is_json
    story = backend.get_story(current_user, story_id)
    if story is None:
        error = 'Story "{story_id}" not found, unable to tag'
        if is_json:
            abort(404, error)
        else:
            flash(error, "error")
            return redirect(url_for("story.list_all"))
    tag_id = request.form.get("tag_id", None)
    error = None
    if not story_id:
        error = "Story ID not found, Reload Page"
    elif not tag_id:
        error = "TagID not found, Reload Page"
    elif backend.get_tag_story(current_user, story_id, tag_id) is None:
        error = "Tag already deleted from Story"
    if error is None:
        backend.delete_tag_story(current_user, story_id, tag_id)
        if is_json:
            return {"Success": True, "story_id": story_id, "tag_id": tag_id}
        return redirect(url_for("story.tag", story_id=story_id))
    if is_json:
        abort(500, error)
    flash(error, "error")

    tags = get_tags_for_story(current_user, story.id)
    return render_template("story/tag.html", story_id=story_id, story=story, tags=tags)


@bp.get("/")
@login_required
def list_all():
    """
    List all the stories for a particular user
    """
    is_json = request.args.get("is_json", False)
    stories = backend.get_stories(current_user)
    epics = get_epics(current_user)
    if is_json:
        return {"Success": True, "stories": [x.to_dict() for x in stories]}
    return render_template("story/list.html", stories=stories, epics=epics)


@bp.get("/<int:story_id>")
@login_required
def show(path: StoryPath, query: NoscrumBaseQuery):
    """
    Return details for a given story
    """
    is_json = query.is_json
    story_id = path.story_id
    story = backend.get_story(current_user, story_id)
    if not story:
        error = "Story ID does not exist."
        if is_json:
            abort(404, error)
        else:
            flash(error, "error")
            return redirect(url_for("story.list_all"))
    if is_json:
        logger.info(isinstance(story, Story))
        logger.info(story.id)
        return {"Success": True, "story": story.to_dict()}
    return render_template("story/show.html", story=story)


@bp.post("/<int:story_id>")
@login_required
def update(path: StoryPath):
    """
    Show details of a story with some identity
    @param story_id identity for a story value
    """
    story_id = path.story_id
    story = backend.get_story(current_user, story_id)
    if not story:
        error = "Story ID does not exist."
        return abort(404, error)
    story_name = request.form.get("story", story.story)
    epic_id = request.form.get("epic_id", story.epic_id)
    prioritization = request.form.get("prioritization", story.prioritization)
    deadline = request.form.get("deadline", story.deadline)
    if isinstance(deadline, str):
        deadline = datetime.strptime(deadline, "%Y-%m-%d")
    error = None
    # Handle null input from user
    if not story_name:
        story_name = story.story
    if not epic_id:
        epic_id = story.epic_id
    if not prioritization:
        prioritization = story.prioritization
    if get_epic(current_user, epic_id) is None:
        error = f"Epic {epic_id} not found."
    if error is None:
        story = backend.update_story(
            current_user, story_id, story_name, epic_id, prioritization, deadline
        )
        return {"Success": True, "story": story.to_dict()}
    return abort(500, error)


@bp.post("/close/<int:story_id>")
@login_required
def close_story(path: StoryPath):
    """
    Close the story
    """
    story_id = path.story_id
    if story_id == 0:
        abort(401, "Invalid: cannot close NULL story")
    story = backend.get_story(current_user, story_id)
    # is_json = request.args.get("is_json",False)
    closure_state = request.form.get("closure")
    if closure_state not in ["Closed", "Cancelled"]:
        abort(401, "Invalid Closure")
    if story is None:
        abort(404, "Story not found")
    story = backend.close_story_update(
        current_user, story.id, closure_state=closure_state
    )
    return {"Success": True, "story": story.to_dict()}


@bp.delete("/close/<int:story_id>")
@login_required
def reopen_story(path: StoryPath):
    """
    Reopen the story"
    """
    story_id = path.story_id
    if story_id == 0:
        return abort(401, "Invalid, cannot close NULL story")
    story = backend.get_story(current_user, story_id)
    if story is None:
        return abort(404, "Story not found")
    story = backend.close_story_update(current_user, story.id, closure_state=None)
    return {"Success": True, "story": story.to_dict()}
