from noscrum.noscrum_backend.db import get_db, Tag


def get_tags(
    current_user,
):
    """
    Get tag records for the given current user
    """
    return Tag.query.filter(Tag.user_id == current_user.id).distinct().all()


def get_tags_for_story(current_user, story_id):
    """
    Get all the tag records for the given story
    @param story_id Identity record for a story
    """
    return (
        Tag.query.filter(Tag.user_id == current_user.id)
        .distinct()
        .filter(Tag.stories.any(id=story_id))
        .all()
    )


def get_tag(current_user, tag_id):
    """
    Get the Tag record having a given identity
    @param tag_id Identity for the queried tag
    """
    return (
        Tag.query.filter(Tag.id == tag_id)
        .filter(Tag.user_id == current_user.id)
        .first()
    )


def get_tag_from_name(current_user, tag):
    """
    Get the Tag record using a particular name
    @param tag The name of the tag in question
    """
    return (
        Tag.query.filter(Tag.tag == tag).filter(Tag.user_id == current_user.id).first()
    )


def create_tag(current_user, tag):
    """
    Create some new tag for organizing stories
    @param tag The name of the tag in question
    """
    app_db = get_db()
    newtag = Tag(tag=tag, user_id=current_user.id)
    app_db.session.add(newtag)
    app_db.session.commit()
    return get_tag_from_name(current_user, tag)


def update_tag(current_user, tag_id, tag):
    """
    Update some tag record through using ident
    @param tag The name of the tag in question
    @param tag_id identity for the queried tag
    """
    app_db = get_db()
    Tag.query.filter(Tag.id == tag_id).filter(Tag.user_id == current_user.id).update(
        {tag: tag}, synchronize_session="fetch"
    )
    app_db.session.commit()
    return get_tag(current_user, tag_id)


def delete_tag(current_user, tag_id):
    """
    Delete tag record having provided identity
    @param tag_id identity for the deleted tag
    """
    app_db = get_db()
    Tag.query.filter(Tag.id == tag_id).filter(Tag.user_id == current_user.id).delete()
    app_db.session.commit()
