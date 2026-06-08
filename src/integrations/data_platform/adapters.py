from src.integrations.data_platform.client import DataPlatformHttpClient
from src.integrations.data_platform.contracts import DataPlatformReadAdapter


class SaveBasketDataPlatformAdapter(DataPlatformReadAdapter):
    """Read adapter for normalized upstream datasets only."""

    def __init__(self, client: DataPlatformHttpClient) -> None:
        self._client = client

    async def fetch_catalog_snapshot(self) -> dict:
        return await self._client.get("catalog/snapshot")

    async def fetch_pricing_snapshot(self) -> dict:
        return await self._client.get("pricing/snapshot")

    async def fetch_offer_snapshot(self) -> dict:
        return await self._client.get("offers/snapshot")
