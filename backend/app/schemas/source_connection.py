import uuid
from datetime import datetime

from pydantic import BaseModel


class SourceConnectionCreate(BaseModel):
    organization_id: uuid.UUID
    name: str
    source_type: str  # csv | json | api_generic | demo
    config: dict = {}


class SourceConnectionUpdate(BaseModel):
    name: str | None = None
    config: dict | None = None
    is_active: bool | None = None


class SourceConnectionOut(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    source_type: str
    config: dict
    is_active: bool
    last_synced_at: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True
