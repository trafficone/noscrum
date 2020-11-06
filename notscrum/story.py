import functools
import json

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, abort
)

from notscrum.db import get_db

bp = Blueprint('story', __name__, url_prefix='/story')


@bp.route('/create/<int:epic_id>', methods=('GET', 'POST'))
def create(epic_id):
    db = get_db()
    is_json = request.args.get('is_json',False)
    if is_json and request.method == 'GET':
        abort(405,'Method not supported for AJAX')
    is_asc = request.args.get('is_asc',False)
    epic = db.execute(
        'SELECT id, epic, color, deadline FROM epic where id = ?',
        (epic_id,)
    ).fetchone()
    if epic is None:
        flash(f'Epic with ID "{epic_id}" Not found.','error')
        return redirect(url_for('story.list_all'))
    if request.method == 'POST':
        story = request.form.get('story',None)
        prioritization = request.form.get('prioritization',None)
        deadline = request.form.get('deadline',None)
        error = None

        if not story:
            error = 'Story Name is Required'
        elif not epic_id:
            error = 'Epic Name not Found, Reload Page'
        elif db.execute(
            'SELECT id FROM story WHERE story = ? and epicID = ?',
            (story, epic_id, )
        ).fetchone() is not None:
            error = f'Story {story} already exists'

        if error is None:
            db.execute(
                'INSERT INTO story (story, epicID, prioritization, deadline) VALUES (?, ?, ?, ?)',
                (story, epic_id, prioritization, deadline)
            )
            db.commit()
            story = db.execute(
                'SELECT id FROM story WHERE story = ? and epicID = ?',
                (story, epic_id)
            ).fetchone()
            if is_json:
                return json.dumps({'Success':True,'story_id':story['id']})
            return redirect(url_for('story.show', story_id=story['id']))
        if is_json:
            abort(500, error)
        flash(error,'error')
    return render_template('story/create.html', epic=epic, asc=is_asc)


@bp.route('/<int:story_id>/tag', methods=('GET', 'POST', 'DELETE'))
def tag(story_id):
    db = get_db()
    is_json = request.args.get('is_json',False)
    story = db.execute(
        'SELECT id, story, deadline FROM story WHERE id = ?',
        (story_id,)
    ).fetchone()
    if story is None:
        error = 'Story "{story_id}" not found, unable to tag'
        if is_json:
            abort(404,error)
        else:
            flash(error,'error')
            return redirect(url_for('story.list_all'))
    if request.method == 'POST':
        tag_id = request.form.get('tag_id',None)
        error = None

        if not story_id:
            error = 'Story ID not found, how did this happen? Return home'
        elif not tag_id:
            error = 'TagID not found, Reload Page'
        elif db.execute(
            'SELECT id FROM tag_story WHERE storyID = ? and tagID = ?',
            (story_id, tag_id, )
        ).fetchone() is not None:
            error = 'Tag already exists on Story'

        if error is None:
            db.execute(
                'INSERT INTO tag_story (storyID, tagID) VALUES (?, ?)',
                (story_id, tag_id)
            )
            db.commit()
            if is_json:
                return json.dumps({'Success':True,'story_id':story_id,'tag_id':tag_id})
            return redirect(url_for('story.tag', story_id = story_id))
        if is_json:
            abort(500,error)
        flash(error,'error')
    
    elif request.method == 'DELETE':
        tag_id = request.form.get('tag_id',None)
        error = None

        if not story_id:
            error = 'Story ID not found, Reload Page'
        elif not tag_id:
            error = 'TagID not found, Reload Page'
        elif db.execute(
            'SELECT id FROM tag_story WHERE storyID = ? and tagID = ?',
            (story_id, tag_id, )
        ).fetchone() is None:
            error = 'Tag already deleted from Story'

        if error is None:
            db.execute(
                'DELETE FROM tag_story WHERE  storyID = ? AND tagID = ?',
                (story_id, tag_id)
            )
            db.commit()
            if is_json:
                return json.dumps({'Success':True,'story_id':story_id,'tag_id':tag_id})
            return redirect(url_for('story.tag', story_id = story_id))
        if is_json:
            abort(500,error)
        flash(error,'error')

    tags = db.execute(
        'SELECT tag.id, tag, tag_story.id IS NOT NULL as tag_in_story FROM tag '+
        'LEFT OUTER JOIN tag_story ON tag.id = tag_story.tagID '+
        'AND tag_story.storyID = ?',
        (story_id,)
    ).fetchall()
    if tags is not None:
        tags = [dict(x) for x in tags]
    if is_json:
        return json.dumps({'Success':True,'story_id':story_id,'story':dict(story),'tags':[dict(x) for x in tags if x['tags_in_story']]})
    return render_template('story/tag.html', story_id=story_id, story=story, tags=tags)


@bp.route('/', methods=('GET',))
def list_all():
    db = get_db()
    is_json = request.args.get('is_json',False)
    stories = db.execute(
        'SELECT story.id, story.story, story.deadline, epicID, epic, color, prioritization from ' +
        'story JOIN epic ON story.epicID = epic.id ' +
        'order by color, epic, prioritization desc'
    ).fetchall()
    epics = db.execute(
        'SELECT id, epic, deadline color FROM epic'
    ).fetchall()
    if is_json:
        return json.dumps({'Success':True,'stories':[dict(x) for x in stories]})
    return render_template('story/list.html', stories=stories, epics=epics)


@bp.route('/<int:story_id>', methods=('GET','POST'))
def show(story_id):
    db = get_db()
    is_json = request.args.get('is_json',False)
    story = db.execute(
        'SELECT story.id, story, story.deadline, epicID, epic, color, prioritization from ' +
        'story JOIN epic ON story.epicID = epic.id ' +
        'WHERE story.id = ? ' +
        'order by color, epic, prioritization desc',
        (story_id,)
    ).fetchone()
    if not story:
        error = f"Story ID {story_id} does not exist."
        if is_json:
            abort(404, error)
        else:
            flash(error,'error')
            return redirect(url_for('story.list_all'))

    if request.method == 'POST':
        story_name = request.form.get('story',story['story'])
        epic_id = request.form.get('epic_id',story['epicID'])
        prioritization = request.form.get('prioritization',story['prioritization'])
        deadline = request.form.get('deadline',story['deadline'])
        error = None
        
        if not story_name:
            story_name = story['story']
        if not epic_id:
            epic_id = story['epicID']
        if not prioritization:
            prioritization = story['prioritization']
        if db.execute(
            'SELECT * FROM epic WHERE id = ?',
            (epic_id,)
        ).fetchone() is None:
            error = f'Epic {epic_id} not found.'
        
        if error is None:
            db.execute(
                'UPDATE story SET '+
                    'story = ?, '+
                    'epicID = ?, '+
                    'prioritization = ?, '+
                    'deadline = ? ' +
                'WHERE id = ?',
                (story_name, epic_id, prioritization, deadline, story_id,)
            )
            db.commit()
            if is_json:
                return json.dumps({'Success':True,'story_id':story_id})
            return redirect(url_for('story.show', story_id = story_id))
        
        if is_json:
            abort(500,error)
        flash(error,'error')
    if is_json:
        return json.dumps({'Success':True,'story':dict(story)})
    return render_template('story/show.html', story=story)