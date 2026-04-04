from fastapi import APIRouter, Depends, status
from fastapi.responses import HTMLResponse

from app.models.schema import Presentation
from app.services.render_service import RenderService


router = APIRouter(prefix="/api", tags=["render"])


def get_render_service() -> RenderService:
    return RenderService()


@router.post(
    "/render/html",
    response_class=HTMLResponse,
    status_code=status.HTTP_200_OK,
)
async def render_html_preview(
    presentation: Presentation,
    service: RenderService = Depends(get_render_service),
) -> HTMLResponse:
    html = service.render_preview_html(presentation)
    return HTMLResponse(content=html)


@router.post(
    "/update",
    response_model=Presentation,
    status_code=status.HTTP_200_OK,
)
async def update_presentation(
    presentation: Presentation,
) -> Presentation:
    return presentation
