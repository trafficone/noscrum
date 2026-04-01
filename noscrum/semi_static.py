"""
Semi-static page handler (eg about index)
"""

from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates

from noscrum.model import User
from noscrum.user import fastapi_users

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/")
async def index(request: Request, user: User = Depends(fastapi_users.current_user(optional=True))):
    """
    Render the application's main landing page
    """
    return templates.TemplateResponse("/index.html", {"request": request, "current_user": user})
