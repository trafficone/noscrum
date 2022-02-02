import functools
from pprint import pprint
import json

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, abort
)
from flask_user import current_user, login_required

from noscrum.db import get_db, Story, TagStory, Task, Tag
from noscrum.epic import get_epic, get_epics
from noscrum.tag import get_tags

bp = Blueprint('story', __name__, url_prefix='/story')

def get_stories(sprint_view = False,sprint_id = None):
    db = get_db()
    if not sprint_view:
        return Story.query.filter(Story.user_id == current_user.id).all()
    return db.session.execute(
        'SELECT story.id, story, epic_id, prioritization, story.deadline, '+
        'sum(coalesce(estimate,0)) as estimate, ' +
        'count(task.id) as tasks, ' +
        "COUNT(DISTINCT CASE WHEN task.status <> 'Done' THEN task.id ELSE NULL END) as active_tasks, "  +
        'COUNT(DISTINCT CASE WHEN task.estimate IS NULL THEN task.id ELSE NULL END) as unestimated_tasks, ' +
        "SUM(CASE WHEN task.status <> 'Done' THEN task.estimate - coalesce(task.actual,0) ELSE 0 END) AS rem_estimate " +
        'FROM task '+
        'LEFT OUTER JOIN story on task.story_id = story.id '+
        'WHERE task.user_id = :user_id and task.sprint_id = :sprint_id ' +
        'GROUP BY story.id, story, epic_id, prioritization '+
        'ORDER BY prioritization DESC',{'user_id':current_user.id, 'sprint_id':sprint_id}).fetchall()

def get_story_summary():
    db = get_db()
    # FIXME: Should this be in task.py?
    return db.session.query(
        Task.story_id,
        db.func.sum(Task.estimate).label('est'),
        db.func.count(Task.id).filter(Task.estimate is None).label('unest'),
        db.func.count(Task.id).filter(Task.status != 'Done').label('incomplete'),
        db.func.count().label('task_count')).group_by(Task.story_id).all()
 

def get_stories_by_epic(epic_id):
    db = get_db()
    query = Story.query.filter(Story.epic_id == epic_id).filter(Story.user_id == current_user.id)
    return query.all()
 

def get_story_by_name(story,epic_id):
    db = get_db()
    return Story.query.filter(Story.story == story)\
        .filter(Story.epic_id == epic_id)\
        .filter(Story.user_id == current_user.id).first()

def get_story(id,exclude_nostory=True):
    db = get_db()
    query = Story.query.filter(Story.id == id)\
        .filter(Story.user_id == current_user.id)
    if exclude_nostory:
        query.filter(Story.story is not None)
    return query.first()

def get_null_story_for_epic(epic_id):
    db = get_db()
    story = Story.query.filter(Story.story is None).filter(Story.epic_id == epic_id)\
        .filter(Story.user_id == current_user.id).first()
    if (story is None):
        story = create_story(epic_id,'NULL',None,None)
    return story

def create_story(epic_id,story,prioritization,deadline):
    db = get_db()
    if prioritization is None:
        new_story = Story(story=story,
            epic_id = epic_id,
            deadline = deadline,
            user_id = current_user.id
        )
    else:
        new_story = Story(story=story,
            epic_id=epic_id,
            prioritization=prioritization,
            deadline=deadline,
            user_id = current_user.id)
    db.session.add(new_story)
    db.session.commit()
    story = get_story_by_name(story, epic_id)
    return story

def update_story(id,story,epic_id,prioritization,deadline):
    db = get_db()
    Story.query.filter(Story.id == id).filter(Story.user_id==current_user.id)\
        .update({
            story:story,
            epic_id:epic_id,
            prioritization:prioritization,
            deadline:deadline
        },synchronize_session="fetch")
    db.session.commit()
    return get_story(id)

def get_tag_story(story_id,tag_id):
    story = get_story(story_id)
    return Tag.query.filter(Tag.stories.contains(story)).filter(Tag.user_id == current_user.id).filter(Tag.id == tag_id).first()

def insert_tag_story(story_id,tag_id):
    db = get_db()
    # TODO: SQLAlchemy makes it so you can add a tag directly to story w/o needing to update this table directly
    tag_story_record = TagStory(story_id=story_id,tag_id=tag_id)
    db.session.add(tag_story_record)
    db.session.commit()
    return get_tag_story(story_id,tag_id)

def delete_tag_story(story_id,tag_id):
    db = get_db()
    TagStory.query.filter(TagStory.story_id==story_id)\
        .filter(TagStory.tag_id==tag_id)\
        .delete()
    db.session.commit()
   

@bp.route('/create/<int:epic_id>', methods=('GET', 'POST'))
@login_required
def create(epic_id):
    is_json = request.args.get('is_json',False)
    if is_json and request.method == 'GET':
        abort(405,'Method not supported for AJAX')
    is_asc = request.args.get('is_asc',False)
    epic = get_epic(epic_id)
    if epic is None:
        flash(f'Epic with ID "{epic_id}" Not found.','error')
        return redirect(url_for('story.list_all'))
    if request.method == 'POST':
        story = request.form.get('story',None)
        prioritization = request.form.get('prioritization',None)
        deadline = request.form.get('deadline',None)
        error = None

        if not story or story == 'NULL':
            error = 'Story Name is Required'
        elif not epic_id:
            error = 'Epic Name not Found, Reload Page'
        elif get_story_by_name(story,epic_id) is not None:
            error = f'Story {story} already exists'

        if error is None:
            story = create_story(epic_id,story,prioritization,deadline)
            if is_json:
                return json.dumps({'Success':True,'story_id':story.id})
            return redirect(url_for('story.show', story_id=story.id))
        if is_json:
            abort(500, error)
        flash(error,'error')
    return render_template('story/create.html', epic=epic, asc=is_asc)


@bp.route('/<int:story_id>/tag', methods=('GET', 'POST', 'DELETE'))
@login_required
def tag(story_id):
    db = get_db()
    is_json = request.args.get('is_json',False)
    story = get_story(story_id)
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
        elif get_tag_story(story_id,tag_id) is not None:
            error = 'Tag already exists on Story'

        if error is None:
            tag_story = insert_tag_story(story_id,tag_id)
            if is_json:
                return json.dumps({'Success':True,'story_id':story_id,'tag_id':tag_id,'tag_story_id':tag_story.id})
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
        elif get_tag_story(story_id,tag_id) is None:
            error = 'Tag already deleted from Story'

        if error is None:
            delete_tag_story(story_id,tag_id)            
            if is_json:
                return json.dumps({'Success':True,'story_id':story_id,'tag_id':tag_id})
            return redirect(url_for('story.tag', story_id = story_id))
        if is_json:
            abort(500,error)
        flash(error,'error')
    
    tags = get_tags(story=story)
    for tag in tags:
        pprint(tag)
        pprint(dir(tag))
    if is_json:
        return json.dumps({'Success':True,'story_id':story_id,'story':dict(story),'tags':[tag for tag in tags if tag.tag_in_story]})
    return render_template('story/tag.html', story_id=story_id, story=story, tags=tags)


@bp.route('/', methods=('GET',))
@login_required
def list_all():
    db = get_db()
    is_json = request.args.get('is_json',False)
    stories = get_stories()
    epics = get_epics()
    if is_json:
        return json.dumps({'Success':True,'stories':[dict(x) for x in stories]})
    return render_template('story/list.html', stories=stories, epics=epics)


@bp.route('/<int:story_id>', methods=('GET','POST'))
@login_required
def show(story_id):
    db = get_db()
    is_json = request.args.get('is_json',False)
    story = get_story(story_id)
    if not story:
        error = f"Story ID {story_id} does not exist."
        if is_json:
            abort(404, error)
        else:
            flash(error,'error')
            return redirect(url_for('story.list_all'))

    if request.method == 'POST':
        story_name = request.form.get('story',story['story'])
        epic_id = request.form.get('epic_id',story['epic_id'])
        prioritization = request.form.get('prioritization',story['prioritization'])
        deadline = request.form.get('deadline',story['deadline'])
        error = None
        
        if not story_name:
            story_name = story['story']
        if not epic_id:
            epic_id = story['epic_id']
        if not prioritization:
            prioritization = story['prioritization']
        if get_epic(epic_id) is None:
            error = f'Epic {epic_id} not found.'
        
        if error is None:
            story = update_story(story_id,story_name,epic_id,prioritization,deadline)
            if is_json:
                return json.dumps({'Success':True,'story_id':story_id})
            return redirect(url_for('story.show', story_id = story_id))
        
        if is_json:
            abort(500,error)
        flash(error,'error')
    if is_json:
        return json.dumps({'Success':True,'story':dict(story)})
    return render_template('story/show.html', story=story)