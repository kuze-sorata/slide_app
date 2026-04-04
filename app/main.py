from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.routes.export import router as export_router
from app.routes.generate import router as generate_router
from app.routes.render import router as render_router
from app.utils.config import get_settings


settings = get_settings()
APP_DIR = Path(__file__).resolve().parent

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="API-hosted LLM powered slide draft generator for Japanese internal presentations.",
)

app.include_router(generate_router)
app.include_router(export_router)
app.include_router(render_router)
app.mount("/static", StaticFiles(directory=APP_DIR / "static"), name="static")

templates = Jinja2Templates(directory=str(APP_DIR / "templates"))


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"request": request, "app_name": settings.app_name},
    )


@app.get("/preview", response_class=HTMLResponse)
async def preview(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="preview.html",
        context={"request": request, "app_name": settings.app_name},
    )
