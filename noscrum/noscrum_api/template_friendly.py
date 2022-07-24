"""
Classes and methods to simplify templating for NoScrum pages
"""
from flask import render_template
from pydantic import BaseModel, Field


def friendly_render(filename: str, **context):
    """
    Shim between API and template rendering,
    allows for easy mutations as the templating
    engine may change
    """
    return render_template(filename, **context)


class NoscrumBaseQuery(BaseModel):
    """
    Query base model for NoScrum API Requests
    """

    is_asc: bool = Field(default=False)
    is_json: bool = Field(default=False)
