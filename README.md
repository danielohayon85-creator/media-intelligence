# Media Intelligence — מערכת תובנות ומודיעין תקשורתי

מערכת SaaS לדוברים, יועצי תקשורת ומנהלי משברים, הקולטת פרסומים תקשורתיים,
מנתחת אותם באמצעות AI ומציגה תובנות מודיעיניות — לא רק נתונים כמותיים.

**שלב זה (שלב א' / MVP)** כולל: הקמת DB, יבוא CSV/JSON, Adapter גנרי ל-API,
קליטה ומניעת כפילויות, סיווג רלוונטיות וסנטימנט, דשבורד KPI, גרף מגמות, רשימת
פרסומים עם Drill-down, תובנות AI בסיסיות (4 רמות), וסינון לפי תקופה/מקור/נושא.
שלבים ב'-ג' (נרטיבים, מנוע התרעות, אפקטיביות דוברות, Chat with Your Media,
דוחות אוטומטיים) ייבנו בהמשך על גבי אותה ארכיטקטורה מודולרית.

## ארכיטקטורה

```
backend/   FastAPI + SQLAlchemy + PostgreSQL
  app/adapters/   שכבת קליטה: csv / json / api_generic / demo — כולן מיישמות
                  את אותו Adapter ABC, כך שחיבור ספק חדש הוא קונפיגורציה,
                  לא שינוי קוד.
  app/ai/         שכבת ניתוח AI: AIProvider ABC עם מימוש Mock (דטרמיניסטי,
                  מבוסס כללים) ומימוש Anthropic (Claude API). הבחירה ביניהם
                  נקבעת ב-env (AI_PROVIDER), ללא שינוי קוד בשאר המערכת.
  app/services/   דה-דופ, קליטה, מגמות, תובנות — כל אחד מופרד ובר-בדיקה.
  app/jobs/       תור עיבוד AI אסינכרוני (in-process); נקודת הרחבה ל-Redis/RQ.
  app/api/routes/ ה-API הפנימי שה-Frontend צורך.
  app/seed/       מחולל נתוני הדגמה סינתטיים (פרופיל "רשות לאכיפה במקרקעין").

frontend/  Next.js (App Router) + TypeScript + Tailwind CSS
  רכיבי UI בסגנון shadcn/ui (נבנו ידנית — ראו הערה למטה), RTL מלא, מצב
  בהיר/כהה, Recharts לגרפים.
```

### עקרון ההפרדה

קליטה ← עיבוד/דה-דופ ← ניתוח AI (דרך תור) ← הצגה. כל שכבה ניתנת להחלפה
בנפרד: ספק ניטור חדש = מחלקת Adapter חדשה; מודל AI אחר = מחלקת AIProvider
חדשה; מסד נתונים/תור אחר = שינוי בשכבת services/jobs בלבד.

### הערה לגבי shadcn/ui

ה-CLI הרשמי (`npx shadcn init`) דורש גישת רשת ל-`ui.shadcn.com` שלא הייתה
זמינה בסביבת הפיתוח שבה נבנה הפרויקט. רכיבי ה-UI תחת `frontend/components/ui`
נכתבו ידנית לפי אותה שיטת עבודה בדיוק (Tailwind + class-variance-authority +
Radix patterns) ומתנהגים זהה. אפשר להריץ את ה-CLI בהמשך כדי להוסיף רכיבים
נוספים מהקטלוג הרשמי.

## הרצה מקומית

### עם Docker Compose (הכי מהיר)

```bash
docker compose up --build
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000 (תיעוד אוטומטי: http://localhost:8000/docs)
- PostgreSQL: localhost:5432 (user/pass: media/media)

בפתיחה ראשונה אין נתונים — לחצו "טען נתוני הדגמה" במסך הראשי, או קראו
ל-`POST /api/demo/seed`.

### ידנית (ללא Docker)

```bash
# PostgreSQL מקומי צריך לרוץ, עם DB בשם media_intelligence ומשתמש media/media

cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # ערכו לפי הצורך
alembic upgrade head   # או: המערכת יוצרת טבלאות אוטומטית ב-startup
uvicorn app.main:app --reload

# בטרמינל נפרד
cd frontend
npm install
cp .env.local.example .env.local 2>/dev/null || echo 'NEXT_PUBLIC_API_BASE_URL=http://localhost:8000' > .env.local
npm run dev
```

## בדיקות

```bash
cd backend
# דרוש DB בדיקה נפרד: createdb media_intelligence_test
TEST_DATABASE_URL="postgresql+psycopg://media:media@localhost:5432/media_intelligence_test" \
  pytest tests/ -q
```

13 בדיקות: דה-דופ (כפילות מדויקת מול reprint מול follow_up), MockAIProvider
(סיווג רלוונטיות/סנטימנט, הגנה מפני מסקנות על מדגם קטן), וזרימת API מקצה
לקצה (זריעת הדגמה → דשבורד → תיקון ידני).

## חיבור ספק ניטור תקשורתי אמיתי

1. במסך **הגדרות וחיבורי API** צרו מקור חדש מסוג "API חיצוני".
2. הזינו את כתובת ה-endpoint, שיטת הזדהות (Bearer / API Key) והמפתח.
3. אם שמות השדות של הספק שונים מהשמות הפנימיים (title, content,
   published_at וכו'), עדכנו את `field_mapping` בקונפיגורציית המקור
   (כרגע דרך ה-API ישירות — `PATCH /api/sources/{id}`; ממשק ייעודי למיפוי
   שדות הוא הרחבה טבעית לשלב הבא).
4. לחצו "סנכרון עכשיו", או הגדירו תזמון חיצוני (cron) שקורא ל-
   `POST /api/sources/{id}/sync`.

הנתונים הסינתטיים (demo) לעולם לא מתערבבים עם נתונים אמיתיים — כל אחד
מסומן ברמת SourceConnection.source_type ו-Organization.is_demo.

## הפעלת AI אמיתי (Anthropic / Claude)

כברירת מחדל המערכת פועלת עם `MockAIProvider` — מנוע כללים דטרמיניסטי,
ללא תלות ברשת או במפתח API, כך שהמערכת עובדת מהקופסה.

כדי לעבור ל-Claude:

```bash
# backend/.env
AI_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-sonnet-5-5
```

אם המפתח לא מוגדר, המערכת נופלת אוטומטית חזרה ל-Mock (ראו
`app/ai/factory.py`). שני המימושים מיישמים את אותו Interface
(`app/ai/base.py`), כך שהחלפה בין ספקי AI נוספים בעתיד היא תוספת מחלקה
אחת בלבד.

## פריסה ל-Render

`render.yaml` מגדיר: מסד PostgreSQL מנוהל, שירות Web ל-Backend (כולל
`alembic upgrade head` בבנייה) ושירות Web ל-Frontend. לאחר `render blueprint
deploy` יש להזין את `ANTHROPIC_API_KEY` (אופציונלי) דרך לוח הבקרה של Render —
המשתנה מוגדר כ-`sync: false` ולכן לא נשמר בקובץ.

## מגבלות ידועות של שלב א' (ולאן ממשיכים בשלב ב')

- תור העיבוד הוא in-process (thread-based) — מתאים לנפח MVP; לעומס ייצור
  יש להחליף ל-Redis/RQ דרך `app/jobs/queue.py` בלבד.
- מיפוי שדות לספק API חיצוני נעשה כרגע דרך קריאת API ישירה; ממשק גרפי
  ייעודי הוא תוספת UI.
- אין עדיין: זיהוי נרטיבים, מנוע התרעות, ניתוח כלי תקשורת/כתבים, אפקטיביות
  דוברות, דוחות מתוזמנים, ו-Chat with Your Media — כולם מתוכננים לשלבים
  הבאים על גבי אותה ארכיטקטורה (ראו מבנה `app/services`, `app/ai`).
