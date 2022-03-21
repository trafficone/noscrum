"""
Semi-static page handler (eg about index)
"""
from flask import Blueprint, render_template

bp = Blueprint("semi_static", __name__, url_prefix="/")


@bp.route("/", methods=("GET",))
def index():
    """
    Render the application's main landing page
    """
    return render_template("index.html")
