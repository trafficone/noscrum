"""
Semi-static page handler (eg about index)
"""
from datetime import date
from flask_openapi3 import APIBlueprint as Blueprint
from flask_login import current_user
from noscrum.noscrum_backend.sprint import (
    get_current_sprint,
    get_schedule_tasks_filtered,
)
from noscrum.noscrum_api.template_friendly import friendly_render as render_template

bp = Blueprint("semi_static", __name__, url_prefix="/")


@bp.get("/")
def index():
    """
    Render the application's main landing page
    """
    if not current_user.is_authenticated:
        return render_template("index.html", current_user=current_user)
    current_sprint = get_current_sprint(current_user)
    print(date.today())
    if current_sprint is not None:
        todays_tasks = get_schedule_tasks_filtered(
            current_user, current_sprint.id, None, date.today(), None
        )
    else:
        todays_tasks = {}
    return render_template(
        "index.html",
        current_user=current_user,
        todays_tasks=todays_tasks,
        today=date.today(),
    )
