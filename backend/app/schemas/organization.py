import uuid
from datetime import datetime

from pydantic import BaseModel


class OrganizationOut(BaseModel):
    id: uuid.UUID
    name: str
    profile_key: str
    relevance_profile: dict
    is_demo: bool
    created_at: datetime

    class Config:
        from_attributes = True
