from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import NewsArticle, User
from app.auth import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

async def admin_guard(request: Request):
    user = await get_current_user(request)
    if not user or not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Forbidden")
    return user

@router.get("/", response_class=HTMLResponse)
async def admin_dashboard(request: Request, user=Depends(admin_guard)):
    return templates.TemplateResponse("admin/dashboard.html", {"request": request, "user": user})

@router.get("/news/new", response_class=HTMLResponse)
async def new_news_form(request: Request, user=Depends(admin_guard)):
    return templates.TemplateResponse("admin/news_form.html", {"request": request})

@router.post("/news/create")
async def create_news(request: Request, db: AsyncSession = Depends(get_db), user=Depends(admin_guard)):
    form = await request.form()
    # Handle image upload (save to /tmp or S3)
    image_url = None
    if "image" in form and form["image"].filename:
        # Save file logic here
        pass
        
    article = NewsArticle(
        title=form["title"],
        content=form["content"],
        category=form["category"],
        is_featured="is_featured" in form,
        image_url=image_url,
        meta_description=form.get("meta_description")
    )
    db.add(article)
    await db.commit()
    return RedirectResponse("/admin", status_code=303)