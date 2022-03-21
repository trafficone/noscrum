"""
To handle Story Model controller and views
"""
import json
from datetime import datetime
from flask import Blueprint, flash, redirect, render_template, request, url_for, abort
from flask_user import current_user, login_required

from noscrum.db import get_db, Story, TagStory, Tag
from noscrum.epic import get_epic, get_epics, get_null_epic
from noscrum.tag import get_tags_for_story

bp = Blueprint("story", __name__, url_prefix="/story")


def get_stories(sprint_view=False, sprint_id=None):
    """
    Get story records with calculated metadata
    @sprint_view True if querying for a sprint
    @sprint_id Identity of the sprint to query
    """
    app_db = get_db()
    if not sprint_view:
        return Story.query.filter(Story.user_id == current_user.id).all()
    return app_db.session.execute(
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
        + "ORDER BY prioritization DESC",
        {"user_id": current_user.id, "sprint_id": sprint_id},
    ).fetchall()


def get_stories_by_epic(epic_id):
    """
    Return queried stories faor the given epic
    @param epic_id Identity of epic being used
    """
    query = Story.query.filter(Story.epic_id == epic_id).filter(
        Story.user_id == current_user.id
    )
    return query.all()


def get_story_by_name(story, epic_id):
    """
    Returns the story record with a name given
    @param story Story name (unique per users)
    @param epic_id Identity of epic being used
    """
    return (
        Story.query.filter(Story.story == story)
        .filter(Story.epic_id == epic_id)
        .filter(Story.user_id == current_user.id)
        .first()
    )


def get_story(story_id, exclude_nostory=True):
    """
    Get the story record by its identity value
    @param story_id story identification value
    @param exclude_nostory exclude special val
    "story" which is null (optional parameter)
    """
    if story_id == 0:
        return get_null_story_for_epic(0)
    query = Story.query.filter(Story.id == story_id)
    if exclude_nostory:
        query = query.filter(Story.story is not None)
    query = query.filter(Story.user_id == current_user.id)
    return query.first()


def get_null_story_for_epic(epic_id):
    """
    Returns the special null "story" record
    """
    if epic_id == 0:
        epic_id = get_null_epic().id
    story = (
        Story.query.filter(Story.story == "NULL")
        .filter(Story.epic_id == epic_id)
        .filter(Story.user_id == current_user.id)
        .first()
    )
    if story is None:
        story = create_story(epic_id, "NULL", None, None)
    return story


def create_story(epic_id, story, prioritization, deadline):
    """
    Create a new story under the given epic id
    @param epic_id Epic record identity number
    @param story Name to describe a story with
    @param prioritization 1-5 with 1 being low
    @param deadline date the story will be due
    """
    if epic_id == 0:
        raise Exception("Tried to create a story without an epic")
    app_db = get_db()
    if prioritization is None:
        new_story = Story(
            story=story, epic_id=epic_id, deadline=deadline, user_id=current_user.id
        )
    else:
        new_story = Story(
            story=story,
            epic_id=epic_id,
            prioritization=prioritization,
            deadline=deadline,
            user_id=current_user.id,
        )
    app_db.session.add(new_story)
    app_db.session.commit()
    story = get_story_by_name(story, epic_id)
    return story


def update_story(story_id, story, epic_id, prioritization, deadline):
    """
    Update properties for a given story record
    @param story_id story identification value
    @param story Name to describe a story with
    @param epic_id Epic record identity number
    @param prioritization 1-5 with 1 being low
    @param deadline date the story will be due
    """
    app_db = get_db()
    Story.query.filter(Story.id == story_id).filter(
        Story.user_id == current_user.id
    ).update(
        {
            "story": story,
            "epic_id": epic_id,
            "prioritization": prioritization,
            "deadline": deadline,
        },
        synchronize_session="fetch",
    )
    app_db.session.commit()
    return get_story(story_id)


def get_tag_story(story_id, tag_id):
    """
    Get a tag for a story given their id value
    @param story_id story identification value
    @param tag_id tag record identifier number
    """
    story = get_story(story_id)
    return (
        Tag.query.filter(Tag.stories.contains(story))
        .filter(Tag.user_id == current_user.id)
        .filter(Tag.id == tag_id)
        .first()
    )


def insert_tag_story(story_id, tag_id):
    """
    Attach a tag to a given story using the id
    @param story_id story identification value
    @param tag_id tag record identifier number
    """
    app_db = get_db()
    tag_story_record = TagStory(story_id=story_id, tag_id=tag_id)
    app_db.session.add(tag_story_record)
    app_db.session.commit()
    return get_tag_story(story_id, tag_id)


def delete_tag_story(story_id, tag_id):
    """
    Remove tag from story by their identifiers
    @param story_id story identification value
    @param tag_id tag record identifier number
    """
    app_db = get_db()
    TagStory.query.filter(TagStory.story_id == story_id).filter(
        TagStory.tag_id == tag_id
    ).delete()
    app_db.session.commit()


@bp.route("/create/<int:epic_id>", methods=("GET", "POST"))
@login_required
def create(epic_id):
    """
    Handle creation requests for the new story
    GET: Returns form: create new story record
    POST: Create new story record for database
    @param epic_id Epic record identity number
    """
    is_json = request.args.get("is_json", False)
    if is_json and request.method == "GET":
        abort(405, "Method not supported for AJAX")
    is_asc = request.args.get("is_asc", False)
    epic = get_epic(epic_id)
    if epic is None:
        flash(f'Epic with ID "{epic_id}" Not found.', "error")
        return redirect(url_for("story.list_all"))
    if request.method == "POST":
        story = request.form.get("story", None)
        prioritization = request.form.get("prioritization", None)
        deadline = request.form.get("deadline", None)
        error = None

        if not story or story == "NULL":
            error = "Story Name is Required"
        elif not epic_id:
            error = "Epic Name not Found, Reload Page"
        elif get_story_by_name(story, epic_id) is not None:
            error = f"Story {story} already exists"

        if error is None:
            story = create_story(epic_id, story, prioritization, deadline)
            if is_json:
                return json.dumps({"Success": True, "story_id": story.id})
            return redirect(url_for("story.show", story_id=story.id))
        if is_json:
            abort(500, error)
        flash(error, "error")
    return render_template("story/create.html", epic=epic, asc=is_asc)


@bp.route("/<int:story_id>/tag", methods=("GET", "POST", "DELETE"))
@login_required
def tag(story_id):
    """
    Handle tag records for a given story value
    GET: Get tags for some particular story id
    POST: Attach some tag to an inquired story
    DELETE: Remove a tag from the story record
    @param story_id story identification value
    """
    is_json = request.args.get("is_json", False)
    story = get_story(story_id)
    if story is None:
        error = 'Story "{story_id}" not found, unable to tag'
        if is_json:
            abort(404, error)
        else:
            flash(error, "error")
            return redirect(url_for("story.list_all"))
    if request.method == "POST":
        tag_id = request.form.get("tag_id", None)
        error = None

        if not story_id:
            error = "Story ID not found, how did this happen? Return home"
        elif not tag_id:
            error = "TagID not found, Reload Page"
        elif get_tag_story(story_id, tag_id) is not None:
            error = "Tag already exists on Story"

        if error is None:
            tag_story = insert_tag_story(story_id, tag_id)
            if is_json:
                return json.dumps(
                    {
                        "Success": True,
                        "story_id": story_id,
                        "tag_id": tag_id,
                        "tag_story_id": tag_story.id,
                    }
                )
            return redirect(url_for("story.tag", story_id=story_id))
        if is_json:
            abort(500, error)
        flash(error, "error")

    elif request.method == "DELETE":
        tag_id = request.form.get("tag_id", None)
        error = None

        if not story_id:
            error = "Story ID not found, Reload Page"
        elif not tag_id:
            error = "TagID not found, Reload Page"
        elif get_tag_story(story_id, tag_id) is None:
            error = "Tag already deleted from Story"

        if error is None:
            delete_tag_story(story_id, tag_id)
            if is_json:
                return json.dumps(
                    {"Success": True, "story_id": story_id, "tag_id": tag_id}
                )
            return redirect(url_for("story.tag", story_id=story_id))
        if is_json:
            abort(500, error)
        flash(error, "error")

    tags = get_tags_for_story(story.id)
    if is_json:
        return json.dumps(
            {
                "Success": True,
                "story_id": story_id,
                "story": dict(story),
                "tags": [tag for tag in tags if tag.tag_in_story],
            }
        )
    return render_template("story/tag.html", story_id=story_id, story=story, tags=tags)


@bp.route("/", methods=("GET",))
@login_required
def list_all():
    """
    List all the stories for a particular user
    """
    is_json = request.args.get("is_json", False)
    stories = get_stories()
    epics = get_epics()
    if is_json:
        return json.dumps({"Success": True, "stories": [dict(x) for x in stories]})
    return render_template("story/list.html", stories=stories, epics=epics)


@bp.route("/<int:story_id>", methods=("GET", "POST"))
@login_required
def show(story_id):
    """
    Show details of a story with some identity
    @param story_id identity for a story value
    """
    is_json = request.args.get("is_json", False)
    story = get_story(story_id)
    if not story:
        error = "Story ID does not exist."
        if is_json:
            abort(404, error)
        else:
            flash(error, "error")
            return redirect(url_for("story.list_all"))

    if request.method == "POST":
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
        if get_epic(epic_id) is None:
            error = f"Epic {epic_id} not found."

        if error is None:
            story = update_story(
                story_id, story_name, epic_id, prioritization, deadline
            )
            if is_json:
                return json.dumps({"Success": True, "story_id": story.id})
            return redirect(url_for("story.show", story_id=story.id))

        if is_json:
            abort(500, error)
        flash(error, "error")
    if is_json:
        return json.dumps({"Success": True, "story": dict(story)})
    return render_template("story/show.html", story=story)
