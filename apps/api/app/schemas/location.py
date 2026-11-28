import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict


class LocationIn(BaseModel):
    name: str
    address: str
    timezone: str
    opening_hours: dict[str, Any] | None = None


class LocationUpdate(BaseModel):
    name: str | None = None
    address: str | None = None
    timezone: str | None = None
    opening_hours: dict[str, Any] | None = None


class LocationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    address: str
    timezone: str
    opening_hours: dict[str, Any] | None
