"""מימוש AI מבוסס-כללים, דטרמיניסטי וללא תלות ברשת — משמש כברירת מחדל ל-MVP
וכ-fallback כשאין מפתח API לספק חיצוני. אינו ממציא נתונים: כל סיווג נובע
מתוכן הפריט עצמו, וכל תובנה מצטטת רק item_id-ים שהועברו בפועל."""

from collections import Counter
from datetime import datetime

from app.ai.base import AIProvider, ItemAnalysis, ItemLike, PeriodInsight

NEGATIVE_WORDS = [
    "כשל", "כישלון", "אוזלת יד", "בכיר", "ביקורת", "כותרת", "פגיעה", "נזק",
    "חריג", "אלימות", "שחיתות", "מחדל", "תלונה", "תביעה", "עיכוב", "התרשלות",
    "אפליה", "בררנית", "הפליה", "אסון", "פרשה", "חקירה",
]
POSITIVE_WORDS = [
    "הצלחה", "שיפור", "הישג", "שבח", "יעיל", "חדשנות", "שיתוף פעולה",
    "פתרון", "סיוע", "תרומה", "קידום", "שקיפות", "פריצת דרך", "שימור",
]
CRITICAL_STYLE_WORDS = ["ביקורת", "כשל", "מחדל", "חקירה", "פרשה"]
INVESTIGATIVE_WORDS = ["חקירה", "תחקיר", "חושף", "מתגלה"]
LEGAL_WORDS = ["בית משפט", "פסיקה", "צו", "תביעה", "עתירה"]
DISPUTE_WORDS = ["מחלוקת", "עימות", "מול", "נגד"]


SENTIMENT_LABEL_HE = {
    "positive": "חיובי",
    "negative": "שלילי",
    "neutral": "ניטרלי",
    "mixed": "מעורב",
}


def _text_of(item: ItemLike) -> str:
    return " ".join(filter(None, [item.title, item.summary, item.content]))


def _count_hits(text: str, words: list[str]) -> int:
    return sum(text.count(w) for w in words)


class MockAIProvider(AIProvider):
    name = "mock"

    def analyze_item(self, item: ItemLike, relevance_profile: dict) -> ItemAnalysis:
        text = _text_of(item)
        keyword_pool = set(item.keywords or []) | set(item.entities or [])

        direct_kw = set(relevance_profile.get("direct_keywords", []))
        indirect_kw = set(relevance_profile.get("indirect_keywords", []))
        background_kw = set(relevance_profile.get("background_keywords", []))

        direct_hits = len(keyword_pool & direct_kw) + _count_hits(text, list(direct_kw))
        indirect_hits = len(keyword_pool & indirect_kw) + _count_hits(text, list(indirect_kw))
        background_hits = len(keyword_pool & background_kw) + _count_hits(text, list(background_kw))

        if direct_hits > 0:
            relevance, rel_conf = "direct", min(0.6 + 0.1 * direct_hits, 0.97)
        elif indirect_hits > 0:
            relevance, rel_conf = "indirect", min(0.5 + 0.08 * indirect_hits, 0.9)
        elif background_hits > 0:
            relevance, rel_conf = "background", min(0.4 + 0.05 * background_hits, 0.8)
        else:
            relevance, rel_conf = "not_relevant", 0.65

        neg_hits = _count_hits(text, NEGATIVE_WORDS)
        pos_hits = _count_hits(text, POSITIVE_WORDS)
        if neg_hits > 0 and pos_hits > 0:
            sentiment, sent_conf = "mixed", 0.55
        elif neg_hits > pos_hits:
            sentiment, sent_conf = "negative", min(0.5 + 0.1 * neg_hits, 0.95)
        elif pos_hits > neg_hits:
            sentiment, sent_conf = "positive", min(0.5 + 0.1 * pos_hits, 0.95)
        else:
            sentiment, sent_conf = "neutral", 0.6

        if _count_hits(text, INVESTIGATIVE_WORDS) > 0:
            style = "investigative"
        elif _count_hits(text, CRITICAL_STYLE_WORDS) > 0:
            style = "critical"
        elif pos_hits > neg_hits and pos_hits > 0:
            style = "supportive"
        else:
            style = "factual"

        framing = []
        if _count_hits(text, LEGAL_WORDS) > 0:
            framing.append("legal_issue")
        if _count_hits(text, DISPUTE_WORDS) > 0:
            framing.append("confrontation")
        if neg_hits > 0 and "הארגון" not in text and relevance != "direct":
            framing.append("public_interest")
        if neg_hits > 0 and relevance == "direct":
            framing.append("organizational_failure")
        if pos_hits > 0 and relevance == "direct":
            framing.append("organizational_success")
        if not framing:
            framing.append("routine_activity")

        return ItemAnalysis(
            relevance=relevance,
            relevance_confidence=round(rel_conf, 2),
            sentiment=sentiment,
            sentiment_confidence=round(sent_conf, 2),
            coverage_style=style,
            framing=framing,
        )

    def generate_period_insights(
        self,
        items: list[dict],
        period_start: datetime,
        period_end: datetime,
        previous_period_items: list[dict],
    ) -> list[PeriodInsight]:
        insights: list[PeriodInsight] = []
        relevant = [i for i in items if i.get("relevance") != "not_relevant"]
        prev_relevant = [i for i in previous_period_items if i.get("relevance") != "not_relevant"]

        if not relevant:
            return insights

        total = len(relevant)
        prev_total = len(prev_relevant)

        # תיאורית
        sentiment_counts = Counter(i.get("sentiment") for i in relevant)
        top_sentiment, top_count = sentiment_counts.most_common(1)[0]
        insights.append(
            PeriodInsight(
                level="descriptive",
                title=f"{total} אזכורים רלוונטיים בתקופה הנבחרת",
                explanation=(
                    f"נקלטו {total} פרסומים רלוונטיים בתקופה שנבדקה, מתוכם "
                    f"{top_count} ({round(top_count/total*100)}%) בעלי סנטימנט "
                    f"{SENTIMENT_LABEL_HE.get(top_sentiment, top_sentiment)}."
                ),
                supporting_item_ids=[i["id"] for i in relevant[:10]],
                confidence=0.9,
            )
        )

        # השוואתית — רק אם יש בסיס השוואה סביר (לפחות 3 פריטים בתקופה הקודמת)
        if prev_total >= 3:
            change_pct = round((total - prev_total) / prev_total * 100)
            direction = "עלייה" if change_pct > 0 else ("ירידה" if change_pct < 0 else "ללא שינוי")
            insights.append(
                PeriodInsight(
                    level="comparative",
                    title=f"{direction} של {abs(change_pct)}% בהיקף הסיקור לעומת התקופה הקודמת",
                    explanation=(
                        f"בתקופה הקודמת נקלטו {prev_total} פרסומים רלוונטיים, לעומת {total} "
                        f"בתקופה הנוכחית — שינוי של {change_pct}%."
                    ),
                    supporting_item_ids=[i["id"] for i in relevant[:10]],
                    confidence=0.8,
                )
            )
        elif prev_total:
            insights.append(
                PeriodInsight(
                    level="comparative",
                    title="אין מספיק נתונים מהתקופה הקודמת להשוואה מובהקת",
                    explanation=(
                        f"בתקופה הקודמת נקלטו רק {prev_total} פרסומים רלוונטיים — מדגם קטן מכדי "
                        "לקבוע מגמה. יש להימנע מהצגת שינוי אחוזי כמובהק."
                    ),
                    supporting_item_ids=[],
                    confidence=0.95,
                )
            )

        # פרשנית — נושא/מילת מפתח דומיננטית בפריטים שליליים
        negative_items = [i for i in relevant if i.get("sentiment") == "negative"]
        if negative_items:
            kw_counter: Counter[str] = Counter()
            for i in negative_items:
                kw_counter.update(i.get("keywords") or [])
            if kw_counter:
                top_kw, kw_count = kw_counter.most_common(1)[0]
                supporting = [i["id"] for i in negative_items if top_kw in (i.get("keywords") or [])][:10]
                insights.append(
                    PeriodInsight(
                        level="interpretive",
                        title=f"הסיקור השלילי מתרכז סביב '{top_kw}'",
                        explanation=(
                            f"מתוך {len(negative_items)} פרסומים שליליים, {kw_count} קושרו למילת המפתח "
                            f"'{top_kw}' — ייתכן שמדובר באירוע או נרטיב ממוקד הדורש מעקב."
                        ),
                        supporting_item_ids=supporting,
                        confidence=0.65,
                    )
                )

        # אופרטיבית
        if negative_items and len(negative_items) / total > 0.3:
            insights.append(
                PeriodInsight(
                    level="operational",
                    title="מומלץ לבחון תגובה יזומה לסיקור השלילי",
                    explanation=(
                        f"{len(negative_items)} מתוך {total} פרסומים רלוונטיים ({round(len(negative_items)/total*100)}%) "
                        "נושאים סנטימנט שלילי. מומלץ לבחון מול הדובר אם נדרשת תגובה ציבורית ממוקדת."
                    ),
                    supporting_item_ids=[i["id"] for i in negative_items[:10]],
                    confidence=0.6,
                    recommendation="לקבוע עם הדובר האם להוציא תגובה או דף מסרים לנושא המרכזי שזוהה.",
                )
            )
        else:
            insights.append(
                PeriodInsight(
                    level="operational",
                    title="אין צורך בפעולה דחופה כעת",
                    explanation="שיעור הסיקור השלילי בתקופה זו אינו חריג, לפי הנתונים שנקלטו.",
                    supporting_item_ids=[i["id"] for i in relevant[:5]],
                    confidence=0.55,
                )
            )

        return insights
