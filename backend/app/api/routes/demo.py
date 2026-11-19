from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.seed.seed_runner import seed_demo_data

router = APIRouter(prefix="/api/demo", tags=["demo"])


@router.post("/seed")
def seed_demo(db: Session = Depends(get_db)):
    """יוצר/מרענן ארגון הדגמה עם נתונים סינתטיים מסומנים כ-demo (סעיף 18)."""
    return seed_demo_data(db)
