import uuid

from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.ai.factory import get_ai_provider
from app.db.session import SessionLocal
from app.models.analysis_result import AnalysisResult
from app.models.media_item import MediaItem
from app.models.organization import Organization


def analyze_item_by_id(item_id: str) -> None:
    """מנתח פריט בודד ושומר/מעדכן AnalysisResult באופן אטומי (INSERT ... ON
    CONFLICT DO UPDATE). שתי שכבות עשויות לנתח את אותו פריט במקביל (תור הרקע
    וניתוח סינכרוני בזמן זריעת הדגמה) — upsert אטומי מונע race condition."""

    db = SessionLocal()
    try:
        item = db.get(MediaItem, item_id)
        if not item:
            return

        org = db.get(Organization, item.organization_id)
        relevance_profile = org.relevance_profile if org else {}

        provider = get_ai_provider()
        result = provider.analyze_item(item, relevance_profile)

        values = {
            "id": uuid.uuid4(),
            "media_item_id": item.id,
            "relevance": result.relevance,
            "relevance_confidence": result.relevance_confidence,
            "sentiment": result.sentiment,
            "sentiment_confidence": result.sentiment_confidence,
            "coverage_style": result.coverage_style,
            "framing": result.framing,
            "ai_provider": provider.name,
            "manually_corrected": False,
            "correction_notes": None,
        }
        stmt = pg_insert(AnalysisResult).values(**values)
        stmt = stmt.on_conflict_do_update(
            index_elements=[AnalysisResult.media_item_id],
            set_={
                "relevance": stmt.excluded.relevance,
                "relevance_confidence": stmt.excluded.relevance_confidence,
                "sentiment": stmt.excluded.sentiment,
                "sentiment_confidence": stmt.excluded.sentiment_confidence,
                "coverage_style": stmt.excluded.coverage_style,
                "framing": stmt.excluded.framing,
                "ai_provider": stmt.excluded.ai_provider,
                "manually_corrected": False,
                "correction_notes": None,
            },
        )
        db.execute(stmt)
        db.commit()
    finally:
        db.close()


def analyze_items_sync(item_ids: list[str]) -> None:
    """ניתוח סינכרוני (ללא תור) — שימושי לבדיקות ולזריעת נתוני הדגמה, כדי
    שהדשבורד יציג נתונים מסווגים באופן מיידי."""
    for item_id in item_ids:
        analyze_item_by_id(item_id)
