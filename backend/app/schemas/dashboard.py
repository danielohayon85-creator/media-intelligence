import uuid
from datetime import datetime

from pydantic import BaseModel


class KpiResponse(BaseModel):
    total_mentions: int
    unique_publications: int
    positive_pct: float
    negative_pct: float
    neutral_pct: float
    mixed_pct: float
    change_vs_previous_period_pct: float | None
    period_start: datetime
    period_end: datetime


class TrendPoint(BaseModel):
    bucket: datetime
    positive: int
    negative: int
    neutral: int
    mixed: int
    total: int


class TrendResponse(BaseModel):
    granularity: str
    points: list[TrendPoint]


class DataQualityResponse(BaseModel):
    last_synced_at: datetime | None
    items_fetched: int
    items_new: int
    items_duplicate: int
    items_rejected: int
    items_pending_analysis: int
    items_with_full_content_pct: float
    items_with_exposure_data_pct: float
    sync_errors: list[dict]


class InsightOut(BaseModel):
    id: uuid.UUID
    level: str
    title: str
    explanation: str
    supporting_item_ids: list[str]
    confidence: float
    recommendation: str | None
    period_start: datetime
    period_end: datetime
    generated_at: datetime
    ai_provider: str

    class Config:
        from_attributes = True
