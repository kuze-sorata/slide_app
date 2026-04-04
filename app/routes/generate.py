import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from app.models.schema import Presentation, SlideGenerationRequest
from app.services.generation_service import GenerationError, GenerationService
from app.utils.config import get_settings


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["generate"])


def get_generation_service(
    settings = Depends(get_settings),
) -> GenerationService:
    return GenerationService.from_settings(settings)


@router.post(
    "/generate",
    response_model=Presentation,
    status_code=status.HTTP_200_OK,
)
async def generate_presentation(
    payload: SlideGenerationRequest,
    service: GenerationService = Depends(get_generation_service),
) -> Presentation:
    try:
        return await service.generate(payload)
    except GenerationError as exc:
        logger.exception("Slide generation failed")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc


@router.get(
    "/debug/provider-health",
    status_code=status.HTTP_200_OK,
)
async def debug_provider_health(
    service: GenerationService = Depends(get_generation_service),
) -> dict[str, Any]:
    try:
        result = await service.provider.health_check()
    except Exception as exc:
        logger.exception("Provider health check failed")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc
    return result
