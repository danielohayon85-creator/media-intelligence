"""חישוב KPI ומגמות לדשבורד. פריטים עם relevance == not_relevant לא נכללים
ב-KPI (סעיף 17: 'פריטים לא רלוונטיים לא ייכללו במדדי הסיקור הארגוני').
'פרסומים ייחודיים' סופר רק dedup_role == original, כדי לא לספור ציטוטים
חוזרים כסיפורים חדשים (סעיף 3)."""

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.analysis_result import AnalysisResult
from app.models.media_item import MediaItem


@dataclass
class ItemFilters:
    outlet_name: str | None = None
    media_type: str | None = None
    keyword: str | None = None
    sentiment: str | None = None
    search: str | None = None


def _base_query(organization_id, start: datetime, end: datetime, filters: ItemFilters | None = None):
    stmt = (
        select(MediaItem)
        .options(joinedload(MediaItem.analysis))
        .join(AnalysisResult, AnalysisResult.media_item_id == MediaItem.id, isouter=True)
        .where(
            MediaItem.organization_id == organization_id,
            MediaItem.published_at >= start,
            MediaItem.published_at <= end,
        )
    )
    if filters:
        if filters.outlet_name:
            stmt = stmt.where(MediaItem.outlet_name == filters.outlet_name)
        if filters.media_type:
            stmt = stmt.where(MediaItem.media_type == filters.media_type)
        if filters.keyword:
            stmt = stmt.where(MediaItem.keywords.any(filters.keyword))
        if filters.sentiment:
            stmt = stmt.where(AnalysisResult.sentiment == filters.sentiment)
        if filters.search:
            stmt = stmt.where(MediaItem.title.ilike(f"%{filters.search}%"))
    return stmt


def fetch_relevant_items(
    db: Session, organization_id, start: datetime, end: datetime, filters: ItemFilters | None = None
) -> list[MediaItem]:
    items = db.execute(_base_query(organization_id, start, end, filters)).unique().scalars().all()
    return [i for i in items if i.analysis and i.analysis.relevance != "not_relevant"]


def compute_kpis(current_items: list[MediaItem], previous_items: list[MediaItem]) -> dict:
    total = len(current_items)
    unique_pubs = sum(1 for i in current_items if i.dedup_role == "original")

    sentiment_counts: dict[str, int] = defaultdict(int)
    for i in current_items:
        if i.analysis:
            sentiment_counts[i.analysis.sentiment] += 1

    def pct(key: str) -> float:
        return round(sentiment_counts.get(key, 0) / total * 100, 1) if total else 0.0

    prev_total = len(previous_items)
    change_pct = None
    if prev_total >= 3:
        change_pct = round((total - prev_total) / prev_total * 100, 1)

    return {
        "total_mentions": total,
        "unique_publications": unique_pubs,
        "positive_pct": pct("positive"),
        "negative_pct": pct("negative"),
        "neutral_pct": pct("neutral"),
        "mixed_pct": pct("mixed"),
        "change_vs_previous_period_pct": change_pct,
    }


def compute_daily_trend(items: list[MediaItem]) -> list[dict]:
    buckets: dict[str, dict[str, int]] = defaultdict(lambda: {"positive": 0, "negative": 0, "neutral": 0, "mixed": 0})
    for i in items:
        if not i.analysis:
            continue
        day_key = i.published_at.date().isoformat()
        buckets[day_key][i.analysis.sentiment] += 1

    points = []
    for day_key in sorted(buckets.keys()):
        counts = buckets[day_key]
        points.append(
            {
                "bucket": day_key,
                **counts,
                "total": sum(counts.values()),
            }
        )
    return points
