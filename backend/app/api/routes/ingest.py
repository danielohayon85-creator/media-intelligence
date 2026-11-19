import json
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.source_connection import SourceConnection
from app.services.ingestion_service import run_ingestion

router = APIRouter(prefix="/api/ingest", tags=["ingest"])


def _get_source(db: Session, source_id: uuid.UUID) -> SourceConnection:
    source = db.get(SourceConnection, source_id)
    if not source:
        raise HTTPException(404, "Source not found")
    return source


@router.post("/csv")
async def ingest_csv(source_id: uuid.UUID, file: UploadFile = File(...), db: Session = Depends(get_db)):
    source = _get_source(db, source_id)
    if source.source_type != "csv":
        raise HTTPException(400, "Source is not configured as type 'csv'")
    file_bytes = await file.read()
    run = run_ingestion(db, source, extra_config={"file_bytes": file_bytes})
    return {
        "ingestion_run_id": run.id,
        "status": run.status,
        "items_fetched": run.items_fetched,
        "items_new": run.items_new,
        "items_duplicate": run.items_duplicate,
        "items_rejected": run.items_rejected,
        "errors": run.errors,
    }


@router.post("/json")
async def ingest_json(source_id: uuid.UUID, file: UploadFile = File(...), db: Session = Depends(get_db)):
    source = _get_source(db, source_id)
    if source.source_type != "json":
        raise HTTPException(400, "Source is not configured as type 'json'")
    file_bytes = await file.read()
    try:
        json.loads(file_bytes.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise HTTPException(400, f"Invalid JSON file: {exc}") from exc

    run = run_ingestion(db, source, extra_config={"file_bytes": file_bytes})
    return {
        "ingestion_run_id": run.id,
        "status": run.status,
        "items_fetched": run.items_fetched,
        "items_new": run.items_new,
        "items_duplicate": run.items_duplicate,
        "items_rejected": run.items_rejected,
        "errors": run.errors,
    }
