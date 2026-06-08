from typing import Protocol


class DataPlatformReadAdapter(Protocol):
    """Read-only contract for normalized grocery intelligence from SaveBasket."""

    async def fetch_catalog_snapshot(self) -> dict: ...

    async def fetch_pricing_snapshot(self) -> dict: ...

    async def fetch_offer_snapshot(self) -> dict: ...
