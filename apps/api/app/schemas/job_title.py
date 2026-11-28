import uuid

from pydantic import BaseModel, ConfigDict


class JobTitleIn(BaseModel):
    name: str


class JobTitleUpdate(BaseModel):
    name: str | None = None
    is_active: bool | None = None


class JobTitleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    is_active: bool
