#!/usr/bin/env bash
# פריסת Media Intelligence ל-Google Cloud: Cloud Run (backend + frontend) + Cloud SQL (Postgres).
#
# דרישות מוקדמות (על המחשב שממנו מריצים את הסקריפט, לא בסשן הזה):
#   1. gcloud CLI מותקן ומחובר:  gcloud auth login
#   2. פרויקט GCP עם billing מופעל.
#   3. Docker לא נדרש מקומית — הבנייה קורית ב-Cloud Build.
#
# שימוש:
#   PROJECT_ID=my-project ./gcp/deploy.sh
#
# הסקריפט אידמפוטנטי ברובו (אפשר להריץ שוב כדי לעדכן פריסה קיימת), אבל הוא
# יוצר משאבים בתשלום (Cloud SQL, Cloud Run, Artifact Registry) — בדקו תמחור
# לפני ההרצה: https://cloud.google.com/sql/pricing , https://cloud.google.com/run/pricing

set -euo pipefail

# ---- הגדרות — ערכו לפי הצורך ----
PROJECT_ID="${PROJECT_ID:?חובה להגדיר PROJECT_ID, לדוגמה: PROJECT_ID=my-project ./gcp/deploy.sh}"
REGION="${REGION:-me-west1}"
REPO_NAME="${REPO_NAME:-media-intelligence}"
SQL_INSTANCE="${SQL_INSTANCE:-media-intelligence-db}"
SQL_TIER="${SQL_TIER:-db-f1-micro}"
DB_NAME="${DB_NAME:-media_intelligence}"
DB_USER="${DB_USER:-media}"
BACKEND_SERVICE="${BACKEND_SERVICE:-media-intelligence-backend}"
FRONTEND_SERVICE="${FRONTEND_SERVICE:-media-intelligence-frontend}"
AI_PROVIDER="${AI_PROVIDER:-mock}"
ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY:-}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "== פרויקט: $PROJECT_ID | אזור: $REGION =="
gcloud config set project "$PROJECT_ID" >/dev/null

echo "== 1/8 הפעלת APIs נדרשים =="
gcloud services enable \
  run.googleapis.com \
  sqladmin.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  --project "$PROJECT_ID"

echo "== 2/8 Artifact Registry =="
if ! gcloud artifacts repositories describe "$REPO_NAME" --location="$REGION" >/dev/null 2>&1; then
  gcloud artifacts repositories create "$REPO_NAME" \
    --repository-format=docker --location="$REGION" \
    --description="Media Intelligence images"
else
  echo "קיים כבר, מדלג."
fi

IMAGE_BASE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}"

echo "== 3/8 Cloud SQL (Postgres) — זה עשוי לקחת כמה דקות בפעם הראשונה =="
if ! gcloud sql instances describe "$SQL_INSTANCE" >/dev/null 2>&1; then
  gcloud sql instances create "$SQL_INSTANCE" \
    --database-version=POSTGRES_16 \
    --tier="$SQL_TIER" \
    --region="$REGION" \
    --storage-size=10GB \
    --storage-auto-increase
else
  echo "קיים כבר, מדלג."
fi

CONNECTION_NAME="$(gcloud sql instances describe "$SQL_INSTANCE" --format='value(connectionName)')"

if ! gcloud sql databases describe "$DB_NAME" --instance="$SQL_INSTANCE" >/dev/null 2>&1; then
  gcloud sql databases create "$DB_NAME" --instance="$SQL_INSTANCE"
fi

if ! gcloud sql users list --instance="$SQL_INSTANCE" --format='value(name)' | grep -qx "$DB_USER"; then
  DB_PASSWORD="$(openssl rand -base64 24 | tr -dc 'A-Za-z0-9' | head -c 24)"
  gcloud sql users create "$DB_USER" --instance="$SQL_INSTANCE" --password="$DB_PASSWORD"
  echo "!! משתמש DB חדש נוצר. שמרו את הסיסמה הזו במקום בטוח — היא לא תוצג שוב:"
  echo "   DB_PASSWORD=$DB_PASSWORD"
else
  echo ">> המשתמש '$DB_USER' כבר קיים ב-Cloud SQL."
  echo ">> אם זו הרצה ראשונה בלבד על מופע קיים, ספקו את הסיסמה הקיימת:"
  read -r -s -p "   סיסמת DB_USER ($DB_USER): " DB_PASSWORD
  echo
fi

DATABASE_URL="postgresql+psycopg://${DB_USER}:${DB_PASSWORD}@/${DB_NAME}?host=/cloudsql/${CONNECTION_NAME}"

echo "== 4/8 בניית ודחיפת תמונת Backend (Cloud Build) =="
BACKEND_IMAGE="${IMAGE_BASE}/backend:latest"
gcloud builds submit "$REPO_ROOT/backend" --tag "$BACKEND_IMAGE"

echo "== 5/8 פריסת Backend ל-Cloud Run =="
BACKEND_ENV_VARS="DATABASE_URL=${DATABASE_URL},AI_PROVIDER=${AI_PROVIDER}"
if [ -n "$ANTHROPIC_API_KEY" ]; then
  BACKEND_ENV_VARS="${BACKEND_ENV_VARS},ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}"
fi

gcloud run deploy "$BACKEND_SERVICE" \
  --image="$BACKEND_IMAGE" \
  --region="$REGION" \
  --platform=managed \
  --allow-unauthenticated \
  --add-cloudsql-instances="$CONNECTION_NAME" \
  --set-env-vars="$BACKEND_ENV_VARS" \
  --port=8000

BACKEND_URL="$(gcloud run services describe "$BACKEND_SERVICE" --region="$REGION" --format='value(status.url)')"
echo ">> Backend חי בכתובת: $BACKEND_URL"

echo "== 6/8 עדכון CORS_ORIGINS ל-Backend (אחרי שנדע את כתובת ה-Frontend, שלב 8) =="
# בפעם הראשונה אין עדיין כתובת Frontend — נעדכן CORS בסוף הסקריפט (שלב 8).

echo "== 7/8 בניית ודחיפת תמונת Frontend (עם כתובת ה-Backend כ-build-arg) =="
FRONTEND_IMAGE="${IMAGE_BASE}/frontend:latest"
gcloud builds submit "$REPO_ROOT/frontend" \
  --config="$SCRIPT_DIR/cloudbuild.frontend.yaml" \
  --substitutions="_IMAGE=${FRONTEND_IMAGE},_API_URL=${BACKEND_URL}"

echo "== 8/8 פריסת Frontend ל-Cloud Run =="
gcloud run deploy "$FRONTEND_SERVICE" \
  --image="$FRONTEND_IMAGE" \
  --region="$REGION" \
  --platform=managed \
  --allow-unauthenticated \
  --set-env-vars="NEXT_PUBLIC_API_BASE_URL=${BACKEND_URL}" \
  --port=3000

FRONTEND_URL="$(gcloud run services describe "$FRONTEND_SERVICE" --region="$REGION" --format='value(status.url)')"

echo "== עדכון CORS_ORIGINS ב-Backend לכתובת ה-Frontend הסופית =="
gcloud run services update "$BACKEND_SERVICE" \
  --region="$REGION" \
  --set-env-vars="$(echo "$BACKEND_ENV_VARS" | sed "s|AI_PROVIDER=${AI_PROVIDER}|AI_PROVIDER=${AI_PROVIDER},CORS_ORIGINS=[\"${FRONTEND_URL}\"]|")"

cat <<EOF

== הפריסה הושלמה ==
Backend:  $BACKEND_URL
Frontend: $FRONTEND_URL

לאחר פתיחת ה-Frontend, לחצו "טען נתוני הדגמה" כדי לראות את הדשבורד בפעולה.

להוספת מפתח Anthropic מאוחר יותר:
  gcloud run services update $BACKEND_SERVICE --region $REGION \\
    --set-env-vars AI_PROVIDER=anthropic,ANTHROPIC_API_KEY=sk-ant-...
EOF
