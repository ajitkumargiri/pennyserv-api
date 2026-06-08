from typing import Literal

from pydantic import BaseModel


class HealthComponent(BaseModel):
    name: str
    status: Literal["ok", "error", "skipped"]
    detail: str | None = None


class LiveResponse(BaseModel):
    status: Literal["ok"]
    service: str
    version: str


class ReadyResponse(BaseModel):
    status: Literal["ok", "degraded"]
    service: str
    version: str
    components: list[HealthComponent]
