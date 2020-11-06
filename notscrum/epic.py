import functools
import json

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, abort
)

from notscrum.db import get_db

bp = Blueprint('epic', __name__, url_prefix='/epic')


@bp.route('/create', methods=('GET', 'POST'))
def create():
    is_json = request.args.get('is_json',False)
    is_asc = request.args.get('is_asc',False)
    if request.method == 'POST':
        epic = request.form.get('name',None)
        color = request.form.get('color',None)
        deadline = request.form.get('deadline',None)
        db = get_db()
        error = None

        if not epic:
            error = 'Epic Name is Required'
        elif db.execute(
            'SELECT id FROM epic WHERE epic = ?', (epic,)
        ).fetchone() is not None:
            error = f'Epic named "{epic}" already exists'

        if error is None:
            db.execute(
                'INSERT INTO epic (epic, color, deadline) VALUES (?, ?, ?)',
                (epic, color, deadline)
            )
            db.commit()
            epic = db.execute(
                'SELECT id FROM epic where epic = ?', (epic,)
            ).fetchone()
            if is_json:
                return json.dumps({'Success':True,'epic_id':epic['id']})
            return redirect(url_for('epic.show', epic_id=epic['id']))
        if is_json:
            abort(500,error)
        flash(error,'error')

    return render_template('epic/create.html',asc=is_asc)


@bp.route('/<int:epic_id>', methods=('GET', 'POST'))
def show(epic_id):
    db = get_db()
    is_json = request.args.get('is_json',False)
    epic = db.execute(
        'SELECT id, epic, color, deadline FROM epic where id = ?', (epic_id,)
    ).fetchone()
    if epic is None:
        if is_json or request.method == 'POST':
            abort(404,f'Epic ID "{epic_id}" not found in Database')
        else:
            flash(f'Epid ID "{epic_id}" not found.','error')
            return redirect(url_for('epic.list_all'))
    if request.method == 'POST':
        #TODO: Make Epics Editable from template
        error = None
        epic_name = request.form.get('name',epic['epic'])
        color = request.form.get('color',epic['color'])
        deadline = request.form.get('deadline',epic['deadline'])

        if not epic_id:
            error = 'Could not find ID for Epic being edited.'
        elif db.execute(
            'SELECT id FROM epic WHERE epic = ? and epic_id <> ?',
            (epic_name,epic_id)
        ).fetchone() is not None:
            error = f'A different Epic named "{epic}" already exists'
        
        if error is None:
            db.execute(
                "UPDATE epic SET epic = ?, color = ?, deadline = ? WHERE id = ?",
                (epic_name,color,deadline,epic_id)
            )
            db.commit()
            if is_json:
                return json.dumps({'Success':True,'epic_id':epic_id})
            return redirect(url_for('epic.show', epic_id=epic_id))
        if is_json:
            abort(500,error)
        flash(error,'error')

    stories = db.execute(
        'SELECT story.id, story, prioritization, task.sprintID, '+
        'COUNT(task.id) as tasks, '+
        "COUNT(DISTINCT CASE WHEN task.status <> 'Done' THEN task.id ELSE NULL END) as active_tasks, "  +
        'COUNT(DISTINCT CASE WHEN task.estimate IS NULL THEN task.id ELSE NULL END) as unestimated_tasks, ' +
        'SUM(task.estimate) as total_estimate, '+
        "SUM(CASE WHEN task.status <> 'Done' THEN task.estimate ELSE 0 END) AS rem_estimate " +
        'FROM story ' +
        'LEFT OUTER JOIN task ON task.storyID = story.id ' +
        'WHERE epicID = ? ' +
        'GROUP BY story.id, story, prioritization, task.sprintID ' +
        'ORDER BY prioritization DESC',
        (epic_id, )
    )
    if is_json:
        return json.dumps({'Success':True, 'epic':dict(epic), 'stories': [dict(x) for x in stories]})
    return render_template('epic/show.html', epic=epic, stories=stories)


@bp.route('/', methods=('GET',))
def list_all():
    db = get_db()
    is_json = request.args.get('is_json',False)
    epics = db.execute(
        'SELECT id, epic, color, deadline FROM epic'
    ).fetchall()
    if is_json:
        return json.dumps({'Success':True, 'epics':[dict(x) for x in epics]})
    return render_template('epic/list.html', epics=epics)
