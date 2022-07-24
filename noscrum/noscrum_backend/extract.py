"""
Extract and Import data for current user.
"""
from noscrum.noscrum_backend.epic import get_epics
from noscrum.noscrum_backend.story import get_stories
from noscrum.noscrum_backend.task import get_tasks
from noscrum.noscrum_backend.sprint import get_sprints, get_schedules
from noscrum.noscrum_backend.tag import get_tags
from noscrum.noscrum_backend.user import get_preferences
from noscrum.noscrum_backend.work import get_all_work


def get_user_data(current_user):
    """
    Pulls all available data for a given user
    """
    user_export_data = {}
    user_export_data["epic"] = get_epics(current_user)
    user_export_data["story"] = get_stories(current_user)
    user_export_data["task"] = get_tasks(current_user)
    user_export_data["work"] = get_all_work(current_user)
    user_export_data["sprint"] = get_sprints(current_user)
    user_export_data["schedule"] = get_schedules(current_user)
    user_export_data["tags"] = get_tags(current_user)
    user_export_data["preferences"] = get_preferences(current_user)
