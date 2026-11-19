"""נקודת ההחלפה של מודל ה-AI (סעיף 2 במפרט: 'ארכיטקטורה מודולרית... החלפת
ספק'). כל ספק AI (Mock, Anthropic, עתידי) חייב ליישם את ה-ABC הזה. אסור לכל
מימוש להמציא נתונים, ציטוטים או קשרים סיבתיים שלא נגזרים מה-items שהועברו לו."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol


class ItemLike(Protocol):
    id: str
    title: str
    content: str | None
    summary: str | None
    outlet_name: str
    published_at: datetime
    keywords: list[str]
    entities: list[str]


@dataclass
class ItemAnalysis:
    relevance: str  # direct | indirect | background | not_relevant
    relevance_confidence: float
    sentiment: str  # positive | negative | neutral | mixed
    sentiment_confidence: float
    coverage_style: str  # factual | critical | supportive | interpretive | investigative | polemic | sensational
    framing: list[str] = field(default_factory=list)


@dataclass
class PeriodInsight:
    level: str  # descriptive | comparative | interpretive | operational
    title: str
    explanation: str
    supporting_item_ids: list[str]
    confidence: float
    recommendation: str | None = None


class AIProvider(ABC):
    name: str = "base"

    @abstractmethod
    def analyze_item(self, item: ItemLike, relevance_profile: dict) -> ItemAnalysis:
        """מסווג פריט בודד: רלוונטיות, סנטימנט, אופי סיקור, מסגור."""
        raise NotImplementedError

    @abstractmethod
    def generate_period_insights(
        self,
        items: list[dict],
        period_start: datetime,
        period_end: datetime,
        previous_period_items: list[dict],
    ) -> list[PeriodInsight]:
        """מייצר תובנות ברמות: תיאורית/השוואתית/פרשנית/אופרטיבית, מבוססות רק
        על הפריטים שהתקבלו (items הם dict-ים כבר מסווגים, מה-DB)."""
        raise NotImplementedError
