"""
Handle search logic
"""
from flask import Blueprint, render_template, request, abort
from flask_user import current_user, login_required
from noscrum.db import get_db

bp = Blueprint("search", __name__, url_prefix="/search")

def search_db(search_term):
    app_db = get_db()
    alltext = """select 'task' label,task value, task.id, user_id from task
    union all select 'story',story value,story.id, user_id from story
    union all select 'epic',epic value,epic.id, user_id from epic
    union all select 'note',note value,sr.id, user_id from schedule_task sr"""
    magic_search = f"SELECT * from ({alltext}) WHERE lower(value) LIKE '%'||lower(:query)||'%' and user_id == :user_id"
    return app_db.session.execute(magic_search,
        {'user_id':current_user.id,
        'query':search_term})

@bp.route("/", methods=["GET"])
@login_required
def query():
    search_term = request.args.get('s')
    if not query:
        abort(401)
    else:
        results = search_db(search_term)
    return render_template('search/results.html',results=results)