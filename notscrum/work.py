import functools
import json
from datetime import date

from flask import (
    Blueprint, g, redirect, render_template, request, session, url_for, abort, flash
)

from notscrum.db import get_db

bp = Blueprint('work', __name__, url_prefix='/work')

@bp.route('/create/<int:task_id>',methods=('POST','GET'))
def create(task_id):
    is_json = request.args.get('is_json',False)
    db = get_db()
    task = db.execute('SELECT id, task, status, estimate, coalesce(actual,0) as actual FROM task WHERE id = ?',(task_id,)).fetchone()
    if task is None:
        error = f'Task {task_id} Not Found'
        if is_json:
            abort(404, error)
        else:
            flash(error,'error')
            return redirect(url_for('task.list_all'))
    if request.method == 'GET':
        return render_template('work/create.html',task=task)
    elif request.method == 'POST':
        work_date = request.form.get('work_date',date.today())
        hours_worked = request.form.get('hours_worked',0)
        try:
            hours_worked = 0 if hours_worked == '' else int(hours_worked)
        except ValueError:
            if is_json:
                abort(500,'Could not convert hours_worked to int.')
            flash(f"Could not convert hours worked {hours_worked} to int.")
            return redirect(url_for('work.list_for_task',task_id=task_id))
        status = request.form.get('status',task['status'])
        update_status = request.form.get('update_status',False)
        update_status = True if update_status or update_status == 'on' else False
        true_actual = db.execute('select sum(hours_worked) actual from work where taskid = ?',(task_id,)).fetchone()
        new_actual = int(true_actual['actual']) + hours_worked
        task_status = status if update_status else task['status']
        db.execute('''
            INSERT INTO work (work_date, hours_worked, status, taskid) VALUES (?,?,?,?)
        ''', (work_date, hours_worked, status, task_id))
        db.execute('''
            UPDATE task SET
                actual = ?,
                status = ?
            WHERE id = ?
        ''', (new_actual,task_status,task_id))
        db.commit()
        if is_json:
            return json.dumps({'Success':True,'task_id':task_id})
        return redirect(url_for('work.list_for_task',task_id=task_id))

@bp.route('/<int:work_id>',methods=('GET','DELETE'))
def read_delete(work_id):
    is_json = request.args.get('is_json',False)
    db = get_db()
    work_item = db.execute(
        "SELECT id, taskid, work_date, hours_worked, status FROM work where workid = ?",
         (work_id,)
    ).fetchone()
    if work_item is None:
        error = f'Work Item {work_id} Not Found'
        if is_json:
            abort(404, error)
        else:
            flash(error,'error')
            return redirect(url_for('sprint.active'))
    if request.method == 'GET':
        if is_json:
            return json.dumps({'Success':True,'work_id':work_id,'work_item':work_item})
        return render_template('work/read_del',work_item=work_item)
    elif request.method == 'DELETE':
        db.execute('DELETE FROM work WHERE id = ?',(work_id,))
        db.commit()
        if is_json:
            return json.dumps({'Success':True,'work_id':work_id})
        return redirect(url_for('work.list_for_task',task_id=work_item['task_id']))

@bp.route('/list/task/<int:task_id>',methods=('GET',))
def list_for_task(task_id):
    is_json = request.args.get('is_json',False)
    db = get_db()
    tasks = db.execute('SELECT id, task from task where id = ?',(task_id,)).fetchall()
    if tasks is None:
        error = f'Task Item {task_id} not found'
        if is_json:
            abort(404, error)
        else:
            flash(error,'error')
            return redirect(url_for('sprint.active'))
    work_items = db.execute("SELECT id, taskid, work_date, hours_worked, status "+\
        "FROM work where taskid = ? order by work_date",(task_id,)).fetchall()
    if work_items is None:
        error = f'No Work Items found for Task {task_id}'
        if is_json:
            abort(404, error)
        else:
            flash(error, 'error')
            return redirect(url_for('sprint.active'))
    if is_json:
        return json.dumps({'Sucecss':True,'work_items':work_items})
    return render_template('work/list.html',key='Task',tasks=tasks,work_items=work_items)

@bp.route('/list/story/<int:story_id>',methods=('GET',))
def list_for_story(story_id):
    is_json = request.args.get('is_json',False)
    db = get_db()
    story = db.execute('SELECT id, story from story where id = ?',(story_id,)).fetchone()
    if story is None:
        error = f'Story Item {story_id} not found'
        if is_json:
            abort(404, error)
        else:
            flash(error,'error')
            return redirect(url_for('sprint.active'))
    tasks = db.execute('SELECT task.id, task.task from task '+\
        'where storyid = ?',(story_id,)).fetchall()
    if tasks is None:
        error = f'No Tasks found for Story {story_id}'
        if is_json:
            abort(404, error)
        else:
            flash(error,'error')
            return redirect(url_for('sprint.active'))
    work_items = db.execute("SELECT work.id, taskid, work_date, hours_worked, status '+\
        'FROM work JOIN task on work.taskid = task.id '+\
        'WHERE task.storyid = ? order by work_date",(story_id,)).fetchall()
    if work_items is None:
        error = f'No Work Items found for Story {story_id}'
        if is_json:
            abort(404, error)
        else:
            flash(error,'error')
            return redirect(url_for('sprint.active'))
    if is_json:
        return json.dumps({'Sucecss':True,'work_items':work_items})
    return render_template('work/list.html',key='Story '+story['story'],tasks=tasks,work_items=work_items)

@bp.route('/list/epic/<int:epic_id>',methods=('GET',))
def list_for_epic(epic_id):
    is_json = request.args.get('is_json',False)
    db = get_db()
    epic = db.execute('SELECT id, epic from epic where id = ?',(epic_id,)).fetchone()
    if epic is None:
        error = f'Epic Item {epic_id} not found'
        if is_json:
            abort(404, error)
        else:
            flash(error,'error')
            return redirect(url_for('sprint.active'))
    tasks = db.execute('SELECT task.id, task.task from task '+\
        'join story on task.storyid = story.id '+\
        ' where story.epicid = ?',(epic_id,)).fetchall()
    if tasks is None:
        error = f'No Tasks found for Epic {epic_id}'
        if is_json:
            abort(404, error)
        else:
            flash(error,'error')
            return redirect(url_for('sprint.active'))
    work_items = db.execute("SELECT work.id, taskid, work_date, hours_worked, status "+\
        'FROM work JOIN task on work.taskid = task.id '+\
        'JOIN story ON task.storyid = story.id '+\
        ' WHERE story.epicid = ? order by work_date',(epic_id,)).fetchall()
    if work_items is None:
        error = f'No Work Items found for Epic {epic_id}'
        if is_json:
            abort(404, error)
        else:
            flash(error,'error')
            return redirect(url_for('sprint.active'))
    if is_json:
        return json.dumps({'Sucecss':True,'work_items':work_items})
    return render_template('work/list.html',key='Epic ' + epic['epic'],tasks=tasks,work_items=work_items)

@bp.route('/list/dates',methods=('GET',))
def list_for_dates():
    is_json = request.args.get('is_json',False)
    start_date = request.args.get('start_date',date(2020,1,1))
    end_date = request.args.get('start_date',date.today())
    db = get_db()
    tasks = db.execute("SELECT id, task FROM tasks where id in "+\
        "(SELECT DISTINCT taskid FROM work WHERE work_date BETWEEEN ? and ?)",(start_date,end_date)).fetchall()
    work_items = db.execute("SELECT id, taskid, work_date, hours_worked, status FROM work "+\
        "WHERE work_date BETWEEN ? and ? order by work_date",(start_date,end_date)).fetchall()
    if work_items is None:
        error = f'No work items found between {start_date} and {end_date}'
        if is_json:
            abort(404, error)
        else:
            flash(error,'error')
            return redirect(url_for('sprint.active'))
    if is_json:
        return json.dumps({'Success':True,'work_items':work_items})
    return render_template('work/list.html',key=f'Dates from {start_date} to {end_date}',tasks=tasks,work_items=work_items)

