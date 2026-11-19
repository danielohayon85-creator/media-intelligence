import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.db.session import get_db
from app.models.analysis_result import AnalysisResult
from app.models.media_item import MediaItem
from app.schemas.media_item import AnalysisCorrection, MediaItemListResponse, MediaItemOut

router = APIRouter(prefix="/api/items", tags=["items"])


@router.get("", response_model=MediaItemListResponse)
def list_items(
    organization_id: uuid.UUID,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    outlet_name: str | None = None,
    media_type: str | None = None,
    sentiment: str | None = None,
    relevance: str | None = None,
    keyword: str | None = None,
    search: str | None = None,
    include_not_relevant: bool = False,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=200),
    db: Session = Depends(get_db),
):
    date_from = date_from or (datetime.now(timezone.utc) - timedelta(days=30))
    date_to = date_to or datetime.now(timezone.utc)

    stmt = (
        select(MediaItem)
        .options(joinedload(MediaItem.analysis))
        .join(AnalysisResult, AnalysisResult.media_item_id == MediaItem.id, isouter=True)
        .where(
            MediaItem.organization_id == organization_id,
            MediaItem.published_at >= date_from,
            MediaItem.published_at <= date_to,
        )
    )
    if outlet_name:
        stmt = stmt.where(MediaItem.outlet_name == outlet_name)
    if media_type:
        stmt = stmt.where(MediaItem.media_type == media_type)
    if sentiment:
        stmt = stmt.where(AnalysisResult.sentiment == sentiment)
    if relevance:
        stmt = stmt.where(AnalysisResult.relevance == relevance)
    if keyword:
        stmt = stmt.where(MediaItem.keywords.any(keyword))
    if search:
        stmt = stmt.where(MediaItem.title.ilike(f"%{search}%"))
    if not include_not_relevant:
        stmt = stmt.where(
            (AnalysisResult.relevance.is_(None)) | (AnalysisResult.relevance != "not_relevant")
        )

    all_items = db.execute(stmt.order_by(MediaItem.published_at.desc())).unique().scalars().all()
    total = len(all_items)
    start = (page - 1) * page_size
    page_items = all_items[start : start + page_size]

    return MediaItemListResponse(total=total, items=page_items)


@router.get("/{item_id}", response_model=MediaItemOut)
def get_item(item_id: uuid.UUID, db: Session = Depends(get_db)):
    item = db.execute(
        select(MediaItem).options(joinedload(MediaItem.analysis)).where(MediaItem.id == item_id)
    ).unique().scalar_one_or_none()
    if not item:
        raise HTTPException(404, "Item not found")
    return item


@router.patch("/{item_id}/analysis", response_model=MediaItemOut)
def correct_analysis(item_id: uuid.UUID, payload: AnalysisCorrection, db: Session = Depends(get_db)):
    """תיקון ידני לסיווג AI — מתועד (manually_corrected=True) כנדרש בסעיף 16."""
    item = db.execute(
        select(MediaItem).options(joinedload(MediaItem.analysis)).where(MediaItem.id == item_id)
    ).unique().scalar_one_or_none()
    if not item:
        raise HTTPException(404, "Item not found")
    if not item.analysis:
        raise HTTPException(409, "Item has not been analyzed yet")

    data = payload.model_dump(exclude_unset=True, exclude={"correction_notes"})
    for key, value in data.items():
        setattr(item.analysis, key, value)
    item.analysis.manually_corrected = True
    if payload.correction_notes:
        item.analysis.correction_notes = payload.correction_notes

    db.commit()
    db.refresh(item)
    return item
