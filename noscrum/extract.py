"""
Extract and Import data for current user.
"""
from noscrum.epic import get_epics
from noscrum.story import get_stories
from noscrum.task import get_tasks
from noscrum.sprint import get_sprints, get_schedules
from noscrum.tag import get_tags
from noscrum.user import get_preferences

from flask_user import login_required

@login_required
def get_user_data():
    user_export_data = {}
    user_export_data['epic'] = get_epics()
    user_export_data['story'] = get_stories()
    user_export_data['task'] = get_tasks()
    user_export_data['sprint'] = get_sprints()
    user_export_data['schedule'] = get_schedules()
    user_export_data['tags'] = get_tags()
    user_export_data['preferences'] = get_preferences()


