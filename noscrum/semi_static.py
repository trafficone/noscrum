"""
Semi-static page handler (eg about index)
"""
from datetime import date
from flask import render_template
from flask_openapi3 import APIBlueprint as Blueprint
from flask_user import current_user
from noscrum.sprint import get_current_sprint, get_schedule_tasks_filtered

bp = Blueprint("semi_static", __name__, url_prefix="/")


@bp.get("/")
def index():
    """
    Render the application's main landing page
    """
    if not current_user.is_authenticated:
        return render_template("index.html",current_user=current_user)
    else:
        current_sprint = get_current_sprint()
        if current_sprint is not None:
            todays_tasks = get_schedule_tasks_filtered(current_sprint.id, None, date.today(), None)
        else:
            todays_tasks = {}
        return render_template("index.html", current_user=current_user, todays_tasks = todays_tasks)


        
