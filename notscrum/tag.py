import functools
import json

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, abort
)

from notscrum.db import get_db

bp = Blueprint('tag', __name__, url_prefix='/tag')


@bp.route('/create', methods=('GET','POST'))
def create():
    is_json = request.args.get('is_json',False)
    if is_json and request.method == 'GET':
        abort(405,'Method not supported for AJAX mode')
    if request.method == 'POST':
        tag = request.form.get('tag',None)
        error = None
        db = get_db()

        if tag is None:
            error = "Tag not populated."
        elif db.execute(
            'SELECT id FROM tag WHERE tag = ?',
            (tag,)
        ).fetchone() is not None:
            error = f"Tag {tag} already exists."
        
        if error is None:
            db.execute(
                'INSERT INTO tag (tag) VALUES (?)',
                (tag,)
            )
            db.commit()
            tag_id = db.execute(
                'SELECT id FROM tag WHERE tag = ?',
                (tag,)
            ).fetchone()['id']
            if is_json:
                return json.dumps({'Success':True,'tag_id':tag_id})
            return redirect(url_for('tag.show',tag_id = tag_id))
        if is_json:
            abort(500,error)
        flash(error,'error')

    return render_template('tag/create.html')


@bp.route('/<int:tag_id>', methods=('GET','POST','DELETE'))
def show(tag_id):
    db = get_db()
    is_json = request.args.get('is_json',False)
    tag = db.execute(
        'SELECT id, tag FROM tag WHERE id = ?',
        (tag_id,)
    ).fetchone()
    if tag is None:
        error = f'Tag ID "{tag_id}" not found.'
        if is_json:
            abort(404, error)
        else:
            flash(error,'error')
            return redirect(url_for('tag.list_all'))

    if request.method=='POST':
        tag_name = request.form.get('tag',None)
        error = None
        
        if tag_name is None:
            error = "Tag not populated."
        elif db.execute(
            'SELECT id FROM tag WHERE tag = ?',
            (tag_name,)
        ).fetchone() is not None:
            error = f"Tag {tag} already exists."
        
        if error is None:
            db.execute(
                'UPDATE tag SET tag = ? '+
                'WHERE id = ?',
                (tag_name, tag_id)
            )
            db.commit()

            if is_json:
                return json.dumps({'Success':True,'tag_id':tag_id})
            return redirect(url_for('tag.view', tag_id = tag_id))
        
        if is_json:
            abort(500,error)
        flash(error,'error')
    
    elif request.method == 'DELETE':
        db.execute(
            'DELETE FROM tag WHERE id = ?',
            (tag_id,)
        )
        db.commit()
        if is_json:
            return json.dumps({'Success':True,'tag_id':tag_id})
        return redirect(url_for('tag.list_all', tag_id = tag_id))
    if is_json:
        return json.dumps({'Success':True,tag:dict(tag)})
    return render_template('tag/show.html',tag = tag)


@bp.route('/', methods=('GET',))
def list_all():
    db = get_db()
    is_json = request.args.get('is_json',False)
    tags = db.execute(
        'SELECT id, tag FROM tag'
    )

    if is_json:
        return json.dumps({'Success':True,tags:[dict(x) for x in tags]})
    return render_template('tag/list.html', tags = tags)
