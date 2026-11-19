from datetime import datetime

from sqlalchemy.orm import Session

from app.ai.factory import get_ai_provider
from app.models.insight import Insight
from app.models.media_item import MediaItem
from app.services.trend_service import fetch_relevant_items


def _to_dict(item: MediaItem) -> dict:
    return {
        "id": str(item.id),
        "title": item.title,
        "outlet_name": item.outlet_name,
        "sentiment": item.analysis.sentiment if item.analysis else None,
        "relevance": item.analysis.relevance if item.analysis else None,
        "keywords": item.keywords,
    }


def generate_and_store_insights(
    db: Session, organization_id, period_start: datetime, period_end: datetime
) -> list[Insight]:
    period_length = period_end - period_start
    previous_start = period_start - period_length
    previous_end = period_start

    current_items = fetch_relevant_items(db, organization_id, period_start, period_end)
    previous_items = fetch_relevant_items(db, organization_id, previous_start, previous_end)

    provider = get_ai_provider()
    raw_insights = provider.generate_period_insights(
        items=[_to_dict(i) for i in current_items],
        period_start=period_start,
        period_end=period_end,
        previous_period_items=[_to_dict(i) for i in previous_items],
    )

    stored: list[Insight] = []
    for raw in raw_insights:
        insight = Insight(
            organization_id=organization_id,
            level=raw.level,
            title=raw.title,
            explanation=raw.explanation,
            supporting_item_ids=raw.supporting_item_ids,
            confidence=raw.confidence,
            recommendation=raw.recommendation,
            period_start=period_start,
            period_end=period_end,
            ai_provider=provider.name,
        )
        db.add(insight)
        stored.append(insight)

    db.commit()
    return stored
