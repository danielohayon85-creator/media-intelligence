import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.ingestion_run import IngestionRun
from app.models.media_item import MediaItem
from app.models.source_connection import SourceConnection
from app.schemas.dashboard import DataQualityResponse, KpiResponse, TrendResponse
from app.services.trend_service import ItemFilters, compute_daily_trend, compute_kpis, fetch_relevant_items

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


def _resolve_period(date_from: datetime | None, date_to: datetime | None) -> tuple[datetime, datetime]:
    date_to = date_to or datetime.now(timezone.utc)
    date_from = date_from or (date_to - timedelta(days=30))
    return date_from, date_to


@router.get("/kpis", response_model=KpiResponse)
def get_kpis(
    organization_id: uuid.UUID,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    outlet_name: str | None = None,
    media_type: str | None = None,
    keyword: str | None = None,
    db: Session = Depends(get_db),
):
    date_from, date_to = _resolve_period(date_from, date_to)
    filters = ItemFilters(outlet_name=outlet_name, media_type=media_type, keyword=keyword)

    current_items = fetch_relevant_items(db, organization_id, date_from, date_to, filters)

    period_length = date_to - date_from
    previous_items = fetch_relevant_items(
        db, organization_id, date_from - period_length, date_from, filters
    )

    kpis = compute_kpis(current_items, previous_items)
    return KpiResponse(**kpis, period_start=date_from, period_end=date_to)


@router.get("/trend", response_model=TrendResponse)
def get_trend(
    organization_id: uuid.UUID,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    outlet_name: str | None = None,
    media_type: str | None = None,
    keyword: str | None = None,
    db: Session = Depends(get_db),
):
    date_from, date_to = _resolve_period(date_from, date_to)
    filters = ItemFilters(outlet_name=outlet_name, media_type=media_type, keyword=keyword)
    items = fetch_relevant_items(db, organization_id, date_from, date_to, filters)
    points = compute_daily_trend(items)
    return TrendResponse(granularity="daily", points=points)


@router.get("/data-quality", response_model=DataQualityResponse)
def get_data_quality(organization_id: uuid.UUID, db: Session = Depends(get_db)):
    sources = db.execute(
        select(SourceConnection).where(SourceConnection.organization_id == organization_id)
    ).scalars().all()
    source_ids = [s.id for s in sources]

    last_synced = max((s.last_synced_at for s in sources if s.last_synced_at), default=None)

    runs = (
        db.execute(
            select(IngestionRun)
            .where(IngestionRun.source_connection_id.in_(source_ids))
            .order_by(IngestionRun.started_at.desc())
            .limit(20)
        ).scalars().all()
        if source_ids
        else []
    )

    items_fetched = sum(r.items_fetched for r in runs)
    items_new = sum(r.items_new for r in runs)
    items_duplicate = sum(r.items_duplicate for r in runs)
    items_rejected = sum(r.items_rejected for r in runs)
    errors = [e for r in runs for e in (r.errors or [])]

    all_items = (
        db.execute(select(MediaItem).where(MediaItem.organization_id == organization_id)).scalars().all()
    )
    total_items = len(all_items)
    with_content = sum(1 for i in all_items if i.content)
    with_exposure = sum(1 for i in all_items if i.exposure_count is not None)
    unanalyzed = sum(1 for i in all_items if i.analysis is None)

    return DataQualityResponse(
        last_synced_at=last_synced,
        items_fetched=items_fetched,
        items_new=items_new,
        items_duplicate=items_duplicate,
        items_rejected=items_rejected,
        items_pending_analysis=unanalyzed,
        items_with_full_content_pct=round(with_content / total_items * 100, 1) if total_items else 0.0,
        items_with_exposure_data_pct=round(with_exposure / total_items * 100, 1) if total_items else 0.0,
        sync_errors=errors,
    )
