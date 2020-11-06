import functools
import json
from datetime import datetime

from flask import (
    Blueprint, g, redirect, render_template, request, session, url_for, abort, flash
)

from notscrum.db import get_db

bp = Blueprint('task', __name__, url_prefix='/task')

def get_story_summary():
    db = get_db()
    summary = db.execute(
        'SELECT storyID, ' +
        ' sum(estimate) est, ' +
        ' sum(case when estimate is NULL then 1 else 0 END) unest, ' +
        " sum(case when status <> 'Done' then 1 else 0 END) incomplete, " +
        ' count(1) task_count'
        'FROM task ' +
        'GROUP BY storyID'
    )
    return summary


@bp.route('/create/<int:story_id>', methods=('GET', 'POST'))
def create(story_id):
    is_json = request.args.get('is_json', False)
    is_asc = request.args.get('is_asc', False)
    db = get_db()
    story = db.execute(
        'SELECT id, story, prioritization FROM story WHERE id = ?',
        (story_id,)
    ).fetchone()
    if not story:
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
        error = None

        if estimate == 0 or estimate == '':
            estimate is None

        if not task:
            error = 'Task Name is Required'
        elif not story_id:
            error = 'Story ID Not Found, Please Reload'
        elif db.execute(
            'SELECT id FROM task WHERE task = ? AND storyID = ?',
            (task, story_id, )
        ).fetchone() is not None:
            error = f'Task {task} already in Story {story_id}'

        if error is None:
            db.execute(
                'INSERT INTO task (task, storyID, estimate, deadline) VALUES (?, ?, ?, ?)',
                (task, story_id, estimate, deadline)
            )
            db.commit()
            task = db.execute(
                'SELECT id FROM TASK where task = ? AND storyID = ?',
                (task, story_id)
            ).fetchone()
            if is_json:
                return json.dumps({'Success':True, 'task_id':task['id']})
            return redirect(url_for('task.show', task_id=task['id']))
        if is_json:
            abort(500, error)
        flash(error,'error')
    
    if is_json:
        return json.dumps({'Success':True, story:dict(story)})
    return render_template('task/create.html', story=story, asc=is_asc)


@bp.route('/<int:task_id>', methods=('GET', 'POST'))
def show(task_id):
    db = get_db()
    is_json = request.args.get('is_json', False)
    task = db.execute(
        'SELECT id, task, storyID, estimate, actual, status, deadline, recurring, sprintid FROM task where id = ?',
        (task_id, )
    ).fetchone()
    if not task:
        error =  f'Task with ID {task_id} not found'
        if is_json:
            abort(404,error)
        else:
            flash(error,'error')
            redirect(url_for('task.list_all'))
    
    if request.method == 'POST':
        task_name = request.form.get('task', task['task'])
        estimate = request.form.get('estimate', task['estimate'])
        actual = request.form.get('actual', task['actual'])
        story_id = request.form.get('story_id', task['storyID'])
        status = request.form.get('status', task['status'])
        deadline = request.form.get('deadline',task['deadline'])
        sprint_id = request.form.get('sprintid',task['sprintID'])
        recurring = request.form.get('recurring',task['recurring'])

        error = None

        if not task_name:
            task_name = task['task']
        if not estimate:
            estimate = task['estimate']
        if not actual:
            actual = task['actual']
        if not story_id:
            story_id = task['storyID']
        if not status:
            status = task['status']
        if not sprint_id:
            sprint_id = task['sprintID']
        
        if db.execute(
            'SELECT story FROM story where id = ?',
            (story_id,)
        ).fetchone() is None:
            error = f'Story with ID {story_id} not found'
        elif sprint_id and db.execute(
            'SELECT * FROM sprint WHERE id = ?',
            (sprint_id,)
        ).fetchone() is None:
            error = f'Sprint {sprint_id} not found.'

        if error is None:
            db.execute(
                'UPDATE task SET '+
                    'task     = ?, ' +
                    'storyID  = ?, ' +
                    'estimate = ?, ' +
                    'status   = ?, ' +
                    'actual   = ?, ' +
                    'deadline = ?, ' +
                    'sprintid = ?,  ' +
                    'recurring = ? ' +
                'WHERE id = ?',
                (task_name, story_id, estimate, status, actual, deadline, sprint_id, recurring, task_id)
            )
            db.commit()
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
def list_all():
    db = get_db()
    is_json = request.args.get('is_json', False)
    tasks = db.execute(
        "SELECT id, task, deadline, sprintid, recurring, "+
        "coalesce(estimate,'Unestimated') as estimate, coalesce(actual,0) "+
        "as actual, storyID, status from task"
    ).fetchall()

    stories = db.execute(
        'SELECT story.id, story, epicID, prioritization, story.deadline, '+
        'sum(coalesce(estimate,0)) as estimate, ' +
        'count(task.id) as tasks, ' +
        "COUNT(DISTINCT CASE WHEN task.status <> 'Done' THEN task.id ELSE NULL END) as active_tasks, "  +
        'COUNT(DISTINCT CASE WHEN task.estimate IS NULL THEN task.id ELSE NULL END) as unestimated_tasks, ' +
        "SUM(CASE WHEN task.status <> 'Done' THEN task.estimate - coalesce(task.actual,0) ELSE 0 END) AS rem_estimate " +
        'FROM task '+
        'LEFT OUTER JOIN story on task.storyID = story.id '+
        'GROUP BY story.id, story, epicID, prioritization '+
        'ORDER BY prioritization DESC'
    ).fetchall()
    epics = db.execute(
        'SELECT epic, epic.id, color, epic.deadline, '+
        'sum(coalesce(estimate,0)) as estimate, count(task.id) as tasks, ' +
        "COUNT(DISTINCT CASE WHEN task.status <> 'Done' THEN task.id ELSE NULL END) as active_tasks, "  +
        'COUNT(DISTINCT CASE WHEN task.estimate IS NULL THEN task.id ELSE NULL END) as unestimated_tasks, ' +
        "SUM(CASE WHEN task.status <> 'Done' THEN task.estimate - coalesce(task.actual,0) ELSE 0 END) AS rem_estimate " +
        'FROM epic '+
        'LEFT OUTER JOIN story ON story.epicID = epic.id ' +
        'LEFT OUTER JOIN task ON task.storyID = story.id ' +
        'GROUP BY epic, epic.id, color'
    ).fetchall()
    colors=['primary', 'secondary', 'success', 'alert', 'warning']
    current_sprint = db.execute(
        'SELECT id, startdate, enddate FROM sprint '+
        "WHERE ? BETWEEN startdate AND enddate " +
        "AND startdate <> '1969-12-31'",
        (datetime.now().strftime('%Y-%m-%d'),)
    ).fetchone()
    if is_json:
        return json.dumps({'Success':True, 'tasks':[dict(x) for x in tasks],
        'epics':[dict(x) for x in epics],
        'stories':[dict(x) for x in stories],
        'current_sprint':current_sprint['id']})
    return render_template('task/list.html', current_sprint=current_sprint, tasks=tasks, epics=epics, stories=stories, colors=colors)
