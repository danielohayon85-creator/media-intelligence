"""כל ספק ניטור (קיים או עתידי) מתחבר למערכת על ידי מימוש ה-ABC הזה בלבד.
זו שכבת הקליטה — מופרדת לגמרי מעיבוד (dedup), מניתוח (AI) ומהצגה (API/UI),
לפי העיקרון הארכיטקטוני בסעיף 2 במפרט."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class RawMediaItem:
    """פריט כפי שהתקבל מהמקור, לפני דה-דופ וניתוח — שומר את כל השדות
    הפוטנציאליים מסעיף 3 במפרט. שדות לא ידועים נשארים None ולא מומצאים."""

    external_id: str | None
    title: str
    content: str | None
    summary: str | None
    published_at: datetime
    outlet_name: str
    author_name: str | None
    media_type: str
    url: str | None
    keywords: list[str] = field(default_factory=list)
    entities: list[str] = field(default_factory=list)
    exposure_count: int | None = None
    engagement_count: int | None = None
    raw_payload: dict = field(default_factory=dict)


DEFAULT_FIELD_MAPPING = {
    "external_id": "external_id",
    "title": "title",
    "content": "content",
    "summary": "summary",
    "published_at": "published_at",
    "outlet_name": "outlet_name",
    "author_name": "author_name",
    "media_type": "media_type",
    "url": "url",
    "keywords": "keywords",
    "entities": "entities",
    "exposure_count": "exposure_count",
    "engagement_count": "engagement_count",
}


def map_record(record: dict, field_mapping: dict | None) -> RawMediaItem:
    """ממפה רשומת מקור גולמית (dict) ל-RawMediaItem לפי מיפוי שדות מוגדר
    (config.field_mapping) — כנדרש בסעיף 3: 'מיפוי שדות' כחלק מהגדרת ספק."""

    mapping = {**DEFAULT_FIELD_MAPPING, **(field_mapping or {})}

    def get(key: str):
        source_key = mapping.get(key)
        return record.get(source_key) if source_key else None

    published_raw = get("published_at")
    if isinstance(published_raw, str):
        published_at = datetime.fromisoformat(published_raw)
    elif isinstance(published_raw, datetime):
        published_at = published_raw
    else:
        published_at = datetime.utcnow()

    keywords_raw = get("keywords") or []
    if isinstance(keywords_raw, str):
        keywords_raw = [k.strip() for k in keywords_raw.split(",") if k.strip()]
    entities_raw = get("entities") or []
    if isinstance(entities_raw, str):
        entities_raw = [k.strip() for k in entities_raw.split(",") if k.strip()]

    return RawMediaItem(
        external_id=get("external_id"),
        title=get("title") or "",
        content=get("content"),
        summary=get("summary"),
        published_at=published_at,
        outlet_name=get("outlet_name") or "לא ידוע",
        author_name=get("author_name"),
        media_type=get("media_type") or "online",
        url=get("url"),
        keywords=list(keywords_raw),
        entities=list(entities_raw),
        exposure_count=get("exposure_count"),
        engagement_count=get("engagement_count"),
        raw_payload=record,
    )


class SourceAdapter(ABC):
    """config מגיע מ-SourceConnection.config ומכיל לפחות field_mapping; ספקים
    ספציפיים (כמו generic_api) מוסיפים endpoint/auth/filters."""

    source_type: str = "base"

    @abstractmethod
    def fetch(self, config: dict) -> list[RawMediaItem]:
        raise NotImplementedError
