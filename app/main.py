import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.database import engine, Base
from app.routes import radio, news, downloader, transcription, admin, auth_routes

async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

app = FastAPI(on_startup=[startup])

# Mount standard static folder
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Mount temp folder securely to serve video thumbnails
os.makedirs("/tmp/media", exist_ok=True)
app.mount("/tmp", StaticFiles(directory="/tmp"), name="temp")

templates = Jinja2Templates(directory="app/templates")

@app.middleware("http")
async def add_user_to_request(request: Request, call_next):
    from app.auth import get_current_user
    request.state.user = await get_current_user(request)
    response = await call_next(request)
    return response

app.include_router(auth_routes.router, prefix="/auth", tags=["Auth"])
app.include_router(radio.router, tags=["Radio"])
app.include_router(news.router, tags=["News"])
app.include_router(downloader.router, tags=["Downloader"])
app.include_router(transcription.router, tags=["Transcription"])
app.include_router(admin.router, prefix="/admin", tags=["Admin"])

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})
