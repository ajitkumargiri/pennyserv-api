from fastapi import APIRouter, Response, status

from src.core.config import get_settings
from src.observability.application.health_service import HealthService
from src.shared.schemas.health import LiveResponse, ReadyResponse

router = APIRouter(tags=["health"])
settings = get_settings()
health_service = HealthService(settings)


@router.get("/health/live", response_model=LiveResponse, summary="Liveness probe")
def liveness() -> LiveResponse:
    return LiveResponse(status="ok", service="pennyserv-api", version=settings.app_version)


@router.get("/health/ready", response_model=ReadyResponse, summary="Readiness probe")
async def readiness(response: Response) -> ReadyResponse:
    result = await health_service.readiness()
    if result.status == "degraded":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return result
