from dataclasses import dataclass, field
from datetime import datetime, timezone

from app.ai.mock_provider import MockAIProvider

PROFILE = {
    "direct_keywords": ["הרשות לאכיפה במקרקעין"],
    "indirect_keywords": ["צו הריסה"],
    "background_keywords": ["תכנון ובנייה"],
}


@dataclass
class FakeItem:
    title: str
    content: str | None = None
    summary: str | None = None
    outlet_name: str = "ynet"
    published_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    keywords: list[str] = field(default_factory=list)
    entities: list[str] = field(default_factory=list)


def test_direct_relevance_detected_by_keyword():
    provider = MockAIProvider()
    item = FakeItem(title="הרשות לאכיפה במקרקעין פעלה היום", content="תוכן")
    result = provider.analyze_item(item, PROFILE)
    assert result.relevance == "direct"


def test_not_relevant_when_no_keyword_matches():
    provider = MockAIProvider()
    item = FakeItem(title="פתיחת שנת הלימודים בעיר", content="חדשות קהילה")
    result = provider.analyze_item(item, PROFILE)
    assert result.relevance == "not_relevant"


def test_negative_sentiment_detected():
    provider = MockAIProvider()
    item = FakeItem(title="ביקורת על אוזלת יד בטיפול", content="כשל חריג בתהליך")
    result = provider.analyze_item(item, PROFILE)
    assert result.sentiment == "negative"


def test_insights_require_real_support_and_warn_on_small_sample():
    provider = MockAIProvider()
    current = [
        {"id": "1", "sentiment": "negative", "relevance": "direct", "keywords": ["צו הריסה"]},
        {"id": "2", "sentiment": "negative", "relevance": "direct", "keywords": ["צו הריסה"]},
        {"id": "3", "sentiment": "positive", "relevance": "indirect", "keywords": []},
    ]
    previous = [{"id": "p1", "sentiment": "neutral", "relevance": "direct", "keywords": []}]

    insights = provider.generate_period_insights(
        current, datetime(2026, 1, 1), datetime(2026, 1, 31), previous
    )
    levels = {i.level for i in insights}
    assert "descriptive" in levels
    comparative = next(i for i in insights if i.level == "comparative")
    assert "אין מספיק נתונים" in comparative.title
    for insight in insights:
        valid_ids = {item["id"] for item in current}
        assert all(sid in valid_ids for sid in insight.supporting_item_ids)
