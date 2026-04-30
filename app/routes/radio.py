from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.services import radio_service

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/radio", response_class=HTMLResponse)
async def radio_page(request: Request, q: str = None, country: str = "TN"):
    if q:
        stations = await radio_service.search_radios(q, country)
    else:
        stations = await radio_service.get_tunisian_radios()
    return templates.TemplateResponse("radio.html", {"request": request, "stations": stations})