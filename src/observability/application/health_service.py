from src.caching.infrastructure.redis_client import ping_redis
from src.core.config import Settings
from src.core.db.session import ping_database
from src.shared.schemas.health import HealthComponent, ReadyResponse


class HealthService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def readiness(self) -> ReadyResponse:
        components: list[HealthComponent] = []

        db_component = await self._database_component()
        redis_component = await self._redis_component()
        components.extend([db_component, redis_component])

        is_ready = all(component.status in {"ok", "skipped"} for component in components)
        overall_status = "ok" if is_ready else "degraded"

        return ReadyResponse(
            status=overall_status,
            service="pennyserv-api",
            version=self._settings.app_version,
            components=components,
        )

    async def _database_component(self) -> HealthComponent:
        if not self._settings.readiness_check_database:
            return HealthComponent(name="database", status="skipped", detail="Database check disabled")

        is_healthy = await ping_database()
        if is_healthy:
            return HealthComponent(name="database", status="ok")
        return HealthComponent(name="database", status="error", detail="Database is unavailable")

    async def _redis_component(self) -> HealthComponent:
        if not self._settings.readiness_check_redis:
            return HealthComponent(name="redis", status="skipped", detail="Redis check disabled")

        is_healthy = await ping_redis()
        if is_healthy:
            return HealthComponent(name="redis", status="ok")
        return HealthComponent(name="redis", status="error", detail="Redis is unavailable")
