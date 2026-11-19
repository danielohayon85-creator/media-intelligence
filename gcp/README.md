# פריסה ל-Google Cloud (Cloud Run + Cloud SQL)

הסקריפט `deploy.sh` בתיקייה הזו מריץ פריסה מלאה — הוא **לא** רץ מתוך הסשן הזה
(אין לסשן הזה חיבור מאומת ל-Google Cloud), אלא נועד להרצה על ידכם, במחשב או
ב-Cloud Shell שבו `gcloud` כבר מחובר לחשבון Google שלכם.

## לפני ההרצה

1. התקינו את [gcloud CLI](https://cloud.google.com/sdk/docs/install) (או פתחו
   [Cloud Shell](https://console.cloud.google.com/cloudshell) — gcloud שם כבר מותקן).
2. התחברו: `gcloud auth login`
3. ודאו שיש לכם פרויקט GCP עם **billing מופעל**. אם אין:
   `gcloud projects create my-media-intelligence && gcloud billing projects link my-media-intelligence --billing-account=XXXXXX-XXXXXX-XXXXXX`
4. שכפלו את הריפו (אם עוד לא):
   `git clone https://github.com/danielohayon85-creator/media-intelligence && cd media-intelligence`

## הרצה

```bash
PROJECT_ID=your-gcp-project-id REGION=me-west1 ./gcp/deploy.sh
```

משתני סביבה נוספים (אופציונליים, עם ברירות מחדל סבירות):

| משתנה | ברירת מחדל | הסבר |
|---|---|---|
| `REGION` | `me-west1` | אזור GCP (ישראל) |
| `SQL_TIER` | `db-f1-micro` | התוכנית הזולה ביותר ל-Cloud SQL |
| `AI_PROVIDER` | `mock` | `mock` או `anthropic` |
| `ANTHROPIC_API_KEY` | ריק | נדרש רק אם `AI_PROVIDER=anthropic` |

הסקריפט:
1. מפעיל את ה-APIs הנדרשים (Cloud Run, Cloud SQL, Artifact Registry, Cloud Build).
2. יוצר מאגר Artifact Registry לתמונות Docker.
3. יוצר מופע Cloud SQL (Postgres 16) + מסד נתונים + משתמש — **שומרים את
   הסיסמה שמודפסת למסוף, היא לא נשמרת ולא תוצג שוב.**
4. בונה את תמונת ה-Backend ב-Cloud Build ופורס אותה ל-Cloud Run, מחובר ל-Cloud SQL
   דרך Unix socket (`--add-cloudsql-instances`), ללא IP ציבורי למסד הנתונים.
5. בונה את תמונת ה-Frontend עם כתובת ה-Backend כ-build-arg (חובה ב-Next.js —
   המשתנה נצרב בזמן build, לא ניתן להזריק אותו רק כ-env var בזמן ריצה).
6. פורס את ה-Frontend ומעדכן את ה-Backend כך שה-CORS יאפשר רק את כתובת ה-Frontend.

בסיום תקבלו שתי כתובות `https://*.run.app` — פתחו את כתובת ה-Frontend,
ולחצו "טען נתוני הדגמה" כדי לראות את הדשבורד בפעולה.

## עלויות

כל המשאבים בתשלום (אין כאן free tier מובטח): Cloud Run גובה לפי שימוש בפועל
(סקייל-לאפס כשאין תעבורה — לרוב זול מאוד לדמו), Cloud SQL `db-f1-micro` גובה
גם כשאין תעבורה (סביב כמה דולרים בודדים לחודש). לפני הרצה כלכלית ארוכת-טווח
כדאי לבדוק תמחור עדכני:
https://cloud.google.com/run/pricing · https://cloud.google.com/sql/pricing

## הוספת מפתח Anthropic מאוחר יותר

```bash
gcloud run services update media-intelligence-backend --region $REGION \
  --set-env-vars AI_PROVIDER=anthropic,ANTHROPIC_API_KEY=sk-ant-...
```

## הרצה חוזרת / עדכון

הרצה חוזרת של `deploy.sh` עם אותם `PROJECT_ID`/`REGION` תבנה מחדש את
התמונות ותעדכן את שירותי ה-Cloud Run הקיימים (לא תיצור כפילויות של
Cloud SQL/Artifact Registry — הסקריפט בודק קיום לפני יצירה). זו הדרך
הפשוטה לפרוס גרסה מעודכנת אחרי שינויי קוד.

## ניקוי / מחיקת המשאבים

```bash
gcloud run services delete media-intelligence-backend --region $REGION
gcloud run services delete media-intelligence-frontend --region $REGION
gcloud sql instances delete media-intelligence-db
gcloud artifacts repositories delete media-intelligence --location $REGION
```
