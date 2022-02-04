import functools
import json

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, abort
)
from flask_user import current_user

from noscrum.db import get_db, Tag, Story

bp = Blueprint('tag', __name__, url_prefix='/tag')

def get_tags(story=None):
    tags = Tag.query.filter(Tag.user_id==current_user.id).distinct()
    if story is not None:
        tags = tags.add_columns(Tag.stories.any(id=story.id).label('tag_in_story'))
    return tags.all()
    

def get_tags_for_story(story_id):
    db = get_db()
    return [x.tags for x in Story.query.filter(Story.user_id==current_user.id).filter(Story.id==story_id).all()]

def get_tag(id):
    db = get_db()
    return Tag.query.filter(Tag.id == id).filter(Tag.user_id == current_user.id).first()

def get_tag_from_name(tag):
    db = get_db()
    return Tag.query.filter(Tag.tag == tag).filter(Tag.user_id == current_user.id).first()

def create_tag(tag):
    db = get_db()
    newtag = Tag(tag = tag, user_id = current_user.id)
    db.session.add(newtag)
    db.session.commit()
    return get_tag_from_name(tag)

def update_tag(id,tag):
    db = get_db()
    Tag.query.filter(Tag.id==id)\
        .filter(Tag.user_id == current_user.id)\
        .update({tag:tag},synchronize_session="fetch")
    db.session.commit()
    return get_tag(id)
    
def delete_tag(id):
    db = get_db()
    Tag.query.filter(Tag.id==id).filter(Tag.user_id == current_user.id).delete()
    db.session.commit()

@bp.route('/create', methods=('GET','POST'))
def create():
    is_json = request.args.get('is_json',False)
    if is_json and request.method == 'GET':
        abort(405,'Method not supported for AJAX mode')
    if request.method == 'POST':
        tag = request.form.get('tag',None)
        error = None

        if tag is None:
            error = "Tag not populated."
        elif get_tag_from_name(tag) is not None:
            error = f"Tag {tag} already exists."
        
        if error is None:
            tag = create_tag(tag)
            tag_id = tag.id
            if is_json:
                return json.dumps({'Success':True,'tag_id':tag_id})
            return redirect(url_for('tag.show',tag_id = tag_id))
        if is_json:
            abort(500,error)
        flash(error,'error')

    return render_template('tag/create.html')


@bp.route('/<int:tag_id>', methods=('GET','POST','DELETE'))
def show(tag_id):
    is_json = request.args.get('is_json',False)
    tag = get_tag(tag_id)
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
        elif get_tag_from_name(tag) is not None:
            error = f"Tag {tag} already exists."
        
        if error is None:
            update_tag(id,tag)
            if is_json:
                return json.dumps({'Success':True,'tag_id':tag_id})
            return redirect(url_for('tag.view', tag_id = tag_id))
        
        if is_json:
            abort(500,error)
        flash(error,'error')
    
    elif request.method == 'DELETE':
        delete_tag(tag_id)
        if is_json:
            return json.dumps({'Success':True,'tag_id':tag_id})
        return redirect(url_for('tag.list_all', tag_id = tag_id))
    if is_json:
        return json.dumps({'Success':True,tag:dict(tag)})
    return render_template('tag/show.html',tag = tag)


@bp.route('/', methods=('GET',))
def list_all():
    is_json = request.args.get('is_json',False)
    tags = get_tags()

    if is_json:
        return json.dumps({'Success':True,tags:[dict(x) for x in tags]})
    return render_template('tag/list.html', tags = tags)
