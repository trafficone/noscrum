"""
Story Tag controller/view logic of NoScrum
"""

from flask_openapi3 import APIBlueprint as Blueprint
from flask import flash, redirect, request, url_for, abort
from flask_login import current_user, login_required
from pydantic import BaseModel, Field
from noscrum.noscrum_backend.tag import *
from noscrum.noscrum_api.template_friendly import friendly_render as render_template, NoscrumBaseQuery

bp = Blueprint("tag", __name__, url_prefix="/tag")


@bp.get("/create")
@login_required
def get_create():
    return render_template("tag/create.html")


@bp.post("/create")
@login_required
def create():
    """
    Handle a request to creat a new tag record
    """
    is_json = request.args.get("is_json", False)
    tag = request.form.get("tag", None)
    error = None

    if tag is None:
        error = "Tag not populated."
    tag_value = get_tag_from_name(current_user, tag)
    if tag is not None and tag_value is not None:
        error = f"Tag {tag_value.tag} already exists."

    if error is None:
        tag = create_tag(current_user, tag)
        tag_id = tag.id
        if is_json:
            return {"Success": True, "tag_id": tag_id}
        return redirect(url_for("tag.show", tag_id=tag_id))
    if is_json:
        abort(500, error)
    flash(error, "error")

class TagPath(BaseModel):
    tag_id: int

@bp.get("/<int:tag_id>")
@login_required
def show(path: TagPath, query: NoscrumBaseQuery):
    tag_id = path.tag_id
    is_json = query.is_json
    tag = get_tag(current_user, tag_id)
    if tag is None:
        error = "Tag ID not found."
        if is_json:
            abort(404, error)
        else:
            flash(error, "error")
            return redirect(url_for("tag.list_all"))
    if is_json:
        return {"Success": True, tag: dict(tag)}
    return render_template("tag/show.html", tag=tag)


@bp.post("/<int:tag_id>")
def update(tag_id):
    """
    Return the tag information for a tag by id
    Handles updates as well as delete requests
    """
    is_json = request.args.get("is_json", False)
    tag = get_tag(current_user, tag_id)
    if tag is None:
        error = "Tag ID not found."
        if is_json:
            abort(404, error)
        else:
            flash(error, "error")
            return redirect(url_for("tag.list_all"))
    tag_id = tag.id
    tag_name = request.form.get("tag", None)
    error = None
    if tag_name is None:
        error = "Tag not populated."
    tag_value = get_tag_from_name(current_user, tag)
    if tag_name is not None and tag_value is not None:
        error = f"Tag with name {tag_value.tag} already exists."

    if error is None:
        update_tag(current_user, id, tag)
        if is_json:
            return {"Success": True, "tag_id": tag_id}
        return redirect(url_for("tag.view", tag_id=tag_id))
    if is_json:
        abort(500, error)
    flash(error, "error")


@bp.delete("<int:tag_id>/")
@login_required
def delete(tag_id):
    is_json = request.args.get("is_json", False)
    tag = get_tag(current_user, tag_id)
    if tag is None:
        error = "Tag ID not found."
        if is_json:
            abort(404, error)
        else:
            flash(error, "error")
            return redirect(url_for("tag.list_all"))
    tag_id = tag.id
    delete_tag(current_user, tag_id)
    if is_json:
        return {"Success": True, "tag_id": tag_id}
    return redirect(url_for("tag.list_all", tag_id=tag_id))


@bp.get("/")
def list_all():
    """
    Handles requests to list all tags for user
    """
    is_json = request.args.get("is_json", False)
    tags = get_tags(current_user)

    if is_json:
        return {"Success": True, tags: [dict(x) for x in tags]}
    return render_template("tag/list.html", tags=tags)
