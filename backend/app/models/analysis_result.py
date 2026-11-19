import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, ForeignKey, Float, Boolean, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AnalysisResult(Base):
    """תוצאות ניתוח AI לפריט, בטבלה נפרדת מנתוני המקור (לפי סעיף 3: 'יש לשמור
    את נתוני המקור ללא שינוי ולנהל בנפרד את תוצאות הניתוח'). ניתן לתקן ידנית
    (manually_corrected) ולתעד את ההחלטה — סעיף 16."""

    __tablename__ = "analysis_results"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    media_item_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("media_items.id"), unique=True)

    relevance: Mapped[str] = mapped_column(String(30))  # direct|indirect|background|not_relevant
    relevance_confidence: Mapped[float] = mapped_column(Float, default=0.0)

    sentiment: Mapped[str] = mapped_column(String(20))  # positive|negative|neutral|mixed
    sentiment_confidence: Mapped[float] = mapped_column(Float, default=0.0)

    coverage_style: Mapped[str] = mapped_column(String(30), default="factual")
    framing: Mapped[list[str]] = mapped_column(JSONB, default=list)

    ai_provider: Mapped[str] = mapped_column(String(30))
    analyzed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    manually_corrected: Mapped[bool] = mapped_column(Boolean, default=False)
    correction_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    media_item: Mapped["MediaItem"] = relationship("MediaItem", back_populates="analysis")
