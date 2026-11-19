"""מחולל נתוני הדגמה סינתטיים בעברית, בפרופיל 'רשות לאכיפה במקרקעין' (סעיף 17
במפרט). הנתונים מסומנים במפורש כ-demo (SourceConnection.source_type == "demo")
ואינם מעורבבים עם נתוני אמת (סעיף 18). הפלט הוא רשימת dict-ים בפורמט הקנוני
הפנימי (ולכן DemoAdapter ממפה אותם בזהות) — כולל כפילויות/ציטוטים חוזרים
מכוונים כדי לתת תוכן אמיתי למנוע הדה-דופ."""

import hashlib
import random
from datetime import datetime, timedelta, timezone

RELEVANCE_PROFILE = {
    "direct_keywords": [
        "הרשות לאכיפה במקרקעין", "הרשות", "פקחי הרשות", "מפקחי אכיפה",
    ],
    "indirect_keywords": [
        "צו הריסה", "הריסת מבנה", "בנייה בלתי חוקית", "תפיסת כלים",
        "ועדה מקומית", "תיקון 116", "אכיפת חוק התכנון והבנייה",
    ],
    "background_keywords": [
        "תכנון ובנייה", "קרקעות חקלאיות", "שטחים פתוחים", "פרויקט תשתית לאומי",
    ],
}

OUTLETS = [
    ("ynet", "online"), ("וואלה! חדשות", "online"), ("כלכליסט", "online"),
    ("גלובס", "online"), ("הארץ", "online"), ("ישראל היום", "print"),
    ("מעריב", "print"), ("כאן חדשות", "tv"), ("גלי ישראל", "radio"),
    ("לוקאל - חדשות מקומיות", "online"), ("טוויטר - ערוץ אזרחי", "social"),
]

AUTHORS = [
    "רונית כהן", "אבי לוי", "מיכל ברק", "יוסי אזולאי", "דנה שחר",
    "עומר פרץ", "נועה גולן", "אריאל שמעוני",
]

LOCATIONS = [
    "בבקעת הירדן", "בנגב המערבי", "בגליל התחתון", "בשפלת יהודה",
    "באזור המשולש", "בחוף הכרמל", "בבקעת אונו", "בהר חברון",
    "בעמק יזרעאל", "בגליל העליון", "בשרון", "ברמת הגולן",
    "בערבה", "בהרי ירושלים", "בבקעת בית שאן", "בנגב המזרחי",
]

# תבניות כותרת/תוכן לפי נרטיב — מכוונות לתוכן ש-MockAIProvider יוכל לסווג בפועל
TEMPLATES = [
    {
        "key": "enforcement_success",
        "title": "הרשות לאכיפה במקרקעין פעלה להסרת {n} מבני בנייה בלתי חוקית {loc}",
        "body": (
            "במסגרת מבצע אכיפה מתוכנן, ביצעו פקחי הרשות לאכיפה במקרקעין צו הריסה ל-{n} "
            "מבנים שהוקמו ללא היתר {loc}. בהרשות מציינים כי הפעולה בוצעה בשיתוף פעולה עם "
            "המשטרה והוועדה המקומית לתכנון ובנייה, והיא חלק ממגמת שיפור באכיפת חוק התכנון והבנייה."
        ),
        "keywords": ["צו הריסה", "בנייה בלתי חוקית", "הרשות לאכיפה במקרקעין"],
        "sentiment_bias": "positive",
    },
    {
        "key": "selective_enforcement_criticism",
        "title": "טענות לאכיפה בררנית: תושבים {loc} מבקרים את הרשות לאכיפה במקרקעין",
        "body": (
            "תושבים {loc} מלינים על אכיפה בררנית מצד הרשות לאכיפה במקרקעין, לטענתם צווי ההריסה "
            "מופנים באופן לא שווה בין אוכלוסיות שונות. בביקורת שנחשפה עולה כי יש מחלוקת ציבורית "
            "סביב סדרי העדיפויות של הרשות. גורמים ברשות מכחישים את הטענות."
        ),
        "keywords": ["אכיפה בררנית", "הרשות לאכיפה במקרקעין", "ביקורת"],
        "sentiment_bias": "negative",
    },
    {
        "key": "general_illegal_building",
        "title": "בנייה בלתי חוקית {loc}: מבנה חדש הוקם ללא היתר",
        "body": (
            "תושבים {loc} דיווחו על מבנה שהוקם בסמוך לביתם ללא היתר בנייה. ועדה מקומית "
            "לתכנון ובנייה פתחה בבדיקה. אין עדות לכך שהרשות לאכיפה במקרקעין מעורבת בטיפול בשלב זה."
        ),
        "keywords": ["בנייה בלתי חוקית", "תכנון ובנייה"],
        "sentiment_bias": "neutral",
    },
    {
        "key": "court_ruling",
        "title": "בית המשפט אישר צו הריסה למבנה חקלאי {loc}",
        "body": (
            "בפסיקה שניתנה הבוקר, אישר בית המשפט המחוזי צו הריסה למבנה שהוקם על קרקעות חקלאיות "
            "{loc} בניגוד לחוק. הרשות לאכיפה במקרקעין תפעל לאכיפת הפסיקה בתוך 30 יום."
        ),
        "keywords": ["פסיקה", "צו הריסה", "קרקעות חקלאיות", "הרשות לאכיפה במקרקעין"],
        "sentiment_bias": "neutral",
    },
    {
        "key": "infrastructure_support",
        "title": "אכיפת הרשות לאכיפה במקרקעין מסירה חסם לפרויקט תשתית לאומי {loc}",
        "body": (
            "פעולת אכיפה של הרשות לאכיפה במקרקעין הסירה שימוש אסור במקרקעין שחסם את התקדמות "
            "פרויקט תשתית לאומי {loc}. בגורמי התשתיות מציינים כי שיתוף הפעולה עם הרשות תרם "
            "להתקדמות הפרויקט."
        ),
        "keywords": ["פרויקט תשתית לאומי", "הרשות לאכיפה במקרקעין", "שימושים אסורים במקרקעין"],
        "sentiment_bias": "positive",
    },
    {
        "key": "weak_enforcement_criticism",
        "title": "ביקורת: אוזלת יד של הרשות לאכיפה במקרקעין בטיפול בבנייה חקלאית {loc}",
        "body": (
            "דו\"ח ביקורת שהתפרסם מצביע על עיכוב משמעותי בטיפול הרשות לאכיפה במקרקעין בתיקי "
            "בנייה בלתי חוקית בקרקעות חקלאיות {loc}. בדו\"ח נטען כי מחדל באכיפה גרם לנזק לשטחים "
            "פתוחים. הרשות מסרה כי היא פועלת לשיפור תהליכי העבודה."
        ),
        "keywords": ["אוזלת יד", "הרשות לאכיפה במקרקעין", "קרקעות חקלאיות"],
        "sentiment_bias": "negative",
    },
    {
        "key": "vehicle_seizure",
        "title": "תפיסת כלים בפעולת אכיפה {loc}",
        "body": (
            "פקחי הרשות לאכיפה במקרקעין תפסו ציוד הנדסי שעשה שימוש אסור במקרקעין {loc}. "
            "בפעולה שבוצעה בשיתוף פעולה עם המשטרה לא נפצע איש."
        ),
        "keywords": ["תפיסת כלים", "הרשות לאכיפה במקרקעין", "שימושים אסורים במקרקעין"],
        "sentiment_bias": "neutral",
    },
    {
        "key": "irrelevant_local_news",
        "title": "פתיחת שנת הלימודים {loc}: אירועים ופעילויות לתלמידים",
        "body": (
            "ברשויות המקומיות {loc} נערכו אירועים חגיגיים לקראת פתיחת שנת הלימודים. אין קשר "
            "לנושאי תכנון ובנייה או אכיפת מקרקעין."
        ),
        "keywords": ["חינוך", "קהילה"],
        "sentiment_bias": "positive",
    },
]

SENTIMENT_WORD_BOOST = {
    "positive": ["שיפור", "הישג", "שיתוף פעולה", "תרומה"],
    "negative": ["מחדל", "ביקורת", "אוזלת יד", "עיכוב"],
    "neutral": [],
}


def _content_hash_seed(title: str, outlet: str, published_at: datetime) -> str:
    raw = f"{title}|{outlet}|{published_at.date().isoformat()}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]


def generate_demo_records(count: int = 200, seed: int = 42, days_back: int = 60) -> list[dict]:
    rng = random.Random(seed)
    now = datetime.now(timezone.utc)
    records: list[dict] = []

    base_items: list[dict] = []
    n_originals = max(1, int(count * 0.75))

    for i in range(n_originals):
        template = rng.choice(TEMPLATES)
        outlet_name, media_type = rng.choice(OUTLETS)
        author = rng.choice(AUTHORS)
        loc = rng.choice(LOCATIONS)
        n = rng.randint(2, 24)
        days_ago = rng.randint(0, days_back)
        hour = rng.randint(6, 22)
        published_at = now - timedelta(days=days_ago, hours=-hour)
        case_number = rng.randint(1000, 9999)

        title = template["title"].format(n=n, loc=loc)
        body = template["body"].format(n=n, loc=loc)
        body += f" (מספר תיק: {case_number})"
        boost_words = SENTIMENT_WORD_BOOST.get(template["sentiment_bias"], [])
        if boost_words and rng.random() < 0.6:
            body += " " + rng.choice(boost_words) + "."

        external_id = f"demo-{i}-{_content_hash_seed(title, outlet_name, published_at)}"

        item = {
            "external_id": external_id,
            "title": title,
            "content": body,
            "summary": body[:140],
            "published_at": published_at.isoformat(),
            "outlet_name": outlet_name,
            "author_name": author,
            "media_type": media_type,
            "url": f"https://example-media.test/{external_id}",
            "keywords": template["keywords"],
            "entities": [loc.replace("ב", "", 1) if loc.startswith("ב") else loc],
            "exposure_count": rng.randint(500, 50000) if rng.random() < 0.7 else None,
            "engagement_count": rng.randint(5, 2000) if rng.random() < 0.5 else None,
            "_template_key": template["key"],
            "_published_dt": published_at,
        }
        base_items.append(item)

    records.extend({k: v for k, v in item.items() if not k.startswith("_")} for item in base_items)

    # כפילויות/ציטוטים חוזרים מכוונים — אותו סיפור, כלי תקשורת אחר, זמן קרוב (reprint)
    n_reprints = count - n_originals
    for j in range(n_reprints):
        source_item = rng.choice(base_items)
        other_outlets = [o for o in OUTLETS if o[0] != source_item["outlet_name"]]
        outlet_name, media_type = rng.choice(other_outlets)
        reprint_delay_hours = rng.randint(1, 10)
        published_at = source_item["_published_dt"] + timedelta(hours=reprint_delay_hours)
        external_id = f"demo-reprint-{j}-{_content_hash_seed(source_item['title'], outlet_name, published_at)}"
        records.append(
            {
                "external_id": external_id,
                "title": source_item["title"],
                "content": source_item["content"],
                "summary": source_item["summary"],
                "published_at": published_at.isoformat(),
                "outlet_name": outlet_name,
                "author_name": rng.choice(AUTHORS),
                "media_type": media_type,
                "url": f"https://example-media.test/{external_id}",
                "keywords": source_item["keywords"],
                "entities": source_item["entities"],
                "exposure_count": rng.randint(200, 20000) if rng.random() < 0.5 else None,
                "engagement_count": None,
            }
        )

    return records
