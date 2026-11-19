import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.source_connection import SourceConnection
from app.schemas.source_connection import (
    SourceConnectionCreate,
    SourceConnectionOut,
    SourceConnectionUpdate,
)
from app.services.ingestion_service import run_ingestion

router = APIRouter(prefix="/api/sources", tags=["sources"])


@router.get("", response_model=list[SourceConnectionOut])
def list_sources(organization_id: uuid.UUID | None = None, db: Session = Depends(get_db)):
    stmt = select(SourceConnection)
    if organization_id:
        stmt = stmt.where(SourceConnection.organization_id == organization_id)
    return db.execute(stmt).scalars().all()


@router.post("", response_model=SourceConnectionOut)
def create_source(payload: SourceConnectionCreate, db: Session = Depends(get_db)):
    source = SourceConnection(**payload.model_dump())
    db.add(source)
    db.commit()
    db.refresh(source)
    return source


@router.patch("/{source_id}", response_model=SourceConnectionOut)
def update_source(source_id: uuid.UUID, payload: SourceConnectionUpdate, db: Session = Depends(get_db)):
    source = db.get(SourceConnection, source_id)
    if not source:
        raise HTTPException(404, "Source not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(source, key, value)
    db.commit()
    db.refresh(source)
    return source


@router.post("/{source_id}/sync")
def sync_source(source_id: uuid.UUID, db: Session = Depends(get_db)):
    """מפעיל סנכרון ל-Adapter הגנרי של ה-API (פועל כעת מול demo/csv/json;
    חיבור לספק ניטור אמיתי ידרוש רק עדכון config, לא שינוי קוד)."""
    source = db.get(SourceConnection, source_id)
    if not source:
        raise HTTPException(404, "Source not found")
    if source.source_type not in ("api_generic", "demo"):
        raise HTTPException(400, "Source type does not support manual sync; use /ingest endpoints for csv/json")
    run = run_ingestion(db, source)
    return {
        "ingestion_run_id": run.id,
        "status": run.status,
        "items_fetched": run.items_fetched,
        "items_new": run.items_new,
        "items_duplicate": run.items_duplicate,
        "items_rejected": run.items_rejected,
    }
