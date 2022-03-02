"""
Semi-static page handler (eg about index)
"""
from fastapi import APIRouter
from fastapi.templating import Jinja2Templates

router = APIRouter(prefix="/semi_static")
templates = Jinja2Templates(directory="templates")


@router.get("/")
def index():
    """
    Render the application's main landing page
    """
    return templates.TemplateResponse("index.html",{})
