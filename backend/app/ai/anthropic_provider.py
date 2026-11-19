"""מימוש AIProvider מול Claude API (Anthropic). לא מחובר למפתח אמיתי בשלב
הנוכחי — אם ANTHROPIC_API_KEY לא מוגדר, factory.py מחזיר MockAIProvider
במקום. הפרומפטים כאן מחייבים את המודל להחזיר JSON מבנה קבוע ולבסס כל מסקנה
רק על הטקסט שהועבר (ללא מידע כללי), כנדרש בסעיף 12 במפרט."""

import json
from datetime import datetime

from app.ai.base import AIProvider, ItemAnalysis, ItemLike, PeriodInsight
from app.ai.mock_provider import MockAIProvider
from app.core.config import settings

ITEM_ANALYSIS_SYSTEM_PROMPT = """את/ה מנוע ניתוח מודיעין תקשורתי. תקבל/י פריט תקשורתי אחד ופרופיל
רלוונטיות ארגוני. החזר/י אך ורק JSON תקין בפורמט הבא, ללא טקסט נוסף:
{"relevance": "direct|indirect|background|not_relevant", "relevance_confidence": 0.0-1.0,
 "sentiment": "positive|negative|neutral|mixed", "sentiment_confidence": 0.0-1.0,
 "coverage_style": "factual|critical|supportive|interpretive|investigative|polemic|sensational",
 "framing": ["..."]}
בסס/י את הסיווג רק על הטקסט שסופק. אין להמציא מידע שאינו בטקסט."""

INSIGHTS_SYSTEM_PROMPT = """את/ה מנוע תובנות מודיעין תקשורתי. תקבל/י רשימת פרסומים מסווגים
מהתקופה הנוכחית והתקופה הקודמת. הפק/י תובנות בארבע רמות בלבד: descriptive, comparative,
interpretive, operational. כל תובנה חייבת לכלול supporting_item_ids מתוך ה-id-ים שסופקו בלבד —
אסור לצטט id שלא קיים ברשימה. אם אין מספיק נתונים להשוואה (למשל מדגם קטן מ-3 בתקופה הקודמת),
ציינו זאת במפורש במקום לקבוע מגמה. החזר/י JSON: {"insights": [{"level":"...","title":"...",
"explanation":"...","supporting_item_ids":["..."],"confidence":0.0-1.0,"recommendation":"..."}]}"""


class AnthropicAIProvider(AIProvider):
    name = "anthropic"

    def __init__(self):
        from anthropic import Anthropic

        if not settings.anthropic_api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is not configured")
        self._client = Anthropic(api_key=settings.anthropic_api_key)
        self._model = settings.anthropic_model
        self._fallback = MockAIProvider()

    def _call_json(self, system: str, user_content: str) -> dict | None:
        try:
            resp = self._client.messages.create(
                model=self._model,
                max_tokens=1024,
                system=system,
                messages=[{"role": "user", "content": user_content}],
            )
            text = "".join(block.text for block in resp.content if block.type == "text")
            return json.loads(text)
        except Exception:
            return None

    def analyze_item(self, item: ItemLike, relevance_profile: dict) -> ItemAnalysis:
        payload = json.dumps(
            {
                "title": item.title,
                "summary": item.summary,
                "content": (item.content or "")[:4000],
                "outlet_name": item.outlet_name,
                "keywords": item.keywords,
                "entities": item.entities,
                "relevance_profile": relevance_profile,
            },
            ensure_ascii=False,
        )
        data = self._call_json(ITEM_ANALYSIS_SYSTEM_PROMPT, payload)
        if not data:
            return self._fallback.analyze_item(item, relevance_profile)
        try:
            return ItemAnalysis(
                relevance=data["relevance"],
                relevance_confidence=float(data["relevance_confidence"]),
                sentiment=data["sentiment"],
                sentiment_confidence=float(data["sentiment_confidence"]),
                coverage_style=data["coverage_style"],
                framing=list(data.get("framing", [])),
            )
        except (KeyError, ValueError, TypeError):
            return self._fallback.analyze_item(item, relevance_profile)

    def generate_period_insights(
        self,
        items: list[dict],
        period_start: datetime,
        period_end: datetime,
        previous_period_items: list[dict],
    ) -> list[PeriodInsight]:
        valid_ids = {i["id"] for i in items}
        payload = json.dumps(
            {
                "period_start": period_start.isoformat(),
                "period_end": period_end.isoformat(),
                "current_period_items": items,
                "previous_period_items": previous_period_items,
            },
            ensure_ascii=False,
        )
        data = self._call_json(INSIGHTS_SYSTEM_PROMPT, payload)
        if not data:
            return self._fallback.generate_period_insights(
                items, period_start, period_end, previous_period_items
            )
        insights: list[PeriodInsight] = []
        for raw in data.get("insights", []):
            try:
                supporting = [i for i in raw.get("supporting_item_ids", []) if i in valid_ids]
                insights.append(
                    PeriodInsight(
                        level=raw["level"],
                        title=raw["title"],
                        explanation=raw["explanation"],
                        supporting_item_ids=supporting,
                        confidence=float(raw.get("confidence", 0.5)),
                        recommendation=raw.get("recommendation"),
                    )
                )
            except (KeyError, ValueError, TypeError):
                continue
        return insights or self._fallback.generate_period_insights(
            items, period_start, period_end, previous_period_items
        )
