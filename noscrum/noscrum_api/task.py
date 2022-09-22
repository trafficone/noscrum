"""
Task View and Database Interaction Module
"""
import logging
import json
from datetime import datetime

from pydantic import BaseModel, Field
from flask import abort, flash, redirect, request, url_for
from flask_login import current_user, login_required
from flask_openapi3 import APIBlueprint as Blueprint
import noscrum_backend.task as backend
from noscrum_api.story import StoryPath
from noscrum_api.template_friendly import NoscrumBaseQuery
from noscrum_api.template_friendly import friendly_render as render_template
from noscrum_backend.epic import get_epic, get_epics
from noscrum_backend.sprint import get_current_sprint, get_sprint, get_sprints
from noscrum_backend.story import get_null_story_for_epic, get_stories, get_story

logger = logging.getLogger()
bp = Blueprint("task", __name__, url_prefix="/task")


@bp.get("/create/<int:story_id>")
@login_required
def get_create(path: StoryPath, query: NoscrumBaseQuery):
    """
    GET: Get form to create a story's new task
    """
    story_id = path.story_id
    is_asc = query.is_asc
    story = get_story(current_user, story_id)
    if not story:
        error = f"Cannot create task, parent story ID {story_id} not found"
        flash(error, "error")
        return redirect(url_for("task.list_all"))
    return render_template("task/create.html", story=story, asc=is_asc)


@bp.put("/create/<int:story_id>")
@login_required
def create(path: StoryPath, query: NoscrumBaseQuery):
    """
    Handle creation requests for task in story
    GET: Get form to create a story's new task
    POST: Create task in story using the input
    @param story_id story inwhich task will be
    """
    story_id = path.story_id
    is_json = query.is_json
    is_asc = query.is_asc
    story = get_story(current_user, story_id)
    if not story:
        error = f"Cannot create task, parent story ID {story_id} not found"
        if is_json:
            return abort(404, error)
        flash(error, "error")
        return redirect(url_for("task.list_all"))
    req = request.form
    if request.get_json() is not None:
        req = request.get_json()
    task = req.get("task", None)
    estimate = req.get("estimate", None)
    deadline = req.get("deadline", None)
    sprint_id = req.get("sprint_id", None)
    if story_id == 0:
        epic_id = int(req.get("epic_id", 0))
        logger.info("Task thinks Null Epic ID is %s", epic_id)
        story = get_null_story_for_epic(current_user, epic_id)
        story_id = story.id
    error = None
    estimate = estimate if estimate not in [0, ""] else None
    if (
        estimate is not None
        and isinstance(estimate, str)
        and not estimate.strip("-").split(".")[0].isdigit()
    ):
        error = "Cannot set a non-number estimate"
    if task is None:
        error = "Task Name is Required"
    elif story_id is None:
        error = "Story ID Not Found, Please Reload"
    elif backend.get_task_by_name(current_user, task, story_id) is not None:
        error = f"Task {task} already in Story {story_id}"

    if error is None:
        task = backend.create_task(
            current_user, task, story_id, estimate, deadline, sprint_id
        )
        story = get_story(current_user, task.story_id)
        if is_json:
            return {
                "Success": True,
                "task": task.to_dict(),
                "story_id": task.story_id,
                "epic_id": story.epic_id,
            }
        return redirect(url_for("task.show", task_id=task.id))
    if is_json:
        return abort(500, error)
    flash(error, "error")
    return render_template("task/create.html", story=story, asc=is_asc)


class TaskPath(BaseModel):
    """
    API Path Model for Task
    """

    task_id: int = Field(...)


@bp.get("/<int:task_id>")
@login_required
def show(path: TaskPath, query: NoscrumBaseQuery):
    """
    Show details of the specific task given id
    GET: Get a task's information nothing else
    """
    is_json = query.is_json
    task_id = path.task_id
    task = backend.get_task(current_user, task_id)
    if not task:
        error = f"Task with ID {task_id} not found"
        if is_json:
            abort(404, error)
        else:
            flash(error, "error")
            redirect(url_for("task.list_all"))
    if is_json:
        task_dict = task.to_dict()
        story = get_story(current_user, task.story_id)
        epic = get_epic(current_user, story.epic_id)
        task_dict["epic"] = epic.epic
        task_dict["story"] = story.story
        return {"Success": True, "task": task_dict}
    return render_template("task/show.html", task=task)


@bp.post("/<int:task_id>")
@login_required
def update(path: TaskPath, query: NoscrumBaseQuery):
    """
    POST: Update the task given input provided
    @param task_id Task Identity being queried
    """
    error = None
    is_json = query.is_json
    task_id = path.task_id
    task = backend.get_task(current_user, task_id)
    if not task:
        error = f"Task with ID {task_id} not found"
        if is_json:
            abort(404, error)
        else:
            flash(error, "error")
            redirect(url_for("task.list_all"))

    req = request.form
    if request.get_json() is not None:
        req = request.get_json()
    task_name = req.get("task", task.task)
    estimate = req.get("estimate", task.estimate)
    actual = req.get("actual", task.actual)
    story_id = req.get("story_id", task.story_id)
    status = req.get("status", task.status)
    deadline = req.get("deadline", task.deadline)
    if isinstance(deadline, str):
        deadline = datetime.strptime(deadline, "%Y-%m-%d")
    sprint_id = req.get("sprint_id", task.sprint_id)
    recurring = req.get("recurring", task.recurring)
    if status not in ["To-Do", "In Progress", "Done"]:
        error = "Status is invalid. Valid statuses are ['To-Do','In Progress','Done']"
    if get_story(current_user, story_id) is None:
        error = f"Story with ID {story_id} not found"
    elif sprint_id is not None and get_sprint(current_user, sprint_id) is None:
        error = f"Sprint {sprint_id} not found."

    if error is None:
        task = backend.update_task(
            current_user,
            task_id,
            task_name,
            story_id,
            estimate,
            status,
            actual,
            deadline,
            sprint_id,
            recurring,
        )
        if is_json:
            return {"Success": True, "task": task.to_dict()}
        return redirect(url_for("task.show", task_id=task_id))
    return abort(500, error)


rowproxy_to_dict = lambda x: [dict(rowproxy.items()) for rowproxy in x]


@bp.get("/")
@login_required
def list_all(query: NoscrumBaseQuery):
    """
    Task showcase: lists epics stories & tasks
    """
    is_json = query.is_json
    get_closed = request.args.get("archive", False)
    tasks = backend.get_tasks(current_user)
    if get_closed:
        stories = get_stories(current_user, closed=True)
    else:
        stories = get_stories(current_user, closed=False)

    epics = get_epics(current_user)
    colors = ["primary", "secondary", "success", "alert", "warning"]
    current_sprint = get_current_sprint(current_user)
    current_sprint_id = "NA" if current_sprint is None else current_sprint.id
    user_sprints = get_sprints(current_user)
    if is_json:
        return {
            "Success": True,
            "epics": [x.to_dict() for x in epics],
            "current_sprint": current_sprint_id,
        }
    sprints = {x.id: x for x in user_sprints}
    epics_array = [x.to_dict() for x in epics]
    return render_template(
        "task/list.html",
        current_sprint=current_sprint,
        sprints=sprints,
        tasks=tasks,
        epics=epics,
        epics_json=json.dumps(epics_array),
        stories=stories,
        colors=colors,
        archive=get_closed,
    )
