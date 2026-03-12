"""
Semi-static page handler (eg about index)
"""
from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

from noscrum.user import current_user

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/")
def index(request: Request):
    """
    Render the application's main landing page
    """
    return templates.TemplateResponse("/index.html", {"request":request, "current_user":current_user})
