"""
Handle search logic
"""
from flask_openapi3 import APIBlueprint as Blueprint
from flask import request, abort, current_app
from flask_login import current_user, login_required
from noscrum_backend.db import get_db
from noscrum_api.template_friendly import friendly_render as render_template

bp = Blueprint("search", __name__, url_prefix="/search")


@login_required
def search_db(search_term: str):
    """
    Search DB for objects that contain the search_term
    """
    app_db = get_db(current_app)
    alltext = """select 'task' label,task value, task.id, user_id from task
    union all select 'story',story value,story.id, user_id from story
    union all select 'epic',epic value,epic.id, user_id from epic
    union all select 'note',note value,sr.id, user_id from schedule_task sr"""
    magic_search = (
        f"SELECT * from ({alltext}) WHERE lower(value) "
        + "LIKE '%'||lower(:query)||'%' and user_id == :user_id"
    )
    return app_db.session.execute(  # pylint: disable=no-member
        magic_search, {"user_id": current_user.id, "query": search_term}
    )


@bp.get("/")
@login_required
def query():
    """
    Execute search of db for term
    and return list of items in db with that term
    """
    search_term: str = request.args.get("s", "")
    if not query:
        abort(401)
    else:
        results = search_db(search_term)
    return render_template("search/results.html", results=results)
