from __future__ import annotations
from fastapi import APIRouter, Request
from src.api.v1.schemas import HealthPayload, SuccessResponse

import logging
logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health", tags=["system"], response_model=SuccessResponse[HealthPayload])
async def health_check(request: Request) -> SuccessResponse[HealthPayload]:
    """
    Health check endpoint.
    Returns application version and status.
    """
    payload = HealthPayload(version=request.app.version or "0.0.0")
    logger.info("health_check")
    return SuccessResponse(data=payload)