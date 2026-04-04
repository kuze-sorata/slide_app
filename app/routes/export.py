import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import PlainTextResponse

from app.models.schema import Presentation
from app.services.export_service import ExportError, ExportService
from app.services.marp_service import MarpService
from app.services.pptx_service import PptxService
from app.utils.config import Settings, get_settings


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/export", tags=["export"])


def get_export_service(
    settings: Settings = Depends(get_settings),
) -> ExportService:
    return ExportService(
        marp_service=MarpService(theme=settings.marp_theme),
        pptx_service=PptxService(),
        marp_cli_path=settings.resolved_marp_cli_path,
        chrome_path=settings.resolved_chrome_path,
        marp_timeout_seconds=settings.marp_timeout_seconds,
    )


@router.get(
    "/debug/config",
    status_code=status.HTTP_200_OK,
)
async def debug_export_config(
    settings: Settings = Depends(get_settings),
) -> dict[str, str | None]:
    return {
        "marp_cli_path": settings.resolved_marp_cli_path,
        "chrome_path": settings.resolved_chrome_path,
        "marp_theme": settings.marp_theme,
    }


@router.post(
    "/marp",
    response_class=PlainTextResponse,
    status_code=status.HTTP_200_OK,
)
async def export_marp_markdown(
    presentation: Presentation,
    service: ExportService = Depends(get_export_service),
) -> PlainTextResponse:
    try:
        markdown = service.export_markdown(presentation)
    except ExportError as exc:
        logger.exception("Marp markdown export failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc
    return PlainTextResponse(content=markdown, media_type="text/markdown")


@router.post(
    "/pdf",
    status_code=status.HTTP_200_OK,
)
async def export_pdf(
    presentation: Presentation,
    service: ExportService = Depends(get_export_service),
) -> Response:
    try:
        pdf_bytes = await asyncio.to_thread(service.export_pdf, presentation)
    except ExportError as exc:
        logger.exception("PDF export failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    headers = {
        "Content-Disposition": 'attachment; filename="presentation.pdf"',
    }
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers=headers,
    )


@router.post(
    "/pptx",
    status_code=status.HTTP_200_OK,
)
async def export_pptx(
    presentation: Presentation,
    service: ExportService = Depends(get_export_service),
) -> Response:
    try:
        pptx_bytes = await asyncio.to_thread(service.export_pptx, presentation)
    except ExportError as exc:
        logger.exception("PPTX export failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    headers = {
        "Content-Disposition": 'attachment; filename="presentation.pptx"',
    }
    return Response(
        content=pptx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        headers=headers,
    )
