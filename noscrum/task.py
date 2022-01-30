import functools
import json
from datetime import datetime

from flask import (
    Blueprint, g, redirect, render_template, request, session, url_for, abort, flash
)
from flask_user import current_user, login_required

from noscrum.story import get_null_story_for_epic, get_story, get_stories
from noscrum.epic import get_epics
from noscrum.sprint import get_current_sprint, get_sprint
from noscrum.db import get_db, Task,Story,ScheduleTask,Work

bp = Blueprint('task', __name__, url_prefix='/task')

def get_tasks():
    db = get_db()
    return db.session.execute('SELECT task.id, task, estimate, status, story_id, '+
        'epic_id, actual, task.deadline, task.recurring, coalesce(hours_worked,0) hours_worked, ' +
        'coalesce(sum_sched,0) sum_sched, ' +
        '(task.sprint_ID = sched.sprint_id) single_sprint_task '+
        'FROM task ' +
        'JOIN story ON task.story_id = story.id ' +
        'LEFT OUTER JOIN (SELECT task_id, sum(hours_worked) hours_worked '+
                        'from work group by task_id) woik '+
        'ON woik.task_id = task.id '+
        'LEFT OUTER JOIN (select task_id, sprint_id, count(1) * 2 sum_sched '+
                        'FROM schedule_task group by task_id, sprint_id) sched '+
        'ON task.id = sched.task_id '+
        'WHERE task.user_id = :user_id',{'user_id':current_user.id})
    db.select([
        Task.id,
        Task.task,
        Task.estimate,
        Task.status,
        Task.story_id,
        Story.epic_id,
        Task.actual,
        Task.deadline,
        Task.recurring,
        ]).join(db.session.query(db.select([ScheduleTask.task_id,
        (db.func.distinct(ScheduleTask.sprint_id) == 1).label('single_sprint_task')]).group_by(ScheduleTask.task_id)))\
        .join(db.session.query(db.select([Work.task_id,
        db.func.sum(Work.hours_worked).label('hours_worked')]).group_by(Work.task_id)))\
        .group_by(Task.id)\
        .filter(Task.user_id == current_user.id)#)

    oldquery = """
            'SELECT task.id, task, estimate, status, story_id, '+
        'epic_id, actual, task.deadline, task.recurring, coalesce(hours_worked,0) hours_worked, ' +
        'coalesce(sum_sched,0) sum_sched, ' +
        '(task.sprint_id = sched.sprint_id) single_sprint_task '+
    return db.execute(
        "SELECT id, task, deadline, sprint_id, recurring, "+
        "coalesce(estimate,'Unestimated') as estimate, coalesce(actual,0) "+
        "as actual, story_id, status from task"
    ).fetchall()
    """

def get_tasks_for_story(story_id):
    db = get_db()
    return Task.query.filter(Task.story_id == story_id).filter(Task.user_id == current_user.id).all()
    """
    return db.execute(
        'SELECT * from task WHERE story_id = ?',
        (story_id,)
    ).fetchall()
    """

def get_tasks_for_epic(epic_id):
    db = get_db()
    return Task.query.filter(Task.stories.epic_id == epic_id).filter(Task.user_id == current_user.id).all()
    """
    return db.execute('SELECT task.id, task.task from task '+\
        'join story on task.story_id = story.id '+\
        ' where story.epic_id = ?',(epic_id,)).fetchall()
    """

def get_task_by_name(task,story_id):
    db = get_db()
    return Task.query.filter(Task.story_id == story_id).\
        filter(Task.task == task).\
        filter(Task.user_id == current_user.id).first()
    """
    return db.execute(
        'SELECT * FROM task WHERE task = ? AND story_id = ?',
            (task, story_id, )
    ).fetchone()
    """

def create_task(task, story_id, estimate, deadline, sprint_id):
    db = get_db()
    newtask = Task(task=task,
        story_id = story_id,
        estimate=estimate,
        deadline=deadline,
        sprint_id = sprint_id,
        user_id = current_user.id)
    """
    db.execute(
        'INSERT INTO task (task, story_id, estimate, deadline, sprint_id) VALUES (?, ?, ?, ?, ?)',
        (task, story_id, estimate, deadline, sprint_id)
    )
    """
    db.session.add(newtask)
    db.session.commit()
    return get_task_by_name(task,story_id)

def get_task(id):
    db = get_db()
    return Task.query.filter(Task.id==id).filter(Task.user_id == current_user.id).first()
    """
    return db.execute(
        'SELECT id, task, story_id, estimate, actual, status, deadline, recurring, sprint_id FROM task where id = ?',
        (id, )
    ).fetchone()
    """

def update_task(id, task, story_id, estimate, status, actual, deadline, sprint_id, recurring):
    db = get_db()
    data = {}
    query = Task.query.filter(Task.id==id).filter(Task.user_id == current_user.id)
    if task is not None:
        data['task']=task
    if story_id is not None:
        data['story_id']=story_id
    if estimate is not None:
        data['estimate']=estimate 
    if status is not None:
        data['status']=status 
    if actual is not None:
        data['actual']=actual 
    if deadline is not None:
        data['deadline']=deadline 
    if sprint_id is not None:
        data['sprint_id']=sprint_id 
    if recurring is not None:
        data['recurring']=recurring 
    query.update(data,synchronize_session="fetch")
    db.session.commit()

def delete_task(id):
    db = get_db()
    raise NotImplementedError('Deleting Tasks is Not Supported')
    Task.query.filter(Task.id==id).filter(Task.user_id==current_user.id)

@bp.route('/create/<int:story_id>', methods=('GET', 'POST'))
@login_required
def create(story_id):
    is_json = request.args.get('is_json', False)
    is_asc = request.args.get('is_asc', False)
    story = get_story(story_id)
    if not story and not (request.method == 'POST' and 'epic_id' in request.form):
        error = f'Cannot create task, parent story ID {story_id} not found'
        if is_json:
            abort(404, error)
        else:
            flash(error,'error')
            return redirect(url_for('task.list_all'))
    
    if request.method == 'POST':
        task = request.form.get('task', None)
        estimate = request.form.get('estimate', None)
        deadline = request.form.get('deadline',None)
        sprint_id = request.form.get('sprint_id',None)
        if story_id == 0: 
            if 'epic_id' not in request.form:
                abort(500,'EPIC ID not found in input')
            epic_id = request.form['epic_id']
            story = get_null_story_for_epic(epic_id)
            story_id = story.id
        error = None

        if estimate == 0 or estimate == '':
            estimate is None

        if not task:
            error = 'Task Name is Required'
        elif not story_id:
            error = 'Story ID Not Found, Please Reload'
        elif get_task_by_name(task,story_id) is not None:
            error = f'Task {task} already in Story {story_id}'

        if error is None:
            task = create_task(task, story_id, estimate, deadline, sprint_id)
            if is_json:
                return json.dumps({'Success':True, 'task_id':task.id})
            return redirect(url_for('task.show', task_id=task.id))
        if is_json:
            abort(500, error)
        flash(error,'error')
    
    if is_json:
        return json.dumps({'Success':True, story:dict(story)})
    return render_template('task/create.html', story=story, asc=is_asc)


@bp.route('/<int:task_id>', methods=('GET', 'POST'))
@login_required
def show(task_id):
    is_json = request.args.get('is_json', False)
    task = get_task(task_id)
    if not task:
        error =  f'Task with ID {task_id} not found'
        if is_json:
            abort(404,error)
        else:
            flash(error,'error')
            redirect(url_for('task.list_all'))
    
    if request.method == 'POST':
        task_name = request.form.get('task', task.task)
        estimate = request.form.get('estimate', task.estimate)
        actual = request.form.get('actual', task.actual)
        story_id = request.form.get('story_id', task.story_id)
        status = request.form.get('status', task.status)
        deadline = request.form.get('deadline',task.deadline)
        if isinstance(deadline,str):
            deadline = datetime.strptime(deadline,'%Y-%m-%d')
        #TODO: Input validation
        sprint_id = request.form.get('sprint_id',task.sprint_id)
        recurring = request.form.get('recurring',task.recurring)

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
        
        if get_story(story_id) is None:
            error = f'Story with ID {story_id} not found'
        elif sprint_id and get_sprint(sprint_id) is None:
            error = f'Sprint {sprint_id} not found.'

        if error is None:
            task = update_task(task_id,task_name, story_id, estimate, status, actual, deadline, sprint_id, recurring)
            if is_json:
                return json.dumps({'Success':True, 'task_id':task_id})
            return redirect(url_for('task.show', task_id=task_id))
        if is_json:
            abort(500, error)
        flash(error,'error')
    
    if is_json:
        return json.dumps({'Success':True, 'task':dict(task)})
    return render_template('task/show.html', task=task)


@bp.route('/', methods=['GET'])
@login_required
def list_all():
    is_json = request.args.get('is_json', False)
    tasks = get_tasks()
    stories = get_stories()

    epics = get_epics()
    colors=['primary', 'secondary', 'success', 'alert', 'warning']
    current_sprint = get_current_sprint()
    if is_json:
        return json.dumps({'Success':True, 'tasks':[dict(x) for x in tasks],
        'epics':[dict(x) for x in epics],
        'stories':[dict(x) for x in stories],
        'current_sprint':current_sprint.id})
    return render_template('task/list.html', current_sprint=current_sprint, tasks=tasks, epics=epics, stories=stories, colors=colors)
