"""
Handle backend components to Noscrum Tag API
"""
from sqlalchemy import select

from noscrum.noscrum_backend.db import Tag, get_db


def get_tags(
    current_user,
):
    """
    Get tag records for the given current user
    """
    app_db = get_db()
    return app_db.session.execute(select(Tag).filter(Tag.user_id == current_user.id).distinct()).all()


def get_tags_for_story(current_user, story_id):
    """
    Get all the tag records for the given story
    @param story_id Identity record for a story
    """
    app_db = get_db()
    return (
        app_db.session.execute(select(Tag).filter(Tag.user_id == current_user.id)
        .distinct()
        .filter(Tag.stories.any(id=story_id)))
        .all()
    )


def get_tag(current_user, tag_id):
    """
    Get the Tag record having a given identity
    @param tag_id Identity for the queried tag
    """
    app_db = get_db()
    return (
        app_db.session.execute(select(Tag).filter(Tag.id == tag_id)
        .filter(Tag.user_id == current_user.id))
        .scalar_one_or_none()
    )


def get_tag_from_name(current_user, tag):
    """
    Get the Tag record using a particular name
    @param tag The name of the tag in question
    """
    app_db = get_db()
    return (
        app_db.session.execute(select(Tag).filter(Tag.tag == tag).filter(Tag.user_id == current_user.id)).scalar_one_or_none()
    )


def create_tag(current_user, tag):
    """
    Create some new tag for organizing stories
    @param tag The name of the tag in question
    """
    app_db = get_db()
    newtag = Tag(tag=tag, user_id=current_user.id)
    app_db.session.add(newtag)  # pylint: disable=no-member
    app_db.session.commit()  # pylint: disable=no-member
    return get_tag_from_name(current_user, tag)


def update_tag(current_user, tag_id, tag):
    """
    Update some tag record through using ident
    @param tag The name of the tag in question
    @param tag_id identity for the queried tag
    """
    app_db = get_db()
    newtag = app_db.session.execute(select(Tag).filter(Tag.id == tag_id).filter(Tag.user_id == current_user.id)).scalar_one_or_none()
    if newtag is None:
        raise ValueError("Could not find tag with that ID")
    newtag.tag = tag
    app_db.session.commit()  # pylint: disable=no-member
    return get_tag(current_user, tag_id)


def delete_tag(current_user, tag_id):
    """
    Delete tag record having provided identity
    @param tag_id identity for the deleted tag
    """
    app_db = get_db()
    oldtag = app_db.session.execute(select(Tag).filter(Tag.id == tag_id).filter(Tag.user_id == current_user.id)).scalar_one_or_none()
    app_db.session.delete(oldtag)
    app_db.session.commit()  # pylint: disable=no-member
