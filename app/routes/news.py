from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import NewsArticle

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/news", response_class=HTMLResponse)
async def news_page(request: Request, category: str = None, page: int = 1, db: AsyncSession = Depends(get_db)):
    limit = 10
    offset = (page - 1) * limit
    stmt = select(NewsArticle).order_by(NewsArticle.created_at.desc()).offset(offset).limit(limit)
    if category:
        stmt = stmt.where(NewsArticle.category == category)
        
    result = await db.execute(stmt)
    articles = result.scalars().all()
    return templates.TemplateResponse("news.html", {"request": request, "articles": articles, "category": category})