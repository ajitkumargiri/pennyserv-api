from httpx import AsyncClient

from src.core.config import Settings


class DataPlatformHttpClient:
    """HTTP client for the upstream savebasket-data-platform APIs."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def get(self, path: str) -> dict:
        if self._settings.data_platform_base_url is None:
            raise RuntimeError("DATA_PLATFORM_BASE_URL is not configured")

        headers = {}
        if self._settings.data_platform_api_key is not None:
            headers["Authorization"] = (
                f"Bearer {self._settings.data_platform_api_key.get_secret_value()}"
            )

        base_url = str(self._settings.data_platform_base_url).rstrip("/")
        async with AsyncClient(timeout=self._settings.data_platform_timeout_seconds) as client:
            response = await client.get(f"{base_url}/{path.lstrip('/')}" , headers=headers)
            response.raise_for_status()
            return response.json()
