import uuid
from datetime import datetime

from pydantic import BaseModel


class AnalysisResultOut(BaseModel):
    relevance: str
    relevance_confidence: float
    sentiment: str
    sentiment_confidence: float
    coverage_style: str
    framing: list[str]
    ai_provider: str
    manually_corrected: bool
    correction_notes: str | None = None

    class Config:
        from_attributes = True


class MediaItemOut(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    source_connection_id: uuid.UUID
    external_id: str | None
    title: str
    content: str | None
    summary: str | None
    published_at: datetime
    outlet_name: str
    author_name: str | None
    media_type: str
    url: str | None
    keywords: list[str]
    entities: list[str]
    exposure_count: int | None
    engagement_count: int | None
    dedup_role: str
    dedup_of_item_id: uuid.UUID | None
    ingested_at: datetime
    analysis: AnalysisResultOut | None = None

    class Config:
        from_attributes = True


class MediaItemListResponse(BaseModel):
    total: int
    items: list[MediaItemOut]


class AnalysisCorrection(BaseModel):
    relevance: str | None = None
    sentiment: str | None = None
    coverage_style: str | None = None
    framing: list[str] | None = None
    correction_notes: str | None = None
