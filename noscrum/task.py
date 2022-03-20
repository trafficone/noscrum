"""
Task View and Database Interaction Module
"""
from datetime import datetime

from flask import (
    Blueprint, redirect, render_template, request, url_for, abort, flash
)
from flask_user import current_user, login_required

from noscrum.story import get_story, get_stories
from noscrum.epic import get_epics, get_null_epic
from noscrum.sprint import get_current_sprint, get_sprint, get_sprints
from noscrum.db import get_db, Task

bp = Blueprint('task', __name__, url_prefix='/task')


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


def get_task(task_id):
    """
    Task record for user for identifier number
    @task_id task record identification number
    """
    return Task.query.filter(Task.id==task_id).filter(Task.user_id == current_user.id).first()

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
        app_db.func.count(Task.id).filter(Task.estimate is None).label('unest'),
        app_db.func.count(Task.id).filter(Task.status != 'Done').label('incomplete'),
        app_db.func.count().label('task_count')).group_by(Task.story_id).all()

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


@bp.route('/create/<int:story_id>', methods=('GET', 'POST', 'PUT'))
@login_required
def create(story_id):
    """
    Handle creation requests for task in story
    GET: Get form to create a story's new task
    POST: Create task in story using the input
    @param story_id story inwhich task will be
    """
    is_json = request.args.get('is_json', False)
    is_asc = request.args.get('is_asc', False)
    story = get_story(story_id)
    if not story:
        error = f'Cannot create task, parent story ID {story_id} not found'
        if is_json:
            abort(404, error)
        else:
            flash(error, 'error')
            return redirect(url_for('task.list_all'))

    if request.method in ['POST','PUT']:
        task = request.form.get('task', None)
        estimate = request.form.get('estimate', None)
        deadline = request.form.get('deadline', None)
        sprint_id = request.form.get('sprint_id', None)
        if story_id == 0 or request.form.get('epic_id',None) == 0:
            epic_id = request.form.get('epic_id',get_null_epic().id)
            if int(epic_id) == 0:
                epic_id = get_null_epic().id
            #story = get_null_story_for_epic(epic_id)
            story_id = story.id
        error = None

        if estimate == 0 or estimate == '':
            estimate = None
        if estimate is not None and not estimate.strip('-').split('.')[0].isdigit():
            error = 'Cannot set a non-number estimate'

        if task is None:
            error = 'Task Name is Required'
        elif story_id is None:
            error = 'Story ID Not Found, Please Reload'
        elif get_task_by_name(task, story_id) is not None:
            error = f'Task {task} already in Story {story_id}'

        if error is None:
            task = create_task(task, story_id, estimate, deadline, sprint_id)
            story = get_story(task.story_id)
            if is_json:
                return {'Success': True,
                                   'task': task.to_dict(),
                                   'story_id':task.story_id,
                                   'epic_id':story.epic_id}
            return redirect(url_for('task.show', task_id=task.id))
        if is_json:
            abort(500, error)
        flash(error, 'error')

    if is_json:
        return {'Success': True, story: story.to_dict()}
    return render_template('task/create.html', story=story, asc=is_asc)


@bp.route('/<int:task_id>', methods=('GET', 'POST'))
@login_required
def show(task_id):
    """
    Show details of the specific task given id
    GET: Get a task's information nothing else
    POST: Update the task given input provided
    @param task_id Task Identity being queried
    """
    is_json = request.args.get('is_json', False)
    task = get_task(task_id)
    if not task:
        error = f'Task with ID {task_id} not found'
        if is_json:
            abort(404, error)
        else:
            flash(error, 'error')
            redirect(url_for('task.list_all'))

    if request.method == 'POST':
        task_name = request.form.get('task', task.task)
        estimate = request.form.get('estimate', task.estimate)
        actual = request.form.get('actual', task.actual)
        story_id = request.form.get('story_id', task.story_id)
        status = request.form.get('status', task.status)
        deadline = request.form.get('deadline', task.deadline)
        if isinstance(deadline, str):
            deadline = datetime.strptime(deadline, '%Y-%m-%d')
        sprint_id = request.form.get('sprint_id', task.sprint_id)
        recurring = request.form.get('recurring', task.recurring)

        error = None

        if not task_name:
            task_name = task.task
        if not estimate:
            estimate = task.estimate
        if not actual:
            actual = task.actual
        if not story_id:
            story_id = task.story_id
        if not status:
            status = task.status
        if not sprint_id:
            sprint_id = task.sprint_id
        if status not in ['To-Do', 'In Progress', 'Done']:
            error = "Status is invalid. Valid statuses are ['To-Do','In Progress','Done']"

        print(f"Task {task_id} will be in sprint ID {sprint_id}")
        print(sprint_id)
        print(get_sprint(sprint_id))
        if get_story(story_id) is None:
            error = f'Story with ID {story_id} not found'
        elif sprint_id is not None and get_sprint(sprint_id) is None:
            error = f'Sprint {sprint_id} not found.'

        if error is None:
            task = update_task(task_id,
                            task_name,
                            story_id,
                            estimate,
                            status,
                            actual,
                            deadline,
                            sprint_id,
                            recurring)
            if is_json:
                return {'Success': True, 'task': task.to_dict()}
            return redirect(url_for('task.show', task_id=task_id))
        if is_json:
            abort(500, error)
        flash(error, 'error')

    if is_json:
        return {'Success': True, 'task': task.to_dict()}
    return render_template('task/show.html', task=task)

rowproxy_to_dict = lambda x:[{column: value for column, value in rowproxy.items()}
                            for rowproxy in x]

@bp.route('/', methods=['GET'])
@login_required
def list_all():
    """
    Task showcase: lists epics stories & tasks
    """
    is_json = request.args.get('is_json', False)
    tasks = get_tasks()
    stories = get_stories()

    epics = get_epics()
    colors = ['primary', 'secondary', 'success', 'alert', 'warning']
    current_sprint = get_current_sprint()
    user_sprints = get_sprints()
    if is_json:
        return {'Success': True, 'tasks': rowproxy_to_dict(tasks),
                           'epics': [x.to_dict() for x in epics],
                           'stories': [x.to_dict() for x in stories],
                           'current_sprint': current_sprint.id}
    return render_template('task/list.html',
                           current_sprint=current_sprint,
                           sprints=user_sprints,
                           tasks=tasks,
                           epics=epics,
                           stories=stories,
                           colors=colors)
