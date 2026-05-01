from fastapi import APIRouter, Request, Response, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import User
from app.auth import hash_password, verify_password, create_token
from sqlalchemy import select

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("auth/login.html", {"request": request})

@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("auth/register.html", {"request": request})

@router.post("/register")
async def register(request: Request, db: AsyncSession = Depends(get_db)):
    form = await request.form()
    # Check if user exists
    stmt = select(User).where(User.username == form["username"])
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        return templates.TemplateResponse("auth/register.html", {"request": request, "error": "Username already exists"})
    
    user = User(username=form["username"], email=form["email"], hashed_password=hash_password(form["password"]), is_admin=(form.get("username") == "admin")) # Simple admin hack for demo
    db.add(user)
    await db.commit()
    return RedirectResponse("/login", status_code=303)

@router.post("/login")
async def login(request: Request, db: AsyncSession = Depends(get_db)):
    form = await request.form()
    stmt = select(User).where(User.username == form["username"])
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if user and verify_password(form["password"], user.hashed_password):
        token = create_token({"user_id": user.id, "username": user.username, "is_admin": user.is_admin})
        response = RedirectResponse("/", status_code=303)
        response.set_cookie("access_token", token, httponly=True)
        return response
    return templates.TemplateResponse("auth/login.html", {"request": request, "error": "Invalid credentials"})

@router.get("/logout")
async def logout():
    response = RedirectResponse("/", status_code=303)
    response.delete_cookie("access_token")
    return response
