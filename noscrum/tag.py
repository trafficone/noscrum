"""
Story Tag controller/view logic of NoScrum
"""
import json

from flask import (
    Blueprint, flash, redirect, render_template, request, url_for, abort
)
from flask_user import current_user

from noscrum.db import get_db, Tag

bp = Blueprint('tag', __name__, url_prefix='/tag')


def get_tags():
    """
    Get tag records for the given current user
    """
    return Tag.query.filter(Tag.user_id == current_user.id).distinct().all()


def get_tags_for_story(story_id):
    """
    Get all the tag records for the given story
    @param story_id Identity record for a story
    """
    return Tag.query.filter(Tag.user_id == current_user.id).distinct()\
        .filter(Tag.stories.any(id=story_id)).all()


def get_tag(tag_id):
    """
    Get the Tag record having a given identity
    @param tag_id Identity for the queried tag
    """
    return Tag.query.filter(Tag.id == tag_id)\
        .filter(Tag.user_id == current_user.id).first()


def get_tag_from_name(tag):
    """
    Get the Tag record using a particular name
    @param tag The name of the tag in question
    """
    return Tag.query.filter(Tag.tag == tag)\
        .filter(Tag.user_id == current_user.id).first()


def create_tag(tag):
    """
    Create some new tag for organizing stories
    @param tag The name of the tag in question
    """
    app_db = get_db()
    newtag = Tag(tag=tag, user_id=current_user.id)
    app_db.session.add(newtag)
    app_db.session.commit()
    return get_tag_from_name(tag)


def update_tag(tag_id, tag):
    """
    Update some tag record through using ident
    @param tag The name of the tag in question
    @param tag_id identity for the queried tag
    """
    app_db = get_db()
    Tag.query.filter(Tag.id == tag_id)\
        .filter(Tag.user_id == current_user.id)\
        .update({tag: tag}, synchronize_session="fetch")
    app_db.session.commit()
    return get_tag(tag_id)


def delete_tag(tag_id):
    """
    Delete tag record having provided identity
    @param tag_id identity for the deleted tag
    """
    app_db = get_db()
    Tag.query.filter(Tag.id == tag_id)\
        .filter(Tag.user_id == current_user.id).delete()
    app_db.session.commit()


@bp.route('/create', methods=('GET', 'POST'))
def create():
    """
    Handle a request to creat a new tag record
    """
    is_json = request.args.get('is_json', False)
    if is_json and request.method == 'GET':
        abort(405, 'Method not supported for AJAX mode')
    if request.method == 'POST':
        tag = request.form.get('tag', None)
        error = None

        if tag is None:
            error = "Tag not populated."
        tag_value = get_tag_from_name(tag)
        if tag is not None and tag_value is not None:
            error = f"Tag {tag_value.tag} already exists."

        if error is None:
            tag = create_tag(tag)
            tag_id = tag.id
            if is_json:
                return json.dumps({'Success': True, 'tag_id': tag_id})
            return redirect(url_for('tag.show', tag_id=tag_id))
        if is_json:
            abort(500, error)
        flash(error, 'error')

    return render_template('tag/create.html')


@bp.route('/<int:tag_id>', methods=('GET', 'POST', 'DELETE'))
def show(tag_id):
    """
    Return the tag information for a tag by id
    Handles updates as well as delete requests
    """
    is_json = request.args.get('is_json', False)
    tag = get_tag(tag_id)
    if tag is None:
        error = 'Tag ID not found.'
        if is_json:
            abort(404, error)
        else:
            flash(error, 'error')
            return redirect(url_for('tag.list_all'))

    if request.method == 'POST':
        tag_name = request.form.get('tag', None)
        error = None

        if tag_name is None:
            error = "Tag not populated."
        tag_value = get_tag_from_name(tag)
        if tag_name is not None and tag_value is not None:
            error = f"Tag with name {tag_value.tag} already exists."

        if error is None:
            update_tag(id, tag)
            if is_json:
                return json.dumps({'Success': True, 'tag_id': tag_id})
            return redirect(url_for('tag.view', tag_id=tag_id))

        if is_json:
            abort(500, error)
        flash(error, 'error')

    elif request.method == 'DELETE':
        delete_tag(tag_id)
        if is_json:
            return json.dumps({'Success': True, 'tag_id': tag_id})
        return redirect(url_for('tag.list_all', tag_id=tag_id))
    if is_json:
        return json.dumps({'Success': True, tag: dict(tag)})
    return render_template('tag/show.html', tag=tag)


@bp.route('/', methods=('GET',))
def list_all():
    """
    Handles requests to list all tags for user
    """
    is_json = request.args.get('is_json', False)
    tags = get_tags()

    if is_json:
        return json.dumps({'Success': True, tags: [dict(x) for x in tags]})
    return render_template('tag/list.html', tags=tags)
