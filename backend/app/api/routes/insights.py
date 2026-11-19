import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.insight import Insight
from app.schemas.dashboard import InsightOut
from app.services.insight_service import generate_and_store_insights

router = APIRouter(prefix="/api/insights", tags=["insights"])


@router.get("", response_model=list[InsightOut])
def list_insights(
    organization_id: uuid.UUID,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    db: Session = Depends(get_db),
):
    date_to = date_to or datetime.now(timezone.utc)
    date_from = date_from or (date_to - timedelta(days=30))

    existing = db.execute(
        select(Insight)
        .where(
            Insight.organization_id == organization_id,
            Insight.period_start == date_from,
            Insight.period_end == date_to,
        )
        .order_by(Insight.generated_at.desc())
    ).scalars().all()

    if existing:
        return existing

    return generate_and_store_insights(db, organization_id, date_from, date_to)


@router.post("/refresh", response_model=list[InsightOut])
def refresh_insights(
    organization_id: uuid.UUID,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    db: Session = Depends(get_db),
):
    date_to = date_to or datetime.now(timezone.utc)
    date_from = date_from or (date_to - timedelta(days=30))
    return generate_and_store_insights(db, organization_id, date_from, date_to)
