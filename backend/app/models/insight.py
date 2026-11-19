import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, ForeignKey, Float, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID, ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Insight(Base):
    """תובנת AI באחת מ-4 הרמות (סעיף 12): תיאורית/השוואתית/פרשנית/אופרטיבית.
    supporting_item_ids מצביע לפריטים אמיתיים ב-DB — אסור שתהיה תובנה בלי
    עוגן נתוני אמת."""

    __tablename__ = "insights"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"))

    level: Mapped[str] = mapped_column(String(20))  # descriptive|comparative|interpretive|operational
    title: Mapped[str] = mapped_column(String(500))
    explanation: Mapped[str] = mapped_column(Text)
    supporting_item_ids: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    recommendation: Mapped[str | None] = mapped_column(Text, nullable=True)

    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    ai_provider: Mapped[str] = mapped_column(String(30))
    extra: Mapped[dict] = mapped_column(JSONB, default=dict)
