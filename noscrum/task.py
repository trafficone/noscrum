"""
Task View and Database Interaction Module
"""
import json
from datetime import datetime
from fastapi import FastAPI
from fastapi.responses import JSONResponse, RedirectResponse, HTMLResponse
from fastapi.encoders import jsonable_encoder
from fastapi.templating import Jinja2Templates

from noscrum.story import get_story, get_stories, get_null_story_for_epic
from noscrum.epic import get_epics, get_null_epic
from noscrum.sprint import get_current_sprint, get_sprint, get_sprint_number_for_user, get_next_sprint
from noscrum.model import Task
from noscrum.db import get_db
from noscrum.user import current_user


def get_tasks():
    """
    Get every task record for the current user
    """
    app_db = get_db()
    return app_db.session.execute('SELECT task.id, task, estimate, status, story_id, ' +
                                  'epic_id, actual, task.deadline, task.recurring, ' +
                                  'coalesce(hours_worked,0) hours_worked, ' +
                                  'coalesce(sum_sched,0) sum_sched, ' +
                                  '(task.sprint_ID = sched.sprint_id) single_sprint_task ' +
                                  'FROM task ' +
                                  'JOIN story ON task.story_id = story.id ' +
                                  'LEFT OUTER JOIN (SELECT task_id, ' +
                                  'sum(hours_worked) hours_worked ' +
                                  'from work group by task_id) woik ' +
                                  'ON woik.task_id = task.id ' +
                                  'LEFT OUTER JOIN (select task_id, sprint_id, ' +
                                  'count(1) * 2 sum_sched ' +
                                  'FROM schedule_task group by task_id, sprint_id) sched ' +
                                  'ON task.id = sched.task_id ' +
                                  'WHERE task.user_id = :user_id',
                                  {'user_id': current_user.id})


def get_task(task_id):
    """
    Task record for user for identifier number
    @task_id task record identification number
    """
    return Task.query.filter(Task.id == task_id).filter(Task.user_id == current_user.id).first()


def get_tasks_for_story(story_id):
    """
    Get all task records for the current story
    @param story_id asked Story identification
    """
    return Task.query.filter(Task.story_id == story_id)\
        .filter(Task.user_id == current_user.id).all()


def get_story_summary():
    """
    Get task summary for each story by task ID
    """
    app_db = get_db()
    return app_db.session.query(
        Task.story_id,
        app_db.func.sum(Task.estimate).label('est'),
        app_db.func.count(Task.id).filter(
            Task.estimate is None).label('unest'),
        app_db.func.count(Task.id).filter(
            Task.status != 'Done').label('incomplete'),
        app_db.func.count().label('task_count')).group_by(Task.story_id).all()


def get_tasks_for_epic(epic_id):
    """
    Get all task records for a certain epic id
    @param epic_id Epic record identity number
    """
    return Task.query.filter(Task.stories.epic_id == epic_id)\
        .filter(Task.user_id == current_user.id).all()


def get_task_by_name(task, story_id):
    """
    Get a task with a certain name in a sprint
    @param task Name of task being queried for
    @param story_id Identification for a story
    """
    return Task.query.filter(Task.story_id == story_id).\
        filter(Task.task == task).\
        filter(Task.user_id == current_user.id).first()


def create_task(task, story_id, estimate, deadline, sprint_id):
    """
    Create a new task under a given story with
    @param task Name of task being queried for
    @param story_id Identification for a story
    @param estimate number of hours estimation
    @param deadline date when task will be due
    @param sprint_id Sprint where task planned
    """
    app_db = get_db()
    newtask = Task(task=task,
                   story_id=story_id,
                   estimate=estimate,
                   deadline=deadline,
                   sprint_id=sprint_id,
                   user_id=current_user.id)
    app_db.session.add(newtask)
    app_db.session.commit()
    return get_task_by_name(task, story_id)


def update_task(task_id, task, story_id, estimate, status, actual, deadline, sprint_id, recurring):
    """
    Update the properties for an existing task
    @task_id task record identification number
    @param task Name of task being queried for
    @param story_id Identification for a story
    @param estimate number of hours estimation
    @param actual hours spent to complete task
    @param deadline date when task will be due
    @param sprint_id Sprint where task planned
    @param recurring does it recur each sprint
    """
    app_db = get_db()
    data = {}
    query = Task.query.filter(Task.id == task_id).filter(
        Task.user_id == current_user.id)
    if task is not None:
        data['task'] = task
    if story_id is not None:
        data['story_id'] = story_id
    if estimate is not None:
        data['estimate'] = estimate
    if status is not None:
        data['status'] = status
    if actual is not None:
        data['actual'] = actual
    if deadline is not None:
        data['deadline'] = deadline
    if sprint_id is not None:
        data['sprint_id'] = sprint_id
    if recurring is not None:
        if recurring in ['1', 1, 'true', 'T', 'Y']:
            recurring = True
        else:
            recurring = False
        data['recurring'] = recurring
    query.update(data, synchronize_session="fetch")
    app_db.session.commit()
    return get_task(task_id)


def delete_task(task_id):
    """
    Delete task, task deletion not implemented
    """
    #app_db = get_db()
    # Task.query.filter(Task.id==task_id).filter(Task.user_id==current_user.id).delete()
    # app_db.commit()
    raise NotImplementedError('Deleting Tasks is Not Supported')


app = FastAPI()
templates = Jinja2Templates(directory="templates")
def abort(response_code: int, message: str):
    return JSONResponse(status_code = response_code, content={'Error':{'message':message}})

@app.get('/create/{story_id}',response_class=HTMLResponse)
def get_create_form(story_id: int, is_json: bool = False, is_asc: bool = False):
    """
    Handle creation requests for task in story
    GET: Get form to create a story's new task
    POST: Create task in story using the input
    @param story_id story inwhich task will be
    """
    story = get_story(story_id)
    if not story:
        error = f'Cannot create task, parent story ID {story_id} not found'
        return abort(404, error)
    return templates.TemplateResponse('task/create.html', {"story":story, "asc":is_asc})

@app.put('/create/{story_id}')
def api_create(story_id: int, task: Task, epic_id: int = 0):
    story = get_story(story_id)
    if not story:
        error = f'Cannot create task, parent story ID {story_id} not found'
        return abort(404, error)
    if story_id == 0:
        if epic_id == 0:
            epic_id = get_null_epic().id()
        story_id = get_null_story_for_epic(epic_id)
    error = None
    if get_task_by_name(task.task, story_id) is not None:
        error = f'Task {task} already in Story {story_id}'
    if error is None:
        task = create_task(task.task,
                          story_id, 
                          task.estimate, 
                          task.deadline, 
                          task.sprint_id)
        return JSONResponse({'Success': True,
                            'task': jsonable_encoder(task)})
    return abort(500, error)

@app.get('/{task_id}')
def show(task_id: int, is_json: bool = False):
    """
    Show details of the specific task given id
    GET: Get a task's information nothing else
    POST: Update the task given input provided
    @param task_id Task Identity being queried
    """
    task = get_task(task_id)
    if not task:
        error = f'Task with ID {task_id} not found'
        return abort(404, error)
    if is_json:
        return json.dumps({'Success': True, 'task': jsonable_encoder(task)})
    return templates.TemplateResponse('task/show.html', {"task":task})

@app.post('/{task_id}')
def api_update(task_id: int, task: Task):
    error = None
    # TODO: Handle this in model
    if task.status not in ['To-Do', 'In Progress', 'Done']:
        error = "Status is invalid. Valid statuses are ['To-Do','In Progress','Done']"

    if get_story(task.story_id) is None:
        error = f'Story with ID {task.story_id} not found'
    elif task.sprint_id is not None and get_sprint(task.sprint_id) is None:
        error = f'Sprint {task.sprint_id} not found.'

    if error is None:
        task = update_task(task_id,
                        task.task_name,
                        task.story_id,
                        task.estimate,
                        task.status,
                        task.actual,
                        task.deadline,
                        task.sprint_id,
                        task.recurring)
        return JSONResponse({'Success': True, 'task': jsonable_encoder(task)})
    return abort(500, error)


@app.get('/')
def list_all(is_json: bool = False):
    """
    Task showcase: lists epics stories & tasks
    """
    tasks = get_tasks()
    stories = get_stories()

    epics = get_epics()
    colors = ['primary', 'secondary', 'success', 'alert', 'warning']
    current_sprint = get_current_sprint()
    sprint_number = dict()
    if current_sprint is not None:
        sprint_number[current_sprint.id] = get_sprint_number_for_user(current_sprint.id)
    next_sprint = get_next_sprint()
    if next_sprint is not None:
        sprint_number[next_sprint.id] = get_sprint_number_for_user(next_sprint.id)
    if is_json:
        return JSONResponse({'Success': True, 'tasks': [dict(x) for x in tasks],
                           'epics': [dict(x) for x in epics],
                           'stories': [dict(x) for x in stories],
                           'current_sprint': current_sprint.id})
    return templates.TemplateResponse('task/list.html',
                           {"current_sprint":current_sprint,
                           "next_sprint":next_sprint,
                           "sprint_number":sprint_number,
                           "tasks":tasks,
                           "epics":epics,
                           "stories":stories,
                           "colors":colors})