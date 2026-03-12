"""
Backend components for Noscrum Story Model
"""
import logging

from sqlalchemy import select, text

from noscrum.noscrum_backend.db import Story, Tag, TagStory, get_db
from noscrum.noscrum_backend.epic import get_null_epic

logger = logging.getLogger()


def get_stories(current_user, sprint_view=False, sprint_id=None, closed: bool = None):
    """
    Get story records with calculated metadata
    @sprint_view True if querying for a sprint
    @sprint_id Identity of the sprint to query
    """
    app_db = get_db()
    if not sprint_view:
        query = select(Story).filter(Story.user_id == current_user.id)
        if closed is None:
            pass
        elif not closed:
            logger.info(closed, "<- and also here")
            # pylint(singleton-comparison)
            query = query.filter(Story.closure_state == None)
        else:
            query = query.filter(Story.closure_state != None)
        return app_db.session.execute(query).all()
    return app_db.session.execute(  # pylint: disable=no-member
        text("SELECT story.id, "
        + "CASE WHEN story = 'NULL' THEN 'No Story' ELSE story END as story, "
        + "epic_id, prioritization, story.deadline, "
        + "sum(coalesce(estimate,0)) as estimate, "
        + "count(task.id) as tasks, "
        + "COUNT(DISTINCT CASE WHEN task.status <> 'Done' THEN task.id ELSE NULL END) "
        + "as active_tasks, "
        + "COUNT(DISTINCT CASE WHEN task.estimate IS NULL THEN task.id ELSE NULL END) "
        + "as unestimated_tasks, "
        + "SUM(CASE WHEN task.status <> 'Done' THEN task.estimate - coalesce(task.actual,0) ELSE 0 "
        + "END) AS rem_estimate "
        + "FROM story "
        + "LEFT OUTER JOIN task on task.story_id = story.id "
        + "AND task.user_id = :user_id "
        + "AND task.sprint_id = :sprint_id "
        + "GROUP BY story.id, story.story, story.epic_id, story.prioritization "
        + "ORDER BY prioritization DESC"),
        {"user_id": current_user.id, "sprint_id": sprint_id},
    ).fetchall()


def get_stories_by_epic(current_user, epic_id):
    """
    Return queried stories faor the given epic
    @param epic_id Identity of epic being used
    """
    app_db = get_db()
    return app_db.session.execute(select(Story).filter(Story.epic_id == epic_id).filter(
        Story.user_id == current_user.id
    )).all()


def get_story_by_name(current_user, story, epic_id):
    """
    Returns the story record with a name given
    @param story Story name (unique per users)
    @param epic_id Identity of epic being used
    """
    app_db = get_db()
    return (
        app_db.session.execute(select(Story).filter(Story.story == story)
        .filter(Story.epic_id == epic_id)
        .filter(Story.user_id == current_user.id))
        .scalar_one_or_none()
    )


def get_story(current_user, story_id, exclude_nostory=True):
    """
    Get the story record by its identity value
    @param story_id story identification value
    @param exclude_nostory exclude special val
    "story" which is null (optional parameter)
    """
    if story_id == 0:
        return get_null_story_for_epic(current_user, 0)
    app_db = get_db()
    query = select(Story).filter(Story.id == story_id)
    if exclude_nostory:
        query = query.filter(Story.story is not None)
    query = query.filter(Story.user_id == current_user.id)
    return app_db.session.execute(query).scalar_one_or_none()


def get_null_story_for_epic(current_user, epic_id):
    """
    Returns the special null "story" record
    """
    if epic_id == 0:
        epic_id = get_null_epic(current_user).id
    logger.info("Story thinks null epic id is %s", epic_id)
    app_db = get_db()
    story = (
        app_db.session.execute(select(Story).filter(Story.story == "NULL")
        .filter(Story.epic_id == epic_id)
        .filter(Story.user_id == current_user.id))
        .scalar_one_or_none()
    )
    if story is None:
        logger.info(
            "Couldn't find null story? creating new story with epic id %s", epic_id
        )
        story = create_story(current_user, epic_id, "NULL", None, None)
    return story


def create_story(current_user, epic_id, story, prioritization, deadline):
    """
    Create a new story under the given epic id
    @param epic_id Epic record identity number
    @param story Name to describe a story with
    @param prioritization 1-5 with 1 being low
    @param deadline date the story will be due
    """
    if epic_id == 0:
        raise Exception("Tried to create a story without an epic")
    app_db = get_db()
    if prioritization is None:
        new_story = Story(
            story=story, epic_id=epic_id, deadline=deadline, user_id=current_user.id
        )
    else:
        new_story = Story(
            story=story,
            epic_id=epic_id,
            prioritization=prioritization,
            deadline=deadline,
            user_id=current_user.id,
        )
    app_db.session.add(new_story)  # pylint: disable=no-member
    app_db.session.commit()  # pylint: disable=no-member
    story = get_story_by_name(current_user, story, epic_id)
    return story


def update_story(current_user, story_id, story, epic_id, prioritization, deadline):
    """
    Update properties for a given story record
    @param story_id story identification value
    @param story Name to describe a story with
    @param epic_id Epic record identity number
    @param prioritization 1-5 with 1 being low
    @param deadline date the story will be due
    """
    app_db = get_db()
    story_record = app_db.session.execute(select(Story).filter(Story.id == story_id).filter(
        Story.user_id == current_user.id
    )).scalar_one_or_none()
    if story_record is None:
        raise ValueError("No story for given ID")
    
    story_record.story = story
    story_record.epic_id = epic_id
    story_record.prioritization = prioritization
    story_record.deadline = deadline
    app_db.session.commit()  # pylint: disable=no-member
    return get_story(current_user, story_id)


def close_story_update(current_user, story_id, closure_state):
    """
    Set a story to closed cascades story state
    to the tasks which aren't currently "done"
    @param story_id story identification value
    @param closure_state state which closed in
    """
    app_db = get_db()
    story = app_db.session.execute(select(Story).filter(Story.id == story_id).filter(
        Story.user_id == current_user.id
    )).scalar_one_or_none()
    if story is None:
        raise ValueError("No stories found with that ID")
    task_closure_state = closure_state
    if closure_state is None:
        task_closure_state = "To-Do"
    for task in story.tasks:
        if task.status != "Done":
            # task.update({"status":closure_state})
            task.status = task_closure_state
    story.closure_state = closure_state
    app_db.session.commit()  # pylint: disable=no-member
    return story


def get_tag_story(current_user, story_id, tag_id):
    """
    Get a tag for a story given their id value
    @param story_id story identification value
    @param tag_id tag record identifier number
    """
    app_db = get_db()
    story = get_story(current_user, story_id)
    return (
        app_db.session.execute(select(Tag).filter(Tag.stories.contains(story))
        .filter(Tag.user_id == current_user.id)
        .filter(Tag.id == tag_id))
        .scalar_one_or_none()
    )


def insert_tag_story(current_user, story_id, tag_id):
    """
    Attach a tag to a given story using the id
    @param story_id story identification value
    @param tag_id tag record identifier number
    """
    app_db = get_db()
    tag_story_record = TagStory(story_id=story_id, tag_id=tag_id)
    app_db.session.add(tag_story_record)  # pylint: disable=no-member
    app_db.session.commit()  # pylint: disable=no-member
    return get_tag_story(current_user, story_id, tag_id)


def delete_tag_story(current_user, story_id, tag_id):
    """
    Remove tag from story by their identifiers
    @param story_id story identification value
    @param tag_id tag record identifier number
    """
    app_db = get_db()
    tag_to_delete = app_db.session.execute(select(TagStory).filter(TagStory.story_id == story_id).filter(
        TagStory.tag_id == tag_id
    ).filter(TagStory.user_id == current_user.id)).scalar_one_or_none()
    app_db.session.delete(tag_to_delete)
    app_db.session.commit()  # pylint: disable=no-member
